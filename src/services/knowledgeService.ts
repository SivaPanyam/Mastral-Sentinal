import { KnowledgeDocument, KnowledgeType } from '../types';
import { apiRequest } from './api';

let mockKnowledgeDocuments: KnowledgeDocument[] = [
  {
    id: 'KB-RUNBOOK-001',
    title: 'PostgreSQL Connection Pool Exhaustion Mitigation SOP',
    type: KnowledgeType.RUNBOOK,
    content: `# PostgreSQL Connection Pool Exhaustion Mitigation

## Overview
When client pools (e.g. HikariCP, pg-pool) are saturated, clients will report timeouts. PostgreSQL max_connections setting might be exceeded, or an individual service is leaking connections.

## Diagnosis Steps
1. Query active connections:
   \`\`\`sql
   SELECT state, count(*) FROM pg_stat_activity GROUP BY state;
   \`\`\`
2. Check for locked connections:
   \`\`\`sql
   SELECT blocked_locks.pid AS blocked_pid, blocking_locks.pid AS blocking_pid FROM pg_catalog.pg_locks blocked_locks...
   \`\`\`

## Mitigation Actions
1. **Scale-out instances**: Relieve connection pressure if traffic spiked.
2. **Increase max_connections**: Temporarily scale Postgres config (be cautious of RAM overhead).
3. **Terminate idle connections**: Kill idle sessions holding locks.
   \`\`\`sql
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';
   \`\`\`
4. **Deploy PgBouncer**: Ensure a pooler is active.`,
    service: 'postgresql-primary',
    author: 'Elena Rostova',
    tags: ['postgres', 'runbook', 'database', 'mitigation'],
    lastUpdated: '2026-06-15T12:00:00Z',
    vectorsCount: 1536
  },
  {
    id: 'KB-RCA-002',
    title: 'Kubernetes Pod OOMKilled CrashLoop Troubleshooting',
    type: KnowledgeType.RCA,
    content: `# Kubernetes Pod OOMKilled Analysis

## Incident Reference: INC-2026-002
An Out-Of-Memory (OOM) termination occurs when a container exceeds its configured limit.

## Corrective Actions
1. **Analyze Pod Metrics**: Verify if memory climbed steadily (Memory Leak) or spiked abruptly.
2. **Update Resources Config**: Adjust Helm or K8s deployment spec:
   \`\`\`yaml
   resources:
     limits:
       memory: "1Gi"
     requests:
       memory: "512Mi"
   \`\`\`
3. **Verify Node Allocatable**: Ensure the target node is not oversaturated.`,
    service: 'auth-gateway',
    author: 'Marcus Chen',
    tags: ['kubernetes', 'oom', 'crashloop', 'limits'],
    lastUpdated: '2026-07-01T08:30:00Z',
    vectorsCount: 1536
  },
  {
    id: 'KB-SOP-003',
    title: 'CoreDNS Upstream Resolution Latency SOP',
    type: KnowledgeType.SOP,
    content: `# CoreDNS Upstream Resolution SOP

## Issue description
DNS timeouts inside the VPC where services cannot reach SendGrid, Twilio, or external endpoints.

## Resolution
1. Verify CoreDNS pods are healthy in \`kube-system\` namespace:
   \`\`\`bash
   kubectl get pods -n kube-system -l k8s-app=kube-dns
   \`\`\`
2. Check CoreDNS ConfigMap to see upstream forward configuration:
   \`\`\`
   forward . /etc/resolv.conf 8.8.8.8 8.8.4.4
   \`\`\`
3. Force CoreDNS restart to refresh resolver cache:
   \`\`\`bash
   kubectl rollout restart deployment/coredns -n kube-system
   \`\`\``,
    service: 'api-gateway',
    author: 'Marcus Chen',
    tags: ['dns', 'coredns', 'network', 'kube-system'],
    lastUpdated: '2026-05-10T14:45:00Z',
    vectorsCount: 1536
  }
];

const mapApiKnowledgeDoc = (doc: any): KnowledgeDocument => {
  return {
    id: doc.id,
    title: doc.title,
    type: doc.type as KnowledgeType,
    content: doc.content,
    service: doc.service,
    author: 'Elena Rostova',
    tags: [doc.service, doc.type.toLowerCase()],
    lastUpdated: doc.lastUpdated || new Date().toISOString(),
    vectorsCount: 1536
  };
};

export const knowledgeService = {
  getDocuments: async (): Promise<KnowledgeDocument[]> => {
    const { data, isMock } = await apiRequest<any[]>('/api/v1/knowledge/documents');
    if (!isMock && data) {
      return data.map(mapApiKnowledgeDoc);
    }
    return [...mockKnowledgeDocuments];
  },

  getDocumentById: async (id: string): Promise<KnowledgeDocument | undefined> => {
    const docs = await knowledgeService.getDocuments();
    return docs.find(doc => doc.id === id);
  },

  searchDocuments: async (query: string): Promise<KnowledgeDocument[]> => {
    if (!query) return knowledgeService.getDocuments();

    // Try vector search
    const { data, isMock } = await apiRequest<any[]>(`/api/v1/knowledge/search?query=${encodeURIComponent(query)}`);
    if (!isMock && data) {
      // Map vector search results
      return data.map((item: any) => ({
        id: item.id || `KB-${Date.now()}`,
        title: item.title || 'Retrieved SOP Match',
        type: (item.metadata?.type as KnowledgeType) || KnowledgeType.SOP,
        content: item.content || item.payload?.content || '',
        service: item.metadata?.service || 'cluster',
        author: 'Mastra SRE Vector Retrieval',
        tags: ['vector-match', `score-${Math.round(item.score * 100)}`],
        lastUpdated: new Date().toISOString(),
        vectorsCount: 1536
      }));
    }

    // Fallback local text filtering
    const lowerQuery = query.toLowerCase();
    return mockKnowledgeDocuments.filter((doc) => 
      doc.title.toLowerCase().includes(lowerQuery) ||
      doc.content.toLowerCase().includes(lowerQuery) ||
      doc.service.toLowerCase().includes(lowerQuery) ||
      doc.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
    );
  },

  createDocument: async (docData: Omit<KnowledgeDocument, 'id' | 'lastUpdated'>): Promise<KnowledgeDocument> => {
    const { data, isMock } = await apiRequest<any>('/api/v1/knowledge/documents', {
      method: 'POST',
      body: JSON.stringify({
        title: docData.title,
        type: docData.type,
        service: docData.service,
        content: docData.content
      })
    });

    if (!isMock && data) {
      const mapped = mapApiKnowledgeDoc(data);
      mockKnowledgeDocuments = [mapped, ...mockKnowledgeDocuments];
      return mapped;
    }

    const nextId = `KB-${docData.type}-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    const newDoc: KnowledgeDocument = {
      ...docData,
      id: nextId,
      lastUpdated: new Date().toISOString(),
      vectorsCount: 1536
    };
    mockKnowledgeDocuments = [newDoc, ...mockKnowledgeDocuments];
    return newDoc;
  },

  uploadDocument: async (file: File): Promise<KnowledgeDocument | null> => {
    try {
      const token = localStorage.getItem('mastra_token');
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch('/api/v1/knowledge/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      if (!response.ok) throw new Error('Upload failed');
      const data = await response.json();
      const mapped = mapApiKnowledgeDoc(data);
      mockKnowledgeDocuments = [mapped, ...mockKnowledgeDocuments];
      return mapped;
    } catch (e) {
      console.error('File upload failed:', e);
      return null;
    }
  }
};
