/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export enum IncidentStatus {
  TRIGGERED = 'TRIGGERED',
  ACKNOWLEDGED = 'ACKNOWLEDGED',
  TRIAGED = 'TRIAGED',
  DIAGNOSING = 'DIAGNOSING',
  INVESTIGATING = 'INVESTIGATING',
  RESOLVED = 'RESOLVED',
}

export enum IncidentSeverity {
  SEV0 = 'SEV0', // Critical
  SEV1 = 'SEV1', // Major
  SEV2 = 'SEV2', // Minor
}

export enum IncidentPriority {
  P0 = 'P0',
  P1 = 'P1',
  P2 = 'P2',
  P3 = 'P3',
}

export enum AgentType {
  TRIAGE = 'TRIAGE',
  DIAGNOSIS = 'DIAGNOSIS',
  RECOMMENDATION = 'RECOMMENDATION',
  REPORT = 'REPORT',
  KNOWLEDGE = 'KNOWLEDGE',
}

export enum KnowledgeType {
  RUNBOOK = 'RUNBOOK',
  INCIDENT = 'INCIDENT',
  RCA = 'RCA',
  POLICY = 'POLICY',
  SOP = 'SOP',
}

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  avatarUrl?: string;
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  status: IncidentStatus;
  severity: IncidentSeverity;
  priority: IncidentPriority;
  service: string;
  createdAt: string;
  updatedAt: string;
  resolvedAt?: string;
  assignedTo?: User;
  tags: string[];
}

export interface IncidentLog {
  id: string;
  incidentId: string;
  timestamp: string;
  source: string; // e.g. 'Kubernetes', 'CloudWatch', 'Nginx'
  level: 'INFO' | 'WARN' | 'ERROR' | 'FATAL';
  message: string;
}

export interface AgentOutput {
  id: string;
  incidentId: string;
  agentType: AgentType;
  timestamp: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  summary: string;
  payload: Record<string, any>; // JSON structure matching the agent schema
  durationMs: number;
}

export interface Runbook {
  id: string;
  title: string;
  service: string;
  steps: string[];
  lastUpdated: string;
}

export interface Report {
  id: string;
  incidentId: string;
  title: string;
  summary: string;
  rootCause: string;
  timeline: { timestamp: string; event: string }[];
  impact: string;
  actionItems: { id: string; title: string; status: 'TODO' | 'IN_PROGRESS' | 'DONE'; assignee?: string }[];
  createdAt: string;
  createdBy: string;
}

export interface AuditLog {
  id: string;
  userId: string;
  userName: string;
  action: string;
  targetId: string;
  targetType: string;
  timestamp: string;
  details: string;
}

export interface KnowledgeDocument {
  id: string;
  title: string;
  type: KnowledgeType;
  content: string;
  service: string;
  author: string;
  tags: string[];
  lastUpdated: string;
  vectorsCount?: number;
  status?: string;
}

export interface ServiceHealth {
  name: string;
  status: 'HEALTHY' | 'DEGRADED' | 'DOWN';
  latencyMs: number;
  uptime24h: number;
}

export interface MetricPoint {
  date: string;
  incidents: number;
  mttrMinutes: number;
}

