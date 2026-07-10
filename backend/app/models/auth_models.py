"""
models/auth_models.py
---------------------
Models for advanced authentication including API Keys, Sessions, and SSO Identities.
"""

import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from .base import Base, AuditMixin

class ApiKey(Base, AuditMixin):
    __tablename__ = "api_keys"

    id = Column(
        String,
        primary_key=True,
        default=lambda: f"ak-{uuid.uuid4().hex[:12]}",
        index=True,
    )
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False)  # Hashed key for validation
    prefix = Column(String, nullable=False)    # First 4 chars for identification e.g. mastra_abcd...
    scopes = Column(JSON, nullable=True)       # e.g. ["incidents:read", "knowledge:write"]
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="api_keys")


class UserSession(Base, AuditMixin):
    __tablename__ = "user_sessions"

    id = Column(
        String,
        primary_key=True,
        default=lambda: f"sess-{uuid.uuid4().hex}",
        index=True,
    )
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token = Column(String, unique=True, index=True, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="sessions")


class UserIdentity(Base, AuditMixin):
    __tablename__ = "user_identities"

    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String, nullable=False) # e.g. 'google', 'microsoft'
    provider_id = Column(String, nullable=False, index=True) # ID from the SSO provider
    profile_data = Column(JSON, nullable=True) # Extra info like avatar_url or raw claims

    user = relationship("User", back_populates="identities")
