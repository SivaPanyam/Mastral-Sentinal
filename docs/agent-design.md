# Mastra Sentinel SRE Agent Design

Mastra Sentinel's automation layer is driven by **5 specialized AI Agents** built on the Google Gemini API with the structured `@google/genai` TypeScript/Python SDK.

## The Five SRE Agents

| Agent Name | Operational Role | LLM Persona & Focus | Core Output Fields |
| :--- | :--- | :--- | :--- |
| **TriageAgent** | Alert Classifier | Analyzes alerts, assigns severity, identifies affected components. | `classification`, `confidence`, `allocatedTeam`, `summary` |
| **DiagnosisAgent** | SOP Correlator | Integrates with Qdrant vector database RAG search. Correlates incident logs with SOP runbooks. | `sop_match_found`, `matched_runbook_id`, `insights`, `recommendedQuery` |
| **RecommendationAgent** | Action Architect | Generates step-by-step mitigation plans and exact shell/SQL script snippets. | `strategy`, `steps`, `exactCommand`, `safetyRating` |
| **ReportAgent** | RCA Writer | Compiles complete Markdown Root Cause Analysis (RCA) Post-Mortem summaries. | `title`, `summary`, `rootCause`, `timeline`, `actionItems` |
| **KnowledgeAgent** | Feedback Indexer | Ingests finalized RCAs, extracts key tags, updates vector embeddings. | `tags`, `syntheticQueries`, `indexSummary` |

## Code Structure Patterns

The agents are implemented under `/backend/app/mastra/agents.py`. They utilize standard model definitions:

```python
class MastraAgent:
    def __init__(self, name: str, system_instruction: str, model_name: str = "gemini-2.5-flash"):
        self.name = name
        self.system_instruction = system_instruction
        self.model_name = model_name

    def run(self, prompt: str, schema: Optional[type] = None):
        # Structured Output generation
        ...
```

* **Structured JSON Outputs**: When schemas are passed, the agent configures `response_mime_type="application/json"` and specifies the Pydantic class as the `response_schema` to guarantee valid, robust downstream execution.
* **Resilient Failovers**: If the Google Gemini connection is offline or unconfigured, the agents automatically fall back to local rule-based heuristic engines, ensuring absolute uptime in high-availability environments.
