from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LogSource(ABC):
    """
    Abstract Base Class representing a log source adapter.
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """
        Initialize the connection to the log source.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """
        Clean up resources and disconnect from the log source.
        """
        pass

    @abstractmethod
    async def fetch_logs(self) -> List[Dict[str, Any]]:
        """
        Retrieve a batch of logs from the source.
        Returns a list of structured log dictionaries.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the log source is healthy and accessible.
        """
        pass
