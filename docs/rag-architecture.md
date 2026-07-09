# Mastra Sentinel RAG Ingestion Architecture

Mastra Sentinel leverages standard **Retrieval-Augmented Generation (RAG)** integrated with the **Qdrant Vector Database** to surface relevant SOPs during active production incidents.

```
                  ┌───────────────────────────────┐
                  │      SOP Runbooks & RCAs      │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │      Text Ingest & Chunk      │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │     Embedding generation      │
                  │       (384 Dimensions)        │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │    Qdrant Vector Database     │
                  │   (Cosine Distance Metric)    │
                  └───────────────────────────────┘
```

## Core Components

### 1. Vector Ingestion Pipeline
* Documents (e.g. Standard operating procedures) are passed to the `QdrantRagManager` at `/backend/app/mastra/rag.py`.
* The text content is normalized, formatted, and converted into structured vector embeddings.

### 2. Embeddings Model Specs
* **Dimensionality**: 384 dimensions.
* **Metric**: Cosine Similarity.
* **Generation**: Handled deterministically inside `rag.py` using standard text-weighting mappings for dependency-free local runtimes, fully compatible with enterprise standard transformers in production.

### 3. Collection Management
* All runbooks and post-mortems are indexed into a single collection: `sentinel_kb`.
* Points are stored with structured payload maps containing:
  * `doc_id`: Unique document reference.
  * `title`: Title of the runbook or previous RCA.
  * `service`: Service scope (e.g. `postgresql-database`).
  * `type`: Document type (`RUNBOOK` or `POST_MORTEM`).
  * `content`: Full text body context.

### 4. Similarity Querying
During the incident response workflow, the **DiagnosisAgent** queries the collection using cosine proximity scoring. Documents scoring above `0.70` similarity are fed directly into the LLM prompt to contextualize recovery actions.
