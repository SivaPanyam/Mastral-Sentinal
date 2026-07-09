import time
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional

# SSE Manager for streaming live agent pipeline updates
class IncidentSSEManager:
    def __init__(self):
        # Maps incident_id -> List of asyncio.Queue
        self.queues: Dict[str, List[asyncio.Queue]] = {}

    def subscribe(self, incident_id: str) -> asyncio.Queue:
        q = asyncio.Queue()
        if incident_id not in self.queues:
            self.queues[incident_id] = []
        self.queues[incident_id].append(q)
        return q

    def unsubscribe(self, incident_id: str, q: asyncio.Queue):
        if incident_id in self.queues:
            if q in self.queues[incident_id]:
                self.queues[incident_id].remove(q)
            if not self.queues[incident_id]:
                del self.queues[incident_id]

    def publish(self, incident_id: str, data: dict):
        if not incident_id or incident_id not in self.queues:
            return
        
        loop = None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass

        async def _put():
            for q in list(self.queues.get(incident_id, [])):
                await q.put(data)

        if loop and loop.is_running():
            loop.create_task(_put())
        else:
            try:
                new_loop = asyncio.new_event_loop()
                new_loop.run_until_complete(_put())
                new_loop.close()
            except Exception:
                pass

incident_sse_manager = IncidentSSEManager()
