"""
models/user.py
--------------
User account model with role-based access control, security tracking columns,
and relationships to incidents, reports and audit logs.
"""

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from .base import AuditMixin, Base


class User(AuditMixin, Base):
    __tablename__ = "users"

    # ── Primary Key ──────────────────────────────────────────────────────────
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # ── Identity ─────────────────────────────────────────────────────────────
    username        = Column("username",        String,  unique=True, index=True, nullable=False)
    email           = Column("email",           String,  unique=True, index=True, nullable=False)
    name            = Column("name",            String,  nullable=False)
    hashed_password = Column("hashed_password", String,  nullable=False)
    first_name      = Column("first_name",      String,  nullable=True)
    last_name       = Column("last_name",       String,  nullable=True)

    # ── RBAC & Status ────────────────────────────────────────────────────────
    # role:   Admin | SRE | Security Analyst | DevOps | Viewer
    # status: ACTIVE | SUSPENDED | INACTIVE
    role   = Column("role",   String, default="Viewer", nullable=False)
    status = Column("status", String, default="ACTIVE",  nullable=False)

    # ── Profile ───────────────────────────────────────────────────────────────
    avatar_url   = Column("avatar_url",   String, nullable=True)
    phone_number = Column("phone_number", String, nullable=True)
    department   = Column("department",   String, nullable=True)
    timezone     = Column("timezone",     String, default="UTC", nullable=False)

    # ── Security Tracking ────────────────────────────────────────────────────
    last_login            = Column("last_login",            DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column("failed_login_attempts", Integer, default=0,    nullable=False)
    is_active             = Column("is_active",             Boolean, default=True,  nullable=False)
    email_verified        = Column("email_verified",        Boolean, default=False, nullable=False)

    # ── Relationships ────────────────────────────────────────────────────────
    incidents_created = relationship(
        "Incident",
        foreign_keys="[Incident.createdBy]",
        back_populates="creator",
    )
    reports_created = relationship(
        "Report",
        foreign_keys="[Report.approvedBy]",
        back_populates="approver",
    )
    audit_logs = relationship("AuditLog", back_populates="user")
    settings   = relationship("Settings", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # ── Constraints ──────────────────────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "role IN ('Admin', 'SRE', 'Security Analyst', 'DevOps', 'Viewer')",
            name="valid_user_roles",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'SUSPENDED', 'INACTIVE')",
            name="valid_user_status",
        ),
    )
