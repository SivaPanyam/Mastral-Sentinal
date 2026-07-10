"""
models/log_entry.py
-------------------
Generic model to store all normalized telemetry logs regardless of source.
Preserves the raw log and metadata for comprehensive auditing and search.
"""

import uuid
import datetime
from sqlalchemy import Column, String, DateTime, Text, JSON
from .base import Base

class LogEntry(Base):
    __tablename__ = "log_entries"

    # Primary Key
    id = Column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # Core Fields
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
        index=True
    )
    service = Column(String, nullable=False, index=True)
    hostname = Column(String, nullable=True)
    environment = Column(String, nullable=True)
    severity = Column(String, nullable=False, index=True)
    message = Column(Text, nullable=False)
    source = Column(String, nullable=False)
    application = Column(String, nullable=True)
    
    # Tracing
    trace_id = Column(String, nullable=True, index=True)
    span_id = Column(String, nullable=True)
    request_id = Column(String, nullable=True, index=True)

    # JSON Metadata and Raw Log
    metadata_json = Column("metadata", JSON, nullable=True)
    raw_log = Column(Text, nullable=False)
