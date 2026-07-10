import pytest
from unittest.mock import MagicMock
from app.detection.engine import DetectionEngine
from app.pipeline.schema import NormalizedLog
from app.models import Incident, IncidentLog
import datetime

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def rules_yaml(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "rules.yaml"
    p.write_text("""
rules:
  - id: rule-repeated-error
    name: "Repeated ERROR"
    description: "Repeated ERROR messages"
    severity: "HIGH"
    condition:
      field: "severity"
      operator: "in"
      value: ["ERROR"]
    threshold: 2
    time_window_seconds: 60
    enabled: true
    group_by: ["service"]
  - id: rule-critical-crash
    name: "Crash"
    description: "App crashed"
    severity: "CRITICAL"
    condition:
      field: "message"
      operator: "regex"
      value: "(?i)(segmentation fault|core dumped|panic:)"
    threshold: 1
    time_window_seconds: 0
    enabled: true
    group_by: ["service"]
""")
    return str(p)

def test_engine_initialization(rules_yaml):
    engine = DetectionEngine(rules_path=rules_yaml)
    assert len(engine.rules) == 2
    assert engine.rules[0]["id"] == "rule-repeated-error"

def test_single_event_trigger(mock_db, rules_yaml, monkeypatch):
    engine = DetectionEngine(rules_path=rules_yaml)
    
    mock_trigger = MagicMock()
    monkeypatch.setattr(engine, "trigger_incident", mock_trigger)
    
    log = NormalizedLog(
        service="frontend",
        severity="FATAL",
        message="segmentation fault",
        raw_log="segmentation fault at 0x000"
    )
    
    engine.process_log(mock_db, log)
    
    mock_trigger.assert_called_once()
    args, kwargs = mock_trigger.call_args
    rule = args[1]
    assert rule["id"] == "rule-critical-crash"
    assert args[3] == "frontend" # group_key

def test_multi_event_threshold(mock_db, rules_yaml, monkeypatch):
    engine = DetectionEngine(rules_path=rules_yaml)
    
    mock_trigger = MagicMock()
    monkeypatch.setattr(engine, "trigger_incident", mock_trigger)
    
    log1 = NormalizedLog(
        service="backend",
        severity="ERROR",
        message="Timeout fetching data",
        raw_log="Timeout fetching data"
    )
    
    log2 = NormalizedLog(
        service="backend",
        severity="ERROR",
        message="Connection dropped",
        raw_log="Connection dropped"
    )
    
    # Process first log, threshold is 2, so it shouldn't trigger
    engine.process_log(mock_db, log1)
    mock_trigger.assert_not_called()
    
    # Process second log, should trigger now
    engine.process_log(mock_db, log2)
    mock_trigger.assert_called_once()

def test_time_window_expiry(mock_db, rules_yaml, monkeypatch):
    engine = DetectionEngine(rules_path=rules_yaml)
    
    mock_trigger = MagicMock()
    monkeypatch.setattr(engine, "trigger_incident", mock_trigger)
    
    log1 = NormalizedLog(
        service="backend",
        severity="ERROR",
        message="Timeout fetching data",
        raw_log="Timeout fetching data"
    )
    
    log2 = NormalizedLog(
        service="backend",
        severity="ERROR",
        message="Connection dropped",
        raw_log="Connection dropped"
    )
    
    # Process first log
    engine.process_log(mock_db, log1)
    mock_trigger.assert_not_called()
    
    # Fast forward time in the engine's state manually
    group_key = "backend"
    old_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=61)
    engine.state["rule-repeated-error"][group_key] = [old_time]
    
    # Process second log, should clean up the first one because it's older than 60s
    engine.process_log(mock_db, log2)
    mock_trigger.assert_not_called() # Should only have 1 in the window now
