# Mastra Sentinel Folder Structure

Below is the directory structure layout of the fully consolidated Mastra Sentinel enterprise repository.

```
├── /                        # Root of workspace
│   ├── .env.example         # Multi-service configuration template
│   ├── .gitignore           # Version-control exclusions
│   ├── Dockerfile           # Frontend React container
│   ├── docker-compose.yml   # Multi-service local cluster orchestration
│   ├── package.json         # React NPM dependencies
│   ├── tsconfig.json        # TypeScript configuration settings
│   ├── vite.config.ts       # Vite-bundler configuration settings
│   │
│   ├── /backend             # FastAPI SRE Agent Core Service
│   │   ├── Dockerfile       # Python Backend container
│   │   ├── requirements.txt # Python package declarations
│   │   └── /app             # Core Python API logic
│   │       ├── __init__.py  
│   │       ├── main.py      # FastAPI Server Entrypoint
│   │       ├── config.py    # Pydantic Settings
│   │       ├── database.py  # SQLAlchemy engine configs
│   │       ├── models.py    # SQLAlchemy SQL schemas
│   │       ├── schemas.py   # Pydantic schema validations
│   │       ├── auth.py      # JWT auth & Enkrypt Middleware
│   │       │
│   │       ├── /routes      # REST API Router endpoints
│   │       │   ├── __init__.py
│   │       │   ├── incidents.py
│   │       │   ├── agents.py
│   │       │   ├── knowledge.py
│   │       │   └── reports.py
│   │       │
│   │       └── /mastra      # Agentic SRE layer
│   │           ├── __init__.py
│   │           ├── agents.py    # 5 Google Gemini-powered SRE agents
│   │           ├── workflows.py # Mastra Workflow DAG orchestration
│   │           ├── rag.py       # Qdrant client similarity search
│   │           └── prompts.py   # Formatted system prompts
│   │
│   ├── /src                 # React Web Frontend Source
│   │   ├── main.tsx         # Frontend Mount point
│   │   ├── App.tsx          # Main router and shell layout
│   │   ├── index.css        # Tailwind CSS imports & theme overrides
│   │   ├── types.ts         # Central TypeScript interfaces
│   │   │
│   │   ├── /context         # React state managers
│   │   │   └── AppContext.tsx
│   │   │
│   │   ├── /components      # Atomic UI Widgets & dashboards
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Timeline.tsx
│   │   │   ├── IncidentCard.tsx
│   │   │   ├── ReportCard.tsx
│   │   │   └── LogUploader.tsx
│   │   │
│   │   └── /pages          # Consolidated Route Pages
│   │       ├── Dashboard.tsx
│   │       ├── Incidents.tsx
│   │       ├── KnowledgeBase.tsx
│   │       └── Reports.tsx
│   │
│   └── /docs                # Enterprise Engineering Blueprints
│       ├── architecture.md
│       ├── api-design.md
│       └── database-schema.md
```
