import React from 'react';
import { Incident, IncidentStatus, IncidentSeverity } from '../types';
import { Clock, Tag, User, ShieldAlert } from 'lucide-react';

interface IncidentCardProps {
  incident: Incident;
  onClick: () => void;
}

export const IncidentCard: React.FC<IncidentCardProps> = ({ incident, onClick }) => {
  const getSeverityBadge = (severity: IncidentSeverity) => {
    switch (severity) {
      case IncidentSeverity.SEV0:
        return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      case IncidentSeverity.SEV1:
        return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      case IncidentSeverity.SEV2:
        return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
    }
  };

  const getStatusBadge = (status: IncidentStatus) => {
    switch (status) {
      case IncidentStatus.TRIGGERED:
        return 'text-rose-400 border-rose-500/30 bg-rose-950/20 animate-pulse';
      case IncidentStatus.ACKNOWLEDGED:
        return 'text-amber-400 border-amber-500/30 bg-amber-950/20';
      case IncidentStatus.TRIAGED:
        return 'text-blue-400 border-blue-500/30 bg-blue-950/20';
      case IncidentStatus.DIAGNOSING:
        return 'text-indigo-400 border-indigo-500/30 bg-indigo-950/20';
      case IncidentStatus.INVESTIGATING:
        return 'text-purple-400 border-purple-500/30 bg-purple-950/20';
      case IncidentStatus.RESOLVED:
        return 'text-emerald-400 border-emerald-500/30 bg-emerald-950/20';
    }
  };

  const getElapsedTime = (isoString: string) => {
    const start = new Date(isoString).getTime();
    const now = Date.now();
    const diffMins = Math.floor((now - start) / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return new Date(isoString).toLocaleDateString();
  };

  return (
    <div
      onClick={onClick}
      className="p-5 bg-slate-900 border border-slate-800 hover:border-slate-700/80 rounded-xl shadow-xs hover:shadow-md hover:shadow-slate-950/40 cursor-pointer transition-all flex flex-col justify-between group"
    >
      <div className="space-y-3">
        {/* Header Metadata */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-slate-500 group-hover:text-blue-400 transition-colors">
              {incident.id}
            </span>
            <span className="text-slate-700 font-sans">•</span>
            <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${getSeverityBadge(incident.severity)}`}>
              {incident.severity}
            </span>
            <span className="text-slate-700 font-sans">•</span>
            <span className="text-[10.5px] font-mono font-semibold text-slate-400">
              {incident.service}
            </span>
          </div>

          <span className={`text-[10.5px] font-mono font-bold px-2.5 py-0.5 rounded-md border ${getStatusBadge(incident.status)}`}>
            {incident.status}
          </span>
        </div>

        {/* Content */}
        <div className="space-y-1">
          <h4 className="font-sans font-bold text-slate-200 text-[13.5px] leading-tight group-hover:text-slate-100 transition-colors">
            {incident.title}
          </h4>
          <p className="text-[12px] text-slate-400 leading-relaxed font-sans line-clamp-2">
            {incident.description}
          </p>
        </div>
      </div>

      {/* Footer Details */}
      <div className="mt-4 pt-3.5 border-t border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-slate-500 font-mono text-[10.5px]">
          <Clock className="w-3.5 h-3.5" />
          <span>{getElapsedTime(incident.createdAt)}</span>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Tags */}
          <div className="hidden sm:flex items-center gap-1">
            {incident.tags.slice(0, 2).map(tag => (
              <span key={tag} className="text-[10px] font-mono text-slate-500 bg-slate-950 px-1.5 py-0.5 rounded-sm border border-slate-800/40">
                #{tag}
              </span>
            ))}
          </div>

          {/* Assigned Engineer */}
          {incident.assignedTo ? (
            <div className="flex items-center gap-1.5" title={`Assigned: ${incident.assignedTo.name}`}>
              <img
                src={incident.assignedTo.avatarUrl}
                alt={incident.assignedTo.name}
                className="w-5 h-5 rounded-full object-cover border border-slate-700"
              />
              <span className="text-[10.5px] font-sans font-medium text-slate-400 hidden lg:inline">
                {incident.assignedTo.name.split(' ')[0]}
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-slate-500 font-mono text-[10.5px]">
              <User className="w-3.5 h-3.5" />
              <span>Unassigned</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
