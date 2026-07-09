from sqlalchemy import Column, String, Float, JSON, DateTime
from sqlalchemy.sql import func
from app.models.base import Base
import uuid

class Metric(Base):
    __tablename__ = "metrics"

    id = Column(String, primary_key=True, default=lambda: f"METRIC-{uuid.uuid4().hex[:8].upper()}")
    service = Column(String, index=True, nullable=False)
    metric_name = Column(String, index=True, nullable=False)
    value = Column(Float, nullable=False)
    labels = Column(JSON, default={})
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
