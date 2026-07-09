# Mastra Sentinel Relational Database Schema

Mastra Sentinel implements SQL database architectures utilizing the SQLAlchemy ORM for durable persistence.

```
       ┌───────────────────────────┐
       │         incidents         │
       ├───────────────────────────┤
       │ id (PK, String)           │◄─────────────────────┐
       │ title (String)            │                      │
       │ status (String)           │                      │
       │ severity (String)         │                      │
       │ service (String)          │                      │
       │ createdAt (DateTime)      │                      │
       │ resolvedAt (DateTime)     │                      │
       └─────┬──────────────┬──────┘                      │
             │              │                             │
             │ 1:N          │ 1:N                         │ 1:1
             ▼              ▼                             ▼
  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
  │   incident_logs   │  │    agent_runs     │  │    rca_reports    │
  ├───────────────────┤  ├───────────────────┤  ├───────────────────┤
  │ id (PK, String)   │  │ id (PK, String)   │  │ id (PK, String)   │
  │ incidentId (FK)   │  │ incidentId (FK)   │  │ incidentId (FK)   │
  │ timestamp         │  │ agentType (String)│  │ title (String)    │
  │ source (String)   │  │ status (String)   │  │ summary (Text)    │
  │ level (String)    │  │ summary (Text)    │  │ rootCause (Text)  │
  │ message (Text)    │  │ payload (JSON)    │  │ timeline (JSON)   │
  └───────────────────┘  └───────────────────┘  └───────────────────┘
```

## Entity-Relationship Definitions

### 1. `incidents` Table
* **`id`** (`String`, PK): Format `INC-2026-[UUID]`.
* **`status`** (`String`): Current operational state (`TRIGGERED`, `TRIAGED`, `DIAGNOSING`, `INVESTIGATING`, `MITIGATED`, `RESOLVED`).
* **`severity`** (`String`): Priority rating (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
* **`service`** (`String`): Associated microservice.

### 2. `incident_logs` Table
* Holds all diagnostic metrics and warning files uploaded by external targets.
* **`incidentId`** (`String`, FK): Cascades on-delete.
* **`level`** (`String`): Log severity level (`INFO`, `WARN`, `ERROR`, `FATAL`).
* **`message`** (`Text`): Raw console message (processed and encrypted by Enkrypt middleware where appropriate).

### 3. `agent_runs` Table
* Tracks exact execution logs of Mastra AI SRE agents.
* **`agentType`** (`String`): Associated executor (`TRIAGE`, `DIAGNOSIS`, `RECOMMENDATION`, `REPORT`, `KNOWLEDGE`).
* **`payload`** (`JSON`): Complex stage metadata outputted by the model.

### 4. `rca_reports` Table
* Standard Operating root cause analysis and action item documents compiled by the platform.
* **`timeline`** (`JSON`): Chronological SRE event timeline.
* **`actionItems`** (`JSON`): Post-remediation actions containing assignee and status keys.
