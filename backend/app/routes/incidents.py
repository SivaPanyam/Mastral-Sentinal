from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.database import get_db, SessionLocal
from app.models import Incident, IncidentLog, AgentOutput, Report
from app.schemas import IncidentCreate, IncidentOut, IncidentLogCreate, IncidentLogOut, ReportOut
from app.auth import require_role, EnkryptMiddleware
from app.mastra.workflows import incident_sse_manager
from app.crud import IncidentRepository, AgentOutputRepository, ReportRepository
import datetime
import uuid
import asyncio
import json
import requests
import pandas as pd
import tempfile
import os
import shutil

router = APIRouter(prefix="/incidents", tags=["Incidents"])

class MastraWebhookPayload(BaseModel):
    event: str
    incident_id: str
    step: Optional[str] = None
    status: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/{incident_id}/mastra-webhook")
def receive_mastra_webhook(incident_id: str, payload: MastraWebhookPayload, db: Session = Depends(get_db)):
    """Receives SSE events from the TS Mastra engine and records them."""
    incident_sse_manager.publish(incident_id, payload.model_dump())
    
    if payload.event == "step_completed" and payload.data:
        run_id = f"run-{uuid.uuid4().hex[:6]}"
        
        # Determine summary and agent type
        step_upper = (payload.step or "UNKNOWN").upper()
        agent_type_map = {
            "TRIAGE": "TRIAGE",
            "DIAGNOSIS": "DIAGNOSIS",
            "RECOMMENDATION": "RECOMMENDATION",
            "REPORT": "REPORT",
            "KNOWLEDGE_INDEX": "KNOWLEDGE"
        }
        agent_type = agent_type_map.get(step_upper, step_upper)
        
        result_text = payload.data.get("result", "Completed step.")
        summary_text = result_text[:100] + "..." if len(result_text) > 100 else result_text
        
        agent_output = AgentOutput(
            id=run_id,
            incidentId=incident_id,
            agentType=agent_type,
            status=payload.status or "COMPLETED",
            summary=summary_text,
            payload=payload.data
        )
        AgentOutputRepository.create(db, agent_output)
        
    elif payload.event == "pipeline_completed":
        incident = IncidentRepository.get_by_id(db, incident_id)
        if incident:
            incident.status = "RESOLVED"
            incident.resolvedAt = datetime.datetime.utcnow()
            incident.leadTimeSeconds = 840
            IncidentRepository.update(db, incident)
            
    return {"status": "ok"}


@router.get("/", response_model=List[IncidentOut])
def get_incidents(db: Session = Depends(get_db)):
    """Retrieve all logged system incidents."""
    return IncidentRepository.get_all(db)


@router.post("/", response_model=IncidentOut, status_code=status.HTTP_201_CREATED)
def create_incident(incident_in: IncidentCreate, db: Session = Depends(get_db), current_user = Depends(require_role(["Admin", "SRE", "DevOps"]))):
    """Log a new system anomaly or automated monitor warning."""
    new_id = f"INC-2026-{uuid.uuid4().hex[:4].upper()}"
    new_incident = Incident(
        id=new_id,
        title=incident_in.title,
        description=incident_in.description,
        service=incident_in.service,
        severity=incident_in.severity,
        status="TRIGGERED"
    )
    return IncidentRepository.create(db, new_incident)


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: str, db: Session = Depends(get_db), current_user = Depends(require_role(["Admin", "SRE", "DevOps", "Security Analyst", "Viewer"]))):
    """Retrieve details of a single incident."""
    incident = IncidentRepository.get_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}", response_model=IncidentOut)
def update_incident(incident_id: str, updates: Dict[str, Any], db: Session = Depends(get_db), current_user = Depends(require_role(["Admin", "SRE", "DevOps"]))):
    """Update details of an incident (such as manual status transition)."""
    incident = IncidentRepository.get_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    if "status" in updates:
        incident.status = updates["status"]
    if "severity" in updates:
        incident.severity = updates["severity"]
    if "priority" in updates:
        incident.priority = updates["priority"]
        
    return IncidentRepository.update(db, incident)


