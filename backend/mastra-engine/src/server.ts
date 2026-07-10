import './telemetry';
import express from 'express';
import { incidentResponseWorkflow } from './workflows/IncidentResponseWorkflow';
import { register, agentWorkflowDuration } from './telemetry';

const app = express();
app.use(express.json());

// ------------------------------------------------------------------
// Health & Metrics Probes
// ------------------------------------------------------------------
app.get('/metrics', async (req, res) => {
  try {
    res.set('Content-Type', register.contentType);
    res.end(await register.metrics());
  } catch (ex) {
    res.status(500).end(String(ex));
  }
});

app.get('/health/live', (req, res) => {
  res.json({ status: 'UP' });
});

app.get('/health/ready', (req, res) => {
  res.json({ status: 'READY' });
});

app.post('/api/workflows/incident-response', async (req, res) => {
  try {
    const { incidentId, title, service, severity, logs, metadata, historical_incidents } = req.body;
    
    const endTimer = agentWorkflowDuration.startTimer({ agent: 'IncidentResponseWorkflow' });
    
    // We start the workflow asynchronously so the API returns immediately.
    // SSE events will be published during the workflow's execution.
    incidentResponseWorkflow.execute({
      triggerData: {
        incidentId,
        title,
        service,
        severity,
        logs,
        metadata,
        historical_incidents
      }
    }).then(() => {
      endTimer({ status: 'success' });
    }).catch(err => {
      endTimer({ status: 'error' });
      console.error(`Workflow execution failed for ${incidentId}:`, err);
    });
    
    res.status(202).json({ message: 'Workflow started', incidentId });
  } catch (err: any) {
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.MASTRA_PORT || 3000;
app.listen(PORT, () => {
  console.log(`Mastra Engine server running on port ${PORT}`);
});
