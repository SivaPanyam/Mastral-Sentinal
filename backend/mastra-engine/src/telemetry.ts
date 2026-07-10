import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import client from 'prom-client';

// 1. Setup Prometheus Metrics
export const register = new client.Registry();

// Enable default system metrics
client.collectDefaultMetrics({ register, prefix: 'mastra_' });

// Custom Metrics
export const llmTokenCounter = new client.Counter({
  name: 'mastra_llm_tokens_total',
  help: 'Total number of LLM tokens consumed',
  labelNames: ['model', 'type', 'agent'],
  registers: [register]
});

export const agentWorkflowDuration = new client.Histogram({
  name: 'mastra_agent_workflow_duration_seconds',
  help: 'Duration of agent workflow executions',
  labelNames: ['agent', 'status'],
  buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60],
  registers: [register]
});

// 2. Setup OpenTelemetry
const traceExporter = new OTLPTraceExporter({
  url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://jaeger:4318/v1/traces',
});

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'mastra-engine',
  }),
  traceExporter,
  instrumentations: [getNodeAutoInstrumentations()]
});

// Initialize SDK
try {
  sdk.start();
  console.log('OpenTelemetry SDK started for Mastra Engine');
} catch (error) {
  console.error('Error initializing OpenTelemetry:', error);
}

// Ensure graceful shutdown
process.on('SIGTERM', () => {
  sdk.shutdown()
    .then(() => console.log('OpenTelemetry SDK shut down successfully'))
    .catch((error) => console.log('Error shutting down OpenTelemetry SDK', error))
    .finally(() => process.exit(0));
});
