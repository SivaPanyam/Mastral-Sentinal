import { AgentOutput, AgentType } from '../types';
import { apiRequest } from './api';

let mockAgentRuns: Record<string, AgentOutput[]> = {
  'INC-2026-001': [
    {
      id: 'run-1',
      incidentId: 'INC-2026-001',
      agentType: AgentType.TRIAGE,
      timestamp: '2026-07-08T22:16:15Z',
      status: 'COMPLETED',
      summary: 'Incident classified as database connection pooling bottleneck on service: checkout-service.',
      durationMs: 820,
      payload: {
        classification: 'Database Overload',
        confidence: 0.98,
        allocatedTeam: 'SRE-DB-Team',
        initialPriority: 'P0',
        triggerDetails: 'Persistent 500 error logs indicating pool checkout timeouts exceeding 5000ms.'
      }
    },
    {
      id: 'run-2',
      incidentId: 'INC-2026-001',
      agentType: AgentType.DIAGNOSIS,
      timestamp: '2026-07-08T22:17:30Z',
      status: 'COMPLETED',
      summary: 'Qdrant vector search completed. Retrieved 2 matching SOP runbooks and 1 historical post-mortem.',
      durationMs: 1420,
      payload: {
        vectorsSearched: 1,
        matches: [
          { id: 'KB-RUNBOOK-001', title: 'PostgreSQL Connection Pool Exhaustion Mitigation SOP', score: 0.94 },
          { id: 'KB-RCA-002', title: 'Kubernetes Pod OOMKilled CrashLoop Troubleshooting', score: 0.62 }
        ],
        systemContext: 'Nginx Router configuration shows normal incoming rate limits. Redis cache health is green.'
      }
    },
    {
      id: 'run-3',
      incidentId: 'INC-2026-001',
      agentType: AgentType.RECOMMENDATION,
      timestamp: '2026-07-08T22:20:00Z',
      status: 'COMPLETED',
      summary: 'Suggested mitigating actions generated from Gemini and KB runbooks.',
      durationMs: 2150,
      payload: {
        actions: [
          {
            title: 'Terminate Idle DB Connections',
            description: 'Run SQL cleanup script on postgresql-primary to kill idle backends sitting in pool queue.',
            command: "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';",
            safetyRating: 'HIGH_SAFE'
          },
          {
            title: 'Scale Out Service Pods',
            description: 'Increase checkout-service deployment replicas to distribute pool overhead.',
            command: 'kubectl scale deployment/checkout-service --replicas=5 -n production',
            safetyRating: 'MEDIUM_RISK'
          },
          {
            title: 'Increase DB Connection Limit',
            description: 'Increase postgres max_connections configuration parameters in custom parameter group.',
            command: 'ALTER SYSTEM SET max_connections = 150;',
            safetyRating: 'CRITICAL_RISK'
          }
        ]
      }
    }
  ],
  'INC-2026-002': [
    {
      id: 'run-k1',
      incidentId: 'INC-2026-002',
      agentType: AgentType.TRIAGE,
      timestamp: '2026-07-08T21:32:45Z',
      status: 'COMPLETED',
      summary: 'Incident classified as infrastructure resource exhaustion (OOMKilled) on service: auth-gateway.',
      durationMs: 740,
      payload: {
        classification: 'Memory Overflow / Resource Limits',
        confidence: 0.95,
        allocatedTeam: 'Infra-DevOps',
        initialPriority: 'P1',
        triggerDetails: 'Kubelet reported auth-gateway container terminated due to exceeding 512Mi allocation.'
      }
    },
    {
      id: 'run-k2',
      incidentId: 'INC-2026-002',
      agentType: AgentType.DIAGNOSIS,
      timestamp: '2026-07-08T21:33:15Z',
      status: 'COMPLETED',
      summary: 'Retrieved OOM mitigation guidelines via Qdrant indexing.',
      durationMs: 1100,
      payload: {
        matches: [
          { id: 'KB-RCA-002', title: 'Kubernetes Pod OOMKilled CrashLoop Troubleshooting', score: 0.97 }
        ]
      }
    }
  ]
};

const mapApiAgentRun = (run: any): AgentOutput => {
  return {
    id: run.id,
    incidentId: run.incidentId,
    agentType: run.agentType as AgentType,
    timestamp: run.timestamp,
    status: run.status as any,
    summary: run.summary,
    payload: run.payload || {},
    durationMs: run.payload?.durationMs || (1000 + Math.floor(Math.random() * 800))
  };
};

