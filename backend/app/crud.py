from sqlalchemy.orm import Session
from app.models import User, Incident, IncidentLog, AgentOutput, Report, KnowledgeSource, AuditLog, Settings, LogEntry
from typing import List, Optional
from app.ws import broadcast_sync

class UserRepository:
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_all(db: Session) -> List[User]:
        return db.query(User).filter(User.deletedAt == None).all()

    @staticmethod
    def create(db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def soft_delete(db: Session, user: User) -> User:
        import datetime
        user.deletedAt = datetime.datetime.utcnow()
        db.add(user)
        db.commit()
        return user

class IncidentRepository:
    @staticmethod
    def get_all(db: Session) -> List[Incident]:
        return db.query(Incident).filter(Incident.deletedAt == None).order_by(Incident.createdAt.desc()).all()

    @staticmethod
    def get_by_id(db: Session, incident_id: str) -> Optional[Incident]:
        import uuid
        try:
            uuid.UUID(incident_id)
            return db.query(Incident).filter(Incident.id == incident_id).first()
        except ValueError:
            return db.query(Incident).filter(Incident.incident_number == incident_id).first()

    @staticmethod
    def create(db: Session, incident: Incident) -> Incident:
        db.add(incident)
        db.commit()
        db.refresh(incident)
        broadcast_sync("INCIDENT_CREATED", {
            "id": incident.id,
            "title": incident.title,
            "service": incident.service,
            "severity": incident.severity,
            "status": incident.status
        })
        return incident

    @staticmethod
    def create_or_update_incident(db: Session, incident_data: dict, log_record: IncidentLog) -> Incident:
        import uuid
        active_statuses = ["TRIGGERED", "TRIAGED", "DIAGNOSING", "INVESTIGATING", "MITIGATED"]
        
        # We try to find an existing active incident for this rule/service
        service_name = incident_data.get("service")
        # To avoid duplicate for same rule, we can store rule_id in tags or just use service and status.
        # Here we just use service and status to match previous heuristic.
        existing_incident = db.query(Incident).filter(
            Incident.service == service_name,
            Incident.status.in_(active_statuses)
        ).first()

        if existing_incident:
            # Append log to existing incident
            log_record.incidentId = existing_incident.id
            db.add(log_record)
            
            # Maybe bump severity if new log is CRITICAL and incident is HIGH
            if incident_data.get("severity") in ["CRITICAL", "FATAL"] and existing_incident.severity in ["MEDIUM", "LOW", "HIGH"]:
                existing_incident.severity = "CRITICAL"
                
            db.commit()
            db.refresh(existing_incident)
            db.refresh(log_record)
            broadcast_sync("INCIDENT_UPDATED", {
                "id": existing_incident.id,
                "title": existing_incident.title,
                "service": existing_incident.service,
                "severity": existing_incident.severity,
                "status": existing_incident.status
            })
            return existing_incident
        else:
            # Create new
            new_id = f"INC-2026-{uuid.uuid4().hex[:4].upper()}"
            
            rule_name = incident_data.get("rule_name", "Unknown Rule")
            affected_components = incident_data.get("affected_components", [])
            if not affected_components and service_name:
                affected_components = [service_name]
                
            new_incident = Incident(
                id=new_id,
                incident_number=f"INC{uuid.uuid4().hex[:6].upper()}",
                title=incident_data.get("title", f"Automated Detection: {service_name}"),
                description=incident_data.get("description", ""),
                service=service_name,
                severity=incident_data.get("severity", "MEDIUM"),
                status="TRIGGERED",
                source="DETECTION_ENGINE",
                affected_services=affected_components,
                tags={"rule_triggered": rule_name}
            )
            db.add(new_incident)
            db.commit()
            db.refresh(new_incident)
            
            log_record.incidentId = new_incident.id
            db.add(log_record)
            db.commit()
            db.refresh(log_record)
            broadcast_sync("INCIDENT_CREATED", {
                "id": new_incident.id,
                "title": new_incident.title,
                "service": new_incident.service,
                "severity": new_incident.severity,
                "status": new_incident.status
            })
            return new_incident

    @staticmethod
    def update(db: Session, incident: Incident) -> Incident:
        db.add(incident)
        db.commit()
        db.refresh(incident)
        broadcast_sync("INCIDENT_UPDATED", {
            "id": incident.id,
            "title": incident.title,
            "service": incident.service,
            "severity": incident.severity,
            "status": incident.status
        })
        return incident

    @staticmethod
    def soft_delete(db: Session, incident: Incident) -> Incident:
        import datetime
        incident.deletedAt = datetime.datetime.utcnow()
        db.add(incident)
        db.commit()
        return incident

class ReportRepository:
    @staticmethod
    def get_by_incident_id(db: Session, incident_id: str) -> Optional[Report]:
        return db.query(Report).filter(Report.incidentId == incident_id).first()

    @staticmethod
    def get_all(db: Session) -> List[Report]:
        return db.query(Report).order_by(Report.createdAt.desc()).all()

    @staticmethod
    def create(db: Session, report: Report) -> Report:
        db.add(report)
        db.commit()
        db.refresh(report)
        broadcast_sync("REPORT_GENERATED", {
            "id": report.id,
            "incidentId": report.incidentId,
            "title": report.title
        })
        return report

    @staticmethod
    def get_by_id(db: Session, report_id: str) -> Optional[Report]:
        return db.query(Report).filter(Report.id == report_id).first()

    @staticmethod
    def update(db: Session, report: Report) -> Report:
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def delete(db: Session, report: Report) -> None:
        db.delete(report)
        db.commit()

class AgentOutputRepository:
    @staticmethod
    def get_by_incident_id(db: Session, incident_id: str) -> List[AgentOutput]:
        return db.query(AgentOutput).filter(AgentOutput.incidentId == incident_id).order_by(AgentOutput.timestamp.asc()).all()

    @staticmethod
    def create(db: Session, agent_output: AgentOutput) -> AgentOutput:
        db.add(agent_output)
        db.commit()
        db.refresh(agent_output)
        return agent_output

    @staticmethod
    def delete_by_incident_id(db: Session, incident_id: str) -> None:
        db.query(AgentOutput).filter(AgentOutput.incidentId == incident_id).delete()
        db.commit()

    @staticmethod
    def get_by_id(db: Session, run_id: str) -> Optional[AgentOutput]:
        return db.query(AgentOutput).filter(AgentOutput.id == run_id).first()

class KnowledgeSourceRepository:
    @staticmethod
    def get_all(db: Session) -> List[KnowledgeSource]:
        return db.query(KnowledgeSource).all()

    @staticmethod
    def create(db: Session, source: KnowledgeSource) -> KnowledgeSource:
        db.add(source)
        db.commit()
        db.refresh(source)
        broadcast_sync("KNOWLEDGE_UPDATED", {
            "id": source.id,
            "title": source.title
        })
        return source

    @staticmethod
    def get_by_id(db: Session, document_id: str) -> Optional[KnowledgeSource]:
        return db.query(KnowledgeSource).filter(KnowledgeSource.id == document_id).first()

    @staticmethod
    def get_by_checksum(db: Session, checksum: str) -> Optional[KnowledgeSource]:
        return db.query(KnowledgeSource).filter(KnowledgeSource.checksum == checksum).first()

    @staticmethod
    def update(db: Session, source: KnowledgeSource) -> KnowledgeSource:
        db.add(source)
        db.commit()
        db.refresh(source)
        return source

    @staticmethod
    def delete(db: Session, source: KnowledgeSource) -> None:
        db.delete(source)
        db.commit()

class AuditLogRepository:
    @staticmethod
    def get_all(db: Session, limit: int = 100) -> List[AuditLog]:
        return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_by_user(db: Session, user_id: str, limit: int = 100) -> List[AuditLog]:
        return db.query(AuditLog).filter(AuditLog.userId == user_id).order_by(AuditLog.timestamp.desc()).limit(limit).all()

    @staticmethod
    def get_by_resource(db: Session, resource_id: str, limit: int = 100) -> List[AuditLog]:
        return db.query(AuditLog).filter(AuditLog.resourceId == resource_id).order_by(AuditLog.timestamp.desc()).limit(limit).all()

    @staticmethod
    def create(db: Session, audit_log: AuditLog) -> AuditLog:
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log

class SettingsRepository:
    @staticmethod
    def get_by_user_id(db: Session, user_id: str) -> Optional[Settings]:
        return db.query(Settings).filter(Settings.userId == user_id).first()

    @staticmethod
    def create(db: Session, settings: Settings) -> Settings:
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings

    @staticmethod
    def update(db: Session, settings: Settings) -> Settings:
        db.add(settings)
        db.commit()
        db.refresh(settings)
        return settings

class LogEntryRepository:
    @staticmethod
    def create(db: Session, log_entry: LogEntry) -> LogEntry:
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

