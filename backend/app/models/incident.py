"""
models/incident.py
------------------
Core incident record.  Supports full lifecycle state machine from TRIGGERED
through CLOSED, SLA tracking, priority/severity classification, environment
tagging, multi-service impact recording, and soft-delete.

The many-to-many join table to KnowledgeSource is declared here so that
SQLAlchemy can resolve forward references before the mapper finalises.
"""

import uuid

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship

from .base import AuditMixin, Base


# ── Association table: Incident ↔ KnowledgeSource (M:N) ──────────────────────
incident_knowledge_association = Table(
    "incident_knowledge_association",
    Base.metadata,
    Column(
        "incident_id",
        String,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "knowledge_id",
        String,
        ForeignKey("knowledge_sources.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Incident(AuditMixin, Base):
    __tablename__ = "incidents"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    incident_number = Column(
        "incident_number",
        String,
        unique=True,
        index=True,
        nullable=False,
        default=lambda: f"INC-2026-{uuid.uuid4().hex[:6].upper()}",
    )
    title       = Column("title",       String, nullable=False)
    description = Column("description", Text,   nullable=True)

    # ── Classification ────────────────────────────────────────────────────────
    # status:      TRIGGERED | TRIAGED | DIAGNOSING | INVESTIGATING | MITIGATED | RESOLVED | CLOSED
    # severity:    CRITICAL | HIGH | MEDIUM | LOW
    # priority:    P0 | P1 | P2 | P3 | P4
    # category:    INFRASTRUCTURE | APPLICATION | SECURITY | DATABASE | NETWORK
    # environment: PRODUCTION | STAGING | DEVELOPMENT
    # source:      PROMETHEUS | DATADOG | MANUAL | SLACK
    status      = Column("status",      String, default="TRIGGERED",   nullable=False)
    severity    = Column("severity",    String, default="HIGH",         nullable=False)
    priority    = Column("priority",    String, default="P1",           nullable=False)
    category    = Column("category",    String, default="APPLICATION",  nullable=False)
    environment = Column("environment", String, default="PRODUCTION",   nullable=False)
    # 'service' Python attribute → 'service_name' column (backward compat)
    service     = Column("service_name", String, nullable=False)
    source      = Column("source",       String, default="MANUAL",      nullable=False)

    # ── Root-cause & Resolution ───────────────────────────────────────────────
    root_cause     = Column("root_cause",     Text, nullable=True)
    resolution     = Column("resolution",     Text, nullable=True)
    impact_summary = Column("impact_summary", Text, nullable=True)

    # ── Service Impact ────────────────────────────────────────────────────────
    affected_services = Column("affected_services", JSON, nullable=True)
    tags              = Column("tags",              JSON, nullable=True)

    # ── Assignment ────────────────────────────────────────────────────────────
    assignedTo = Column(
        "assigned_to",
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    createdBy = Column(
        "created_by",
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Lifecycle Timestamps ──────────────────────────────────────────────────
    detectedAt     = Column("detected_at",     DateTime(timezone=True), default=__import__("datetime").datetime.utcnow, nullable=False)
    acknowledgedAt = Column("acknowledged_at", DateTime(timezone=True), nullable=True)
    resolvedAt     = Column("resolved_at",     DateTime(timezone=True), nullable=True)
    closedAt       = Column("closed_at",       DateTime(timezone=True), nullable=True)
    slaDue         = Column("sla_due",         DateTime(timezone=True), nullable=True)
    leadTimeSeconds = Column("lead_time_seconds", Integer, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    logs           = relationship("IncidentLog",     back_populates="incident", cascade="all, delete-orphan")
    agent_outputs  = relationship("AgentOutput",     back_populates="incident", cascade="all, delete-orphan")
    reports        = relationship("Report",          back_populates="incident", cascade="all, delete-orphan")
    knowledge_entries = relationship(
        "KnowledgeSource",
        secondary=incident_knowledge_association,
        back_populates="incidents",
    )
    creator  = relationship("User", foreign_keys=[createdBy],  back_populates="incidents_created")
    assignee = relationship("User", foreign_keys=[assignedTo])

    # ── Constraints ───────────────────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "status IN ('TRIGGERED','TRIAGED','DIAGNOSING','INVESTIGATING','MITIGATED','RESOLVED','CLOSED')",
            name="valid_incident_status",
        ),
        CheckConstraint(
            "severity IN ('CRITICAL','HIGH','MEDIUM','LOW')",
            name="valid_incident_severity",
        ),
        CheckConstraint(
            "priority IN ('P0','P1','P2','P3','P4')",
            name="valid_incident_priority",
        ),
    )
