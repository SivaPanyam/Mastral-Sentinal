import React from 'react';
import { useApp } from '../context/AppContext';
import { 
  LayoutDashboard, 
  ShieldAlert, 
  BookOpen, 
  FileText, 
  BarChart3, 
  Settings, 
  Terminal,
  Activity,
  Cpu,
  Sparkles
} from 'lucide-react';
import { motion } from 'motion/react';

export const Sidebar: React.FC = () => {
  const { currentView, setView, systemOverview } = useApp();

  const menuItems = [
    { id: 'dashboard', name: 'Dashboard', icon: LayoutDashboard },
    { id: 'incidents', name: 'Incidents', icon: ShieldAlert },
    { id: 'knowledge', name: 'Knowledge Base', icon: BookOpen },
    { id: 'reports', name: 'Reports', icon: FileText },
    { id: 'analytics', name: 'Analytics', icon: BarChart3 },
    { id: 'copilot', name: 'AI Copilot', icon: Sparkles },
    { id: 'settings', name: 'Settings', icon: Settings },
  ] as const;

  return (
    <aside id="main-sidebar" className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between h-full select-none">
      {/* Brand Header */}
      <div>
        <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-2.5">
          <div className="p-1.5 bg-blue-600/15 text-blue-400 rounded-lg border border-blue-500/30">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-sans font-bold text-slate-100 tracking-tight leading-none text-base">MASTRA</h1>
            <span className="font-mono text-[9px] text-blue-400 font-semibold tracking-wider uppercase">SENTINEL v1.0</span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-1.5">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                id={`sidebar-link-${item.id}`}
                onClick={() => setView(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all cursor-pointer relative group ${
                  isActive 
                    ? 'text-white bg-slate-800 border-l-2 border-blue-500' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border-l-2 border-transparent'
                }`}
              >
                <Icon className={`w-4 h-4 transition-transform group-hover:scale-105 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                <span>{item.name}</span>
                {item.id === 'incidents' && systemOverview.activeAlertsCount > 0 && (
                  <span className="ml-auto bg-rose-500/15 text-rose-400 border border-rose-500/30 font-mono text-[10px] font-bold px-2 py-0.5 rounded-full">
                    {systemOverview.activeAlertsCount}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Agents Orchestration Console Footer */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/40">
        <div className="bg-slate-950/60 rounded-xl p-3 border border-slate-800/60 flex flex-col gap-2.5">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-emerald-400 animate-pulse" />
            <span className="text-xs font-semibold text-slate-300 font-sans">Mastra Agent Pool</span>
          </div>
          
          <div className="space-y-1.5">
            {['Triage', 'Diagnosis', 'Recommendation', 'RCA Reporter', 'Knowledge Engine'].map((agentName, idx) => (
              <div key={agentName} className="flex items-center justify-between text-[10.5px]">
                <div className="flex items-center gap-1.5 text-slate-400 font-mono">
                  <Terminal className="w-3 h-3 text-slate-500" />
                  <span>{agentName}</span>
                </div>
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping" style={{ animationDelay: `${idx * 300}ms` }}></span>
                  <span className="text-slate-400 font-semibold font-mono text-[9px] uppercase tracking-wider">Active</span>
                </div>
              </div>
            ))}
          </div>

          <div className="h-px bg-slate-800 my-1"></div>
          
          <div className="flex items-center justify-between text-[11px] font-mono">
            <span className="text-slate-500">Vector Search</span>
            <span className="text-blue-400 font-semibold">Qdrant Live</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
