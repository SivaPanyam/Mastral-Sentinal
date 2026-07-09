"""
models/knowledge_source.py
--------------------------
Represents a document ingested into the Qdrant vector store.
Tracks source provenance (path / URL / checksum), embedding parameters,
chunking metadata, and ingestion lifecycle status.
"""

import datetime
import uuid

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from .base import Base
from .incident import incident_knowledge_association


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    title = Column("title", String, nullable=False)
    # 'type' Python attribute → 'source_type' column
    # Values: RUNBOOK | POST_MORTEM | ARCHITECTURE | PLAYBOOK | WIKI
    type = Column("source_type", String, nullable=False)

    # ── Source Provenance ─────────────────────────────────────────────────────
    source_path = Column("source_path", String, nullable=True)
    source_url  = Column("source_url",  String, nullable=True)
    checksum    = Column("checksum",    String, nullable=True)

    # ── Embedding / Vector Parameters ─────────────────────────────────────────
    embedding_model   = Column("embedding_model",   String,  default="text-embedding-004", nullable=False)
    chunk_count       = Column("chunk_count",       Integer, default=1,               nullable=False)
    vector_collection = Column("vector_collection", String,  default="sentinel_kb",   nullable=False)

    # ── Ingestion Lifecycle ───────────────────────────────────────────────────
    # Values: PENDING | PROCESSING | COMPLETED | FAILED
    ingestion_status = Column("ingestion_status", String, default="COMPLETED", nullable=False)
    uploadedBy       = Column("uploaded_by",      String, nullable=True)

    # ── Content ───────────────────────────────────────────────────────────────
    content         = Column("content",   Text,   nullable=False)
    vectorId        = Column("vector_id", String, nullable=True)  # backward compat
    source_metadata = Column("metadata",  JSON,   nullable=True)

    # ── Enterprise Audit Columns (manually declared so we can alias updatedAt) ─
    createdAt  = Column("created_at",  DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False)
    # 'lastUpdated' Python attr → 'updated_at' column (backward compat with routes)
    lastUpdated = Column("updated_at", DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    deletedAt  = Column("deleted_at",  DateTime(timezone=True), nullable=True)
    createdBy  = Column("created_by",  String, nullable=True)
    updatedBy  = Column("updated_by",  String, nullable=True)
    version    = Column("version",     Integer, default=1, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    incidents = relationship(
        "Incident",
        secondary=incident_knowledge_association,
        back_populates="knowledge_entries",
    )
