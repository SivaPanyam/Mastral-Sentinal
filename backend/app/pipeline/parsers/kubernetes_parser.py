import re
import datetime
from typing import Dict, Any

from app.pipeline.schema import NormalizedLog
from app.pipeline.parsers.base import BaseParser

# Standard Kubernetes CRI log format:
# <timestamp> <stream> <tag> <message>
# e.g., 2023-10-10T12:00:00.123456789Z stdout F This is the log message
CRI_LOG_REGEX = re.compile(
    r'^(?P<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+'
    r'(?P<stream>stdout|stderr)\s+'
    r'(?P<tag>[FP])\s+'
    r'(?P<message>.*)$'
)

class KubernetesParser(BaseParser):
    
    def can_parse(self, raw_log: str) -> bool:
        return bool(CRI_LOG_REGEX.match(raw_log))
        
    def parse(self, raw_log: str, source_metadata: Dict[str, Any]) -> NormalizedLog:
        match = CRI_LOG_REGEX.match(raw_log)
        if not match:
            raise ValueError("Failed to parse Kubernetes CRI log")
            
        data = match.groupdict()
        
        time_str = data.get("time")
        parsed_time = datetime.datetime.now(datetime.timezone.utc)
        if time_str:
            try:
                # Truncate nanoseconds to microseconds for python datetime
                if "." in time_str:
                    main_part, frac = time_str.split(".")
                    frac = frac.replace("Z", "")
                    frac = frac[:6]
                    time_str = f"{main_part}.{frac}Z"
                parsed_time = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                parsed_time = parsed_time.replace(tzinfo=datetime.timezone.utc)
            except ValueError:
                pass
                
        stream = data.get("stream", "stdout")
        level = "INFO"
        if stream == "stderr":
            level = "ERROR"
            
        message = data.get("message", "")
        
        # In k8s, metadata usually comes from the source (fluentbit, etc.)
        metadata = source_metadata.get("metadata") or {}
        metadata.update({"cri_stream": stream, "cri_tag": data.get("tag")})
        
        return NormalizedLog(
            timestamp=parsed_time,
            service=str(source_metadata.get("service", "kubernetes")),
            hostname=str(source_metadata.get("host")),
            environment=str(source_metadata.get("namespace")),
            severity=level,
            message=message,
            source=str(source_metadata.get("source", "kubernetes_parser")),
            application=str(source_metadata.get("component", source_metadata.get("container"))),
            trace_id=str(source_metadata.get("trace_id")),
            span_id=str(source_metadata.get("span_id")),
            request_id=None,
            metadata=metadata,
            raw_log=raw_log
        )
