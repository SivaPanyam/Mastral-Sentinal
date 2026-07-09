"""
models/settings.py
------------------
Per-user persisted preferences: UI theme, notification config, AI model
preferences, Enkrypt guardrail overrides, default dashboard and locale.
One Settings row per User (enforced by UniqueConstraint on user_id).
"""

import uuid

from sqlalchemy import Column, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from .base import AuditMixin, Base


class Settings(AuditMixin, Base):
    __tablename__ = "settings"

    # ── Primary Key ───────────────────────────────────────────────────────────
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # ── UI Preferences ────────────────────────────────────────────────────────
    theme             = Column("theme",             String, default="dark",                nullable=False)
    language          = Column("language",          String, default="en",                  nullable=False)
    timezone          = Column("timezone",          String, default="UTC",                 nullable=False)
    default_dashboard = Column("default_dashboard", String, default="Incident Analytics",  nullable=False)

    # ── Notification Configuration ────────────────────────────────────────────
    # JSON schema: { email: bool, slack: bool, pagerduty: bool, digest_interval: str }
    notifications = Column("notifications", JSON, nullable=True)

    # ── AI & Guardrail Preferences ────────────────────────────────────────────
    # JSON schema: { model: str, temperature: float, max_tokens: int }
    ai_preferences = Column("ai_preferences", JSON, nullable=True)
    # JSON schema: { prompt_injection: bool, sensitive_data: bool, hallucination: bool }
    guardrail_settings = Column("guardrail_settings", JSON, nullable=True)

    # ── Linked User (1:1) ─────────────────────────────────────────────────────
    userId = Column(
        "user_id",
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user = relationship(
        "User",
        back_populates="settings",
        uselist=False,
    )
