"""
models/report.py
----------------
AI-generated Root Cause Analysis (RCA) report attached to an incident.
Supports human review / approval workflow, export format tracking,
and preventive-action recommendations.
"""

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import AuditMixin, Base


class Report(AuditMixin, Base):
    __tablename__ = "reports"

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

    # ── Report Content ────────────────────────────────────────────────────────
    title = Column("title", String, nullable=False)

    # 'summary' Python attribute → 'executive_summary' column (backward compat)
    summary  = Column("executive_summary",   Text, nullable=False)
    timeline = Column("timeline",            JSON, nullable=False)   # list[{timestamp, event}]

    # 'rootCause' Python attribute → 'root_cause_analysis' column
    rootCause = Column("root_cause_analysis", Text, nullable=False)
    # 'impact' Python attribute → 'impact_analysis' column
    impact    = Column("impact_analysis",      Text, nullable=False)

    recommendations   = Column("recommendations",    JSON, nullable=True)  # list[str]
    preventive_actions = Column("preventive_actions", JSON, nullable=True)  # list[str]

    # ── Generation Metadata ───────────────────────────────────────────────────
    generated_by_agent = Column("generated_by_agent", Boolean, default=True, nullable=False)

    # ── Approval Workflow ─────────────────────────────────────────────────────
    # approval_status: PENDING | APPROVED | REJECTED
    approvedBy = Column(
        "approved_by",
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approval_status = Column("approval_status", String, default="APPROVED", nullable=False)
    exported_formats = Column("exported_formats", JSON, nullable=True)   # ["PDF","JSON","HTML"]

    # ── Override createdBy default ────────────────────────────────────────────
    createdBy = Column("created_by", String, default="Mastra SRE Pipeline", nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    incident = relationship("Incident",  back_populates="reports")
    approver = relationship("User", foreign_keys=[approvedBy], back_populates="reports_created")

    # ── Constraints ───────────────────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "approval_status IN ('PENDING', 'APPROVED', 'REJECTED')",
            name="valid_report_approval_status",
        ),
    )
