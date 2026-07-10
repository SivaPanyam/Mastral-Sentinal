from typing import List, Dict, Any
from app.log_sources.base import LogSource

class BaseScaffoldAdapter(LogSource):
    """Base class for adapters that are not yet fully implemented."""
    def __init__(self, name: str):
        self.name = name
        
    async def connect(self) -> None:
        print(f"[{self.name}] Connect called (Not implemented)")

    async def disconnect(self) -> None:
        print(f"[{self.name}] Disconnect called (Not implemented)")

    async def fetch_logs(self) -> List[Dict[str, Any]]:
        return []

    async def health_check(self) -> bool:
        return False


class SyslogAdapter(BaseScaffoldAdapter):
    def __init__(self, port: int = 514):
        super().__init__("SyslogAdapter")
        self.port = port

class DockerAdapter(BaseScaffoldAdapter):
    def __init__(self, socket_path: str = "/var/run/docker.sock"):
        super().__init__("DockerAdapter")
        self.socket_path = socket_path

class KubernetesAdapter(BaseScaffoldAdapter):
    def __init__(self, namespace: str = "default"):
        super().__init__("KubernetesAdapter")
        self.namespace = namespace

class AWSCloudWatchAdapter(BaseScaffoldAdapter):
    def __init__(self, log_group: str, region: str):
        super().__init__("AWSCloudWatchAdapter")
        self.log_group = log_group
        self.region = region

class AzureMonitorAdapter(BaseScaffoldAdapter):
    def __init__(self, workspace_id: str):
        super().__init__("AzureMonitorAdapter")
        self.workspace_id = workspace_id

class GCPLoggingAdapter(BaseScaffoldAdapter):
    def __init__(self, project_id: str):
        super().__init__("GCPLoggingAdapter")
        self.project_id = project_id
