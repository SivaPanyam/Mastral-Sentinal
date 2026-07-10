import pandas as pd
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Incident, IncidentLog, KnowledgeSource
from app.mastra.rag import rag_manager
from typing import Dict, Any

class IncidentProcessor:
    def __init__(self, db: Session):
        self.db = db

    def process(self, file_path: str) -> Dict[str, Any]:
        stats = {"rows": 0, "inserted": 0, "skipped": 0, "errors": 0}
        try:
            df = pd.read_csv(file_path)
            for _, row in df.iterrows():
                stats["rows"] += 1
                try:
                    incident_id = str(row.get("Incident_ID"))
                    existing = self.db.query(Incident).filter(Incident.incident_number == incident_id).first()
                    if existing:
                        stats["skipped"] += 1
                        continue

                    # Mapping logic for it_incident_dataset.csv
                    priority_mapping = {"Low": "P3", "Medium": "P2", "High": "P1", "Critical": "P0"}
                    severity_mapping = {"Low": "LOW", "Medium": "MEDIUM", "High": "HIGH", "Critical": "CRITICAL"}
                    
                    priority = priority_mapping.get(row.get("Priority", "Medium"), "P2")
                    severity = severity_mapping.get(row.get("Priority", "Medium"), "MEDIUM")
                    status_raw = str(row.get("Status", "Closed")).upper()
                    if status_raw not in ['TRIGGERED','TRIAGED','DIAGNOSING','INVESTIGATING','MITIGATED','RESOLVED','CLOSED']:
                        status = "CLOSED" if "RESOLVED" in status_raw or "CLOSED" in status_raw else "RESOLVED"
                    else:
                        status = status_raw
                        
                    incident = Incident(
                        id=f"INC-2026-{uuid.uuid4().hex[:6].upper()}",
                        incident_number=incident_id,
                        title=f"{row.get('Incident_Type')} at {row.get('Location')}",
                        description=f"Incident reported by {row.get('Assigned_Department')}.",
                        severity=severity,
                        priority=priority,
                        service=str(row.get('Assigned_Department', 'Unknown')),
                        source="MANUAL",
                        status=status,
                        resolution=str(row.get('Resolution_Type')),
                        detectedAt=datetime.strptime(str(row.get('Reported_Time')), "%Y-%m-%d %H:%M:%S") if pd.notna(row.get('Reported_Time')) else datetime.utcnow(),
                        resolvedAt=datetime.strptime(str(row.get('Resolved_Time')), "%Y-%m-%d %H:%M:%S") if pd.notna(row.get('Resolved_Time')) else None,
                    )
                    
                    self.db.add(incident)
                    self.db.commit()
                    
                    # Store incident as knowledge for search
                    rag_metadata = {
                        "type": "POST_MORTEM",
                        "service": incident.service,
                        "incident_id": incident.id
                    }
                    content = f"Incident: {incident.title}\nDescription: {incident.description}\nResolution: {incident.resolution}"
                    rag_manager.index_document(
                        doc_id=incident.id,
                        title=incident.title,
                        content=content,
                        metadata=rag_metadata
                    )
                    
                    stats["inserted"] += 1
                except Exception as e:
                    self.db.rollback()
                    print(f"Error processing incident row: {e}")
                    stats["errors"] += 1
        except Exception as e:
            print(f"Failed to process file {file_path}: {e}")
        return stats

class LogProcessor:
    def __init__(self, db: Session):
        self.db = db

    def process(self, file_path: str) -> Dict[str, Any]:
        stats = {"rows": 0, "inserted": 0, "skipped": 0, "errors": 0}
        
        # Need a default incident to attach generic logs, or we just create one
        default_incident = self.db.query(Incident).filter(Incident.title == "Bulk Log Ingestion").first()
        if not default_incident:
            default_incident = Incident(
                id=f"INC-2026-LOGS-{uuid.uuid4().hex[:4].upper()}",
                incident_number=f"INC-LOGS",
                title="Bulk Log Ingestion",
                description="Default incident for unattached bulk logs.",
                service="system",
            )
            self.db.add(default_incident)
            self.db.commit()

        try:
            df = pd.read_csv(file_path)
            # Batch inserts for speed
            logs_to_insert = []
            
            for _, row in df.iterrows():
                stats["rows"] += 1
                try:
                    level = str(row.get("log_level", "INFO")).upper()
                    if level not in ["INFO", "WARN", "ERROR", "FATAL"]:
                        level = "INFO"
                        
                    log = IncidentLog(
                        id=f"LOG-{uuid.uuid4().hex[:8]}",
                        incidentId=default_incident.id,
                        timestamp=pd.to_datetime(row.get("timestamp")).to_pydatetime() if pd.notna(row.get("timestamp")) else datetime.utcnow(),
                        level=level,
                        service=str(row.get("pod_name", "unknown")),
                        namespace=str(row.get("namespace", "default")),
                        message=str(row.get("message", ""))
                    )
                    logs_to_insert.append(log)
                    stats["inserted"] += 1
                    
                    if len(logs_to_insert) >= 500:
                        self.db.bulk_save_objects(logs_to_insert)
                        self.db.commit()
                        logs_to_insert = []
                        
                except Exception as e:
                    print(f"Error processing log row: {e}")
                    stats["errors"] += 1
                    
            if logs_to_insert:
                self.db.bulk_save_objects(logs_to_insert)
                self.db.commit()
                
        except Exception as e:
            self.db.rollback()
            print(f"Failed to process file {file_path}: {e}")
        return stats

class KnowledgeProcessor:
    def __init__(self, db: Session):
        self.db = db

    def process(self, file_path: str) -> Dict[str, Any]:
        stats = {"rows": 1, "inserted": 0, "skipped": 0, "errors": 0}
        try:
            res = rag_manager.ingest_file(file_path)
            
            existing = self.db.query(KnowledgeSource).filter(KnowledgeSource.title == res["title"]).first()
            if existing:
                stats["skipped"] = 1
                return stats
                
            metadata = res["metadata"]
            
            ks = KnowledgeSource(
                id=res["doc_id"],
                title=res["title"],
                type=metadata.get("type", "WIKI"),
                source_path=file_path,
                checksum=res["content_hash"],
                content=res["content"],
                source_metadata=metadata
            )
            self.db.add(ks)
            self.db.commit()
            
            # Embed into Qdrant
            rag_manager.index_document(
                doc_id=ks.id,
                title=ks.title,
                content=ks.content,
                metadata=metadata
            )
            stats["inserted"] = 1
        except Exception as e:
            self.db.rollback()
            print(f"Failed to process knowledge {file_path}: {e}")
            stats["errors"] = 1
            
        return stats