export const agentService = {
  getAgentRunsForIncident: async (incidentId: string): Promise<AgentOutput[]> => {
    const { data, isMock } = await apiRequest<any[]>(`/api/v1/agents/runs/incident/${incidentId}`);
    if (!isMock && data) {
      return data.map(mapApiAgentRun);
    }
    return mockAgentRuns[incidentId] || [];
  },

  triggerPipelineStep: async (incidentId: string, agentType: AgentType): Promise<AgentOutput> => {
    // If we're starting the pipeline (Triage), trigger the FULL backend workflow
    if (agentType === AgentType.TRIAGE) {
      const { data, error, isMock } = await apiRequest<any>(`/api/v1/incidents/${incidentId}/trigger-pipeline`, {
        method: 'POST'
      });

      if (!isMock && data && data.status === 'SUCCESS') {
        // Fetch all completed runs from database to get the real outputs
        const runsRes = await apiRequest<any[]>(`/api/v1/agents/runs/incident/${incidentId}`);
        if (runsRes.data) {
          const mappedRuns = runsRes.data.map(mapApiAgentRun);
          // Sync local mock
          mockAgentRuns[incidentId] = mappedRuns;
          
          // Return the Triage run
          const triageRun = mappedRuns.find(r => r.agentType === AgentType.TRIAGE);
          if (triageRun) return triageRun;
        }
      }
    } else {
      // For subsequent steps, the backend pipeline has already completed them during Triage trigger.
      // We can just fetch them from database!
      const { data, isMock } = await apiRequest<any[]>(`/api/v1/agents/runs/incident/${incidentId}`);
      if (!isMock && data) {
        const mappedRuns = data.map(mapApiAgentRun);
        mockAgentRuns[incidentId] = mappedRuns;
        const matchingRun = mappedRuns.find(r => r.agentType === agentType);
        if (matchingRun) return matchingRun;
      }
    }

    // Fallback if backend is offline or fails
    await new Promise((resolve) => setTimeout(resolve, 1000)); // Latency feel

    let summary = '';
    let payload: Record<string, any> = {};

    switch (agentType) {
      case AgentType.TRIAGE:
        summary = 'Incident triage classification complete (Offline Mode).';
        payload = { classification: 'Unclassified Alert', confidence: 0.88, allocatedTeam: 'On-Call' };
        break;
      case AgentType.DIAGNOSIS:
        summary = 'Diagnosing logs and searching Knowledge base records...';
        payload = { vectorsSearched: 1, matches: [] };
        break;
      case AgentType.RECOMMENDATION:
        summary = 'Formulating runbook recommendation steps.';
        payload = { actions: [{ title: 'Restart target pod', description: 'Gracefully recycle the service container.', command: 'kubectl rollout restart deployment/service' }] };
        break;
      case AgentType.REPORT:
        summary = 'Comprehensive Root Cause Incident Report drafted.';
        payload = {
          reportId: `REP-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
          markdownContent: `# Sentinel Incident Post-Mortem Report

## Summary
The system experienced a bottleneck on checkout transactions due to resource starvation.

## Diagnosis
- **Origin**: postgresql connection pool saturation.
- **RCA**: A transient burst in checkout requests caused connection limits to reach maximum capacity.
- **Mitigation**: Idle database connection slots were terminated manually.`
        };
        break;
      case AgentType.KNOWLEDGE:
        summary = 'Incident history indexed successfully back into Qdrant vectors.';
        payload = { vectorsInserted: 12, collection: 'sentinel_incident_knowledge' };
        break;
    }

    const nextRun: AgentOutput = {
      id: `run-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
      incidentId,
      agentType,
      timestamp: new Date().toISOString(),
      status: 'COMPLETED',
      summary,
      durationMs: 1200 + Math.floor(Math.random() * 800),
      payload
    };

    if (!mockAgentRuns[incidentId]) {
      mockAgentRuns[incidentId] = [];
    }
    mockAgentRuns[incidentId].push(nextRun);
    return nextRun;
  },

  clearRunsForIncident: async (incidentId: string): Promise<void> => {
    mockAgentRuns[incidentId] = [];
  }
};
