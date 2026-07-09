import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import { IncidentStatus, IncidentSeverity, IncidentPriority, IncidentLog } from '../types';
import { AgentStatusCard } from '../components/AgentStatusCard';
import { Timeline } from '../components/Timeline';
import { LogUploader } from '../components/LogUploader';
import { 
  ArrowLeft, 
  Terminal, 
  User, 
  ShieldAlert, 
  Calendar, 
  Settings, 
  ExternalLink,
  RefreshCw
} from 'lucide-react';

interface IncidentDetailsProps {
  id: string;
}

export const IncidentDetails: React.FC<IncidentDetailsProps> = ({ id }) => {
  const { 
    incidents, 
    setView, 
    getLogs, 
    notifications, 
    updateIncidentStatus,
    isLoading 
  } = useApp();

  const [logs, setLogs] = useState<IncidentLog[]>([]);
  const [isRefreshingLogs, setIsRefreshingLogs] = useState(false);

  const incident = incidents.find(inc => inc.id === id);

  const loadIncidentLogs = async () => {
    if (!id) return;
    setIsRefreshingLogs(true);
    try {
      const fetchedLogs = await getLogs(id);
      setLogs(fetchedLogs);
    } catch (err) {
      console.error(err);
    } finally {
      setIsRefreshingLogs(false);
    }
  };

  // Reload logs on mount and whenever a new notification/log is captured globally
  useEffect(() => {
    loadIncidentLogs();
  }, [id, notifications]);

  if (!incident) {
    return (
      <div className="text-center py-20 select-none">
        <h4 className="font-sans font-bold text-slate-400">Incident Not Found</h4>
        <button 
          onClick={() => setView('incidents')}
          className="mt-4 text-blue-400 hover:underline text-xs font-semibold cursor-pointer"
        >
          Return to Incident Queue
        </button>
      </div>
    );
  }

  const getLogLevelStyle = (level: string) => {
    switch (level) {
      case 'FATAL': return 'text-rose-500 font-bold bg-rose-500/10 px-1.5 rounded';
      case 'ERROR': return 'text-rose-400 font-bold';
      case 'WARN': return 'text-amber-400 font-semibold';
      default: return 'text-blue-400';
    }
  };

  return (
    <div className="space-y-6 pb-12 select-none animate-fadeIn">
      {/* Breadcrumb Back row */}
      <button
        onClick={() => setView('incidents', null)}
        className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-slate-200 transition-colors cursor-pointer group"
      >
        <ArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-0.5" />
        <span>Back to Incident Queue</span>
      </button>

      {/* Main Grid: Left is diagnostics, Right is automation */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Column: Summary & Logs (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          
          {/* Summary Panel */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 border-b border-slate-800 pb-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-slate-500 font-bold">{incident.id}</span>
                  <span className="text-slate-800 font-sans">•</span>
                  <span className="text-xs font-mono font-semibold text-blue-400">{incident.service}</span>
                </div>
                <h3 className="font-sans font-bold text-slate-200 text-[15px] leading-tight">
                  {incident.title}
                </h3>
              </div>

              {/* Status drop control */}
              <div className="flex items-center gap-1.5 font-mono text-xs">
                <span className="text-slate-500">State:</span>
                <select
                  value={incident.status}
                  onChange={(e) => updateIncidentStatus(incident.id, e.target.value as any)}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-200 font-bold focus:outline-hidden cursor-pointer"
                >
                  {Object.values(IncidentStatus).map(st => (
                    <option key={st} value={st}>{st}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Description lines */}
            <p className="text-xs text-slate-400 leading-relaxed font-sans bg-slate-950/40 p-3.5 border border-slate-800/60 rounded-lg">
              {incident.description}
            </p>

            {/* Stats list */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs border-t border-slate-800 pt-3">
              <div>
                <span className="block text-slate-500 font-sans text-[10.5px]">Severity</span>
                <span className="font-mono font-bold text-rose-400">{incident.severity}</span>
              </div>
              <div>
                <span className="block text-slate-500 font-sans text-[10.5px]">Priority</span>
                <span className="font-mono font-bold text-amber-400">{incident.priority}</span>
              </div>
              <div>
                <span className="block text-slate-500 font-sans text-[10.5px]">Triggered</span>
                <span className="font-sans text-slate-300 font-semibold">{new Date(incident.createdAt).toLocaleTimeString()}</span>
              </div>
              <div>
                <span className="block text-slate-500 font-sans text-[10.5px]">Owner SRE</span>
                <div className="flex items-center gap-1.5 mt-0.5">
                  {incident.assignedTo ? (
                    <>
                      <img src={incident.assignedTo.avatarUrl} alt="SRE" className="w-4 h-4 rounded-full object-cover" />
                      <span className="text-slate-300 font-semibold truncate">{incident.assignedTo.name.split(' ')[0]}</span>
                    </>
                  ) : (
                    <span className="text-slate-500">Unassigned</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Telemetry log stream */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xs flex flex-col h-[320px]">
            <div className="p-3 bg-slate-950 border-b border-slate-800/80 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Terminal className="w-3.5 h-3.5 text-blue-400" />
                <h4 className="font-mono text-xs font-bold text-slate-300">Live Telemetry Terminal Log Stream</h4>
              </div>
              
              <button
                onClick={loadIncidentLogs}
                disabled={isRefreshingLogs}
                className="p-1 hover:bg-slate-800 text-slate-500 hover:text-slate-300 rounded cursor-pointer disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isRefreshingLogs ? 'animate-spin' : ''}`} />
              </button>
            </div>

            <div className="p-4 flex-1 bg-slate-950/70 font-mono text-[10.5px] overflow-y-auto space-y-2 select-all scrollbar-thin">
              {logs.length === 0 ? (
                <p className="text-slate-600 italic text-center py-10">No diagnostic telemetry logged. Drag or upload log files below.</p>
              ) : (
                logs.map((log) => (
                  <div key={log.id} className="flex items-start gap-2.5 hover:bg-slate-900/40 p-1 rounded transition-colors">
                    <span className="text-slate-500 shrink-0">
                      [{new Date(log.timestamp).toLocaleTimeString()}]
                    </span>
                    <span className="text-blue-400 shrink-0 font-bold" title="Source">
                      [{log.source}]
                    </span>
                    <span className={`shrink-0 ${getLogLevelStyle(log.level)}`}>
                      {log.level}
                    </span>
                    <span className="text-slate-300 leading-relaxed break-all">
                      {log.message}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Log Uploader */}
          <LogUploader incidentId={incident.id} />

        </div>

        {/* Right Column: Multi-Agent Automation (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <AgentStatusCard incident={incident} />
          <Timeline incidentId={incident.id} />
        </div>

      </div>

    </div>
  );
};
