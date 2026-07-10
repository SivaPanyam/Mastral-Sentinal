import asyncio
import os
import sys

# Setup path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import Base, engine, SessionLocal
from app.models import LogEntry
from app.services.event_pipeline import process_incoming_log

async def test_log_ingestion():
    # Ensure tables are created
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Plaintext log test
        plaintext_log = {
            "service": "billing-service",
            "message": "WARN User 1234 has insufficient funds for transaction.",
            "source": "test_script"
        }
        await process_incoming_log(db, plaintext_log)
        
        # 2. JSON log test
        json_log = {
            "service": "auth-service",
            "message": '{"time":"2023-10-24T12:00:00Z", "level":"INFO", "msg":"User logged in", "user_id":"999"}',
            "source": "test_script"
        }
        await process_incoming_log(db, json_log)
        
        # Verify in DB
        logs = db.query(LogEntry).filter(LogEntry.source == "test_script").all()
        print(f"Successfully retrieved {len(logs)} logs from database.")
        for log in logs:
            print(f"ID: {log.id}, Service: {log.service}, Severity: {log.severity}, Message: {log.message}, Metadata: {log.metadata_json}")
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_log_ingestion())
