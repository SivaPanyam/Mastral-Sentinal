"""
models/tenant.py
----------------
Tenant and Environment models for multi-tenancy and environment separation.
"""

import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base, AuditMixin

class Tenant(Base, AuditMixin):
    __tablename__ = "tenants"

    id = Column(
        String,
        primary_key=True,
        default=lambda: f"tnt-{uuid.uuid4().hex[:8]}",
        index=True,
    )
    name = Column("name", String, unique=True, index=True, nullable=False)
    slug = Column("slug", String, unique=True, index=True, nullable=False)
    is_active = Column("is_active", Boolean, default=True, nullable=False)
    
    # Optional SSO configuration for the tenant
    sso_domain = Column("sso_domain", String, nullable=True)

    environments = relationship("Environment", back_populates="tenant", cascade="all, delete-orphan")


class Environment(Base, AuditMixin):
    __tablename__ = "environments"

    id = Column(
        String,
        primary_key=True,
        default=lambda: f"env-{uuid.uuid4().hex[:8]}",
        index=True,
    )
    tenant_id = Column("tenant_id", String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column("name", String, nullable=False) # e.g. PRODUCTION, STAGING, DEVELOPMENT
    is_active = Column("is_active", Boolean, default=True, nullable=False)

    tenant = relationship("Tenant", back_populates="environments", foreign_keys=[tenant_id], primaryjoin="Environment.tenant_id == Tenant.id")
