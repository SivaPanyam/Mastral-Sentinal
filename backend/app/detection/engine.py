import yaml
import os
import uuid
from datetime import datetime, timezone, timedelta
import asyncio
import logging

from app.pipeline.schema import NormalizedLog
from app.detection.rule_evaluator import evaluate_condition
from app.crud import IncidentRepository
from app.models import IncidentLog
from app.ws import global_ws_manager

logger = logging.getLogger(__name__)

class DetectionEngine:
    def __init__(self, rules_path: str = "rules.yaml"):
        self.rules = []
        self.rules_path = rules_path
        self.load_rules()
        
        # In-memory state for threshold tracking:
        # { rule_id: { group_by_key: [timestamp1, timestamp2, ...] } }
        self.state = {}

    def load_rules(self):
        if not os.path.exists(self.rules_path):
            logger.warning(f"Rules file not found at {self.rules_path}")
            return
            
        with open(self.rules_path, 'r') as f:
            try:
                data = yaml.safe_load(f)
                self.rules = data.get("rules", [])
                logger.info(f"Loaded {len(self.rules)} rules from {self.rules_path}")
            except Exception as e:
                logger.error(f"Failed to load rules: {e}")

    def evaluate_rule_condition(self, rule: dict, log: NormalizedLog) -> bool:
        try:
            condition = rule.get("condition")
            if not condition:
                return True
                
            field = condition.get("field")
            # Extract the field value from NormalizedLog
            if hasattr(log, field):
                field_value = getattr(log, field)
            elif field in log.metadata:
                field_value = log.metadata[field]
            else:
                return False
                
            return evaluate_condition(condition, field_value)
        except Exception as e:
            logger.error(f"Error evaluating rule '{rule.get('name')}' against log: {e}", exc_info=True)
            return False

    def process_log(self, db, log: NormalizedLog):
        """
        Evaluate the log against all enabled rules.
        """
        now = datetime.now(timezone.utc)
        
        for rule in self.rules:
            try:
                if not rule.get("enabled", True):
                    continue
                    
                if self.evaluate_rule_condition(rule, log):
                    rule_id = rule.get("id")
                    threshold = rule.get("threshold", 1)
                    time_window = rule.get("time_window_seconds", 0)
                    group_by_fields = rule.get("group_by", ["service"])
                    
                    # Generate group_by key
                    group_key_parts = []
                    for field in group_by_fields:
                        if hasattr(log, field):
                            group_key_parts.append(str(getattr(log, field)))
                        elif field in log.metadata:
                            group_key_parts.append(str(log.metadata[field]))
                        else:
                            group_key_parts.append("unknown")
                    group_key = ":".join(group_key_parts)
                    
                    if threshold <= 1:
                        # Immediate trigger
                        self.trigger_incident(db, rule, log, group_key)
                    else:
                        # State tracking
                        if rule_id not in self.state:
                            self.state[rule_id] = {}
                        if group_key not in self.state[rule_id]:
                            self.state[rule_id][group_key] = []
                            
                        # Add current timestamp
                        self.state[rule_id][group_key].append(now)
                        
                        # Remove old timestamps
                        window_start = now - timedelta(seconds=time_window)
                        self.state[rule_id][group_key] = [
                            t for t in self.state[rule_id][group_key] if t >= window_start
                        ]
                        
                        # Check threshold
                        if len(self.state[rule_id][group_key]) >= threshold:
                            self.trigger_incident(db, rule, log, group_key)
                            # Reset state to avoid spamming
                            self.state[rule_id][group_key] = []
                            
            except Exception as e:
                logger.error(f"Failed to process rule {rule.get('id')} for log: {e}", exc_info=True)

    def trigger_incident(self, db, rule: dict, log: NormalizedLog, group_key: str):
        try:
            # Create IncidentLog record
            log_id = f"log-{uuid.uuid4().hex[:6]}"
            
            log_metadata = log.metadata.copy()
            if log.request_id:
                log_metadata["request_id"] = log.request_id
            log_metadata["trigger_rule"] = rule.get("name")
                
            incident_log = IncidentLog(
                id=log_id,
                level=log.severity,
                service=log.service,
                component=log.application,
                host=log.hostname,
                namespace=log.environment,
                trace_id=log.trace_id,
                span_id=log.span_id,
                message=log.message,
                parsed_log=None,
                log_metadata=log_metadata
            )
            
            incident_data = {
                "title": f"Detection: {rule.get('name')} in {log.service}",
                "description": f"Triggered by rule: {rule.get('name')} - {rule.get('description')}",
                "service": log.service,
                "severity": rule.get("severity", "MEDIUM"),
                "rule_name": rule.get('name'),
                "affected_components": [log.application] if log.application else [log.service]
            }
            
            # Use CRUD to create or update existing incident
            incident = IncidentRepository.create_or_update_incident(db, incident_data, incident_log)
            logger.info(f"Incident triggered/updated: {incident.id} for rule {rule.get('name')}")
            
            # Fire WS event and async workflow
            from app.services.event_pipeline import trigger_mastra_workflow # lazy import to avoid circular dep
            
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(global_ws_manager.broadcast("INCIDENT_UPDATED", {
                    "id": incident.id,
                    "title": incident.title,
                    "service": incident.service,
                    "severity": incident.severity,
                    "status": incident.status
                }))
                
                # Workflow
                asyncio.create_task(trigger_mastra_workflow(incident, incident_log))
                
        except Exception as e:
            logger.error(f"Failed to trigger incident for rule {rule.get('id')}: {e}", exc_info=True)

detection_engine = DetectionEngine(rules_path="rules.yaml")
