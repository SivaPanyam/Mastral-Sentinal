# Mastra Sentinel API Design

The Core SRE Backend service exposes a series of highly structured RESTful endpoints.

## Authentication & Guards
All routes (except `/auth/login` and `/health`) are secured by an OAuth2 JWT Bearer verification guard. To query protected resources, include the following HTTP Authorization Header:
`Authorization: Bearer <JWT_ACCESS_TOKEN>`

## Endpoints Specification

### 1. Authentication
* **POST `/auth/login`**
  * Description: Authenticates SRE staff.
  * Request Body:
    ```json
    { "email": "admin@example.com", "password": "your_password_here" }
    ```
  * Response Body (200 OK):
    ```json
    {
      "access_token": "eyJhbGciOi...",
      "token_type": "bearer",
      "email": "sivapanyam1@gmail.com",
      "role": "SRE_ADMIN"
    }
    ```

### 2. Incident Lifecycle
* **GET `/api/v1/incidents/`**
  * Description: Lists all active/resolved system anomalies.
  * Response Body (200 OK): List of `Incident` objects.
* **POST `/api/v1/incidents/`**
  * Description: Logs a new alert or diagnostic container issue.
* **POST `/api/v1/incidents/{incident_id}/logs`**
  * Description: Appends standard server log traces. Securely redacts sensitive keys using the `Enkrypt` filter middleware.
* **POST `/api/v1/incidents/{incident_id}/trigger-pipeline`**
  * Guard: `SRE_ADMIN` or `SRE_OPERATOR` role required.
  * Description: Executes the autonomous **5-Agent Mastra SRE Workflow DAG** on the target incident.

### 3. Agent Execution Core
* **GET `/api/v1/agents/status`**
  * Description: Retrieves real-time health metrics and latency stats for the five active agents.
* **GET `/api/v1/agents/runs/incident/{incident_id}`**
  * Description: Lists sequential output histories for the Mastra agent workflow.

### 4. Vector RAG Knowledge Base
* **GET `/api/v1/knowledge/documents`**
  * Description: Lists all indexed SOPs.
* **POST `/api/v1/knowledge/documents`**
  * Description: Ingests a new runbook and registers similarity embeddings inside Qdrant Vector database.
* **GET `/api/v1/knowledge/search?query=pool`**
  * Description: Cosine similarity-search engine lookup returning documents and score pairings.
