from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.database import get_db
from app.log_sources import log_manager

router = APIRouter(prefix="/ingestion", tags=["Data Ingestion"])

class IncomingLog(BaseModel):
    service: str = Field(..., description="Service name generating the log")
    level: str = Field(default="INFO", description="Log level (INFO, WARN, ERROR, CRITICAL)")
    message: str = Field(..., description="Raw log message")
    source: Optional[str] = "api_ingestion"
    component: Optional[str] = None
    host: Optional[str] = None
    container: Optional[str] = None
    namespace: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parsed_log: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

@router.post("/logs", status_code=202)
async def ingest_logs(logs: List[IncomingLog]):
    """
    Ultra-fast ingestion endpoint for incoming telemetry data.
    Pushes logs into the REST API Adapter queue for decoupled processing.
    """
    rest_adapter = log_manager.get_rest_adapter()
    accepted_count = 0
    
    for log in logs:
        success = await rest_adapter.push_log(log.model_dump())
        if success:
            accepted_count += 1
            
    return {"status": "accepted", "count": accepted_count, "total_received": len(logs)}

@router.get("/health", status_code=200)
async def get_ingestion_health():
    """
    Returns the real-time health and connection status of all configured log sources.
    """
    return log_manager.get_health()
