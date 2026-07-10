import os
from fastapi import FastAPI
from prometheus_client import Counter, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

# Custom Prometheus Metrics
INCIDENT_DETECTED_COUNTER = Counter(
    "sentinel_incidents_detected_total",
    "Total number of incidents detected by rules",
    ["severity", "rule"]
)

LOG_INGESTION_COUNTER = Counter(
    "sentinel_logs_ingested_total",
    "Total number of logs ingested",
    ["source"]
)

VECTOR_SEARCH_COUNTER = Counter(
    "sentinel_vector_searches_total",
    "Total number of Qdrant vector searches",
    ["collection"]
)

KNOWLEDGE_GROWTH_GAUGE = Gauge(
    "sentinel_knowledge_documents_total",
    "Total number of documents in knowledge base",
    ["status"]
)

def setup_telemetry(app: FastAPI):
    # 1. Prometheus Instrumentator
    # Exposes /metrics endpoint with default HTTP metrics
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health", "/health/live", "/health/ready"]
    )
    instrumentator.instrument(app).expose(app, include_in_schema=False)

    # 2. OpenTelemetry Tracing Setup
    # Only enable if jaeger/otlp is running and configured
    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4318/v1/traces")
    
    resource = Resource(attributes={
        SERVICE_NAME: "sentinel-backend"
    })
    
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint))
    provider.add_span_processor(processor)
    
    trace.set_tracer_provider(provider)

    # 3. Auto-instrumentation
    FastAPIInstrumentor.instrument_app(app)
    RequestsInstrumentor().instrument()
    
    # SQLAlchemy gets instrumented separately using engine inside database.py,
    # but we can optionally call SQLAlchemyInstrumentor().instrument() here if engine is created after.
