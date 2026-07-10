import asyncio
import os
import json
from typing import List, Dict, Any
from app.log_sources.base import LogSource

class LocalFileAdapter(LogSource):
    """
    Adapter that tails a local log file, reading new lines as they are appended.
    """
    def __init__(self, file_path: str = "app.log"):
        self.file_path = file_path
        self.file_handle = None
        self.is_connected = False
        
    async def connect(self) -> None:
        if not os.path.exists(self.file_path):
            # Create if it doesn't exist so we can tail it
            with open(self.file_path, "a") as f:
                pass
                
        self.file_handle = open(self.file_path, "r")
        # Seek to the end of the file so we only get new logs
        self.file_handle.seek(0, os.SEEK_END)
        self.is_connected = True

    async def disconnect(self) -> None:
        self.is_connected = False
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None

    async def fetch_logs(self) -> List[Dict[str, Any]]:
        logs = []
        if not self.is_connected or not self.file_handle:
            return logs

        # Read all available new lines
        while True:
            line = self.file_handle.readline()
            if not line:
                break
                
            line = line.strip()
            if not line:
                continue
                
            # Attempt to parse as JSON; fallback to simple message wrapper
            try:
                log_data = json.loads(line)
                # Ensure it has basic structure required by pipeline
                if isinstance(log_data, dict) and "message" in log_data:
                    if "service" not in log_data:
                        log_data["service"] = "local_file"
                    if "level" not in log_data:
                        log_data["level"] = "INFO"
                    logs.append(log_data)
                else:
                    logs.append({
                        "service": "local_file",
                        "level": "INFO",
                        "message": line
                    })
            except json.JSONDecodeError:
                # Not JSON, wrap it
                logs.append({
                    "service": "local_file",
                    "level": "INFO",
                    "message": line
                })
                
        return logs

    async def health_check(self) -> bool:
        return self.is_connected and self.file_handle is not None and not self.file_handle.closed
