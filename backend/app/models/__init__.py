"""
models/__init__.py
------------------
Public surface of the models package.

Every file that currently does:

    from app.models import User, Incident, ...

will continue to work without any change because all symbols are
re-exported here.

Import order matters: Base must be imported before any model so that
SQLAlchemy's mapper can resolve the shared metadata object.  Models with
forward-reference relationships are imported last.
"""

# 1. Shared declarative base and audit mixin
from .base import Base, AuditMixin                          # noqa: F401

# 2. Models with no foreign-key dependencies
from .user        import User                               # noqa: F401
from .audit_log   import AuditLog                          # noqa: F401

# 3. Core domain model (declares the M:N association table)
from .incident        import Incident, incident_knowledge_association   # noqa: F401

# 4. Child models that FK → incidents
from .incident_log    import IncidentLog                   # noqa: F401
from .agent_output    import AgentOutput                   # noqa: F401
from .report          import Report                        # noqa: F401
from .knowledge_source import KnowledgeSource             # noqa: F401

# 5. User-linked preference model
from .settings        import Settings                      # noqa: F401

__all__ = [
    "Base",
    "AuditMixin",
    "User",
    "AuditLog",
    "Incident",
    "incident_knowledge_association",
    "IncidentLog",
    "AgentOutput",
    "Report",
    "KnowledgeSource",
    "Settings",
]
