import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { StatCard } from '../components/StatCard';
import { IncidentCard } from '../components/IncidentCard';
import { ActivityFeed } from '../components/ActivityFeed';
import { NotificationPanel } from '../components/NotificationPanel';
import { 
  ShieldAlert, 
  Activity, 
  Clock, 
  Cpu, 
  Heart, 
  Server, 
  AlertOctagon,
  ArrowRight
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const { 
    incidents, 
    serviceHealth, 
    systemOverview, 
    setView,
    isLoading 
  } = useApp();

  const unresolvedIncidents = incidents.filter(inc => inc.status !== 'RESOLVED');
  
  // Calculate health averages
  const overallUptime = (serviceHealth.reduce((acc, sh) => acc + sh.uptime24h, 0) / serviceHealth.length).toFixed(2);
  const avgLatency = Math.round(serviceHealth.reduce((acc, sh) => acc + sh.latencyMs, 0) / serviceHealth.length);

  return (
    <div className="space-y-6 pb-12 select-none animate-fadeIn">
      
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="font-sans font-bold text-slate-100 text-lg leading-tight">MastSentinel Operations Center</h3>
          <p className="text-slate-400 text-xs font-sans mt-0.5">Automated AI SRE agent pool and proactive incident mitigation sandbox.</p>
        </div>
        <div className="flex items-center gap-2 font-mono text-[11px] text-slate-500 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
          <span>Active Host:</span>
          <span className="text-emerald-400 font-bold animate-pulse">0.0.0.0:3000</span>
        </div>
      </div>

      {/* Stats Cards Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Alert Queue"
          value={unresolvedIncidents.length}
          subtext="Unresolved alerts awaiting resolution"
          icon={ShieldAlert}
          variant={unresolvedIncidents.length > 0 ? 'rose' : 'blue'}
          trend={unresolvedIncidents.length > 0 ? { value: `${unresolvedIncidents.length} trigger`, isPositive: false } : undefined}
        />

        <StatCard
          title="Mean Time To Acknowledge (MTTA)"
          value={`${systemOverview.mttaAvg24h} min`}
          subtext="Average SRE pipeline triage lag"
          icon={Clock}
          variant="amber"
          trend={{ value: '-2.4m', isPositive: true }}
        />

        <StatCard
          title="Mean Time To Resolve (MTTR)"
          value={`${systemOverview.mttrAvg24h} min`}
          subtext="Mean automated agent resolution"
          icon={Activity}
          variant="blue"
          trend={{ value: '-8.1m', isPositive: true }}
        />

        <StatCard
          title="MastPool Engine Status"
          value={`${systemOverview.agentsOnlineCount}/5 Active`}
          subtext="Autonomous diagnostic daemons"
          icon={Cpu}
          variant="emerald"
        />
      </div>

      {/* Main Grid: Services, Alert queue, SRE activity logs */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        
        {/* Column 1 & 2: Alerts queue and Services Health */}
        <div className="xl:col-span-2 space-y-6">
          
          {/* Services Health Status Card Grid */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div className="flex items-center gap-2">
                <Heart className="w-4 h-4 text-emerald-400 animate-pulse" />
                <h4 className="font-sans font-bold text-slate-200 text-xs uppercase tracking-wider">Service Cluster Topology</h4>
              </div>
              <div className="flex gap-4 font-mono text-[10.5px]">
                <span className="text-slate-500">Avg Uptime: <strong className="text-emerald-400">{overallUptime}%</strong></span>
                <span className="text-slate-500">Latency: <strong className="text-blue-400">{avgLatency}ms</strong></span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {serviceHealth.map((sh) => (
                <div 
                  key={sh.name}
                  className="p-3.5 bg-slate-950/40 border border-slate-800/60 rounded-xl space-y-2 hover:border-slate-800 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[11px] font-bold text-slate-300 truncate max-w-[120px]" title={sh.name}>
                      {sh.name}
                    </span>
                    <span className={`w-2 h-2 rounded-full ${
                      sh.status === 'HEALTHY' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
                    }`} />
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[10px] font-mono border-t border-slate-900 pt-2 text-slate-500">
                    <div>
                      <span>Latency</span>
                      <p className="font-bold text-slate-300 mt-0.5">{sh.latencyMs}ms</p>
                    </div>
                    <div>
                      <span>Uptime 24h</span>
                      <p className="font-bold text-slate-300 mt-0.5">{sh.uptime24h}%</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Active Incidents Queue */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                <h4 className="font-sans font-bold text-slate-200 text-xs uppercase tracking-wider">Active SRE Alert Queue</h4>
              </div>
              
              <button 
                onClick={() => setView('incidents')}
                className="flex items-center gap-1 text-xs font-mono text-slate-500 hover:text-slate-300 transition-colors cursor-pointer"
              >
                <span>View Full Queue ({incidents.length})</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {unresolvedIncidents.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-10 border border-dashed border-slate-800 rounded-xl bg-slate-950/20 text-center">
                <Heart className="w-8 h-8 text-emerald-400 mb-2.5 animate-bounce" />
                <h4 className="font-sans font-bold text-slate-400 text-xs">All Systems Secure</h4>
                <p className="text-[11px] text-slate-500 font-sans max-w-xs mt-1">
                  No active incidents detected. Use <strong>Trigger Alert</strong> above to simulate a system failure.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {unresolvedIncidents.map((inc) => (
                  <IncidentCard
                    key={inc.id}
                    incident={inc}
                    onClick={() => setView('incidents', inc.id)}
                  />
                ))}
              </div>
            )}
          </div>

        </div>

        {/* Column 3: SRE Audit logs terminal and Indicator Panel */}
        <div className="space-y-6">
          <NotificationPanel />
          <ActivityFeed />
        </div>

      </div>

    </div>
  );
};
