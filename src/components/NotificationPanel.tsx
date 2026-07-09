import React from 'react';
import { useApp } from '../context/AppContext';
import { Bell, ShieldAlert, Cpu, Database, Wifi } from 'lucide-react';

export const NotificationPanel: React.FC = () => {
  const { notifications, systemOverview } = useApp();

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xs select-none">
      <div className="p-4 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-blue-400" />
          <h3 className="font-sans font-bold text-slate-200 text-sm">Cluster Health Indicators</h3>
        </div>
        <span className="font-mono text-[9px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-1.5 py-0.5 rounded font-semibold">
          ALL SYSTEMS NOMINAL
        </span>
      </div>

      <div className="p-5 space-y-4">
        {/* Core telemetry scores */}
        <div className="grid grid-cols-3 gap-2.5">
          <div className="p-2.5 bg-slate-950 border border-slate-800/80 rounded-lg flex flex-col items-center justify-center text-center">
            <Cpu className="w-3.5 h-3.5 text-blue-400 mb-1" />
            <span className="font-sans text-[10px] text-slate-400">Agents</span>
            <span className="font-mono text-xs font-bold text-slate-200">{systemOverview.agentsOnlineCount} online</span>
          </div>

          <div className="p-2.5 bg-slate-950 border border-slate-800/80 rounded-lg flex flex-col items-center justify-center text-center">
            <Database className="w-3.5 h-3.5 text-indigo-400 mb-1" />
            <span className="font-sans text-[10px] text-slate-400">KB Vectors</span>
            <span className="font-mono text-xs font-bold text-slate-200">{systemOverview.ragVectorsIndexed}</span>
          </div>

          <div className="p-2.5 bg-slate-950 border border-slate-800/80 rounded-lg flex flex-col items-center justify-center text-center">
            <Wifi className="w-3.5 h-3.5 text-emerald-400 mb-1" />
            <span className="font-sans text-[10px] text-slate-400">SRE Sync</span>
            <span className="font-mono text-xs font-bold text-emerald-400">100%</span>
          </div>
        </div>

        {/* Short list of alerts */}
        <div className="space-y-2">
          <span className="block text-[10px] font-mono font-bold text-slate-500 uppercase tracking-wider">
            Recent SRE Events
          </span>
          <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
            {notifications.slice(0, 4).map((not) => (
              <div key={not.id} className="p-2 bg-slate-950/80 border border-slate-900 rounded-lg flex items-start gap-2 text-[11px]">
                <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                  not.type === 'error' ? 'bg-rose-500' : not.type === 'warn' ? 'bg-amber-500' : 'bg-blue-500'
                }`} />
                <div className="font-sans text-slate-400">
                  <span className="text-slate-300">{not.text}</span>
                  <span className="text-[9px] font-mono text-slate-600 block mt-0.5">
                    {new Date(not.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
