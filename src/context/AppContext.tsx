import React, { createContext, useContext, useState, useEffect } from 'react';
import { Incident, IncidentStatus, IncidentLog, AgentOutput, AgentType, KnowledgeDocument, ServiceHealth, MetricPoint, Report } from '../types';
import { incidentService } from '../services/incidentService';
import { knowledgeService } from '../services/knowledgeService';
import { analyticsService } from '../services/analyticsService';
import { agentService } from '../services/agentService';
import { reportService } from '../services/reportService';
import { wsService } from '../services/wsService';
import { auditLogService } from '../services/auditLogService';

interface AppContextType {
  currentView: 'dashboard' | 'incidents' | 'knowledge' | 'reports' | 'analytics' | 'settings' | 'copilot';
  selectedIncidentId: string | null;
  setView: (view: 'dashboard' | 'incidents' | 'knowledge' | 'reports' | 'analytics' | 'settings' | 'copilot', incidentId?: string | null) => void;
  
  incidents: Incident[];
  serviceHealth: ServiceHealth[];
  metricHistory: MetricPoint[];
  systemOverview: {
    activeAlertsCount: number;
    mttaAvg24h: number;
    mttrAvg24h: number;
    agentsOnlineCount: number;
    ragVectorsIndexed: number;
  };
  knowledgeDocs: KnowledgeDocument[];
  reports: Report[];
  auditLogs: any[];
  
  isLoading: boolean;
  refreshData: () => Promise<void>;
  
  // Incident Handlers
  createNewIncident: (title: string, description: string, service: string, severity: any, priority: any) => Promise<Incident>;
  updateIncidentStatus: (id: string, status: IncidentStatus) => Promise<void>;
  addIncidentLog: (incidentId: string, message: string, source: string, level: 'INFO' | 'WARN' | 'ERROR' | 'FATAL') => Promise<void>;
  getLogs: (incidentId: string) => Promise<IncidentLog[]>;
  
  // Agent Pipeline Handlers
  agentRuns: Record<string, AgentOutput[]>;
  isRunningAgent: boolean;
  triggerAgent: (incidentId: string, agentType: AgentType) => Promise<void>;
  resetAgentPipeline: (incidentId: string) => Promise<void>;

  // Search Knowledge
  searchKB: (query: string) => Promise<void>;
  addKBDoc: (doc: Omit<KnowledgeDocument, 'id' | 'lastUpdated'>) => Promise<void>;
  uploadKBDoc: (file: File) => Promise<void>;

