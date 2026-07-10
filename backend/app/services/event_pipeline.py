import uuid
import datetime
import requests
import asyncio
import logging
from sqlalchemy.orm import Session
from app.models import Incident, IncidentLog, LogEntry
from app.crud import IncidentRepository, LogEntryRepository
from app.ws import global_ws_manager
from app.auth import EnkryptMiddleware
from app.pipeline.normalizer import normalizer
from app.config import settings
from app.database import SessionLocal

logger = logging.getLogger(__name__)

async def process_incoming_log(db: Session, log_data: dict):
    """
    Core heuristic engine for Sprint 0.
    1. Redacts sensitive data.
    2. Normalizes log.
    3. Stores normalized log.
    4. Evaluates via DetectionEngine.
    """
    raw_message = log_data.get("message", "")
    
    # Redact sensitive data before normalization
    if "api_key" in raw_message.lower() or "password" in raw_message.lower() or "token" in raw_message.lower():
        raw_message = EnkryptMiddleware.encrypt_data(raw_message)
        
    normalized_log = normalizer.normalize(raw_message, log_data)
    
    # 0. Always store the normalized log generically
    generic_log = LogEntry(
        timestamp=normalized_log.timestamp,
        service=normalized_log.service,
        hostname=normalized_log.hostname,
        environment=normalized_log.environment,
        severity=normalized_log.severity,
        message=normalized_log.message,
        source=normalized_log.source,
        application=normalized_log.application,
        trace_id=normalized_log.trace_id,
        span_id=normalized_log.span_id,
        request_id=normalized_log.request_id,
        metadata_json=normalized_log.metadata,
        raw_log=normalized_log.raw_log
    )
    LogEntryRepository.create(db, generic_log)

    # 1. Run detection engine
    from app.detection.engine import detection_engine
    detection_engine.process_log(db, normalized_log)


async def trigger_mastra_workflow(incident: Incident, initial_log: IncidentLog):
    """
    Triggers the Mastra Node.js engine for AI diagnostic workflow.
    Implements robust error boundaries, background workers, and automated retries.
    """
    try:
        # Isolated DB session for background task
        db = SessionLocal()
        
        # Fetch historical incidents for this service (last 3 closed/resolved)
        historical_incidents = db.query(Incident).filter(
            Incident.service == incident.service,
            Incident.status.in_(["CLOSED", "RESOLVED"]),
            Incident.id != incident.id
        ).order_by(Incident.createdAt.desc()).limit(3).all()
        
        historical_data = []
        for hist in historical_incidents:
            historical_data.append({
                "id": hist.id,
                "title": hist.title,
                "resolution": hist.resolution,
                "root_cause": hist.root_cause
            })
            
        db.close()

        mastra_url = settings.MASTRA_ENGINE_URL
        
        logs_str = "No initial logs available."
        metadata = {}
        if initial_log:
             logs_str = f"[{initial_log.source}] ({initial_log.level}): {initial_log.message}"
             if initial_log.log_metadata:
                 metadata = initial_log.log_metadata

        payload = {
            "incidentId": incident.id,
            "title": incident.title,
            "service": incident.service,
            "severity": incident.severity,
            "logs": logs_str,
            "metadata": metadata,
            "historical_incidents": historical_data
        }
        
        # Robust Retry Logic with Exponential Backoff
        max_retries = settings.PIPELINE_MAX_RETRIES
        delay = settings.PIPELINE_RETRY_DELAY_SECONDS
        
        for attempt in range(1, max_retries + 1):
            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: requests.post(mastra_url, json=payload, timeout=10)
                )
                response.raise_for_status()
                logger.info(f"Successfully triggered Mastra workflow for Incident {incident.id}")
                return
            except requests.RequestException as e:
                logger.warning(f"Mastra trigger failed for {incident.id} (Attempt {attempt}/{max_retries}): {e}")
                if attempt == max_retries:
                    logger.error(f"Exhausted all retries for triggering Mastra workflow on Incident {incident.id}")
                    # Could update incident status here to 'ORCHESTRATION_FAILED' if required
                    break
                await asyncio.sleep(delay * attempt) # exponential backoff

    except Exception as e:
        logger.error(f"Critical failure in Mastra workflow trigger for Incident {incident.id}: {e}", exc_info=True)
