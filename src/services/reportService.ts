import { Report } from '../types';
import { apiRequest } from './api';

let mockReports: Report[] = [
  {
    id: 'REP-2026-001',
    incidentId: 'INC-2026-001',
    title: 'RCA: postgresql connection pooling bottleneck on checkout-service',
    summary: 'The checkout-service reported multiple timeouts resulting in 500 server errors. Saturated primary database pooling resources directly prevented order completion.',
    rootCause: 'pg_stat_activity queries revealed 100 connections were active, completely saturating max_connections. A transient retry storm combined with unindexed search queries on product catalogs held connections open longer than 12000ms, triggering pool starvation.',
    impact: 'Billing gateway downtime: 35 minutes. Estimated 184 failed client checkouts. Overall customer order throughput degraded by 42%.',
    timeline: [
      { timestamp: '2026-07-08T22:15:00Z', event: 'Datadog triggered High Latency alert on checkout transactions' },
      { timestamp: '2026-07-08T22:15:10Z', event: 'Triage Agent parsed billing error stacks, classified as Database Pool Saturation' },
      { timestamp: '2026-07-08T22:17:30Z', event: 'Diagnosis Agent scanned Qdrant, matched KB-RUNBOOK-001 pool guide' },
      { timestamp: '2026-07-08T22:20:00Z', event: 'On-Call SRE approved Gemini recommendation: SELECT pg_terminate_backend(pid)' },
      { timestamp: '2026-07-08T22:25:00Z', event: 'Idle client backend connections successfully terminated, health metrics returned to baseline' }
    ],
    actionItems: [
      { id: 'act-1', title: 'Provision PgBouncer proxy layer in front of postgresql-primary', status: 'TODO', assignee: 'Marcus Chen' },
      { id: 'act-2', title: 'Add database query indexes for the product search query lines', status: 'DONE', assignee: 'Elena Rostova' },
      { id: 'act-3', title: 'Update checkout pool checkoutTimeout limit to 3000ms (was 15000ms)', status: 'TODO', assignee: 'Elena Rostova' }
    ],
    createdAt: '2026-07-08T22:45:00Z',
    createdBy: 'Mastra RCA Report Agent'
  },
  {
    id: 'REP-2026-002',
    incidentId: 'INC-2026-004',
    title: 'RCA: Let\'s Encrypt SSL Cert Renewal Challenge Failures',
    summary: 'SSL certificate verification failed on API subdomains, creating browser trust issues across sandbox APIs.',
    rootCause: 'Automated ACME challenge requests path `/.well-known/acme-challenge/` were blocked by Nginx reverse proxy rewrite configurations which had an incorrect routing parameter.',
    impact: 'Dev subdomains reported trust dialog errors for 12 minutes. No customer-facing production services were affected.',
    timeline: [
      { timestamp: '2026-07-08T18:00:00Z', event: 'ACME challenge validation returned 404 response on routing path' },
      { timestamp: '2026-07-08T18:05:00Z', event: 'SRE on duty adjusted rewrite rules inside nginx ingress configurations' },
      { timestamp: '2026-07-08T21:00:00Z', event: 'Challenge validation rerun successfully completed. Certificate active' }
    ],
    actionItems: [
      { id: 'act-4', title: 'Add test script to verify cert validation paths in CI deployment checks', status: 'DONE', assignee: 'Sarah Jenkins' },
      { id: 'act-5', title: 'Create secondary cron checker to alert 14 days prior to SSL expiration', status: 'DONE', assignee: 'Sarah Jenkins' }
    ],
    createdAt: '2026-07-08T21:15:00Z',
    createdBy: 'Sarah Jenkins'
  }
];

const mapApiReport = (rep: any): Report => {
  return {
    id: rep.id,
    incidentId: rep.incidentId,
    title: rep.title,
    summary: rep.summary,
    rootCause: rep.rootCause,
    impact: rep.impact,
    timeline: rep.timeline || [],
    actionItems: rep.actionItems || [],
    createdAt: rep.createdAt,
    createdBy: rep.createdBy
  };
};

export const reportService = {
  getReports: async (): Promise<Report[]> => {
    const { data, isMock } = await apiRequest<any[]>('/api/v1/reports/');
    if (!isMock && data) {
      return data.map(mapApiReport);
    }
    return [...mockReports];
  },

  createReport: async (reportData: Omit<Report, 'id' | 'createdAt'>): Promise<Report> => {
    const { data, isMock } = await apiRequest<any>('/api/v1/reports/', {
      method: 'POST',
      body: JSON.stringify(reportData)
    });

    if (!isMock && data) {
      const mapped = mapApiReport(data);
      mockReports = [mapped, ...mockReports];
      return mapped;
    }

    const newId = `REP-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    const newReport: Report = {
      ...reportData,
      id: newId,
      createdAt: new Date().toISOString()
    };
    mockReports = [newReport, ...mockReports];
    return newReport;
  }
};
