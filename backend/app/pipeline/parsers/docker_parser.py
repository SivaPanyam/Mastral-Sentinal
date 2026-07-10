import json
import datetime
from typing import Dict, Any
from dateutil import parser as date_parser

from app.pipeline.schema import NormalizedLog
from app.pipeline.parsers.base import BaseParser

class DockerParser(BaseParser):
    
    def can_parse(self, raw_log: str) -> bool:
        raw_log = raw_log.strip()
        if not (raw_log.startswith('{') and raw_log.endswith('}')):
            return False
            
        try:
            data = json.loads(raw_log)
            # Docker json-file format uses {"log": "...", "stream": "...", "time": "..."}
            if "log" in data and "time" in data:
                return True
        except ValueError:
            pass
        return False
        
    def parse(self, raw_log: str, source_metadata: Dict[str, Any]) -> NormalizedLog:
        data = json.loads(raw_log)
        
        time_str = data.get("time")
        parsed_time = datetime.datetime.now(datetime.timezone.utc)
        if time_str:
            try:
                parsed_time = date_parser.parse(time_str)
                if not parsed_time.tzinfo:
                    parsed_time = parsed_time.replace(tzinfo=datetime.timezone.utc)
            except Exception:
                pass
                
        stream = data.get("stream", "stdout")
        level = "INFO"
        if stream == "stderr":
            level = "ERROR"
            
        message = data.get("log", "").strip()
        
        metadata = source_metadata.get("metadata") or {}
        metadata.update({"docker_stream": stream})
        
        return NormalizedLog(
            timestamp=parsed_time,
            service=str(source_metadata.get("service", "docker")),
            hostname=str(source_metadata.get("host")),
            environment=str(source_metadata.get("namespace")),
            severity=level,
            message=message,
            source=str(source_metadata.get("source", "docker_parser")),
            application=str(source_metadata.get("component")),
            trace_id=str(source_metadata.get("trace_id")),
            span_id=str(source_metadata.get("span_id")),
            request_id=None,
            metadata=metadata,
            raw_log=raw_log
        )
