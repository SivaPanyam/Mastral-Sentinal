import logging
from typing import Dict, Any, List

from app.pipeline.schema import NormalizedLog
from app.pipeline.parsers.base import BaseParser
from app.pipeline.parsers.json_parser import JsonParser
from app.pipeline.parsers.nginx_parser import NginxParser
from app.pipeline.parsers.apache_parser import ApacheParser
from app.pipeline.parsers.docker_parser import DockerParser
from app.pipeline.parsers.kubernetes_parser import KubernetesParser
from app.pipeline.parsers.plaintext_parser import PlaintextParser

logger = logging.getLogger(__name__)

class LogNormalizer:
    def __init__(self):
        # Order matters! More specific parsers should come first.
        # Plaintext is the fallback and should always be last.
        self.parsers: List[BaseParser] = [
            KubernetesParser(),
            DockerParser(),
            JsonParser(),
            NginxParser(),
            ApacheParser(),
            PlaintextParser()
        ]
        
    def normalize(self, raw_log: str, source_metadata: Dict[str, Any] = None) -> NormalizedLog:
        if source_metadata is None:
            source_metadata = {}
            
        for parser in self.parsers:
            try:
                if parser.can_parse(raw_log):
                    return parser.parse(raw_log, source_metadata)
            except Exception as e:
                logger.warning(f"Parser {parser.__class__.__name__} failed during parsing: {e}")
                
        # We should theoretically never reach here if PlaintextParser is at the end, 
        # but just in case, we instantiate one explicitly.
        fallback = PlaintextParser()
        return fallback.parse(raw_log, source_metadata)

# Singleton instance for the application to use
normalizer = LogNormalizer()
