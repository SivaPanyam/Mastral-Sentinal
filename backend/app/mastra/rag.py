import os
import uuid
import hashlib
import json
import re
import time
import requests
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from app.config import settings
from app.knowledge.loaders import get_loader
from app.knowledge.chunking import ChunkingEngine

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.provider = getattr(settings, "EMBEDDING_PROVIDER", "ollama").lower()
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", settings.OLLAMA_BASE_URL)
        if not self.ollama_base_url.endswith("/api/embeddings"):
            self.ollama_endpoint = f"{self.ollama_base_url.rstrip('/')}/api/embeddings"
        else:
            self.ollama_endpoint = self.ollama_base_url
            
        self.gemini_client = None
        if self.provider == "google":
            try:
                from google import genai
                gemini_api_key = os.getenv("GEMINI_API_KEY")
                if gemini_api_key:
                    self.gemini_client = genai.Client(api_key=gemini_api_key)
                else:
                    logger.warning("GEMINI_API_KEY missing, falling back to Ollama")
                    self.provider = "ollama"
            except ImportError:
                logger.warning("google-genai not installed, falling back to Ollama")
                self.provider = "ollama"

    @property
    def vector_size(self) -> int:
        return 768 if self.provider == "google" else 768 # nomic-embed-text is 768, text-embedding-004 is 768

    def get_embedding(self, text: str, retries: int = 5, backoff_factor: float = 2.0) -> List[float]:
        for attempt in range(retries):
            try:
                if self.provider == "google" and self.gemini_client:
                    result = self.gemini_client.models.embed_content(
                        model="text-embedding-004",
                        contents=text
                    )
                    return result.embeddings[0].values
                else:
                    payload = {
                        "model": "nomic-embed-text",
                        "prompt": text
                    }
                    response = requests.post(self.ollama_endpoint, json=payload, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    return data.get("embedding", [])
            except Exception as e:
                if attempt < retries - 1:
                    sleep_time = backoff_factor ** attempt
                    time.sleep(sleep_time)
                    continue
                logger.error(f"Failed to get embedding: {e}")
                raise e

class QdrantService:
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION
        try:
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
            )
        except Exception as e:
            logger.error(f"Could not connect to Qdrant cluster: {e}")
            self.client = None

    def ensure_collection_exists(self, vector_size: int = 768):
        if not self.client: return
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=vector_size,
                        distance=qmodels.Distance.COSINE
                    )
                )
        except Exception as e:
            logger.error(f"Failed to verify Qdrant collections: {e}")

    def upsert_points(self, points: List[qmodels.PointStruct]):
        if not self.client: return
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def search_points(self, query_vector: List[float], query_filter: Optional[qmodels.Filter] = None, limit: int = 3):
        if not self.client: return []
        return self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        ).points

