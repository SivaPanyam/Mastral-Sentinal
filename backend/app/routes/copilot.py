import re
import json
import time
import datetime
import uuid
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models import Incident, AgentOutput, Report, IncidentLog
from app.mastra.rag import rag_manager
from app.auth import EnkryptMiddleware, get_current_user
from app.crud import IncidentRepository, ReportRepository, AgentOutputRepository

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    incidentId: Optional[str] = None
    chatHistory: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    message: str
    referencedIncident: Optional[Dict[str, Any]] = None
    retrievedDocuments: List[Dict[str, Any]] = []
    guardrailStatus: Dict[str, Any] = {}

def extract_incident_ids(text: str) -> List[str]:
    """Helper to extract incident IDs matching the INC-XXXX pattern from text."""
    matches = re.findall(r"\b(INC-2026-\w+|INC-\w+)\b", text, re.IGNORECASE)
    return [m.upper() for m in matches]

@router.post("/chat", response_model=ChatResponse)
def copilot_chat(req: ChatRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Orchestrated enterprise AI Copilot Chat Endpoint.
    Classifies user intents, routes queries to specific backend CRUD repositories or Mastra agent workflows,
    and runs Enkrypt security guardrails.
    """
    user_query = req.message
    
    # 1. Enkrypt Input Validation
    input_scan = EnkryptMiddleware.validate_input(user_query)
    if input_scan["status"] == "ALERT":
        alert_msg = (
            "### 🛡️ Security Shield Alert\n\n"
            "The Enkrypt Input Guardrail has flagged your request due to potential security risks:\n"
        )
        for threat in input_scan["threats"]:
            alert_msg += f"- *{threat}*\n"
        alert_msg += "\n*This request has been blocked for compliance and security audit logs.*"
        
        return ChatResponse(
            message=alert_msg,
            referencedIncident=None,
            retrievedDocuments=[],
            guardrailStatus={
                "inputStatus": input_scan["status"],
                "inputThreats": input_scan["threats"],
                "outputStatus": "PASSED",
                "outputThreats": []
            }
        )

    # 2. Extract Incident context
    incident_context = None
    extracted_ids = extract_incident_ids(user_query)
    primary_id = req.incidentId or (extracted_ids[0] if extracted_ids else None)
    
    if primary_id:
        incident = IncidentRepository.get_by_id(db, primary_id)
        if incident:
            logs_summary = "\n".join([f"[{l.source}] ({l.level}): {l.message}" for l in incident.logs[:15]])
            rca_report = ReportRepository.get_by_incident_id(db, incident.id)
            agent_outputs = AgentOutputRepository.get_by_incident_id(db, incident.id)
            runs_summary = "\n".join([f"- {run.agentType}: {run.summary} (Status: {run.status})" for run in agent_outputs])
            
            incident_context = {
                "id": incident.id,
                "title": incident.title,
                "description": incident.description,
                "status": incident.status,
                "severity": incident.severity,
                "priority": getattr(incident, "priority", "HIGH"),
                "service": incident.service,
                "createdAt": incident.createdAt.isoformat() if incident.createdAt else None,
                "logs": logs_summary or "No logs available",
                "runs": runs_summary or "No agent execution runs recorded yet",
                "rca": {
                    "title": rca_report.title,
                    "summary": rca_report.summary,
                    "rootCause": rca_report.rootCause,
                    "impact": rca_report.impact
                } if rca_report else None
            }

    # 3. Intent Classification
    intent = "Operational Q&A"
    # Regex classifier fallback

    if intent == "Operational Q&A":
        lower_query = user_query.lower()
        if "explain" in lower_query or "diagnose" in lower_query or "what happened" in lower_query:
            intent = "Explain Incident"
        elif "search" in lower_query or "find" in lower_query or "runbook" in lower_query:
            intent = "Search Knowledge"
        elif "compare" in lower_query or "difference" in lower_query:
            intent = "Compare Incidents"
        elif "summarize" in lower_query or "rca" in lower_query or "post-mortem" in lower_query:
            intent = "Summarize Report"
        elif "trigger" in lower_query or "run pipeline" in lower_query or "remediate" in lower_query:
            intent = "Trigger Workflow"

    # 4. Route Intent Execution
    copilot_response = ""
    retrieved_docs = []

    if intent == "Explain Incident":
        if not primary_id:
            copilot_response = "Please provide the incident ID you would like me to explain (e.g., INC-2026-XXXX)."
        else:
            incident = IncidentRepository.get_by_id(db, primary_id)
            if not incident:
                copilot_response = f"Could not find incident with ID `{primary_id}` in PostgreSQL."
            else:
                logs_summary = "\n".join([f"[{l.source}] ({l.level}): {l.message}" for l in incident.logs[:15]])
                # Elegant static fallback response since diagnosis_agent has moved to TS
                copilot_response = (
                    f"### 🔍 Diagnostics for `{incident.id}`\n\n"
                    f"**Service**: `{incident.service}`\n"
                    f"**Severity**: `{incident.severity}`\n"
                    f"**Recent Logs ({len(incident.logs)} entries)**:\n"
                    f"```\n"
                    f"{logs_summary[:400]}...\n"
                    f"```\n"
                    f"*Mastra AI diagnostic reasoning is now handled asynchronously. Please use the 'Trigger Workflow' command to run the pipeline.*"
                )
                    copilot_response = (
                        f"### 🔍 Diagnostics for `{incident.id}` (Static Fallback)\n\n"
                        f"**Service**: `{incident.service}`\n"
                        f"**Severity**: `{incident.severity}`\n"
                        f"**Recent Logs ({len(incident.logs)} entries)**:\n"
                        f"```\n"
                        f"{logs_summary[:400]}...\n"
                        f"```\n"
                        f"*Provide a valid `GEMINI_API_KEY` to enable AI diagnostic reasoning.*"
                    )

    elif intent == "Search Knowledge":
        retrieved_docs = rag_manager.query_sop_runbooks(query=user_query, limit=3)
        if not retrieved_docs:
            copilot_response = "I searched the Qdrant vector index but found no matching SOP runbooks."
        else:
            copilot_response = "### 📖 Matching SOP Runbooks from Qdrant Index:\n\n"
            for doc in retrieved_docs:
                copilot_response += (
                    f"#### **{doc.get('title')}** (ID: `{doc.get('doc_id')}`)\n"
                    f"- **Service**: `{doc.get('service')}`\n"
                    f"- **Score**: `{doc.get('score', 0):.4f}`\n"
                    f"- **SOP Guidelines**:\n"
                    f"  *{doc.get('content')}*\n\n"
                )

    elif intent == "Compare Incidents":
        if len(extracted_ids) < 2:
            copilot_response = "To compare incidents, please specify at least two incident IDs (e.g., *'compare INC-2026-A and INC-2026-B'*)."
        else:
            inc1_id, inc2_id = extracted_ids[0], extracted_ids[1]
            inc1 = IncidentRepository.get_by_id(db, inc1_id)
            inc2 = IncidentRepository.get_by_id(db, inc2_id)
            
            if not inc1 or not inc2:
                copilot_response = f"Could not find both `{inc1_id}` and `{inc2_id}` in the database."
            else:
                prompt = (
                    f"Provide a technical comparative analysis between these two incidents:\n\n"
                    f"**Incident 1 (`{inc1.id}`):**\n"
                    f"- Title: {inc1.title}\n"
                    f"- Service: {inc1.service}\n"
                    f"- Status: {inc1.status}\n"
                    f"- Severity: {inc1.severity}\n\n"
                    f"**Incident 2 (`{inc2.id}`):**\n"
                    f"- Title: {inc2.title}\n"
                    f"- Service: {inc2.service}\n"
                    f"- Status: {inc2.status}\n"
                    f"- Severity: {inc2.severity}\n"
                )
                if gemini_service and gemini_service.client:
                    res = gemini_service.generate(prompt=prompt, system_instruction="You are an expert SRE comparing outages. Highlight similarities and anomalies.")
                    copilot_response = res.get("text", "")
                else:
                    copilot_response = (
                        f"### 📊 Comparative Analysis (Static Fallback)\n\n"
                        f"- **Incident 1 (`{inc1.id}`)**: {inc1.title} ({inc1.service}) - {inc1.severity}\n"
                        f"- **Incident 2 (`{inc2.id}`)**: {inc2.title} ({inc2.service}) - {inc2.severity}\n\n"
                        f"*Provide a valid `GEMINI_API_KEY` to enable AI comparative analysis.*"
                    )

    elif intent == "Summarize Report":
        if not primary_id:
            copilot_response = "Please provide the incident ID to summarize its RCA report (e.g., summarize report for INC-2026-XXXX)."
        else:
            report = ReportRepository.get_by_incident_id(db, primary_id)
            if not report:
                copilot_response = f"No RCA post-mortem report was found for incident `{primary_id}`. You may need to trigger the agent pipeline first."
            else:
                report_content = (
                    f"RCA Title: {report.title}\n"
                    f"Summary: {report.summary}\n"
                    f"Root Cause: {report.rootCause}\n"
                    f"Impact: {report.impact}\n"
                )
                copilot_response = f"### 📝 RCA Post-Mortem Summary for `{primary_id}`\n\n"
                if gemini_service and gemini_service.client:
                    copilot_response += gemini_service.summarize(report_content)
                else:
                    copilot_response += (
                        f"**RCA Summary**: {report.summary}\n\n"
                        f"**Root Cause**: {report.rootCause}\n\n"
                        f"**Impact**: {report.impact}\n\n"
                        f"*(Provide a valid `GEMINI_API_KEY` to generate a polished AI summary)*"
                    )

    elif intent == "Trigger Workflow":
        if not primary_id:
            copilot_response = "Please specify which incident ID to trigger the agent workflow for."
        else:
            incident = IncidentRepository.get_by_id(db, primary_id)
            if not incident:
                copilot_response = f"Could not find incident with ID `{primary_id}`."
            else:
                copilot_response = f"### ⚙️ Executing Agent Workflow Pipeline for `{primary_id}`...\n\n"
                try:
                    # Gather logs
                    logs_list = [f"[{log.source}] ({log.level}): {log.message}" for log in incident.logs]
                    if not logs_list:
                        logs_list = ["No logs attached. Default diagnostic health check reports latency spike."]

                    # Trigger workflow via Node Mastra Engine
                    try:
                        mastra_url = "http://mastra_engine:3001/api/workflows/incident-response"
                        requests.post(mastra_url, json={
                            "incidentId": incident.id,
                            "title": incident.title,
                            "service": incident.service,
                            "severity": incident.severity,
                            "logs": "\n".join(logs_list)
                        }, timeout=5)
                        copilot_response += "Pipeline has been successfully triggered. See the SSE stream for live updates."
                    except Exception as e:
                        copilot_response += f"Failed to trigger Mastra Engine: {e}"
                        
                except Exception as e:
                    copilot_response = f"❌ **Pipeline Execution Failed**: {str(e)}"

    else:
        # Operational Q&A
        retrieved_docs = rag_manager.query_sop_runbooks(query=user_query, limit=3)
        context = "\n".join([f"- Runbook '{d.get('title')}': {d.get('content')}" for d in retrieved_docs])
        prompt = (
            f"You are the elite SRE Copilot for Mastra Sentinel. Ground your answer strictly on the provided context.\n\n"
            f"Grounding context:\n{context}\n\n"
            f"User Question: {user_query}\n"
        )
        if gemini_service and gemini_service.client:
            res = gemini_service.generate(prompt=prompt, system_instruction="Provide a technical, elegant markdown answer grounded on context.")
            copilot_response = res.get("text", "")
        else:
            if retrieved_docs:
                copilot_response = (
                    f"### 📖 Grounded Knowledge Search (Fallback):\n\n"
                    f"{context}\n\n"
                    f"*Provide a valid `GEMINI_API_KEY` to enable AI operational chat generation.*"
                )
            else:
                copilot_response = f"I searched the knowledge index but found no SOP runbooks answering: '{user_query}'."

    # 5. Enkrypt Output Validation
    output_scan = EnkryptMiddleware.validate_output(copilot_response)

    return ChatResponse(
        message=copilot_response,
        referencedIncident=incident_context,
        retrievedDocuments=retrieved_docs,
        guardrailStatus={
            "inputStatus": input_scan["status"],
            "inputThreats": input_scan["threats"],
            "outputStatus": output_scan["status"],
            "outputThreats": output_scan["threats"]
        }
    )
