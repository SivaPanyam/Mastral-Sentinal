import React from 'react';
import { useApp } from '../context/AppContext';
import { BarChart3, TrendingDown, Clock, ShieldAlert, CheckCircle2 } from 'lucide-react';

export const Analytics: React.FC = () => {
  const { metricHistory, serviceHealth, systemOverview } = useApp();

  // Coordinates calculation for SVG Chart
  // We have 7 days. Chart width = 600, height = 200.
  const chartWidth = 600;
  const chartHeight = 200;
  const padding = 40;

  // Find max values for scaling
  const maxIncidents = Math.max(...metricHistory.map(m => m.incidents), 1);
  const maxMttr = Math.max(...metricHistory.map(m => m.mttrMinutes), 1);

  // Map metricHistory data points to X, Y coordinates
  const pointsIncidents = metricHistory.map((pt, idx) => {
    const x = padding + (idx * (chartWidth - padding * 2)) / (metricHistory.length - 1);
    const y = chartHeight - padding - (pt.incidents * (chartHeight - padding * 2)) / maxIncidents;
    return { x, y, ...pt };
  });

  const pointsMttr = metricHistory.map((pt, idx) => {
    const x = padding + (idx * (chartWidth - padding * 2)) / (metricHistory.length - 1);
    const y = chartHeight - padding - (pt.mttrMinutes * (chartHeight - padding * 2)) / maxMttr;
    return { x, y, ...pt };
  });

  // Create SVG path strings
  const incidentsLinePath = pointsIncidents.reduce((acc, pt, idx) => {
    return idx === 0 ? `M ${pt.x} ${pt.y}` : `${acc} L ${pt.x} ${pt.y}`;
  }, '');

  const mttrLinePath = pointsMttr.reduce((acc, pt, idx) => {
    return idx === 0 ? `M ${pt.x} ${pt.y}` : `${acc} L ${pt.x} ${pt.y}`;
  }, '');

  // Area paths (closing with the bottom axis)
  const incidentsAreaPath = incidentsLinePath 
    ? `${incidentsLinePath} L ${pointsIncidents[pointsIncidents.length - 1].x} ${chartHeight - padding} L ${pointsIncidents[0].x} ${chartHeight - padding} Z`
    : '';

  const mttrAreaPath = mttrLinePath
    ? `${mttrLinePath} L ${pointsMttr[pointsMttr.length - 1].x} ${chartHeight - padding} L ${pointsMttr[0].x} ${chartHeight - padding} Z`
    : '';

  return (
    <div className="space-y-6 pb-12 select-none animate-fadeIn">
      {/* Page Header */}
      <div>
        <h3 className="font-sans font-bold text-slate-100 text-lg leading-tight">SRE Performance Analytics</h3>
        <p className="text-slate-400 text-xs font-sans mt-0.5">Track mean-time parameters, incident densities, and recovery trend rates.</p>
      </div>

      {/* Analytics Bento Grid summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">7-Day Incident Load</span>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-100 font-sans">17 Triggered</span>
          </div>
          <p className="text-[10px] text-rose-400 font-mono flex items-center gap-1">
            <ShieldAlert className="w-3.5 h-3.5" />
            Avg 2.4 daily triggers
          </p>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">Mean Response Speed (MTTA)</span>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-100 font-sans">7.2 minutes</span>
          </div>
          <p className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
            <TrendingDown className="w-3.5 h-3.5" />
            -18.4% faster than last week
          </p>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">Mean Recovery Duration (MTTR)</span>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-100 font-sans">31.5 minutes</span>
          </div>
          <p className="text-[10px] text-emerald-400 font-mono flex items-center gap-1">
            <TrendingDown className="w-3.5 h-3.5" />
            -34.1% reduction via Mastra agents
          </p>
        </div>

        <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl space-y-1">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">Preventative Action Completion</span>
          <div className="flex items-baseline gap-2">
            <span className="text-xl font-bold text-slate-100 font-sans">82.5%</span>
          </div>
          <p className="text-[10px] text-blue-400 font-mono flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            33/40 post-mortem items closed
          </p>
        </div>

      </div>

      {/* Interactive SRE Historical Charts Panel */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            <h4 className="font-sans font-bold text-slate-200 text-xs uppercase tracking-wider">Historical Performance Trends (7-Day Cycle)</h4>
          </div>

          <div className="flex gap-4 text-xs font-mono">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 bg-rose-500/20 border border-rose-500/80 rounded"></span>
              <span className="text-slate-400">Incident Count</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 bg-blue-500/20 border border-blue-500/80 rounded"></span>
              <span className="text-slate-400">MTTR Minutes</span>
            </div>
          </div>
        </div>

        {/* Lightweight SVG Render Engine */}
        <div className="overflow-x-auto">
          <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full max-w-3xl mx-auto h-auto text-slate-700">
            {/* Gradients */}
            <defs>
              <linearGradient id="incidentsGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#ef4444" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
              </linearGradient>
              <linearGradient id="mttrGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
              </linearGradient>
            </defs>

            {/* Grid lines */}
            <line x1={padding} y1={padding} x2={chartWidth - padding} y2={padding} stroke="#1e293b" strokeDasharray="4 4" />
            <line x1={padding} y1={chartHeight / 2} x2={chartWidth - padding} y2={chartHeight / 2} stroke="#1e293b" strokeDasharray="4 4" />
            <line x1={padding} y1={chartHeight - padding} x2={chartWidth - padding} y2={chartHeight - padding} stroke="#334155" />

            {/* Areas */}
            {incidentsAreaPath && <path d={incidentsAreaPath} fill="url(#incidentsGrad)" />}
            {mttrAreaPath && <path d={mttrAreaPath} fill="url(#mttrGrad)" />}

            {/* Lines */}
            {incidentsLinePath && <path d={incidentsLinePath} fill="none" stroke="#f43f5e" strokeWidth="2.5" strokeLinecap="round" />}
            {mttrLinePath && <path d={mttrLinePath} fill="none" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" />}

            {/* Grid Dots & Tooltips */}
            {pointsIncidents.map((pt, idx) => (
              <g key={`inc-${idx}`} className="cursor-pointer group">
                <circle cx={pt.x} cy={pt.y} r="4" className="fill-rose-500 stroke-slate-900 stroke-2 hover:r-6 transition-all" />
                <text x={pt.x} y={pt.y - 10} className="font-mono text-[9px] font-bold fill-rose-400 text-center opacity-0 group-hover:opacity-100 transition-opacity" textAnchor="middle">
                  {pt.incidents} incs
                </text>
              </g>
            ))}

            {pointsMttr.map((pt, idx) => (
              <g key={`mttr-${idx}`} className="cursor-pointer group">
                <circle cx={pt.x} cy={pt.y} r="4" className="fill-blue-500 stroke-slate-900 stroke-2 hover:r-6 transition-all" />
                <text x={pt.x} y={pt.y - 10} className="font-mono text-[9px] font-bold fill-blue-400 text-center opacity-0 group-hover:opacity-100 transition-opacity" textAnchor="middle">
                  {pt.mttrMinutes}m mttr
                </text>
              </g>
            ))}

            {/* X-Axis Dates */}
            {pointsIncidents.map((pt, idx) => (
              <text key={`date-${idx}`} x={pt.x} y={chartHeight - 14} className="font-mono text-[9px] fill-slate-500" textAnchor="middle">
                {pt.date}
              </text>
            ))}

            {/* Y-Axis scale guides */}
            <text x={padding - 8} y={padding + 4} className="font-mono text-[9px] fill-slate-600" textAnchor="end">MAX</text>
            <text x={padding - 8} y={chartHeight - padding + 4} className="font-mono text-[9px] fill-slate-600" textAnchor="end">0</text>
          </svg>
        </div>

        {/* Dashboard metadata footer */}
        <p className="text-[11px] text-slate-500 font-sans leading-relaxed border-t border-slate-800/80 pt-3.5 text-center">
          Mean recovery speed correlates with autonomous <strong>Qdrant SOP extraction</strong> which bypassed manual triage steps.
        </p>

      </div>
    </div>
  );
};
