# Mastra Sentinel System Overview

## Platform Mission

Mastra Sentinel is designed to solve a critical issue in modern DevOps, Security, and SRE: **Incident alert fatigue and slow Mean Time to Resolution (MTTR)**. 

When a microservice begins reporting timeouts or memory limits (OOM), traditional monitors simply trigger a PagerDuty ping. Mastra Sentinel intercepts alerts, ingests active logs, and triggers an **autonomous 5-agent pipeline** to diagnose and suggest (or automatically apply) precise mitigation commands using local vector standard operating procedures (SOPs).

## Core Modules

* **Incident Lifecycle Dashboard**: Beautiful real-time interactive SRE control board tracking incidents from `TRIGGERED`, through active diagnostic pipelines, to final `RESOLVED` states.
* **Mastra SRE Pipeline (Agent workflow)**: Directed Acyclic Graph orchestrating 5 dedicated agents to handle incident classification, historical runbook search, recipe formulation, RCA generation, and knowledge persistence.
* **Vector RAG (Qdrant Database)**: Cosine similarity-search index of standard company runbooks (SOPs) and historical incident post-mortems.
* **Secure Telemetry & Log Ingestion**: High-performance HTTP endpoint allowing Kubernetes containers, Cloud Run logs, or third-party webhooks to append logs directly.
* **Enkrypt Security Abstraction**: Intercepts ingested logs to redact or encrypt API keys and credentials, keeping audit data strictly secure.
