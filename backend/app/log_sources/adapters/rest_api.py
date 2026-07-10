import asyncio
from typing import List, Dict, Any
from app.log_sources.base import LogSource

class RestApiAdapter(LogSource):
    """
    Adapter that receives logs via a REST API push model.
    It acts as a buffer queue that the API route pushes into,
    and the central manager pulls from via fetch_logs().
    """
    def __init__(self, max_queue_size: int = 10000):
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.is_connected = False

    async def connect(self) -> None:
        self.is_connected = True

    async def disconnect(self) -> None:
        self.is_connected = False
        # Optional: flush or discard remaining logs
        while not self.queue.empty():
            self.queue.get_nowait()
            self.queue.task_done()

    async def fetch_logs(self) -> List[Dict[str, Any]]:
        logs = []
        # Drain the queue up to a certain batch size or until empty
        batch_size = 100
        while not self.queue.empty() and len(logs) < batch_size:
            try:
                log = self.queue.get_nowait()
                logs.append(log)
                self.queue.task_done()
            except asyncio.QueueEmpty:
                break
        return logs

    async def health_check(self) -> bool:
        return self.is_connected

    async def push_log(self, log_data: Dict[str, Any]) -> bool:
        """
        API endpoint calls this method to enqueue a log.
        """
        if not self.is_connected:
            return False
            
        try:
            self.queue.put_nowait(log_data)
            return True
        except asyncio.QueueFull:
            print("Warning: REST API Log Queue is full. Dropping log.")
            return False