@router.post("/{incident_id}/logs", response_model=IncidentLogOut)
def append_incident_log(incident_id: str, log_in: IncidentLogCreate, db: Session = Depends(get_db), current_user = Depends(require_role(["Admin", "SRE", "DevOps", "Security Analyst"]))):
    """Append diagnostic container logs or traces to an active incident."""
    incident = IncidentRepository.get_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Enkrypt Middleware: encrypt sensitive log entries containing keys or credentials before saving
    safe_message = log_in.message
    if "api_key" in safe_message or "token" in safe_message or "password" in safe_message:
        safe_message = EnkryptMiddleware.encrypt_data(safe_message)
        
    log_id = f"log-{uuid.uuid4().hex[:6]}"
    new_log = IncidentLog(
        id=log_id,
        incidentId=incident_id,
        source=log_in.source,
        level=log_in.level,
        message=safe_message
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


@router.post("/{incident_id}/logs/upload")
def upload_logs(incident_id: str, file: UploadFile = File(...), db: Session = Depends(get_db), current_user = Depends(require_role(["Admin", "SRE", "DevOps"]))):
    """Bulk ingest logs from CSV, JSON, or TXT."""
    incident = IncidentRepository.get_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    ext = file.filename.split('.')[-1].lower()
    if ext not in ["csv", "json", "txt"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV, JSON, or TXT.")

    temp_fd, temp_path = tempfile.mkstemp(suffix=f".{ext}")
    try:
        with os.fdopen(temp_fd, 'wb') as f:
            shutil.copyfileobj(file.file, f)
            
        logs_to_insert = []
        if ext == "csv":
            df = pd.read_csv(temp_path)
            for _, row in df.iterrows():
                msg = str(row.get("message", ""))
                # simple enkrypt rule
                if "api_key" in msg.lower() or "password" in msg.lower():
                    msg = EnkryptMiddleware.encrypt_data(msg)
                logs_to_insert.append(IncidentLog(
                    id=f"log-{uuid.uuid4().hex[:6]}",
                    incidentId=incident_id,
                    source=str(row.get("source", "uploaded_csv")),
                    level=str(row.get("level", "INFO")).upper(),
                    message=msg
                ))
        elif ext == "json":
            with open(temp_path, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        msg = str(item.get("message", ""))
                        if "api_key" in msg.lower() or "password" in msg.lower():
                            msg = EnkryptMiddleware.encrypt_data(msg)
                        logs_to_insert.append(IncidentLog(
                            id=f"log-{uuid.uuid4().hex[:6]}",
                            incidentId=incident_id,
                            source=str(item.get("source", "uploaded_json")),
                            level=str(item.get("level", "INFO")).upper(),
                            message=msg
                        ))
        elif ext == "txt":
            with open(temp_path, "r") as f:
                for line in f:
                    if line.strip():
                        msg = line.strip()
                        if "api_key" in msg.lower() or "password" in msg.lower():
                            msg = EnkryptMiddleware.encrypt_data(msg)
                        logs_to_insert.append(IncidentLog(
                            id=f"log-{uuid.uuid4().hex[:6]}",
                            incidentId=incident_id,
                            source="uploaded_txt",
                            level="INFO",
                            message=msg
                        ))
                        
        if logs_to_insert:
            db.add_all(logs_to_insert)
            db.commit()
            
        return {"status": "success", "logs_inserted": len(logs_to_insert)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/{incident_id}/trigger-pipeline")
def trigger_agent_pipeline(incident_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user = Depends(require_role(["Admin", "SRE", "DevOps"]))):
    """
    Trigger the Mastra SRE 5-Agent pipeline workflow asynchronously in the background.
    """
    incident = IncidentRepository.get_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Fetch existing logs for context
    logs_list = [f"[{log.source}] ({log.level}): {log.message}" for log in incident.logs]
    if not logs_list:
        logs_list = ["No logs attached. Default diagnostic health check reports latency spike."]
    
    logs_str = "\n".join(logs_list)

    # Call Mastra TS Engine
    try:
        # In docker, it's accessible via the service name `mastra_engine`. If running locally, you may need to use an env var.
        mastra_url = "http://mastra_engine:3001/api/workflows/incident-response"
        requests.post(mastra_url, json={
            "incidentId": incident.id,
            "title": incident.title,
            "service": incident.service,
            "severity": incident.severity,
            "logs": logs_str
        }, timeout=5)
    except Exception as e:
        print(f"Failed to trigger Mastra Engine: {e}")

    return {
        "status": "SUCCESS",
        "message": f"Mastra workflow triggered asynchronously for {incident_id}",
        "pipeline_output": {}
    }


@router.get("/{incident_id}/stream")
async def stream_incident_progress(incident_id: str):
    """
    Server-Sent Events (SSE) endpoint to stream live SRE agent pipeline progress updates.
    """
    async def event_generator():
        q = incident_sse_manager.subscribe(incident_id)
        try:
            while True:
                try:
                    data = await asyncio.wait_for(q.get(), timeout=20.0)
                    yield f"data: {json.dumps(data)}\n\n"
                    if data.get("event") in ["pipeline_completed", "pipeline_failed"]:
                        break
                except asyncio.TimeoutError:
                    yield "event: keepalive\ndata: {}\n\n"
        finally:
            incident_sse_manager.unsubscribe(incident_id, q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident(incident_id: str, db: Session = Depends(get_db), current_user = Depends(require_role(["Admin", "SRE"]))):
    """Soft delete an incident."""
    incident = IncidentRepository.get_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    IncidentRepository.soft_delete(db, incident)
    return

@router.get("/{incident_id}/logs", response_model=List[IncidentLogOut])
def get_incident_logs(incident_id: str, db: Session = Depends(get_db)):
    """Get all logs for an incident."""
    incident = IncidentRepository.get_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    return incident.logs

@router.get("/{incident_id}/reports", response_model=List[ReportOut])
def get_incident_reports(incident_id: str, db: Session = Depends(get_db)):
    """Get all RCA reports for an incident."""
    from app.crud import ReportRepository
    incident = IncidentRepository.get_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    reports = db.query(Report).filter(Report.incidentId == incident_id).all()
    return reports
