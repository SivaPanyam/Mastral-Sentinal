"""
models/audit_log.py
-------------------
Immutable append-only audit trail for every state-changing operation in the
platform.  Captures actor, resource, request payload and HTTP response code.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from .base import AuditMixin, Base


class AuditLog(AuditMixin, Base):
    __tablename__ = "audit_logs"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # ── Actor ─────────────────────────────────────────────────────────────────
    userId = Column(
        "user_id",
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Operation ─────────────────────────────────────────────────────────────
    action       = Column("action",        String, nullable=False)
    resourceType = Column("resource_type", String, nullable=False)
    resourceId   = Column("resource_id",   String, nullable=True)

    # ── Request Context ───────────────────────────────────────────────────────
    ip_address      = Column("ip_address",      String, nullable=True)
    user_agent      = Column("user_agent",      String, nullable=True)
    # 'details' Python attribute → 'request_payload' column (backward compat)
    details         = Column("request_payload", JSON,   nullable=True)
    response_status = Column("response_status", String, nullable=True)

    # ── Event Timestamp ───────────────────────────────────────────────────────
    timestamp = Column(
        "timestamp",
        DateTime(timezone=True),
        default=__import__("datetime").datetime.utcnow,
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user = relationship("User", back_populates="audit_logs")
