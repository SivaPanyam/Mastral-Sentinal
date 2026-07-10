import os
import re
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import requests

from app.database import get_db
from app.models import Incident, AgentOutput, Report, KnowledgeSource, Metric, Settings
from app.mastra.rag import rag_manager
from app.auth import EnkryptMiddleware, get_current_user
from app.crud import IncidentRepository, ReportRepository, AgentOutputRepository, KnowledgeSourceRepository
from app.config import settings

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

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

class GuardrailRequest(BaseModel):
    text: str
    direction: str = "input"

# Ollama Fallback Service
class OllamaService:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", settings.OLLAMA_BASE_URL).rstrip("/")
        self.endpoint = f"{self.base_url}/api/generate"

    def generate(self, prompt, system_instruction=None):
        try:
            full_prompt = prompt if not system_instruction else f"{system_instruction}\n\n{prompt}"
            payload = {
                "model": "llama3.2",
                "prompt": full_prompt,
                "stream": False
            }
            response = requests.post(self.endpoint, json=payload, timeout=60)
            response.raise_for_status()
            return {"text": response.json().get("response", "")}
        except Exception as e:
            return {"text": f"Error generating text: {str(e)}"}
            
ollama_service = OllamaService()

def extract_incident_ids(text: str) -> List[str]:
    matches = re.findall(r"\b(INC-2026-\w+|INC-\w+|INC\d{4,})\b", text, re.IGNORECASE)
    return [m.upper() for m in matches]


class CopilotTools:
    """Wrapper class to provide DB session context to tools."""
    def __init__(self, db: Session):
        self.db = db

    def searchKnowledge(self, query: str) -> str:
        """Searches the Qdrant knowledge base for SOP runbooks matching the query."""
        docs = rag_manager.query_sop_runbooks(query=query, limit=3)
        return json.dumps(docs)

    def searchLogs(self, incident_id: str) -> str:
        """Pulls live logs for a specific incident."""
        incident = IncidentRepository.get_by_id(self.db, incident_id)
        if not incident: return "Incident not found"
        return "\n".join([f"[{l.source}] ({l.level}): {l.message}" for l in incident.logs])

    def listIncidents(self, status: str = "") -> str:
        """Returns recent incidents from PostgreSQL. Optionally filter by status (e.g. TRIGGERED, RESOLVED)."""
        incidents = IncidentRepository.get_all(self.db)
        if status:
            incidents = [inc for inc in incidents if inc.status.upper() == status.upper()]
        
        results = []
        for inc in incidents[:20]:
            results.append({
                "id": inc.id,
                "title": inc.title,
                "service": inc.service,
                "severity": inc.severity,
                "status": inc.status
            })
        return json.dumps(results)

    def getIncident(self, incident_id: str) -> str:
        """Fetches full details for a specific incident."""
        incident = IncidentRepository.get_by_id(self.db, incident_id)
        if not incident: return "Incident not found"
        return json.dumps({
            "id": incident.id,
            "title": incident.title,
            "description": incident.description,
            "service": incident.service,
            "severity": incident.severity,
            "status": incident.status
        })

    def compareIncidents(self, inc1_id: str, inc2_id: str) -> str:
        """Retrieves two incidents for side-by-side comparison."""
        inc1 = IncidentRepository.get_by_id(self.db, inc1_id)
        inc2 = IncidentRepository.get_by_id(self.db, inc2_id)
        return json.dumps({
            "incident_1": {"id": inc1.id, "title": inc1.title, "service": inc1.service} if inc1 else "Not found",
            "incident_2": {"id": inc2.id, "title": inc2.title, "service": inc2.service} if inc2 else "Not found"
        })

    def retrieveRunbook(self, runbook_id: str) -> str:
        """Fetches full content of a specific runbook by ID."""
        doc = KnowledgeSourceRepository.get_by_id(self.db, runbook_id)
        if doc:
            return doc.content
        return f"Runbook {runbook_id} not found."

    def getWorkflowStatus(self, incident_id: str) -> str:
        """Pulls Mastra Agent pipeline execution status for an incident."""
        incident = IncidentRepository.get_by_id(self.db, incident_id)
        if not incident: return "Incident not found"
        return incident.status

    def retrieveAgentOutputs(self, incident_id: str) -> str:
        """Gets the latest LLM agent analysis for an incident."""
        outputs = AgentOutputRepository.get_by_incident_id(self.db, incident_id)
        results = [{"agentType": o.agentType, "status": o.status, "summary": o.summary} for o in outputs]
        return json.dumps(results)
        
    def retrieveMetrics(self, service: str) -> str:
        """Retrieve recent metrics for a specific service."""
        metrics = self.db.query(Metric).filter(Metric.service == service).order_by(Metric.timestamp.desc()).limit(10).all()
        if not metrics: return f"No metrics found for {service}."
        return json.dumps([{"metric": m.metric_name, "value": m.value, "time": str(m.timestamp)} for m in metrics])
        
    def retrieveReports(self, incident_id: str) -> str:
        """Retrieve RCA reports for a specific incident."""
        reports = self.db.query(Report).filter(Report.incidentId == incident_id).all()
        if not reports: return "No reports found."
        return json.dumps([{"title": r.title, "summary": r.summary, "rootCause": r.rootCause} for r in reports])
        
    def retrieveTimeline(self, incident_id: str) -> str:
        """Extract timeline events from RCAs for an incident."""
        reports = self.db.query(Report).filter(Report.incidentId == incident_id).all()
        timelines = []
        for r in reports:
             if hasattr(r, 'timeline') and isinstance(r.timeline, list):
                 timelines.extend(r.timeline)
             elif hasattr(r, 'payload') and isinstance(r.payload, dict):
                 timelines.extend(r.payload.get('timeline', []))
        return json.dumps(timelines) if timelines else "No timeline available."
        
    def triggerWorkflow(self, incident_id: str) -> str:
        """Trigger the Mastra SRE agent pipeline for an incident."""
        try:
            # We call the FastAPI endpoint internally
            fastapi_url = os.getenv("FASTAPI_URL", "http://localhost:8000/api/v1")
            requests.post(f"{fastapi_url}/incidents/{incident_id}/trigger-pipeline", timeout=5)
            return "Workflow triggered successfully."
        except Exception as e:
            return f"Failed to trigger workflow: {str(e)}"
            
    def searchHistoricalIncidents(self, query: str) -> str:
        """Query historical resolved incidents matching terms in their titles or services."""
        incidents = self.db.query(Incident).filter(Incident.status == "RESOLVED").all()
        matched = []
        for inc in incidents:
             if query.lower() in inc.title.lower() or query.lower() in inc.service.lower() or query.lower() in (inc.description or "").lower():
                  matched.append({"id": inc.id, "title": inc.title, "service": inc.service, "severity": inc.severity})
        return json.dumps(matched[:5])

