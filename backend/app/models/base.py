"""
models/base.py
--------------
Shared declarative Base (imported from app.database so the whole project
shares one SQLAlchemy metadata object) and the AuditMixin that stamps every
enterprise model with the standard tracking columns:

  created_at / updated_at / deleted_at   – timezone-aware timestamps
  created_by / updated_by               – actor strings (user-id or system label)
  version                               – optimistic-locking counter
"""

import datetime

from sqlalchemy import Column, DateTime, Integer, String

# Single source of truth: the Base declared in database.py carries the shared
# MetaData that Alembic and create_all() use.
from app.database import Base  # noqa: F401  (re-exported for convenience)


class AuditMixin:
    """
    Mixin that injects standard enterprise audit / soft-delete columns into
    any model that inherits from it.  All timestamps are stored WITH timezone.

    Models that need to rename an inherited column (e.g. KnowledgeSource maps
    'updated_at' to Python attr 'lastUpdated') should simply redeclare the
    column with a different Python name in the concrete model class.
    """

    createdAt = Column(
        "created_at",
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        nullable=False,
    )
    updatedAt = Column(
        "updated_at",
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )
    deletedAt = Column("deleted_at", DateTime(timezone=True), nullable=True)
    createdBy = Column("created_by", String, nullable=True)
    updatedBy = Column("updated_by", String, nullable=True)
    version   = Column("version", Integer, default=1, nullable=False)

