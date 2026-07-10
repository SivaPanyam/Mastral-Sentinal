from abc import ABC, abstractmethod
from typing import Dict, Any
from app.pipeline.schema import NormalizedLog

class BaseParser(ABC):
    """
    Abstract base class for all log parsers.
    """
    
    @abstractmethod
    def can_parse(self, raw_log: str) -> bool:
        """
        Determines if this parser can successfully parse the given raw log string.
        """
        pass
        
    @abstractmethod
    def parse(self, raw_log: str, source_metadata: Dict[str, Any]) -> NormalizedLog:
        """
        Parses the raw log string and returns a NormalizedLog object.
        """
        pass