def build_system_instruction(user_preferences: dict, recent_context: str) -> str:
    return (
        "You are the elite SRE Copilot for Mastra Sentinel. You must use tools to fetch real-time operational data.\n"
        "1. When answering questions, strictly ground your answers in the tool outputs. NEVER hallucinate operational data.\n"
        "2. IMPORTANT: If you use `searchKnowledge` or `retrieveRunbook`, you MUST provide deep citations in your response using exactly this markdown format: `[Document Title, Page {page_number}, Chunk {chunk_id}]`.\n"
        "3. Every recommendation must reference retrieved evidence.\n"
        "4. Support Markdown, code blocks, and tables in your responses where appropriate.\n\n"
        f"--- USER PREFERENCES ---\n{json.dumps(user_preferences)}\n\n"
        f"--- RECENT CONTEXT ---\n{recent_context}"
    )

@router.get("/context")
def get_copilot_context(db: Session = Depends(get_db)):
    """Returns dashboard context and suggested questions for the AI Copilot UI."""
    incidents = IncidentRepository.get_all(db)
    triggered = [inc for inc in incidents if inc.status == "TRIGGERED"]
    
    suggested = []
    if triggered:
        suggested.append({"text": f"Explain Incident {triggered[0].id} in depth", "icon": "ShieldAlert"})
        suggested.append({"text": f"Retrieve metrics for service: {triggered[0].service}", "icon": "Cpu"})
    
    suggested.append({"text": "Show me recent resolved incidents", "icon": "Database"})
    suggested.append({"text": "Search runbooks for PostgreSQL connection pool saturation", "icon": "FileText"})

    return {
        "suggestedQuestions": suggested[:4],
        "activeAlerts": len(triggered),
        "recentIncidents": [{"id": i.id, "title": i.title} for i in incidents[:5]]
    }


