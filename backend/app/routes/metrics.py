from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.metric import Metric
from app.auth import require_role
import datetime
import uuid

router = APIRouter(prefix="/metrics", tags=["Metrics & Telemetry"])

class MetricCreate(BaseModel):
    service: str
    metric_name: str
    value: float
    labels: Optional[Dict[str, Any]] = {}

class MetricOut(BaseModel):
    id: str
    service: str
    metric_name: str
    value: float
    labels: Dict[str, Any]
    timestamp: datetime.datetime
    
    class Config:
        from_attributes = True

@router.post("/", response_model=MetricOut, status_code=status.HTTP_201_CREATED)
def ingest_metric(metric_in: MetricCreate, db: Session = Depends(get_db), current_user = Depends(require_role(["Admin", "SRE", "DevOps"]))):
    """Ingest a new telemetry metric."""
    new_metric = Metric(
        id=f"METRIC-{uuid.uuid4().hex[:8].upper()}",
        service=metric_in.service,
        metric_name=metric_in.metric_name,
        value=metric_in.value,
        labels=metric_in.labels
    )
    db.add(new_metric)
    db.commit()
    db.refresh(new_metric)
    return new_metric

@router.get("/{service}", response_model=List[MetricOut])
def get_service_metrics(service: str, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve recent metrics for a specific service."""
    metrics = db.query(Metric).filter(Metric.service == service).order_by(Metric.timestamp.desc()).limit(limit).all()
    return metrics
