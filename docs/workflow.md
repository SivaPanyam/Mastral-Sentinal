# Mastra Sentinel Autonomous Workflow Engine

Mastra Sentinel implements a **Mastra Workflow DAG** that links the 5 SRE agents in a sequence of automated diagnostic steps.

## Workflow Execution DAG

```
                      ┌──────────────────────┐
                      │   Trigger Incident   │
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │    Triage Agent      │  (Classification)
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │   Diagnosis Agent    │  (Qdrant RAG Runbooks)
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │ Recommendation Agent │  (Formulates CLI plan)
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │     Report Agent     │  (Drafts RCA Document)
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │   Knowledge Agent    │  (Saves Feedback to RAG)
                      └──────────────────────┘
```

## State Transitions Matrix

When an incident flows through the pipeline, its database operational status is modified:

1. **`TRIGGERED`**: Alert is logged in the system. Logs are appended.
2. **`TRIAGED`**: The `TriageAgent` finishes evaluating logs and classifies the category.
3. **`DIAGNOSING`**: The `DiagnosisAgent` searches the vector index and matches guidelines.
4. **`INVESTIGATING`**: The `RecommendationAgent` crafts shell scripts or terminal mitigation strategies.
5. **`RESOLVED`**: The SRE team approves recommendations, executes the mitigation script, the `ReportAgent` files the post-mortem RCA report, and the `KnowledgeAgent` indexes findings back into Qdrant.
