from sqlalchemy.orm import Session
from app.models import User, Incident, IncidentLog, AgentOutput, Report, KnowledgeSource, AuditLog, Settings
from typing import List, Optional

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
        return db.query(Incident).filter(Incident.id == incident_id).first()

    @staticmethod
    def create(db: Session, incident: Incident) -> Incident:
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def update(db: Session, incident: Incident) -> Incident:
        db.add(incident)
        db.commit()
        db.refresh(incident)
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
