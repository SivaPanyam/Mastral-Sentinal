from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.database import get_db
from app.models import KnowledgeSource
from app.schemas import KnowledgeSourceCreate, KnowledgeSourceOut
from app.mastra.rag import rag_manager
from app.crud import KnowledgeSourceRepository
from app.auth import require_role, EnkryptMiddleware
from app.config import settings
import uuid
import os
import tempfile
import shutil

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

@router.get("/stats", response_model=Dict[str, Any])
def get_knowledge_stats(db: Session = Depends(get_db)):
    """Retrieve Enterprise Knowledge Platform dashboard statistics."""
    stats = {
        "indexed_documents": KnowledgeSourceRepository.get_all(db).__len__(),
        "embedding_provider": rag_manager.embedder.provider,
        "qdrant_collection": settings.QDRANT_COLLECTION,
        "collection_health": "UNKNOWN",
        "total_vectors": 0
    }
    try:
        if rag_manager.qdrant.client:
            col_info = rag_manager.qdrant.client.get_collection(settings.QDRANT_COLLECTION)
            stats["collection_health"] = col_info.status.value
            stats["total_vectors"] = col_info.points_count
    except Exception as e:
        stats["collection_health"] = f"ERROR: {str(e)}"
    
    return stats


@router.get("/documents", response_model=List[KnowledgeSourceOut])
def get_documents(db: Session = Depends(get_db)):
    """Retrieve all indexed standard operating procedures and previous post-mortems."""
    return KnowledgeSourceRepository.get_all(db)


@router.post("/documents", response_model=KnowledgeSourceOut, status_code=status.HTTP_201_CREATED)
def add_document(doc_in: KnowledgeSourceCreate, db: Session = Depends(get_db), current_user = Depends(require_role(["Admin", "SRE", "DevOps"]))):
    """Index a new SOP runbook and register it in Qdrant Vector indexes."""
    doc_id = f"KB-RUNBOOK-{uuid.uuid4().hex[:4].upper()}"
    
    # SCAN DOCUMENT
    scan_result = EnkryptMiddleware.scan_document(doc_in.content, current_user, db)
    
    # Register document into database
    new_doc = KnowledgeSource(
        id=doc_id,
        title=doc_in.title,
        type=doc_in.type,
        service=doc_in.service,
        content=scan_result.get("sanitized_text", doc_in.content),
        vectorId=doc_id,
        ingestion_status=scan_result.get("status", "COMPLETED")
    )
    
    # Only index if it passed
    if scan_result.get("status") != "QUARANTINED":
        # Sync with Qdrant vector manager
        rag_manager.index_document(
            doc_id=doc_id,
            title=doc_in.title,
            content=scan_result.get("sanitized_text", doc_in.content),
            metadata={"type": doc_in.type, "service": doc_in.service}
        )
    
    return KnowledgeSourceRepository.create(db, new_doc)

def _background_index_document(doc_id: str, title: str, content: str, metadata: dict, db: Session, pages=None):
    try:
        rag_manager.index_document(doc_id=doc_id, title=title, content=content, metadata=metadata, pages=pages)
        doc = KnowledgeSourceRepository.get_by_id(db, doc_id)
        if doc:
            doc.ingestion_status = "COMPLETED"
            KnowledgeSourceRepository.update(db, doc)
    except Exception as e:
        print(f"Background indexing failed for {doc_id}: {e}")
        doc = KnowledgeSourceRepository.get_by_id(db, doc_id)
        if doc:
            doc.ingestion_status = "FAILED"
            KnowledgeSourceRepository.update(db, doc)

@router.post("/upload", response_model=KnowledgeSourceOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["Admin", "SRE", "DevOps"]))
):
    """Upload a document, extract metadata, chunk by semantic strategies, and index."""
    ext = file.filename.split('.')[-1].lower()
    if ext not in ["txt", "md", "pdf", "html", "htm"]:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    # Save to temp file
    temp_fd, temp_path = tempfile.mkstemp(suffix=f".{ext}")
    try:
        with os.fdopen(temp_fd, 'wb') as f:
            shutil.copyfileobj(file.file, f)
            
        # Parse and extract metadata
        parsed_data = rag_manager.ingest_file(temp_path)
        content_hash = parsed_data["content_hash"]
        
        # Check duplicates
        existing = KnowledgeSourceRepository.get_by_checksum(db, content_hash)
        if existing:
            return existing

        doc_id = parsed_data["doc_id"]
        metadata = parsed_data["metadata"]
        
        # SCAN DOCUMENT
        scan_result = EnkryptMiddleware.scan_document(parsed_data["content"], current_user, db)
        
        # Create DB record
        new_doc = KnowledgeSource(
            id=doc_id,
            title=parsed_data["title"],
            type=metadata.get("type", "UNKNOWN"),
            service=metadata.get("service", "unknown"),
            content=scan_result.get("sanitized_text", parsed_data["content"]),
            vectorId=doc_id,
            checksum=content_hash,
            ingestion_status=scan_result.get("status", "PROCESSING"),
            source_path=file.filename,
            uploadedBy=current_user.get("id", "anonymous") if isinstance(current_user, dict) else getattr(current_user, 'id', 'anonymous')
        )
        
        created_doc = KnowledgeSourceRepository.create(db, new_doc)
        
        # Only schedule background indexing if it passed security checks
        if scan_result.get("status") != "QUARANTINED":
            background_tasks.add_task(
                _background_index_document,
                doc_id=doc_id,
                title=parsed_data["title"],
                content=scan_result.get("sanitized_text", parsed_data["content"]),
                metadata=metadata,
                db=db,
                pages=parsed_data.get("pages")
            )
        
        return created_doc
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

