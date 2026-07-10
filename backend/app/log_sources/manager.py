import asyncio
import os
import logging
import time
from typing import Dict, Any

from app.log_sources.base import LogSource
from app.log_sources.adapters.rest_api import RestApiAdapter
from app.log_sources.adapters.local_file import LocalFileAdapter
from app.log_sources.adapters.scaffolding import (
    SyslogAdapter, DockerAdapter, KubernetesAdapter,
    AWSCloudWatchAdapter, AzureMonitorAdapter, GCPLoggingAdapter
)
from app.services.event_pipeline import process_incoming_log
from app.database import SessionLocal

logger = logging.getLogger("LogSourceManager")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(ch)

class LogSourceManager:
    """
    Manages the lifecycle and polling of all active LogSources with
    robust retry logic, exponential backoff, and health monitoring.
    """
    def __init__(self):
        self.adapters: Dict[str, LogSource] = {}
        self.is_running = False
        self._polling_task = None
        
        self.polling_interval = float(os.getenv("POLLING_INTERVAL_SECONDS", "1.0"))
        self.max_backoff = float(os.getenv("MAX_BACKOFF_SECONDS", "60.0"))
        
        # State tracking for retries/backoff per adapter
        self.adapter_states: Dict[str, Dict[str, Any]] = {}
        
        # Ensure a RestApiAdapter is always available for FastAPI
        self.rest_adapter = RestApiAdapter()
        self.adapters["rest"] = self.rest_adapter
        self._init_state("rest")

    def _init_state(self, name: str):
        self.adapter_states[name] = {
            "status": "disconnected",
            "consecutive_failures": 0,
            "next_retry_at": 0.0,
            "last_error": None
        }

    def initialize_from_config(self):
        """
        Reads environment configuration and instantiates requested adapters.
        """
        active_sources_env = os.getenv("ACTIVE_LOG_SOURCES", "rest,local_file")
        active_sources = [s.strip().lower() for s in active_sources_env.split(",") if s.strip()]
        
        if "local_file" in active_sources and "local_file" not in self.adapters:
            self.adapters["local_file"] = LocalFileAdapter()
            self._init_state("local_file")
            
        if "syslog" in active_sources and "syslog" not in self.adapters:
            self.adapters["syslog"] = SyslogAdapter()
            self._init_state("syslog")
            
        if "docker" in active_sources and "docker" not in self.adapters:
            self.adapters["docker"] = DockerAdapter()
            self._init_state("docker")
            
        if "kubernetes" in active_sources and "kubernetes" not in self.adapters:
            self.adapters["kubernetes"] = KubernetesAdapter()
            self._init_state("kubernetes")
            
        if "cloudwatch" in active_sources and "cloudwatch" not in self.adapters:
            self.adapters["cloudwatch"] = AWSCloudWatchAdapter(log_group="/ecs/sentinel", region="us-east-1")
            self._init_state("cloudwatch")
            
        if "azure" in active_sources and "azure" not in self.adapters:
            self.adapters["azure"] = AzureMonitorAdapter(workspace_id="test-workspace-id")
            self._init_state("azure")
            
        if "gcp" in active_sources and "gcp" not in self.adapters:
            self.adapters["gcp"] = GCPLoggingAdapter(project_id="test-project-id")
            self._init_state("gcp")
            
        logger.info(f"Initialized adapters: {list(self.adapters.keys())} (Interval: {self.polling_interval}s)")

    async def connect_all(self):
        self.is_running = True
        for name, adapter in self.adapters.items():
            try:
                await adapter.connect()
                self.adapter_states[name]["status"] = "connected"
                self.adapter_states[name]["consecutive_failures"] = 0
                logger.info(f"Connected log source: {name}")
            except Exception as e:
                self.adapter_states[name]["status"] = "error"
                self.adapter_states[name]["last_error"] = str(e)
                logger.error(f"Failed to connect log source {name}: {e}")
                
        self._polling_task = asyncio.create_task(self._polling_loop())

    async def disconnect_all(self):
        self.is_running = False
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
            
        for name, adapter in self.adapters.items():
            try:
                await adapter.disconnect()
                self.adapter_states[name]["status"] = "disconnected"
                logger.info(f"Disconnected log source: {name}")
            except Exception as e:
                logger.error(f"Failed to disconnect log source {name}: {e}")

    async def _polling_loop(self):
        """
        Continuously polls all active sources for new logs, implementing exponential backoff.
        """
        logger.info("Started background polling loop.")
        try:
            while self.is_running:
                now = time.time()
                for name, adapter in self.adapters.items():
                    state = self.adapter_states[name]
                    
                    # Skip if we are backing off
                    if now < state["next_retry_at"]:
                        continue
                        
                    try:
                        logs = await adapter.fetch_logs()
                        if logs:
                            db = SessionLocal()
                            try:
                                for log in logs:
                                    await process_incoming_log(db, log)
                            finally:
                                db.close()
                                
                        # Reset failure count on success
                        if state["consecutive_failures"] > 0:
                            logger.info(f"Log source '{name}' recovered.")
                        state["consecutive_failures"] = 0
                        state["status"] = "connected"
                        state["last_error"] = None
                        
                    except asyncio.CancelledError:
                        raise
                    except Exception as e:
                        state["consecutive_failures"] += 1
                        state["status"] = "error"
                        state["last_error"] = str(e)
                        
                        # Exponential backoff: 2^failures * interval (capped at max_backoff)
                        backoff = min(self.max_backoff, (2 ** state["consecutive_failures"]) * self.polling_interval)
                        state["next_retry_at"] = time.time() + backoff
                        
                        logger.warning(f"Error fetching logs from {name}: {e}. Backing off for {backoff}s")
                        
                await asyncio.sleep(self.polling_interval)
        except asyncio.CancelledError:
            logger.info("Polling loop cancelled.")
        finally:
            logger.info("Background polling loop exited.")

    def get_health(self) -> Dict[str, Any]:
        """
        Returns health status for all adapters.
        """
        return {
            "is_running": self.is_running,
            "polling_interval": self.polling_interval,
            "sources": self.adapter_states
        }
        
    def get_rest_adapter(self) -> RestApiAdapter:
        return self.rest_adapter

# Global singleton
log_manager = LogSourceManager()
