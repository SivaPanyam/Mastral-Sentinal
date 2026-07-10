import os
import uuid
import hashlib
import json
import re
import time
import requests
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from pypdf import PdfReader
from app.config import settings
from app.ingestion.chunking import chunk_text

class EmbeddingService:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", settings.OLLAMA_BASE_URL)
        if not self.base_url.endswith("/api/embeddings"):
            self.endpoint = f"{self.base_url.rstrip('/')}/api/embeddings"
        else:
            self.endpoint = self.base_url

    def get_embedding(self, text: str, retries: int = 5, backoff_factor: float = 2.0) -> List[float]:
        for attempt in range(retries):
            try:
                payload = {
                    "model": "nomic-embed-text",
                    "prompt": text
                }
                response = requests.post(self.endpoint, json=payload, timeout=30)
                response.raise_for_status()
                data = response.json()
                return data.get("embedding", [])
            except Exception as e:
                if attempt < retries - 1:
                    sleep_time = backoff_factor ** attempt
                    print(f"Embedding retry: Rate limit/error hit. Retrying in {sleep_time} seconds (Attempt {attempt+1}/{retries})...")
                    time.sleep(sleep_time)
                    continue
                print(f"Failed to get embedding: {e}")
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
            raise ConnectionError(f"Could not connect to Qdrant cluster: {e}")

    def ensure_collection_exists(self, vector_size: int = 768):
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
            print(f"Failed to verify Qdrant collections: {e}")

    def upsert_points(self, points: List[qmodels.PointStruct]):
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def search_points(self, query_vector: List[float], limit: int = 3):
        return self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit
        ).points

class RAGService:
    def __init__(self):
        self.embedder = EmbeddingService()
        self.qdrant = QdrantService()
        self.qdrant.ensure_collection_exists(vector_size=768)

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Splits raw text into overlapping chunks using ingestion rules."""
        return chunk_text(text, chunk_size, overlap)

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
            print(f"Metadata extraction failed: {e}")
        return {"title": "Unknown Document", "service": "unknown", "type": "UNKNOWN"}

    def ingest_file(self, file_path: str, metadata: Dict[str, Any] = None):
        """Production pipeline for extracting text from TXT, MD, PDF, DOCX and indexing."""
        ext = file_path.split('.')[-1].lower()
        content = ""
        
        if ext in ["txt", "md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        elif ext == "pdf":
            try:
                reader = PdfReader(file_path)
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        content += extracted + "\n"
            except Exception as e:
                print(f"Error reading PDF {file_path}: {e}")
        elif ext == "docx":
            try:
                from docx import Document
                doc = Document(file_path)
                content = "\n".join([para.text for para in doc.paragraphs])
            except Exception as e:
                print(f"Error reading DOCX {file_path}: {e}")
        elif ext == "ipynb":
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    nb = json.load(f)
                    for cell in nb.get("cells", []):
                        if cell.get("cell_type") in ["markdown", "code"]:
                            src = cell.get("source", [])
                            if isinstance(src, list):
                                src = "".join(src)
                            if src:
                                content += src + "\n\n"
            except Exception as e:
                print(f"Error reading notebook {file_path}: {e}")
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        if not metadata:
            metadata = self.extract_metadata(content)

        doc_id = metadata.get("doc_id", f"FILE-{uuid.uuid4().hex[:8]}")
        title = metadata.get("title", os.path.basename(file_path))
        
        return {"doc_id": doc_id, "content_hash": content_hash, "metadata": metadata, "content": content, "title": title}

    def index_document(self, doc_id: str, title: str, content: str, metadata: Dict[str, Any]):
        """Chunks document, calls EmbeddingService, and stores in QdrantService."""
        chunks = self._chunk_text(content)
        
        points = []
        for i, chunk in enumerate(chunks):
            vector = self.embedder.get_embedding(chunk)
            payload = {
                "title": title,
                "content": chunk,
                "doc_id": doc_id,
                "chunk_index": i,
                **metadata
            }
            # Generate deterministic UUID point ID based on doc_id and chunk index
            point_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"{doc_id}_{i}"))
            points.append(qmodels.PointStruct(id=point_id, vector=vector, payload=payload))
            
        batch_size = 100
        if points:
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                self.qdrant.upsert_points(batch)

    def query_sop_runbooks(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Maintains the legacy interface expected by workflows.py but returns full metadata."""
        query_vector = self.embedder.get_embedding(query)
        results = self.qdrant.search_points(query_vector=query_vector, limit=limit)
        
        enhanced_results = []
        for r in results:
            payload = r.payload or {}
            enhanced_results.append({
                "content": payload.get("content", ""),
                "score": r.score,
                "title": payload.get("title", "Unknown"),
                "doc_id": payload.get("doc_id"),
                "chunk_index": payload.get("chunk_index"),
                "service": payload.get("service"),
                "type": payload.get("type"),
                "incident_id": payload.get("incident_id")
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
    print(f"Skipping RAG initialization and seeding due to missing dependencies: {e}")
    # Creating a stub rag_manager to avoid ImportErrors in workflows.py
    # if services fail to boot (e.g. no Qdrant connection).
    class StubRagManager:
        def query_sop_runbooks(self, query: str, limit: int = 3): return []
        def index_document(self, doc_id: str, title: str, content: str, metadata: Dict[str, Any]): pass
    rag_manager = StubRagManager()
