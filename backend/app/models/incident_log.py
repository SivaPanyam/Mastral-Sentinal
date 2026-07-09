"""
models/incident_log.py
----------------------
Structured log entry emitted by a service during an incident window.
Supports distributed-tracing identifiers (trace_id / span_id), component
topology (host / container / namespace), and an optional JSON parsed_log
blob for pre-parsed structured output.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import relationship

from .base import AuditMixin, Base


class IncidentLog(AuditMixin, Base):
    __tablename__ = "incident_logs"

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

    # ── Event Timestamp ───────────────────────────────────────────────────────
    timestamp = Column(
        "timestamp",
        DateTime(timezone=True),
        default=__import__("datetime").datetime.utcnow,
        nullable=False,
    )

    # ── Log Classification ────────────────────────────────────────────────────
    # 'level' Python attribute → 'log_level' column (backward compat)
    # Values: INFO | WARN | ERROR | FATAL
    level = Column("log_level", String, default="ERROR", nullable=False)

    # ── Source Topology ───────────────────────────────────────────────────────
    service   = Column("service",   String, nullable=False)
    component = Column("component", String, nullable=True)
    host      = Column("host",      String, nullable=True)
    container = Column("container", String, nullable=True)
    namespace = Column("namespace", String, nullable=True)

    # ── Distributed Tracing ───────────────────────────────────────────────────
    trace_id = Column("trace_id", String, nullable=True)
    span_id  = Column("span_id",  String, nullable=True)

    # ── Log Content ───────────────────────────────────────────────────────────
    # 'message' Python attribute → 'raw_log' column (backward compat)
    message    = Column("raw_log",    Text, nullable=False)
    parsed_log = Column("parsed_log", JSON, nullable=True)
    # 'log_metadata' avoids clash with SQLAlchemy's reserved 'metadata' attr
    log_metadata = Column("metadata", JSON, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    incident = relationship("Incident", back_populates="logs")
