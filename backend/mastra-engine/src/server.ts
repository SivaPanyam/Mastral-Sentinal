import express from 'express';
import { incidentResponseWorkflow } from './workflows/IncidentResponseWorkflow';

const app = express();
app.use(express.json());

app.post('/api/workflows/incident-response', async (req, res) => {
  try {
    const { incidentId, title, service, severity, logs } = req.body;
    
    // We start the workflow asynchronously so the API returns immediately.
    // SSE events will be published during the workflow's execution.
    incidentResponseWorkflow.execute({
      triggerData: {
        incidentId,
        title,
        service,
        severity,
        logs
      }
    }).catch(err => {
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
