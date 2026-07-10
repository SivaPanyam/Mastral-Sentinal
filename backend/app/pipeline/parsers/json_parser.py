import json
import datetime
from typing import Dict, Any
from dateutil import parser as date_parser

from app.pipeline.schema import NormalizedLog
from app.pipeline.parsers.base import BaseParser

class JsonParser(BaseParser):
    """
    Parses standard JSON logs. 
    Extracts common fields if present, else places them in metadata.
    """
    
    def can_parse(self, raw_log: str) -> bool:
        raw_log = raw_log.strip()
        if not (raw_log.startswith('{') and raw_log.endswith('}')):
            return False
        try:
            json.loads(raw_log)
            return True
        except ValueError:
            return False
            
    def parse(self, raw_log: str, source_metadata: Dict[str, Any]) -> NormalizedLog:
        data = json.loads(raw_log)
        
        # Extract Timestamp
        timestamp_val = data.pop("timestamp", data.pop("time", data.pop("date", None)))
        parsed_time = datetime.datetime.now(datetime.timezone.utc)
        if timestamp_val:
            try:
                # Handle numeric unix timestamps or ISO strings
                if isinstance(timestamp_val, (int, float)):
                    parsed_time = datetime.datetime.fromtimestamp(timestamp_val, tz=datetime.timezone.utc)
                else:
                    parsed_time = date_parser.parse(str(timestamp_val))
                    if not parsed_time.tzinfo:
                        parsed_time = parsed_time.replace(tzinfo=datetime.timezone.utc)
            except Exception:
                pass # fallback to current time
                
        # Extract Level
        level = data.pop("level", data.pop("severity", "INFO")).upper()
        
        # Extract Message
        message = data.pop("message", data.pop("msg", data.pop("log", raw_log)))
        if isinstance(message, dict):
            message = json.dumps(message)
            
        # Extract identifiers
        service = data.pop("service", data.pop("service_name", source_metadata.get("service", "UNKNOWN_SERVICE")))
        hostname = data.pop("hostname", data.pop("host", source_metadata.get("host")))
        environment = data.pop("environment", data.pop("env", data.pop("namespace", source_metadata.get("namespace"))))
        application = data.pop("application", data.pop("app", data.pop("component", source_metadata.get("component"))))
        trace_id = data.pop("trace_id", data.pop("traceId", source_metadata.get("trace_id")))
        span_id = data.pop("span_id", data.pop("spanId", source_metadata.get("span_id")))
        request_id = data.pop("request_id", data.pop("requestId", data.pop("reqId", None)))
        
        # Any remaining JSON keys go into metadata
        metadata = source_metadata.get("metadata") or {}
        metadata.update(data)
        
        return NormalizedLog(
            timestamp=parsed_time,
            service=str(service),
            hostname=str(hostname) if hostname else None,
            environment=str(environment) if environment else None,
            severity=str(level),
            message=str(message),
            source=str(source_metadata.get("source", "json_parser")),
            application=str(application) if application else None,
            trace_id=str(trace_id) if trace_id else None,
            span_id=str(span_id) if span_id else None,
            request_id=str(request_id) if request_id else None,
            metadata=metadata,
            raw_log=raw_log
        )
