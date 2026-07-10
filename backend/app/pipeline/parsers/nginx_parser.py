import re
import datetime
from typing import Dict, Any

from app.pipeline.schema import NormalizedLog
from app.pipeline.parsers.base import BaseParser

# Standard NGINX access log combined format regex
NGINX_ACCESS_REGEX = re.compile(
    r'^(?P<remote_ip>\S+) \S+ (?P<remote_user>\S+) \[(?P<time>[^\]]+)\] '
    r'"(?P<method>\S+)?\s?(?P<request>[^\"]*)?\s?(?P<http_version>HTTP/\d\.\d)?" '
    r'(?P<status>\d{3}) (?P<body_bytes_sent>\d+) '
    r'"(?P<http_referer>[^\"]*)" "(?P<http_user_agent>[^\"]*)"'
)

class NginxParser(BaseParser):
    
    def can_parse(self, raw_log: str) -> bool:
        # A quick heuristic to avoid running the full regex on everything
        if "GET " in raw_log or "POST " in raw_log:
            return bool(NGINX_ACCESS_REGEX.match(raw_log))
        return False
        
    def parse(self, raw_log: str, source_metadata: Dict[str, Any]) -> NormalizedLog:
        match = NGINX_ACCESS_REGEX.match(raw_log)
        if not match:
            # Should not happen if can_parse returns True, but fallback gracefully
            raise ValueError("Failed to parse NGINX log")
            
        data = match.groupdict()
        
        # Parse time (e.g., 10/Oct/2000:13:55:36 -0700)
        time_str = data.get("time")
        parsed_time = datetime.datetime.now(datetime.timezone.utc)
        if time_str:
            try:
                parsed_time = datetime.datetime.strptime(time_str, "%d/%b/%Y:%H:%M:%S %z")
            except ValueError:
                pass
                
        status = data.get("status", "200")
        level = "INFO"
        if status.startswith("4"):
            level = "WARN"
        elif status.startswith("5"):
            level = "ERROR"
            
        message = f"NGINX {data.get('method', 'REQ')} {data.get('request', '')} - {status}"
        
        metadata = source_metadata.get("metadata") or {}
        metadata.update(data)
        
        return NormalizedLog(
            timestamp=parsed_time,
            service=str(source_metadata.get("service", "nginx")),
            hostname=str(source_metadata.get("host")),
            environment=str(source_metadata.get("namespace")),
            severity=level,
            message=message,
            source=str(source_metadata.get("source", "nginx_parser")),
            application=str(source_metadata.get("component")),
            trace_id=str(source_metadata.get("trace_id")),
            span_id=str(source_metadata.get("span_id")),
            request_id=None,
            metadata=metadata,
            raw_log=raw_log
        )
