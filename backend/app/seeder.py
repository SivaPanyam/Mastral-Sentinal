from sqlalchemy.orm import Session
from app.models import User, Incident, KnowledgeSource, Metric
import uuid

def seed_users(db: Session, data: list):
    """Seed users."""
    for item in data:
        # Framework stub: expected to construct User objects and add to db
        pass
    db.commit()

def seed_incidents(db: Session, data: list):
    """Seed incidents and their logs."""
    for item in data:
        # Framework stub: expected to construct Incident objects and add to db
        pass
    db.commit()

def seed_knowledge(db: Session, data: list):
    """Seed knowledge base."""
    for item in data:
        # Framework stub: expected to construct KnowledgeSource objects and add to db
        pass
    db.commit()

def seed_metrics(db: Session, data: list):
    """Seed metrics."""
    for item in data:
        # Framework stub: expected to construct Metric objects and add to db
        pass
    db.commit()

def run_seeder(db: Session, seeder_type: str, data: list):
    """Main seeder entrypoint."""
    if seeder_type == "users":
        seed_users(db, data)
    elif seeder_type == "incidents":
        seed_incidents(db, data)
    elif seeder_type == "knowledge":
        seed_knowledge(db, data)
    elif seeder_type == "metrics":
        seed_metrics(db, data)
    else:
        raise ValueError(f"Invalid seeder type: {seeder_type}")
