import React, { useState } from 'react';
import { Report } from '../types';
import { FileText, ClipboardList, AlertCircle, CheckCircle, ChevronDown, ChevronUp, Calendar, ArrowRight } from 'lucide-react';

interface ReportCardProps {
  report: Report;
}

export const ReportCard: React.FC<ReportCardProps> = ({ report }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getActionItemIcon = (status: 'TODO' | 'IN_PROGRESS' | 'DONE') => {
    switch (status) {
      case 'DONE': return CheckCircle;
      default: return AlertCircle;
    }
  };

  const getActionItemColor = (status: 'TODO' | 'IN_PROGRESS' | 'DONE') => {
    switch (status) {
      case 'DONE': return 'text-emerald-400';
      default: return 'text-amber-400 animate-pulse';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700/80 transition-all shadow-xs select-none">
      {/* Header Summary click panel */}
      <div 
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-5 flex items-start justify-between gap-4 cursor-pointer hover:bg-slate-800/20 transition-colors"
      >
        <div className="space-y-2 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] text-blue-400 font-bold bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
              RCA-{report.incidentId}
            </span>
            <span className="text-slate-700 font-sans">•</span>
            <div className="flex items-center gap-1 text-slate-500 font-mono text-[10.5px]">
              <Calendar className="w-3.5 h-3.5" />
              <span>{new Date(report.createdAt).toLocaleDateString()}</span>
            </div>
          </div>

          <h4 className="font-sans font-bold text-slate-200 text-[14px] tracking-tight hover:text-slate-100 transition-colors">
            {report.title}
          </h4>

          <p className="text-xs text-slate-400 font-sans line-clamp-2">
            {report.summary}
          </p>
        </div>

        <div className="flex items-center gap-3 pt-0.5">
          <span className="font-mono text-[10.5px] text-slate-500 bg-slate-950 px-2 py-0.5 rounded border border-slate-800/40">
            {report.actionItems.length} Actions
          </span>
          <button className="p-1 hover:bg-slate-800 text-slate-400 rounded-lg transition-colors">
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Expanded Report Content */}
      {isExpanded && (
        <div className="p-5 border-t border-slate-800 bg-slate-950/40 space-y-5">
          
          {/* Root Cause Block */}
          <div className="space-y-1.5">
            <h5 className="text-[10px] font-mono font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5" />
              Root Cause Identification (RCA)
            </h5>
            <p className="text-xs text-slate-300 leading-relaxed font-sans bg-slate-900 border border-slate-800/80 rounded-lg p-3">
              {report.rootCause}
            </p>
          </div>

          {/* Timeline Block */}
          {report.timeline && report.timeline.length > 0 && (
            <div className="space-y-2">
              <h5 className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5" />
                Incident Lifecycle Timeline
              </h5>
              <div className="border border-slate-800/80 bg-slate-950/80 rounded-lg p-3 space-y-2.5 font-mono text-[10.5px]">
                {report.timeline.map((item, idx) => (
                  <div key={idx} className="flex gap-4">
                    <span className="text-slate-500 shrink-0">[{new Date(item.timestamp).toLocaleTimeString()}]</span>
                    <span className="text-slate-300 leading-relaxed">{item.event}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Impact Block */}
          <div className="space-y-1.5">
            <h5 className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
              Systemic Blast Radius & Impact
            </h5>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              {report.impact}
            </p>
          </div>

          {/* Corrective Action Items Checklist */}
          <div className="space-y-2.5">
            <h5 className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <ClipboardList className="w-3.5 h-3.5 text-blue-400" />
              Corrective Action Items
            </h5>
            <div className="space-y-1.5">
              {report.actionItems.map((act) => {
                const ActionIcon = getActionItemIcon(act.status);
                const iconColor = getActionItemColor(act.status);

                return (
                  <div key={act.id} className="p-2.5 bg-slate-950 border border-slate-900 rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <ActionIcon className={`w-4 h-4 shrink-0 ${iconColor}`} />
                      <span className={`text-xs font-sans ${act.status === 'DONE' ? 'text-slate-500 line-through' : 'text-slate-300'}`}>
                        {act.title}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 font-mono text-[10px] text-slate-500">
                      <span>Owner: <strong className="text-slate-400">{act.assignee || 'On-Call SRE'}</strong></span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[10.5px] font-mono text-slate-500">
            <span>Author SRE: <strong className="text-slate-400">{report.createdBy}</strong></span>
            <span>Mastra Report Engine v1.0</span>
          </div>

        </div>
      )}
    </div>
  );
};
