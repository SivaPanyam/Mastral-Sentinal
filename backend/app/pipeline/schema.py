from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import datetime

class NormalizedLog(BaseModel):
    """
    The unified schema for all parsed logs across the pipeline.
    """
    timestamp: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc), 
        description="Event timestamp"
    )
    service: str = Field(default="UNKNOWN_SERVICE", description="Service name generating the log")
    hostname: Optional[str] = Field(default=None, description="Host/node name")
    environment: Optional[str] = Field(default=None, description="Environment (prod, staging, dev)")
    severity: str = Field(default="INFO", description="Log level/severity")
    message: str = Field(..., description="The main log message")
    source: str = Field(default="unknown", description="Source parser or ingestion method")
    application: Optional[str] = Field(default=None, description="Application or component name")
    trace_id: Optional[str] = Field(default=None, description="Distributed tracing trace_id")
    span_id: Optional[str] = Field(default=None, description="Distributed tracing span_id")
    request_id: Optional[str] = Field(default=None, description="Unique HTTP request ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional unstructured metadata extracted from the log")
    raw_log: str = Field(..., description="The exact original raw log line")