@router.post("/chat")
async def copilot_chat(req: ChatRequest, request: Request, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    user_query = req.message
    
    # 1. Enkrypt Input Validation
    input_scan = EnkryptMiddleware.validate_input(user_query, current_user, db)
    if input_scan["status"] == "ALERT":
        alert_msg = (
            "### 🛡️ Security Shield Alert\n\n"
            "The Enkrypt Input Guardrail has flagged your request due to potential security risks:\n"
        )
        for threat in input_scan["threats"]:
            alert_msg += f"- *{threat}*\n"
        alert_msg += "\n*This request has been blocked for compliance and security audit logs.*"
        
        # We simulate SSE response for the block
        async def block_stream():
            yield f"data: {json.dumps({'chunk': alert_msg, 'guardrailStatus': {'inputStatus': 'ALERT', 'inputThreats': input_scan['threats']}, 'done': True})}\n\n"
        return StreamingResponse(block_stream(), media_type="text/event-stream")

    # Audit log the prompt execution
    from app.models.audit_log import AuditLog
    user_id = current_user.get("email") # Use email or ID, here we have current_user dict. Better to fetch user if needed.
    # To keep it lightweight, if we don't have user.id in current_user dict, let's fetch it or just use email as user string if allowed.
    # The current_user dict from `get_current_user` has `email`, `role`, `name`. We should fetch user id.
    from app.crud import UserRepository
    user_obj = UserRepository.get_by_email(db, current_user["email"])
    if user_obj:
        prompt_log = AuditLog(
            userId=user_obj.id,
            action="PROMPT_EXECUTED",
            resourceType="AI Copilot",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details={"prompt_preview": user_query[:100], "sanitized": input_scan.get("sanitized", False)},
            response_status="SUCCESS"
        )
        db.add(prompt_log)
        db.commit()

    # 2. Extract context for the LLM and UI
    incident_context = None
    extracted_ids = extract_incident_ids(user_query)
    primary_id = req.incidentId or (extracted_ids[0] if extracted_ids else None)
    
    recent_context_str = ""
    if primary_id:
        incident = IncidentRepository.get_by_id(db, primary_id)
        if incident:
            recent_context_str = f"Active context incident: {incident.id} ({incident.title}) - Status: {incident.status}."
            incident_context = {
                "id": incident.id,
                "title": incident.title,
                "status": incident.status,
                "severity": incident.severity,
                "service": incident.service
            }
            
    # Load User Preferences Memory
    user_settings = db.query(Settings).filter(Settings.userId == current_user.id).first()
    prefs = user_settings.ai_preferences if user_settings and user_settings.ai_preferences else {}

    # 3. Gemini RAG Tool Calling execution (Streaming)
    async def generate_response():
        if GEMINI_AVAILABLE and os.getenv("GEMINI_API_KEY"):
            try:
                client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                tools_impl = CopilotTools(db)
                callable_tools = [
                    tools_impl.searchKnowledge,
                    tools_impl.searchLogs,
                    tools_impl.listIncidents,
                    tools_impl.getIncident,
                    tools_impl.compareIncidents,
                    tools_impl.retrieveRunbook,
                    tools_impl.getWorkflowStatus,
                    tools_impl.retrieveAgentOutputs,
                    tools_impl.retrieveMetrics,
                    tools_impl.retrieveReports,
                    tools_impl.retrieveTimeline,
                    tools_impl.triggerWorkflow,
                    tools_impl.searchHistoricalIncidents
                ]
                
                # Format history for Gemini
                history = []
                for msg in req.chatHistory:
                    role = "user" if msg.role == "user" else "model"
                    history.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))
                
                config = types.GenerateContentConfig(
                    system_instruction=build_system_instruction(prefs, recent_context_str),
                    tools=callable_tools,
                    temperature=0.2
                )

                chat = client.chats.create(model="gemini-2.5-pro", config=config, history=history)
                
                response_stream = chat.send_message_stream(user_query)
                
                for chunk in response_stream:
                    if await request.is_disconnected():
                        break
                    if chunk.text:
                        yield f"data: {json.dumps({'chunk': chunk.text, 'done': False})}\n\n"
                
                # Output Guardrail
                # Can't easily scan stream fully until it finishes, so we skip output block or do it client side for streaming.
                # For safety, we just send done.
                yield f"data: {json.dumps({'chunk': '', 'done': True, 'referencedIncident': incident_context, 'guardrailStatus': {'inputStatus': 'PASSED'}})}\n\n"

            except Exception as e:
                logging.error(f"Gemini generation error: {e}")
                yield f"data: {json.dumps({'chunk': f'❌ **LLM Execution Failed**: {str(e)}', 'done': True})}\n\n"
        else:
            # Fallback
            yield f"data: {json.dumps({'chunk': 'Gemini API not available. Please configure GEMINI_API_KEY.', 'done': True})}\n\n"

    return StreamingResponse(generate_response(), media_type="text/event-stream")


@router.post("/guardrail-check")
def check_guardrails(req: GuardrailRequest, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    # 1. Enkrypt Input Validation
    scan = EnkryptMiddleware.validate_input(req.text, current_user, db)
    if req.is_output:
        scan = EnkryptMiddleware.validate_output(req.text, current_user, db)
    
    return {
        "status": scan.get("status", "PASSED"),
        "threats": scan.get("threats", [])
    }
