# SRE Troubleshooting Guide: Mastra Sentinel

This manual assists DevOps teams in debugging operational issues inside Mastra Sentinel.

## Diagnostic Scenarios

### Scenario A: Platform hangs on starting dev server or loading preview
* **Indication**: The browser displays "Please wait while your application starts..." indefinitely.
* **Reason**: Missing required secret configurations or database timeouts crashing the server at start-up.
* **Resolution**: 
  1. Check if PostgreSQL or Qdrant ports are bound.
  2. Ensure `.env` is initialized. If necessary, allow local database fallback by setting `DATABASE_URL` to a SQLite configuration for sandboxed dev: `sqlite:///./mastra_sentinel.db`.

### Scenario B: AI SRE workflows fail with API-key exceptions
* **Indication**: "Gemini API run error: API_KEY_INVALID" in backend logs.
* **Reason**: Unconfigured, expired, or incorrect `GEMINI_API_KEY` environmental variable.
* **Resolution**: The backend gracefully captures this error and falls back to our local **Rule-based Heuristic SRE Engine**, but to restore full AI capabilities, make sure your Gemini Key is saved under Google AI Studio secrets.

### Scenario C: Qdrant similarity searches return zero results
* **Indication**: Log correlations fail to associate matching SOP guides.
* **Reason**: The `sentinel_kb` vector collection hasn't been created, or has been purged.
* **Resolution**:
  1. Trigger collection instantiation by executing `/api/v1/knowledge/documents` with a POST payload.
  2. Verify if the Qdrant instance is running on port `6333` using: `curl http://localhost:6333/dashboard`.
