# Mastra Sentinel

> **Autonomous AI-Driven SRE Incident Response & Remediation Control Plane**

Mastra Sentinel is an enterprise-grade AI-powered Incident Intelligence Platform designed for DevOps, SRE, and Security teams. It automates incident triage, correlation, remediation, and reporting using a coordinated multi-agent workflow powered by **Local AI (Ollama Llama 3.2)** and Qdrant Vector Search (RAG).

---

## 🚀 Architectural Blueprint

The platform is structured into clean, modular tiers adhering to SOLID engineering design principles:

* **Presentation Tier**: A highly polished, single-view interactive SRE console built with React 19, TypeScript, Tailwind CSS, and Framer Motion.
* **Core Application Tier**: A robust, secure FastAPI backend providing telemetry aggregation, relational database persistence (SQLAlchemy + PostgreSQL), and JWT user access controls.
* **Agentic SRE Tier**: An autonomous Mastra Workflow DAG coordinating **5 dedicated SRE Agents** using local, private LLMs via Ollama.
* **Vector Storage (RAG)**: A high-performance Qdrant similarity database containing Standard Operating Procedures (SOPs) and historical incident post-mortems encoded with `nomic-embed-text`.

---

## 📂 Repository Layout

```
├── /                        # Root of workspace
│   ├── Dockerfile           # Frontend deployment container
│   ├── docker-compose.yml   # Multi-service local cluster orchestration
│   ├── package.json         # React NPM dependencies
│   ├── /backend             # FastAPI SRE Agent Core Service
│   │   ├── requirements.txt # Python package declarations
│   │   └── /app             # Core Python API logic
│   ├── /src                 # React Web Frontend Source
│   └── /docs                # Enterprise Engineering Blueprints & Manuals
```

*For a full directory breakdown, consult [docs/folder-structure.md](docs/folder-structure.md).*

---

## 🛠️ Local Development & Quick Start

Deploy the entire Mastra Sentinel stack locally in seconds using Docker Compose:

### 1. Configure Secrets
Copy the environment template and insert your keys:

```bash
cp .env.example .env
```

Ensure you have [Ollama](https://ollama.com/) running locally with `llama3.2` and `nomic-embed-text` models pulled (`ollama pull llama3.2` and `ollama pull nomic-embed-text`). The platform runs 100% locally with absolute data privacy. You can optionally add an `ENKRYPTAI_API_KEY` for enterprise AI guardrails, though it falls back to a local regex engine gracefully.

### 2. Launch the Stack
```bash
docker-compose up --build -d
```

### 3. Access Services
* **React Web Frontend**: `http://localhost:3000`
* **FastAPI Backend Server**: `http://localhost:8000`
* **Interactive API Documentation (Swagger)**: `http://localhost:8000/api/docs`
* **Qdrant Vector Console**: `http://localhost:6333/dashboard`

---

## 🛡️ Key Enterprise Features

### 1. Autonomous 5-Agent SRE Pipeline
When an anomaly is logged, the platform orchestrates a sequential DAG of five dedicated agents:
1. **TriageAgent**: Classifies incoming incident logs and delegates ownership.
2. **DiagnosisAgent**: Queries Qdrant using vector similarity embeddings to match SOPs.
3. **RecommendationAgent**: Formulates precise step-by-step mitigation command recipes.
4. **ReportAgent**: Compiles comprehensive Root Cause Analysis (RCA) post-mortems.
5. **KnowledgeAgent**: Tags, summarizes, and updates vector runbook indexes.

### 2. Enkrypt Middleware Abstraction
Telemetry logs often contain sensitive credentials. Our custom `EnkryptMiddleware` (located in `/backend/app/auth.py`) automatically intercepts logs, redacts credentials, and encrypts sensitive parameters in-transit before persisting them to disk.

### 3. Graceful Degraded Operations
In high-pressure situations, external APIs can timeout. Because Mastra Sentinel runs 100% locally with Ollama, you are protected from cloud vendor outages. Furthermore, if the Enkrypt AI Guardrails API is unreachable, the system automatically transitions to a robust offline regex-based security heuristic engine, guaranteeing absolute service uptime.

---

## 📚 Technical Documentation Blueprints

We have compiled comprehensive architectural reviews and manuals under the `/docs` directory:

1. [Architecture Blueprint](docs/architecture.md) - Logical component structures and tier explanations.
2. [System Overview](docs/system-overview.md) - Business missions and problem statements.
3. [API Specification](docs/api-design.md) - HTTP REST endpoints and request formats.
4. [Database Schema](docs/database-schema.md) - Relational SQL constraint columns.
5. [Agentic SRE Design](docs/agent-design.md) - Model definitions and prompts.
6. [RAG & Vector Architecture](docs/rag-architecture.md) - Cosine similarity and chunking strategies.
7. [Zero-Trust Security](docs/security-architecture.md) - Encryption, RBAC, and container hardening.
8. [Workflow DAG Transitions](docs/workflow.md) - Agent state changes and transitions.
9. [Production Deployment](docs/deployment.md) - GKE, Cloud Run, and managed database setups.
10. [Testing Guidelines](docs/testing.md) - API pytest guides and frontend specs.
11. [Troubleshooting Guide](docs/troubleshooting.md) - Debugging configurations and logs.
12. [Enterprise Architecture Review](docs/architecture-review.md) - Senior Reviewer checklist.

---

## ⚖️ License
Mastra Sentinel is distributed under the [MIT License](LICENSE).
