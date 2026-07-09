from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import KnowledgeSource
from app.schemas import KnowledgeSourceCreate, KnowledgeSourceOut
from app.mastra.rag import rag_manager
from app.crud import KnowledgeSourceRepository
from app.auth import require_role
from app.config import settings
import uuid
import os
import tempfile
import shutil

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

@router.get("/documents", response_model=List[KnowledgeSourceOut])
def get_documents(db: Session = Depends(get_db)):
    """Retrieve all indexed standard operating procedures and previous post-mortems."""
    return KnowledgeSourceRepository.get_all(db)


@router.post("/documents", response_model=KnowledgeSourceOut, status_code=status.HTTP_201_CREATED)
def add_document(doc_in: KnowledgeSourceCreate, db: Session = Depends(get_db), current_user = Depends(require_role(["Admin", "SRE", "DevOps"]))):
    """Index a new SOP runbook and register it in Qdrant Vector indexes."""
    doc_id = f"KB-RUNBOOK-{uuid.uuid4().hex[:4].upper()}"
    
    # Register document into database
    new_doc = KnowledgeSource(
        id=doc_id,
        title=doc_in.title,
        type=doc_in.type,
        service=doc_in.service,
        content=doc_in.content,
        vectorId=doc_id
    )
    
    # Sync with Qdrant vector manager
    rag_manager.index_document(
        doc_id=doc_id,
        title=doc_in.title,
        content=doc_in.content,
        metadata={"type": doc_in.type, "service": doc_in.service}
    )
    
    return KnowledgeSourceRepository.create(db, new_doc)

def _background_index_document(doc_id: str, title: str, content: str, metadata: dict, db: Session):
    try:
        rag_manager.index_document(doc_id=doc_id, title=title, content=content, metadata=metadata)
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
    """Upload a document (PDF, TXT, MD, DOCX), extract metadata, and index in background."""
    ext = file.filename.split('.')[-1].lower()
    if ext not in ["txt", "md", "pdf", "docx"]:
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
        
        # Create DB record
        new_doc = KnowledgeSource(
            id=doc_id,
            title=parsed_data["title"],
            type=metadata.get("type", "UNKNOWN"),
            service=metadata.get("service", "unknown"),
            content=parsed_data["content"],
            vectorId=doc_id,
            checksum=content_hash,
            ingestion_status="PROCESSING",
            source_path=file.filename,
            uploadedBy=current_user.id
        )
        
        created_doc = KnowledgeSourceRepository.create(db, new_doc)
        
        # Schedule background indexing
        background_tasks.add_task(
            _background_index_document,
            doc_id=doc_id,
            title=parsed_data["title"],
            content=parsed_data["content"],
            metadata=metadata,
            db=db
        )
        
        return created_doc
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/search")
def search_vector_kb(query: str, limit: Optional[int] = 3):
    """
    Query the Qdrant vector indexes using similarity embeddings.
    Returns matched SOP runbooks with proximity scores.
    """
    if not query:
        raise HTTPException(status_code=400, detail="Query text cannot be empty")
    try:
        return rag_manager.query_sop_runbooks(query=query, limit=limit)
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
                rag_manager.qdrant.client.delete(
                    collection_name=settings.QDRANT_COLLECTION,
                    points_selector=[doc.vectorId]
                )
        except Exception as e:
            print(f"Failed to delete vector {doc.vectorId} from Qdrant: {e}")
            
    KnowledgeSourceRepository.delete(db, doc)
    return
