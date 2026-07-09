import React from 'react';
import { useApp } from '../context/AppContext';
import { Terminal, Shield, AlertCircle, Info } from 'lucide-react';

export const ActivityFeed: React.FC = () => {
  const { notifications } = useApp();

  const getLogColor = (type: 'info' | 'warn' | 'error') => {
    switch (type) {
      case 'error': return 'text-rose-400';
      case 'warn': return 'text-amber-400';
      default: return 'text-blue-400';
    }
  };

  const getLogIcon = (type: 'info' | 'warn' | 'error') => {
    switch (type) {
      case 'error': return AlertCircle;
      case 'warn': return Shield;
      default: return Info;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xs flex flex-col h-full min-h-[300px] select-none">
      {/* Console Header */}
      <div className="p-3 bg-slate-950 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
          <h3 className="font-mono text-xs font-bold text-slate-300">Sentinel SRE Audit Feed</h3>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 bg-emerald-500 rounded-full animate-ping"></span>
          <span className="font-mono text-[9px] text-slate-500 font-bold uppercase tracking-wider">Stream Live</span>
        </div>
      </div>

      {/* Terminal View */}
      <div className="p-4 flex-1 bg-slate-950/80 font-mono text-[11px] overflow-y-auto space-y-2.5 max-h-[380px] scrollbar-thin">
        {notifications.length === 0 ? (
          <p className="text-slate-600 italic text-center py-6">Awaiting cluster telemetry events...</p>
        ) : (
          notifications.map((not) => {
            const LogIcon = getLogIcon(not.type);
            const colorClass = getLogColor(not.type);
            
            return (
              <div key={not.id} className="flex gap-2.5 hover:bg-slate-900/40 p-1.5 rounded transition-colors group">
                <span className="text-slate-600 shrink-0 font-medium">
                  [{new Date(not.timestamp).toLocaleTimeString()}]
                </span>
                
                <span className={`shrink-0 mt-0.5 ${colorClass}`}>
                  <LogIcon className="w-3.5 h-3.5" />
                </span>

                <div className="flex-1 text-slate-300 group-hover:text-slate-200 transition-colors leading-relaxed">
                  {not.text}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Console footer */}
      <div className="p-2.5 bg-slate-950 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-600 font-mono">
        <span>Sentinel Engine v1.0.0</span>
        <span>Secure TLS Log Sink</span>
      </div>
    </div>
  );
};
