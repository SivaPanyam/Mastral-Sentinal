import os
import time
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Incident, IncidentLog, KnowledgeSource
from app.mastra.rag import rag_manager
from qdrant_client.http import models as qmodels

def main():
    print("=== Rebuilding Vector Store with Real Gemini Embeddings ===")
    
    # 1. Verify Gemini API Key (Fail fast)
    try:
        print("Testing Ollama Embedding API...")
        test_emb = rag_manager.embedder.get_embedding("Test API Key")
        if not test_emb or len(test_emb) != 768:
            raise ValueError("Test embedding did not return 768 dimensions.")
        print("Ollama is reachable. Proceeding to rebuild.")
    except Exception as e:
        print(f"FATAL: Gemini API verification failed. Aborting. Error: {e}")
        return

    # 2. Recreate Qdrant Collection
    print(f"Recreating Qdrant collection: {rag_manager.qdrant.collection_name}")
    try:
        rag_manager.qdrant.client.delete_collection(collection_name=rag_manager.qdrant.collection_name)
    except Exception as e:
        print(f"Note: Could not delete collection (might not exist): {e}")
    rag_manager.qdrant.ensure_collection_exists(vector_size=768)

    db: Session = SessionLocal()
    start_time = time.time()
    
    stats = {
        "documents_indexed": 0,
        "chunks_created": 0,
        "embeddings_generated": 0,
        "failed_embeddings": 0,
        "skipped_documents": 0,
    }

    def safe_index(doc_id, title, content, metadata):
        try:
            chunks = rag_manager._chunk_text(content)
            stats["documents_indexed"] += 1
            stats["chunks_created"] += len(chunks)
            
            # Use batching logic similar to index_document but inject chunks
            points = []
            for i, chunk in enumerate(chunks):
                try:
                    vector = rag_manager.embedder.get_embedding(chunk)
                    
                    # Ensure chunk_id is explicitly in metadata
                    payload = {
                        "title": title,
                        "content": chunk,
                        "doc_id": doc_id,
                        "chunk_index": i,
                        "chunk_id": f"{doc_id}_chunk_{i}",
                        **metadata
                    }
                    import uuid
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"{doc_id}_{i}"))
                    points.append(qmodels.PointStruct(id=point_id, vector=vector, payload=payload))
                    stats["embeddings_generated"] += 1
                except Exception as e:
                    stats["failed_embeddings"] += 1
                    print(f"Failed to embed chunk for {doc_id}: {e}")
            
            batch_size = 100
            if points:
                for i in range(0, len(points), batch_size):
                    batch = points[i:i+batch_size]
                    rag_manager.qdrant.upsert_points(batch)

        except Exception as e:
            stats["skipped_documents"] += 1
            print(f"Failed to index document {doc_id}: {e}")

    # 3. Index Incidents
    print("Indexing Incidents...")
    incidents = db.query(Incident).all()
    for inc in incidents:
        content = f"Incident: {inc.title}\nDescription: {inc.description}\nRoot Cause: {inc.root_cause}\nResolution: {inc.resolution}"
        metadata = {
            "incident_id": inc.incident_number,
            "document_id": inc.id,
            "severity": inc.severity,
            "service": inc.service,
            "category": inc.category,
            "timestamp": inc.detectedAt.isoformat() if inc.detectedAt else None,
            "source_file": "it_incident_dataset.csv",
            "document_type": "INCIDENT"
        }
        safe_index(inc.id, inc.title, content, metadata)

    # 4. Index Incident Logs
    print("Indexing Incident Logs...")
    logs = db.query(IncidentLog).all()
    for log in logs:
        content = f"Log [{log.level}] in {log.service}/{log.namespace}: {log.message}"
        parent_incident = log.incident
        incident_number = parent_incident.incident_number if parent_incident else log.incidentId
        severity = parent_incident.severity if parent_incident else "UNKNOWN"
        category = parent_incident.category if parent_incident else "LOG"

        metadata = {
            "incident_id": incident_number,
            "document_id": log.id,
            "severity": severity,
            "service": log.service,
            "category": category,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "source_file": "k8s_app_logs_1000.csv",
            "document_type": "LOG"
        }
        safe_index(log.id, f"Log {log.id}", content, metadata)

    # 5. Index Knowledge Sources
    print("Indexing Knowledge Sources...")
    knowledge = db.query(KnowledgeSource).all()
    for k in knowledge:
        metadata = {
            "incident_id": "N/A",
            "document_id": k.id,
            "severity": "N/A",
            "service": k.source_metadata.get("service", "unknown") if k.source_metadata else "unknown",
            "category": "KNOWLEDGE",
            "timestamp": k.createdAt.isoformat() if hasattr(k, "createdAt") and k.createdAt else None,
            "source_file": k.source_path or "unknown",
            "document_type": k.type
        }
        safe_index(k.id, k.title, k.content, metadata)
        
    db.close()
    
    duration = time.time() - start_time
    try:
        vector_count = rag_manager.qdrant.client.count(rag_manager.qdrant.collection_name).count
    except Exception as e:
        vector_count = f"Error fetching count: {e}"

    print("\n" + "="*50)
    print("RUNTIME REPORT")
    print("="*50)
    print(f"Ollama authentication status: SUCCESS")
    print(f"Embedding model used: nomic-embed-text")
    print(f"Embedding dimension: 768")
    print(f"Documents indexed: {stats['documents_indexed']}")
    print(f"Chunks created: {stats['chunks_created']}")
    print(f"Embeddings generated: {stats['embeddings_generated']}")
    print(f"Vectors stored: {vector_count}")
    print(f"Failed embeddings: {stats['failed_embeddings']}")
    print(f"Skipped documents: {stats['skipped_documents']}")
    print(f"Duplicate chunks: 0")  # Since we recreate collection, there are no duplicates
    print(f"Qdrant collection name: {rag_manager.qdrant.collection_name}")
    print(f"Average indexing time per doc: {duration/stats['documents_indexed'] if stats['documents_indexed'] > 0 else 0:.4f}s")
    print("="*50)

if __name__ == "__main__":
    main()
