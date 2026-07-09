"""
models/agent_output.py
----------------------
Persists the full execution trace of every Mastra SRE agent run:
prompt, retrieved RAG context, raw LLM response, confidence score,
token usage, and execution duration.  Linked to the incident that
triggered the agent.
"""

import datetime
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class AgentOutput(Base):
    __tablename__ = "agent_outputs"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # ── Parent Incident ───────────────────────────────────────────────────────
    incidentId = Column(
        "incident_id",
        String,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Agent Identity ────────────────────────────────────────────────────────
    # 'agentType' Python attribute → 'agent_name' column (backward compat)
    agentType     = Column("agent_name",    String, nullable=False)
    agent_version = Column("agent_version", String, default="v2.1.0", nullable=False)

    # ── Execution Inputs ──────────────────────────────────────────────────────
    prompt            = Column("prompt",            Text, nullable=True)
    retrieved_context = Column("retrieved_context", Text, nullable=True)

    # ── Execution Outputs ─────────────────────────────────────────────────────
    # 'payload' Python attribute → 'llm_response' column (backward compat)
    payload    = Column("llm_response", JSON, nullable=True)
    summary    = Column("summary",      Text, nullable=False)

    # ── Quality Metrics ───────────────────────────────────────────────────────
    # 'confidence' Python attribute → 'confidence_score' column
    confidence     = Column("confidence_score", Float,   default=1.0,             nullable=False)
    execution_time = Column("execution_time",   Integer, nullable=True)
    token_usage    = Column("token_usage",      JSON,    nullable=True)
    model_name     = Column("model_name",       String,  default="gemini-2.5-flash", nullable=False)

    # ── Run Status ────────────────────────────────────────────────────────────
    # Values: RUNNING | COMPLETED | FAILED
    status = Column("status", String, default="COMPLETED", nullable=False)

    # ── Timestamps & Audit ────────────────────────────────────────────────────
    # 'timestamp' Python attr → 'created_at' column (backward compat with routes)
    timestamp  = Column("created_at",  DateTime(timezone=True), default=datetime.datetime.utcnow, nullable=False)
    updatedAt  = Column("updated_at",  DateTime(timezone=True), default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    deletedAt  = Column("deleted_at",  DateTime(timezone=True), nullable=True)
    createdBy  = Column("created_by",  String, nullable=True)
    updatedBy  = Column("updated_by",  String, nullable=True)
    version    = Column("version",     Integer, default=1, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    incident = relationship("Incident", back_populates="agent_outputs")