class IngestSourceRequest(BaseModel):
    source_path: str

@router.post("/ingest", response_model=KnowledgeSourceOut, status_code=status.HTTP_201_CREATED)
def ingest_source(
    req: IngestSourceRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["Admin", "SRE", "DevOps"]))
):
    """Ingest a remote URL, GitHub raw link, or local folder."""
    try:
        parsed_data = rag_manager.ingest_file(req.source_path)
        content_hash = parsed_data["content_hash"]
        
        existing = KnowledgeSourceRepository.get_by_checksum(db, content_hash)
        if existing:
            return existing

        doc_id = parsed_data["doc_id"]
        metadata = parsed_data["metadata"]
        
        scan_result = EnkryptMiddleware.scan_document(parsed_data["content"], current_user, db)
        
        new_doc = KnowledgeSource(
            id=doc_id,
            title=parsed_data["title"],
            type=metadata.get("type", "UNKNOWN"),
            service=metadata.get("service", "unknown"),
            content=scan_result.get("sanitized_text", parsed_data["content"]),
            vectorId=doc_id,
            checksum=content_hash,
            ingestion_status=scan_result.get("status", "PROCESSING"),
            source_path=req.source_path,
            uploadedBy=current_user.get("id", "anonymous") if isinstance(current_user, dict) else getattr(current_user, 'id', 'anonymous')
        )
        
        created_doc = KnowledgeSourceRepository.create(db, new_doc)
        
        if scan_result.get("status") != "QUARANTINED":
            background_tasks.add_task(
                _background_index_document,
                doc_id=doc_id,
                title=parsed_data["title"],
                content=scan_result.get("sanitized_text", parsed_data["content"]),
                metadata=metadata,
                db=db,
                pages=parsed_data.get("pages")
            )
        
        return created_doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/{document_id}/reindex", status_code=status.HTTP_202_ACCEPTED)
def reindex_document(document_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user = Depends(require_role(["Admin", "SRE"]))):
    """Force re-embedding and chunking of an existing document."""
    doc = KnowledgeSourceRepository.get_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc.ingestion_status = "PROCESSING"
    KnowledgeSourceRepository.update(db, doc)
    
    metadata = {"type": doc.type, "service": doc.service}
    if doc.source_metadata:
        metadata.update(doc.source_metadata)
        
    background_tasks.add_task(
        _background_index_document,
        doc_id=doc.id,
        title=doc.title,
        content=doc.content,
        metadata=metadata,
        db=db,
        pages=None # will fall back to simple chunking if original pages not stored
    )
    return {"message": "Re-indexing started"}

@router.get("/search")
def search_vector_kb(query: str, service: Optional[str] = None, doc_type: Optional[str] = None, limit: Optional[int] = 3):
    """
    Query the Qdrant vector indexes using Hybrid Retrieval (Semantic + Keyword + Reranking).
    """
    if not query:
        raise HTTPException(status_code=400, detail="Query text cannot be empty")
        
    filter_conditions = {}
    if service:
        filter_conditions["service"] = service
    if doc_type:
        filter_conditions["doc_type"] = doc_type
        
    try:
        from app.telemetry import VECTOR_SEARCH_COUNTER
        VECTOR_SEARCH_COUNTER.labels(collection="knowledge").inc()
        return rag_manager.query_sop_runbooks(query=query, limit=limit, filter_conditions=filter_conditions)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{document_id}", response_model=KnowledgeSourceOut)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get a single knowledge document by ID."""
    doc = KnowledgeSourceRepository.get_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.put("/documents/{document_id}", response_model=KnowledgeSourceOut)
def update_document(document_id: str, doc_in: KnowledgeSourceCreate, db: Session = Depends(get_db), current_user = Depends(require_role(["Admin", "SRE"]))):
    """Update a knowledge document."""
    doc = KnowledgeSourceRepository.get_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # We would ideally update Qdrant here too if the content changed
    for field, value in doc_in.model_dump().items():
        setattr(doc, field, value)
        
    return KnowledgeSourceRepository.update(db, doc)

@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, db: Session = Depends(get_db), current_user = Depends(require_role(["Admin"]))):
    """Delete a knowledge document from DB and Qdrant."""
    doc = KnowledgeSourceRepository.get_by_id(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if doc.vectorId:
        try:
            if hasattr(rag_manager, 'qdrant') and hasattr(rag_manager.qdrant, 'client') and rag_manager.qdrant.client:
                # Assuming chunk IDs use the doc_id prefix, we could delete by filter
                # Or just by point payload filter
                rag_manager.qdrant.client.delete(
                    collection_name=settings.QDRANT_COLLECTION,
                    points_selector=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key="doc_id",
                                match=qmodels.MatchValue(value=doc.vectorId)
                            )
                        ]
                    )
                )
        except Exception as e:
            print(f"Failed to delete vector {doc.vectorId} from Qdrant: {e}")
            
    KnowledgeSourceRepository.delete(db, doc)
    return
