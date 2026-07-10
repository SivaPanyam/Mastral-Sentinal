from fastapi import WebSocket
from typing import List, Dict, Any
import json

class GlobalWebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event_type: str, payload: Dict[str, Any]):
        message = json.dumps({"type": event_type, "payload": payload})
        
        # We need to handle potential disconnections during broadcast
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
                
        for connection in disconnected:
            self.disconnect(connection)

global_ws_manager = GlobalWebSocketManager()

def broadcast_sync(event_type: str, payload: dict):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(global_ws_manager.broadcast(event_type, payload))
        else:
            asyncio.run(global_ws_manager.broadcast(event_type, payload))
    except Exception:
        pass
