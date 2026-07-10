from arq import create_pool
from arq.connections import RedisSettings
from app.database import SessionLocal
from app.models import Incident, Report, AgentOutput
from app.crud import IncidentRepository
import os

# Define the Redis connection
redis_settings = RedisSettings(host=os.getenv("REDIS_HOST", "localhost"), port=6379)

async def _generate_lessons_learned_task(ctx, incident_id: str):
    """ARQ Background Task to index lessons learned into Qdrant."""
    db = SessionLocal()
    try:
        from app.mastra.rag import rag_manager
        incident = IncidentRepository.get_by_id(db, incident_id)
        if not incident:
            return
            
        reports = db.query(Report).filter(Report.incidentId == incident_id).all()
        outputs = db.query(AgentOutput).filter(AgentOutput.incidentId == incident_id).all()
        
        content = f"Incident: {incident.title}\nDescription: {incident.description}\n\n"
        if reports:
            content += "## RCA Reports\n"
            for r in reports:
                content += f"Summary: {r.summary}\n"
                
        if outputs:
            content += "## Agent Execution History\n"
            for o in outputs:
                content += f"- [{o.agentType}] {o.summary}\n"
                
        rag_manager.index_document(
            doc_id=f"KB-INCIDENT-{incident_id}",
            title=f"Lessons Learned: {incident.title}",
            content=content,
            metadata={"type": "POST_MORTEM", "service": incident.service, "author": "auto-pipeline"}
        )
        print(f"Successfully generated lessons learned for {incident_id}")
    except Exception as e:
        print(f"Failed to auto-generate knowledge for {incident_id}: {e}")
    finally:
        db.close()

class WorkerSettings:
    functions = [_generate_lessons_learned_task]
    redis_settings = redis_settings

async def get_arq_pool():
    return await create_pool(redis_settings)
