import React, { useState } from 'react';
import { AgentOutput, AgentType } from '../types';
import { useApp } from '../context/AppContext';
import { 
  ShieldAlert, 
  Search, 
  Wand2, 
  FileText, 
  Database, 
  Terminal, 
  Check, 
  Cpu, 
  Clock, 
  Flame 
} from 'lucide-react';

interface TimelineProps {
  incidentId: string;
}

export const Timeline: React.FC<TimelineProps> = ({ incidentId }) => {
  const { agentRuns, addIncidentLog } = useApp();
  const [executedCommands, setExecutedCommands] = useState<Record<string, boolean>>({});

  const runs = agentRuns[incidentId] || [];

  const getAgentColor = (type: AgentType) => {
    switch (type) {
      case AgentType.TRIAGE: return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      case AgentType.DIAGNOSIS: return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
      case AgentType.RECOMMENDATION: return 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20';
      case AgentType.REPORT: return 'text-purple-400 bg-purple-500/10 border-purple-500/20';
      case AgentType.KNOWLEDGE: return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    }
  };

  const getAgentIcon = (type: AgentType) => {
    switch (type) {
      case AgentType.TRIAGE: return ShieldAlert;
      case AgentType.DIAGNOSIS: return Search;
      case AgentType.RECOMMENDATION: return Wand2;
      case AgentType.REPORT: return FileText;
      case AgentType.KNOWLEDGE: return Database;
    }
  };

  const handleRunCommand = async (actionId: string, cmd: string, actionTitle: string) => {
    if (executedCommands[actionId]) return;
    setExecutedCommands(prev => ({ ...prev, [actionId]: true }));
    // Append mock SRE log
    await addIncidentLog(
      incidentId,
      `SUCCESS: Mitigation command [${actionTitle}] successfully executed. Command output: OK`,
      'Mastra-Mitigation-Engine',
      'INFO'
    );
  };

  if (runs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center border border-dashed border-slate-800 rounded-xl bg-slate-950/20 select-none">
        <Cpu className="w-8 h-8 text-slate-600 animate-pulse mb-3" />
        <h4 className="font-sans font-bold text-slate-400 text-xs uppercase tracking-wider">Awaiting Pipeline Activation</h4>
        <p className="text-slate-500 text-[11px] max-w-sm mt-1 leading-relaxed font-sans">
          Trigger the initial <strong>Triage Agent</strong> step above to activate Mastra's diagnostic sequence.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 select-none relative before:absolute before:left-[17px] before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800/80">
      {runs.map((run, index) => {
        const Icon = getAgentIcon(run.agentType);
        const colorClass = getAgentColor(run.agentType);

        return (
          <div key={run.id} className="relative pl-10 group">
            {/* Pulsating Agent Icon Anchor */}
            <div className={`absolute left-0 top-0.5 p-1.5 rounded-full border shrink-0 z-10 ${colorClass}`}>
              <Icon className="w-4 h-4" />
            </div>

            {/* Container */}
            <div className="p-4 bg-slate-950/40 border border-slate-800/60 rounded-xl space-y-3 hover:border-slate-800 transition-colors">
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                <div className="flex items-center gap-2">
                  <span className="font-sans font-bold text-xs text-slate-200">
                    Mastra {run.agentType} Agent Run
                  </span>
                  <span className="text-slate-700 font-sans">•</span>
                  <span className="font-mono text-[10px] text-slate-500">
                    {run.durationMs}ms latency
                  </span>
                </div>
                <span className="text-[10px] font-mono text-slate-500">
                  {new Date(run.timestamp).toLocaleTimeString()}
                </span>
              </div>

              {/* Summary line */}
              <p className="text-xs text-slate-300 font-sans leading-relaxed">
                {run.summary}
              </p>

              {/* Dynamic Payload Renderings (Agent Contracts) */}
              {run.agentType === AgentType.TRIAGE && run.payload && (
                <div className="p-3 bg-slate-950/80 border border-slate-900 rounded-lg space-y-1.5">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div>
                      <span className="block text-[9.5px] font-mono text-slate-500 uppercase">Classification</span>
                      <span className="text-[11px] font-semibold text-slate-300 font-sans">{run.payload.classification}</span>
                    </div>
                    <div>
                      <span className="block text-[9.5px] font-mono text-slate-500 uppercase">Confidence</span>
                      <span className="text-[11px] font-mono font-bold text-emerald-400">{(run.payload.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div>
                      <span className="block text-[9.5px] font-mono text-slate-500 uppercase">Responders</span>
                      <span className="text-[11px] font-semibold text-slate-300 font-sans">{run.payload.allocatedTeam}</span>
                    </div>
                    <div>
                      <span className="block text-[9.5px] font-mono text-slate-500 uppercase">Initial Priority</span>
                      <span className="text-[11px] font-mono font-bold text-rose-400">{run.payload.initialPriority}</span>
                    </div>
                  </div>
                </div>
              )}

              {run.agentType === AgentType.DIAGNOSIS && run.payload && (
                <div className="p-3 bg-slate-950/80 border border-slate-900 rounded-lg space-y-2">
                  <span className="block text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                    Qdrant Context Retrieval Matches:
                  </span>
                  <div className="space-y-1.5">
                    {run.payload.matches && run.payload.matches.length > 0 ? (
                      run.payload.matches.map((match: any) => (
                        <div key={match.id} className="flex items-center justify-between text-xs font-sans">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-[10px] bg-slate-900 px-1 py-0.5 rounded border border-slate-800 text-blue-400 font-semibold">{match.id}</span>
                            <span className="text-slate-300">{match.title}</span>
                          </div>
                          <span className="font-mono text-[11px] font-bold text-blue-400">{(match.score * 100).toFixed(0)}% score</span>
                        </div>
                      ))
                    ) : (
                      <span className="text-[11px] text-slate-500 font-mono italic">No historical matches indexed. Query parameters stored.</span>
                    )}
                  </div>
                </div>
              )}

              {run.agentType === AgentType.RECOMMENDATION && run.payload && (
                <div className="space-y-2.5">
                  <span className="block text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                    Gemini Auto-Generated Action Plan:
                  </span>
                  <div className="space-y-2">
                    {run.payload.actions && run.payload.actions.map((act: any, actIdx: number) => {
                      const isExecuted = executedCommands[`${run.id}-${actIdx}`];
                      return (
                        <div key={actIdx} className="p-3 bg-slate-950/90 border border-slate-900 rounded-lg flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
                          <div className="space-y-1 max-w-xl">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold text-slate-200">{act.title}</span>
                              <span className={`text-[8.5px] font-mono font-bold px-1.5 py-0.5 rounded-sm uppercase tracking-wide ${
                                act.safetyRating === 'HIGH_SAFE' 
                                  ? 'bg-emerald-500/10 text-emerald-400' 
                                  : act.safetyRating === 'MEDIUM_RISK' 
                                    ? 'bg-amber-500/10 text-amber-400' 
                                    : 'bg-rose-500/10 text-rose-400'
                              }`}>
                                {act.safetyRating}
                              </span>
                            </div>
                            <p className="text-[11.5px] text-slate-400 font-sans leading-relaxed">{act.description}</p>
                            <code className="block font-mono text-[10.5px] text-blue-400 bg-slate-900 border border-slate-800 px-2.5 py-1.5 rounded mt-1.5 select-all overflow-x-auto">
                              {act.command}
                            </code>
                          </div>

                          <button
                            onClick={() => handleRunCommand(`${run.id}-${actIdx}`, act.command, act.title)}
                            disabled={isExecuted}
                            className={`shrink-0 flex items-center gap-1 text-[11px] font-semibold font-sans px-3 py-1.5 rounded-lg border transition-all cursor-pointer ${
                              isExecuted
                                ? 'bg-emerald-500/15 border-emerald-500/20 text-emerald-400 cursor-not-allowed'
                                : 'bg-blue-600 hover:bg-blue-500 text-white border-blue-500'
                            }`}
                          >
                            {isExecuted ? (
                              <>
                                <Check className="w-3.5 h-3.5" />
                                Executed
                              </>
                            ) : (
                              <>
                                <Terminal className="w-3.5 h-3.5" />
                                Execute
                              </>
                            )}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {run.agentType === AgentType.REPORT && run.payload && (
                <div className="p-3.5 bg-slate-950 border border-slate-900 rounded-lg space-y-2">
                  <div className="flex items-center justify-between border-b border-slate-900 pb-1.5">
                    <span className="text-[10px] font-mono font-bold text-slate-400 uppercase tracking-wider">
                      RCA Post-Mortem Draft:
                    </span>
                    <span className="text-[9px] font-mono text-slate-500">{run.payload.reportId}</span>
                  </div>
                  <pre className="text-[10.5px] text-slate-400 font-mono leading-relaxed bg-slate-950 p-2 rounded max-h-36 overflow-y-auto whitespace-pre-wrap select-all">
                    {run.payload.markdownContent}
                  </pre>
                </div>
              )}

              {run.agentType === AgentType.KNOWLEDGE && run.payload && (
                <div className="p-3 bg-slate-950/80 border border-slate-900 rounded-lg flex justify-between items-center text-xs font-mono">
                  <div className="flex items-center gap-2">
                    <Database className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-slate-300">Qdrant Collection Target:</span>
                    <span className="text-blue-400 font-semibold">{run.payload.collection}</span>
                  </div>
                  <span className="text-emerald-400 font-semibold">{run.payload.vectorsInserted} vector partitions stored</span>
                </div>
              )}

            </div>
          </div>
        );
      })}
    </div>
  );
};
