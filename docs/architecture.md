# Mastra Sentinel Architecture Blueprint

This document details the multi-tiered architecture of Mastra Sentinel, an autonomous AI-driven SRE incident response and remediation control plane.

## High-Level Architecture Overview

Mastra Sentinel comprises three primary core logical systems:

```
               ┌────────────────────────────────────────────────────────┐
               │                   React Web Frontend                   │
               │               (Single Page Application)                │
               └───────────────────────────┬────────────────────────────┘
                                           │
                                           │ HTTP/WebSocket
                                           ▼
               ┌────────────────────────────────────────────────────────┐
               │                     FastAPI Backend                    │
               │                   (Core SRE Service)                   │
               └───────────┬───────────────────────┬──────────────┬─────┘
                           │                       │              │
                           │ PostgreSQL            │ Vector Search│ SQL / API Calls
                           ▼                       ▼              ▼
               ┌───────────────────────┐ ┌───────────────────┐ ┌──────────────┐
               │    PostgreSQL DB      │ │   Qdrant Vector   │ │  Google AI   │
               │  (Relational Storage) │ │   Database (RAG)  │ │  Studio SDK  │
               └───────────────────────┘ └───────────────────┘ └──────────────┘
```

## Tier-by-Tier Breakdown

### 1. Presentation Tier (React SPA)
* **Framework**: React 19+ managed via Vite compiler.
* **Styling Engine**: Tailwind CSS.
* **Component Design**: Modular atomic widgets located in `/src/components` and views in `/src/pages`.
* **State Manager**: Consolidated AppContext provider located in `/src/context/AppContext.tsx`.

### 2. Application Tier (FastAPI SRE Core)
* **Web Framework**: FastAPI.
* **ORM**: SQLAlchemy.
* **Authentication**: OAuth2 JWT token-bearer authorization layers.
* **Enkrypt Middleware Abstraction**: Inspects in-transit telemetry logs and ciphers raw access credentials before database write actions.

### 3. Agentic SRE Tier (Mastra SRE Pipeline)
* **Orchestration**: Autonomous Mastra Workflow graph linking 5 SRE Agents (Triage, Diagnosis, Recommendation, Report, and Knowledge).
* **LLM Engine**: Google Gemini API powered by `@google/genai` modern SDK.
* **Vector Embeddings Store (RAG)**: Qdrant Database.