  // Global SRE Notifications Feed
  notifications: Array<{ id: string; timestamp: string; text: string; type: 'info' | 'warn' | 'error' }>;
  addNotification: (text: string, type: 'info' | 'warn' | 'error') => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentView, setCurrentView] = useState<'dashboard' | 'incidents' | 'knowledge' | 'reports' | 'analytics' | 'settings' | 'copilot'>('dashboard');
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null);
  
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [serviceHealth, setServiceHealth] = useState<ServiceHealth[]>([]);
  const [metricHistory, setMetricHistory] = useState<MetricPoint[]>([]);
  const [systemOverview, setSystemOverview] = useState({
    activeAlertsCount: 0,
    mttaAvg24h: 0,
    mttrAvg24h: 0,
    agentsOnlineCount: 0,
    ragVectorsIndexed: 0,
  });
  const [knowledgeDocs, setKnowledgeDocs] = useState<KnowledgeDocument[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [agentRuns, setAgentRuns] = useState<Record<string, AgentOutput[]>>({});
  
  const [isLoading, setIsLoading] = useState(true);
  const [isRunningAgent, setIsRunningAgent] = useState(false);
  const [notifications, setNotifications] = useState<Array<{ id: string; timestamp: string; text: string; type: 'info' | 'warn' | 'error' }>>([
    { id: 'not-1', timestamp: new Date(Date.now() - 300000).toISOString(), text: 'Sentinel Core initialised successfully.', type: 'info' },
    { id: 'not-2', timestamp: new Date(Date.now() - 120000).toISOString(), text: 'SOP Vector Indexes verified in Qdrant (4608 records).', type: 'info' },
  ]);

  const addNotification = (text: string, type: 'info' | 'warn' | 'error') => {
    setNotifications(prev => [
      { id: `not-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`, timestamp: new Date().toISOString(), text, type },
      ...prev.slice(0, 19) // Cap at 20 logs
    ]);
  };

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [incList, healthList, historyList, overview, kbList, reportList, auditList] = await Promise.all([
        incidentService.getIncidents(),
        analyticsService.getServiceHealth(),
        analyticsService.getMetricHistory(),
        analyticsService.getSystemStatusOverview(),
        knowledgeService.getDocuments(),
        reportService.getReports(),
        auditLogService.getAuditLogs(),
      ]);

      setIncidents(incList);
      setServiceHealth(healthList);
      setMetricHistory(historyList);
      setSystemOverview(overview);
      setKnowledgeDocs(kbList);
      setReports(reportList);
      setAuditLogs(auditList);

      // Preload agent runs for default incidents
      const initialRuns: Record<string, AgentOutput[]> = {};
      for (const inc of incList) {
        initialRuns[inc.id] = await agentService.getAgentRunsForIncident(inc.id);
      }
      setAgentRuns(initialRuns);

    } catch (err) {
      console.error("Error loading mock SRE data: ", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    
    // Initialize WebSockets for real-time events
    wsService.connect();
    
    const unsubIncident = wsService.subscribe('INCIDENT_CREATED', (payload) => {
      console.log('WS Event: INCIDENT_CREATED', payload);
      addNotification(`New incident detected: ${payload.id} (${payload.title})`, 'warn');
      incidentService.getIncidents().then(incList => setIncidents(incList));
    });
    
    const unsubIncidentUpdated = wsService.subscribe('INCIDENT_UPDATED', (payload) => {
      console.log('WS Event: INCIDENT_UPDATED', payload);
      incidentService.getIncidents().then(incList => setIncidents(incList));
    });

    const unsubLog = wsService.subscribe('LOG_APPENDED', (payload) => {
      console.log('WS Event: LOG_APPENDED', payload);
      addNotification(`New log appended to ${payload.incident_id}`, 'info');
    });

    const unsubAgentStarted = wsService.subscribe('AGENT_STARTED', (payload) => {
      console.log('WS Event: AGENT_STARTED', payload);
      addNotification(`Mastra Agent ${payload.step} started running...`, 'info');
      setIsRunningAgent(true);
    });

    const unsubAgentFinished = wsService.subscribe('AGENT_FINISHED', (payload) => {
      console.log('WS Event: AGENT_FINISHED', payload);
      addNotification(`Mastra ${payload.agentType} agent finished successfully.`, 'success');
      agentService.getAgentRunsForIncident(payload.incidentId).then(updatedRuns => {
          setAgentRuns(prev => ({
            ...prev,
            [payload.incidentId]: updatedRuns
          }));
      });
      // Incident status is updated by backend, the INCIDENT_UPDATED event will refresh the incidents list.
      setIsRunningAgent(false);
    });

    const unsubReportGenerated = wsService.subscribe('REPORT_GENERATED', (payload) => {
      console.log('WS Event: REPORT_GENERATED', payload);
      addNotification(`RCA Report generated for ${payload.incidentId}`, 'success');
      reportService.getReports().then(updatedReports => setReports(updatedReports));
    });

    const unsubKnowledgeUpdated = wsService.subscribe('KNOWLEDGE_UPDATED', (payload) => {
      console.log('WS Event: KNOWLEDGE_UPDATED', payload);
      addNotification(`Knowledge Base updated: ${payload.title}`, 'info');
      knowledgeService.getDocuments().then(docs => setKnowledgeDocs(docs));
    });

    const unsubMetricsUpdated = wsService.subscribe('METRICS_UPDATED', () => {
      console.log('WS Event: METRICS_UPDATED');
      analyticsService.getSystemStatusOverview().then(overview => setSystemOverview(overview));
      analyticsService.getMetricHistory().then(history => setMetricHistory(history));
    });

    return () => {
      unsubIncident();
      unsubIncidentUpdated();
      unsubLog();
      unsubAgentStarted();
      unsubAgentFinished();
      unsubReportGenerated();
      unsubKnowledgeUpdated();
      unsubMetricsUpdated();
    };
  }, []);

  const setView = (view: 'dashboard' | 'incidents' | 'knowledge' | 'reports' | 'analytics' | 'settings' | 'copilot', incidentId: string | null = null) => {
    setCurrentView(view);
    setSelectedIncidentId(incidentId);
    
    // Set route hash in browser URL for standard browser history behavior inside iframes
    if (incidentId) {
      window.location.hash = `#/${view}/${incidentId}`;
    } else {
      window.location.hash = `#/${view}`;
    }
  };

  // Support direct loading of route on hashchange
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash;
      if (!hash) return;
      const parts = hash.replace('#/', '').split('/');
      const view = parts[0] as any;
      const id = parts[1] || null;
      if (['dashboard', 'incidents', 'knowledge', 'reports', 'analytics', 'settings', 'copilot'].includes(view)) {
        setCurrentView(view);
        setSelectedIncidentId(id);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const createNewIncident = async (title: string, description: string, service: string, severity: any, priority: any) => {
    const nextInc = await incidentService.createIncident({
      title,
      description,
      status: IncidentStatus.TRIGGERED,
      severity,
      priority,
      service,
      tags: [service, 'triage-pending']
    });
    setIncidents(prev => [nextInc, ...prev]);
    setAgentRuns(prev => ({ ...prev, [nextInc.id]: [] }));
    addNotification(`New incident triggered: ${nextInc.id} (${title})`, 'warn');
    return nextInc;
  };

  const updateIncidentStatus = async (id: string, status: IncidentStatus) => {
    const updated = await incidentService.updateIncident(id, { status });
    setIncidents(prev => prev.map(inc => inc.id === id ? updated : inc));
    addNotification(`Incident ${id} status updated to ${status}`, 'info');
  };

  const addIncidentLog = async (incidentId: string, message: string, source: string, level: 'INFO' | 'WARN' | 'ERROR' | 'FATAL') => {
    await incidentService.uploadLog(incidentId, message, source, level);
    addNotification(`New SRE log uploaded to ${incidentId} from ${source}`, 'info');
  };

  const getLogs = async (incidentId: string) => {
    return incidentService.getLogsForIncident(incidentId);
  };

  const triggerAgent = async (incidentId: string, agentType: AgentType) => {
    try {
      setIsRunningAgent(true);
      addNotification(`Launching Mastra ${agentType} agent for ${incidentId}...`, 'info');
      
      // Trigger the pipeline synchronously (it starts the background task in backend)
      await agentService.triggerPipelineStep(incidentId, agentType);
      
      // We no longer manually manage SSE or state here!
      // The backend Mastra engine will process it asynchronously, 
      // push webhooks to FastAPI, which broadcasts WebSockets to ALL clients.
      // The wsService.subscribe hooks will catch AGENT_STARTED, AGENT_FINISHED
      // and update the global state naturally!
      
    } catch (err) {
      console.error(err);
      addNotification(`Mastra ${agentType} agent failed execution.`, 'error');
      setIsRunningAgent(false);
    }
  };

  const resetAgentPipeline = async (incidentId: string) => {
    await agentService.clearRunsForIncident(incidentId);
    setAgentRuns(prev => ({ ...prev, [incidentId]: [] }));
    await updateIncidentStatus(incidentId, IncidentStatus.TRIGGERED);
    addNotification(`Reset agent execution pipeline for ${incidentId}`, 'info');
  };

  const searchKB = async (query: string) => {
    const results = await knowledgeService.searchDocuments(query);
    setKnowledgeDocs(results);
  };

  const addKBDoc = async (docData: Omit<KnowledgeDocument, 'id' | 'lastUpdated'>) => {
    const newDoc = await knowledgeService.createDocument(docData);
    setKnowledgeDocs(prev => [newDoc, ...prev]);
    addNotification(`Indexed new ${docData.type}: ${docData.title}`, 'info');
  };

  const uploadKBDoc = async (file: File) => {
    addNotification(`Uploading and indexing document: ${file.name}...`, 'info');
    const newDoc = await knowledgeService.uploadDocument(file);
    if (newDoc) {
      setKnowledgeDocs(prev => [newDoc, ...prev]);
      addNotification(`Successfully uploaded and indexed ${file.name}`, 'info');
    } else {
      addNotification(`Failed to upload ${file.name}`, 'error');
    }
  };

  return (
    <AppContext.Provider
      value={{
        currentView,
        selectedIncidentId,
        setView,
        incidents,
        serviceHealth,
        metricHistory,
        systemOverview,
        knowledgeDocs,
        reports,
        auditLogs,
        isLoading,
        refreshData: loadData,
        createNewIncident,
        updateIncidentStatus,
        addIncidentLog,
        getLogs,
        agentRuns,
        isRunningAgent,
        triggerAgent,
        resetAgentPipeline,
        searchKB,
        addKBDoc,
        uploadKBDoc,
        notifications,
        addNotification,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
