import { apiRequest } from './api';
import { AuditLog } from '../types';

export const auditLogService = {
  getAuditLogs: async (): Promise<AuditLog[]> => {
    const { data, isMock } = await apiRequest<AuditLog[]>('/api/v1/audit-logs?limit=50');
    if (!isMock && data) {
      return data;
    }
    return [
      {
        id: 'log-1',
        userId: 'admin-1',
        userName: 'Admin User',
        action: 'ENKRYPT_SCAN',
        targetId: 'incident-1',
        targetType: 'Incident',
        timestamp: new Date().toISOString(),
        details: 'Simulated audit log'
      }
    ];
  }
};
