import { Incident, IncidentStatus, IncidentSeverity, IncidentPriority, IncidentLog, User } from '../types';
import { apiRequest } from './api';

const mockUsers: User[] = [
  { id: 'usr-1', name: 'Elena Rostova', email: 'elena@sentinel.ai', role: 'Staff SRE', avatarUrl: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=150&q=80' },
  { id: 'usr-2', name: 'Marcus Chen', email: 'marcus@sentinel.ai', role: 'Senior DevOps Engineer', avatarUrl: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80' },
  { id: 'usr-3', name: 'Sarah Jenkins', email: 'sarah@sentinel.ai', role: 'Security Analyst', avatarUrl: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?auto=format&fit=crop&w=150&q=80' },
];

let mockIncidents: Incident[] = [
  {
    id: 'INC-2026-001',
    title: 'PostgreSQL Connection Pool Exhaustion',
    description: 'The checkout-service is reporting persistent 500 Internal Server Errors. Primary db-pool capacity is at 100% saturation (100/100 active connections). Connection queue times have breached 5000ms.',
    status: IncidentStatus.DIAGNOSING,
    severity: IncidentSeverity.SEV0,
    priority: IncidentPriority.P0,
    service: 'checkout-service',
    createdAt: '2026-07-08T22:15:00Z',
    updatedAt: '2026-07-08T23:20:00Z',
    assignedTo: mockUsers[0],
    tags: ['database', 'postgres', 'pool-exhaustion', 'checkout-service'],
  },
  {
    id: 'INC-2026-002',
    title: 'Kubernetes Pod CrashLoopBackOff on auth-gateway',
    description: 'Auth-gateway pods in namespace production are crashlooping with OOMKilled status. Memory limits are currently set to 512Mi. Occurs under traffic spikes.',
    status: IncidentStatus.INVESTIGATING,
    severity: IncidentSeverity.SEV1,
    priority: IncidentPriority.P1,
    service: 'auth-gateway',
    createdAt: '2026-07-08T21:30:00Z',
    updatedAt: '2026-07-08T22:45:00Z',
    assignedTo: mockUsers[1],
    tags: ['kubernetes', 'auth-gateway', 'oom-killed', 'infra'],
  },
  {
    id: 'INC-2026-003',
    title: 'External DNS Resolution Failures',
    description: 'The notification-worker service is unable to resolve external API hostnames (e.g., api.sendgrid.com). Intermittent lookup timeouts (DNS loop / CoreDNS latency).',
    status: IncidentStatus.TRIGGERED,
    severity: IncidentSeverity.SEV1,
    priority: IncidentPriority.P2,
    service: 'notification-worker',
    createdAt: '2026-07-08T23:10:00Z',
    updatedAt: '2026-07-08T23:10:00Z',
    tags: ['dns', 'coredns', 'network', 'sendgrid'],
  },
  {
    id: 'INC-2026-004',
    title: 'TLS Certificate Approaching Expiration',
    description: 'Production SSL/TLS certificate for *.sentinel.internal will expire in 4 days. Automated Let\'s Encrypt cronjob failed to renew due to challenge path validation failure.',
    status: IncidentStatus.RESOLVED,
    severity: IncidentSeverity.SEV2,
    priority: IncidentPriority.P3,
    service: 'api-gateway',
    createdAt: '2026-07-08T18:00:00Z',
    updatedAt: '2026-07-08T21:00:00Z',
    resolvedAt: '2026-07-08T21:00:00Z',
    assignedTo: mockUsers[2],
    tags: ['security', 'tls', 'certificates', 'cron'],
  }
];

let mockLogs: Record<string, IncidentLog[]> = {
  'INC-2026-001': [
    { id: 'log-1', incidentId: 'INC-2026-001', timestamp: '2026-07-08T22:15:05Z', source: 'checkout-service', level: 'INFO', message: 'Received POST /checkout/charge for order_90138' },
    { id: 'log-2', incidentId: 'INC-2026-001', timestamp: '2026-07-08T22:15:10Z', source: 'checkout-service', level: 'ERROR', message: 'Database connection checkout failure. Timeout after 5000ms awaiting connection from pool [db-pool].' },
    { id: 'log-3', incidentId: 'INC-2026-001', timestamp: '2026-07-08T22:15:11Z', source: 'postgresql-primary', level: 'WARN', message: 'pg_stat_activity shows 100 active clients. max_connections is 100.' },
    { id: 'log-4', incidentId: 'INC-2026-001', timestamp: '2026-07-08T22:15:15Z', source: 'postgresql-primary', level: 'ERROR', message: 'FATAL: remaining connection slots are reserved for non-replication superuser connections' },
    { id: 'log-5', incidentId: 'INC-2026-001', timestamp: '2026-07-08T22:16:00Z', source: 'checkout-service', level: 'FATAL', message: 'Unhandled exception: pool exhaustion triggered healthcheck failure. Pod terminating.' }
  ],
  'INC-2026-002': [
    { id: 'log-6', incidentId: 'INC-2026-002', timestamp: '2026-07-08T21:30:05Z', source: 'kubelet', level: 'INFO', message: 'Container auth-gateway-pod started.' },
    { id: 'log-7', incidentId: 'INC-2026-002', timestamp: '2026-07-08T21:31:42Z', source: 'auth-gateway', level: 'INFO', message: 'Garbage Collection running. Retained memory 490MB / 512MB.' },
    { id: 'log-8', incidentId: 'INC-2026-002', timestamp: '2026-07-08T21:31:55Z', source: 'kubelet', level: 'FATAL', message: 'Container auth-gateway-pod exceeded memory limit. OOMKilled.' },
    { id: 'log-9', incidentId: 'INC-2026-002', timestamp: '2026-07-08T21:32:10Z', source: 'kube-scheduler', level: 'WARN', message: 'Restarting pod auth-gateway-pod (Count: 4)' }
  ],
  'INC-2026-003': [
    { id: 'log-10', incidentId: 'INC-2026-003', timestamp: '2026-07-08T23:10:02Z', source: 'notification-worker', level: 'INFO', message: 'Processing notification queue batch 4421' },
    { id: 'log-11', incidentId: 'INC-2026-003', timestamp: '2026-07-08T23:10:05Z', source: 'notification-worker', level: 'ERROR', message: 'Failed to post email. lookup api.sendgrid.com: i/o timeout.' },
    { id: 'log-12', incidentId: 'INC-2026-003', timestamp: '2026-07-08T23:10:10Z', source: 'coredns', level: 'WARN', message: 'Upstream DNS 8.8.8.8 took 5022ms to respond to api.sendgrid.com' }
  ],
  'INC-2026-004': [
    { id: 'log-13', incidentId: 'INC-2026-004', timestamp: '2026-07-08T18:00:00Z', source: 'cert-manager-cron', level: 'INFO', message: 'Starting certificate renewal cronjob for *.sentinel.internal' },
    { id: 'log-14', incidentId: 'INC-2026-004', timestamp: '2026-07-08T18:00:05Z', source: 'cert-manager-cron', level: 'ERROR', message: 'Failed challenge validation: GET http://sentinel.internal/.well-known/acme-challenge/test returned 404' },
    { id: 'log-15', incidentId: 'INC-2026-004', timestamp: '2026-07-08T21:00:00Z', source: 'cert-manager-cron', level: 'INFO', message: 'Challenge successfully validated after static path fix. Certificate renewed. Valid until Oct 08, 2026.' }
  ]
};

const mapApiIncident = (apiInc: any): Incident => {
  return {
    id: apiInc.id,
    title: apiInc.title,
    description: apiInc.description || '',
    status: (apiInc.status as IncidentStatus) || IncidentStatus.TRIGGERED,
    severity: (apiInc.severity as IncidentSeverity) || IncidentSeverity.SEV1,
    priority: (apiInc.priority as IncidentPriority) || IncidentPriority.P1,
    service: apiInc.service,
    createdAt: apiInc.createdAt,
    updatedAt: apiInc.updatedAt,
    resolvedAt: apiInc.resolvedAt,
    assignedTo: apiInc.id.endsWith('1') ? mockUsers[0] : apiInc.id.endsWith('2') ? mockUsers[1] : mockUsers[2],
    tags: apiInc.tags || [apiInc.service, 'production']
  };
};

export const incidentService = {
  getUsers: async (): Promise<User[]> => {
    return [...mockUsers];
  },

  getIncidents: async (): Promise<Incident[]> => {
    const { data, isMock } = await apiRequest<any[]>('/api/v1/incidents/');
    if (!isMock && data) {
      return data.map(mapApiIncident);
    }
    return [...mockIncidents];
  },

  getIncidentById: async (id: string): Promise<Incident | undefined> => {
    const { data, isMock } = await apiRequest<any>(`/api/v1/incidents/${id}`);
    if (!isMock && data) {
      return mapApiIncident(data);
    }
    return mockIncidents.find((inc) => inc.id === id);
  },

  createIncident: async (incidentData: Omit<Incident, 'id' | 'createdAt' | 'updatedAt'>): Promise<Incident> => {
    const { data, isMock } = await apiRequest<any>('/api/v1/incidents/', {
      method: 'POST',
      body: JSON.stringify({
        title: incidentData.title,
        description: incidentData.description,
        service: incidentData.service,
        severity: incidentData.severity
      })
    });

    if (!isMock && data) {
      const mapped = mapApiIncident(data);
      mockIncidents = [mapped, ...mockIncidents];
      mockLogs[mapped.id] = [];
      return mapped;
    }

    const nextIdNum = mockIncidents.length + 1;
    const newId = `INC-2026-${String(nextIdNum).padStart(3, '0')}`;
    const newIncident: Incident = {
      ...incidentData,
      id: newId,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    mockIncidents = [newIncident, ...mockIncidents];
    mockLogs[newId] = [];
    return newIncident;
  },

  updateIncident: async (id: string, updates: Partial<Incident>): Promise<Incident> => {
    const { data, isMock } = await apiRequest<any>(`/api/v1/incidents/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates)
    });

    if (!isMock && data) {
      const mapped = mapApiIncident(data);
      const index = mockIncidents.findIndex((inc) => inc.id === id);
      if (index !== -1) {
        mockIncidents[index] = mapped;
      }
      return mapped;
    }

    const index = mockIncidents.findIndex((inc) => inc.id === id);
    if (index === -1) {
      throw new Error(`Incident with ID ${id} not found.`);
    }
    const updatedIncident = {
      ...mockIncidents[index],
      ...updates,
      updatedAt: new Date().toISOString(),
    };
    if (updates.status === IncidentStatus.RESOLVED && !mockIncidents[index].resolvedAt) {
      updatedIncident.resolvedAt = new Date().toISOString();
    }
    mockIncidents[index] = updatedIncident;
    return updatedIncident;
  },

  getLogsForIncident: async (incidentId: string): Promise<IncidentLog[]> => {
    const { data, isMock } = await apiRequest<any>(`/api/v1/incidents/${incidentId}`);
    if (!isMock && data && data.logs) {
      return data.logs.map((log: any) => ({
        id: log.id,
        incidentId: log.incidentId,
        timestamp: log.timestamp,
        source: log.source,
        level: log.level as any,
        message: log.message
      }));
    }
    return mockLogs[incidentId] || [];
  },

  uploadLog: async (incidentId: string, logMessage: string, source: string, level: 'INFO' | 'WARN' | 'ERROR' | 'FATAL' = 'ERROR'): Promise<IncidentLog> => {
    const { data, isMock } = await apiRequest<any>(`/api/v1/incidents/${incidentId}/logs`, {
      method: 'POST',
      body: JSON.stringify({ source, level, message: logMessage })
    });

    if (!isMock && data) {
      const newLog: IncidentLog = {
        id: data.id,
        incidentId: data.incidentId,
        timestamp: data.timestamp,
        source: data.source,
        level: data.level as any,
        message: data.message
      };
      if (!mockLogs[incidentId]) {
        mockLogs[incidentId] = [];
      }
      mockLogs[incidentId].push(newLog);
      return newLog;
    }

    const newLog: IncidentLog = {
      id: `log-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
      incidentId,
      timestamp: new Date().toISOString(),
      source,
      level,
      message: logMessage,
    };
    if (!mockLogs[incidentId]) {
      mockLogs[incidentId] = [];
    }
    mockLogs[incidentId].push(newLog);
    return newLog;
  }
};
