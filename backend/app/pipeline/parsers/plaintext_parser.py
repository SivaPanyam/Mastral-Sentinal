import datetime
from typing import Dict, Any

from app.pipeline.schema import NormalizedLog
from app.pipeline.parsers.base import BaseParser

class PlaintextParser(BaseParser):
    """
    Fallback parser for arbitrary plaintext logs.
    Always returns True for can_parse.
    """
    
    def can_parse(self, raw_log: str) -> bool:
        return True
        
    def parse(self, raw_log: str, source_metadata: Dict[str, Any]) -> NormalizedLog:
        # We can try to guess severity from the text
        upper_log = raw_log.upper()
        level = source_metadata.get("level", "INFO")
        
        # Simple heuristic to extract level from text if not provided
        if "level" not in source_metadata:
            if "CRITICAL" in upper_log or "FATAL" in upper_log:
                level = "CRITICAL"
            elif "ERROR" in upper_log:
                level = "ERROR"
            elif "WARN" in upper_log or "WARNING" in upper_log:
                level = "WARN"
            elif "DEBUG" in upper_log:
                level = "DEBUG"
        
        return NormalizedLog(
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            service=str(source_metadata.get("service", "unknown")),
            hostname=str(source_metadata.get("host")),
            environment=str(source_metadata.get("namespace")),
            severity=level,
            message=raw_log.strip(),
            source=str(source_metadata.get("source", "plaintext_parser")),
            application=str(source_metadata.get("component")),
            trace_id=str(source_metadata.get("trace_id")),
            span_id=str(source_metadata.get("span_id")),
            request_id=None,
            metadata=source_metadata.get("metadata") or {},
            raw_log=raw_log
        )
