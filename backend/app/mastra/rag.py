import os
import uuid
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from google import genai
from pypdf import PdfReader
from app.config import settings

class EmbeddingService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", settings.GEMINI_API_KEY)
        self.client = None
        if self.api_key and self.api_key != "mock-gemini-key":
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"Failed to init Gemini in EmbeddingService: {e}")

    def get_embedding(self, text: str) -> List[float]:
        if not self.client:
            raise ValueError("Gemini client not initialized for real embeddings. Provide a valid GEMINI_API_KEY.")
        
        response = self.client.models.embed_content(
            model='text-embedding-004',
            contents=text,
        )
        return response.embeddings[0].values

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
        return self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )

class RAGService:
    def __init__(self):
        self.embedder = EmbeddingService()
        self.qdrant = QdrantService()
        self.qdrant.ensure_collection_exists(vector_size=768)

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Splits raw text into overlapping chunks."""
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = start + chunk_size
            chunks.append(text[start:end])
            if end >= text_len:
                break
            start = end - overlap
        return chunks

    def ingest_file(self, file_path: str, metadata: Dict[str, Any]):
        """Production pipeline for extracting text from TXT, MD, PDF and indexing."""
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
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        doc_id = metadata.get("doc_id", f"FILE-{uuid.uuid4().hex[:8]}")
        title = metadata.get("title", os.path.basename(file_path))
        self.index_document(doc_id=doc_id, title=title, content=content, metadata=metadata)

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
            # Generate deterministic point ID based on doc_id and chunk index
            point_id = hash(f"{doc_id}_{i}") % (10**8)
            points.append(qmodels.PointStruct(id=point_id, vector=vector, payload=payload))
            
        if points:
            self.qdrant.upsert_points(points)

    def query_sop_runbooks(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Maintains the legacy interface expected by workflows.py."""
        query_vector = self.embedder.get_embedding(query)
        results = self.qdrant.search_points(query_vector=query_vector, limit=limit)
        return [{**r.payload, "score": r.score} for r in results]

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