class RAGService:
    def __init__(self):
        self.embedder = EmbeddingService()
        self.qdrant = QdrantService()
        self.qdrant.ensure_collection_exists(vector_size=self.embedder.vector_size)
        self.chunker = ChunkingEngine(chunk_size=1000, overlap=200, strategy="semantic")

    def extract_metadata(self, text: str) -> Dict[str, str]:
        try:
            base_url = os.getenv("OLLAMA_BASE_URL", settings.OLLAMA_BASE_URL).rstrip("/")
            endpoint = f"{base_url}/api/generate"
            prompt = "Analyze the following document and extract metadata. Return ONLY a JSON object with 'title', 'service', and 'type'. The 'type' must be one of: RUNBOOK, POST_MORTEM, ARCHITECTURE, PLAYBOOK, WIKI. Document: " + text[:2000]
            
            payload = {
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(endpoint, json=payload, timeout=60)
            response.raise_for_status()
            text_resp = response.json().get("response", "")
            
            json_str = re.search(r'\{.*\}', text_resp, re.DOTALL)
            if json_str:
                return json.loads(json_str.group(0))
        except Exception as e:
            logger.error(f"Metadata extraction failed: {e}")
        return {"title": "Unknown Document", "service": "unknown", "type": "UNKNOWN"}

    def ingest_file(self, file_path: str, metadata: Dict[str, Any] = None):
        """Production pipeline for extracting text and indexing via Loaders."""
        loader = get_loader(file_path)
        pages = list(loader.load())
        
        full_content = "\n".join([p.get("content", "") for p in pages])
        content_hash = hashlib.sha256(full_content.encode('utf-8')).hexdigest()
        
        if not metadata:
            metadata = self.extract_metadata(full_content)

        doc_id = metadata.get("doc_id", f"FILE-{uuid.uuid4().hex[:8]}")
        title = metadata.get("title", os.path.basename(file_path))
        
        return {
            "doc_id": doc_id, 
            "content_hash": content_hash, 
            "metadata": metadata, 
            "content": full_content, 
            "title": title,
            "pages": pages
        }

    def index_document(self, doc_id: str, title: str, content: str, metadata: Dict[str, Any], pages: List[Dict[str, Any]] = None):
        """Chunks document, calls EmbeddingService, and stores in QdrantService with enriched metadata."""
        if not pages:
            pages = [{"content": content, "page_number": 1}]
            
        chunks = self.chunker.chunk_document(pages)
        
        points = []
        for i, chunk in enumerate(chunks):
            vector = self.embedder.get_embedding(chunk["content"])
            payload = {
                "doc_id": doc_id,
                "title": title,
                "content": chunk["content"],
                "chunk_id": f"{doc_id}-chunk-{i}",
                "page_number": chunk.get("page_number", 1),
                "doc_type": metadata.get("type", "UNKNOWN"),
                "service": metadata.get("service", "unknown"),
                "author": metadata.get("author", "system"),
                "environment": metadata.get("environment", "all"),
                "embedding_model": self.embedder.provider,
                "created_date": str(int(time.time()))
            }
            # Generate deterministic UUID point ID based on doc_id and chunk index
            point_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"{doc_id}_{i}"))
            points.append(qmodels.PointStruct(id=point_id, vector=vector, payload=payload))
            
        batch_size = 100
        if points:
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                self.qdrant.upsert_points(batch)

    def _cross_encoder_rerank(self, query: str, results: List[Any]) -> List[Any]:
        """Local mocked cross-encoder re-ranking for Hybrid Retrieval."""
        # A real implementation would use `cross-encoder/ms-marco-MiniLM-L-6-v2`
        # Here we do a mocked keyword boosting over semantic scores to simulate hybrid reranking
        for r in results:
            content = r.payload.get("content", "").lower()
            q_lower = query.lower()
            keyword_bonus = 0.0
            for word in q_lower.split():
                if len(word) > 4 and word in content:
                    keyword_bonus += 0.05
            
            # Simulated confidence calculation
            r.score = min(1.0, r.score + keyword_bonus)
            
        # Sort by updated scores
        return sorted(results, key=lambda x: x.score, reverse=True)

    def query_sop_runbooks(self, query: str, limit: int = 3, filter_conditions: Dict[str, str] = None) -> List[Dict[str, Any]]:
        """Hybrid Search: Vector Similarity + Metadata Filtering + CrossEncoder Re-Ranking"""
        query_vector = self.embedder.get_embedding(query)
        
        # Build Qdrant Filter
        q_filter = None
        if filter_conditions:
            must_clauses = []
            for key, value in filter_conditions.items():
                must_clauses.append(qmodels.FieldCondition(key=key, match=qmodels.MatchValue(value=value)))
            q_filter = qmodels.Filter(must=must_clauses)
            
        # Fetch 2x limit for reranking pool
        results = self.qdrant.search_points(query_vector=query_vector, query_filter=q_filter, limit=limit * 2)
        
        # Re-Rank
        reranked_results = self._cross_encoder_rerank(query, results)
        
        # Take top limit
        final_results = reranked_results[:limit]
        
        enhanced_results = []
        for r in final_results:
            payload = r.payload or {}
            enhanced_results.append({
                "content": payload.get("content", ""),
                "score": r.score,
                "confidence": f"{int(r.score * 100)}%",
                "title": payload.get("title", "Unknown"),
                "doc_id": payload.get("doc_id"),
                "chunk_id": payload.get("chunk_id"),
                "page_number": payload.get("page_number", 1),
                "service": payload.get("service"),
                "type": payload.get("doc_type"),
            })
        return enhanced_results

# Shared instance maintains identical interface for workflows.py
try:
    rag_manager = RAGService()

    # Seed default SOP knowledge runbooks (requires valid API keys and running Qdrant)
    rag_manager.index_document(
        doc_id="KB-RUNBOOK-001",
        title="Database Connection Pool Saturation Recovery Plan",
        content="This guide outlines step-by-step procedures to resolve database connection pool saturation. Symptom: Client backends reporting 'Timeout acquiring connection from pool'. Solution: Execute 'SELECT pg_terminate_backend(pid) FROM pg_stat_activity' on idle processes to free slots. Ensure PgBouncer connection multiplexers are active.",
        metadata={"type": "RUNBOOK", "service": "postgresql-database"}
    )

    rag_manager.index_document(
        doc_id="KB-RUNBOOK-002",
        title="Memory Saturation and OOM Killer Mitigation SOP",
        content="Guidelines for mitigating Kubernetes Out-Of-Memory (OOM) events. Symptoms: Container exits with Code 137. Resolution: Perform rolling restarts of target deployments. Update container resource request limits by 1.5x in deployment yaml specifications.",
        metadata={"type": "RUNBOOK", "service": "k8s-cluster"}
    )
except Exception as e:
    logger.error(f"Skipping RAG initialization and seeding due to missing dependencies: {e}")
    class StubRagManager:
        def query_sop_runbooks(self, query: str, limit: int = 3, filter_conditions: Dict[str, str] = None): return []
        def index_document(self, doc_id: str, title: str, content: str, metadata: Dict[str, Any], pages=None): pass
        def ingest_file(self, file_path: str, metadata: Dict[str, Any] = None): return {}
    rag_manager = StubRagManager()
