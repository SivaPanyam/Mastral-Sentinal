import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { 
  Bell, 
  Search, 
  Plus, 
  CheckCircle, 
  AlertTriangle, 
  Server, 
  HelpCircle,
  X,
  Play
} from 'lucide-react';
import { IncidentSeverity, IncidentPriority } from '../types';

export const TopNavbar: React.FC = () => {
  const { 
    currentView, 
    selectedIncidentId, 
    setView,
    notifications, 
    createNewIncident, 
    serviceHealth 
  } = useApp();

  const [showNotifications, setShowNotifications] = useState(false);
  const [showNewIncidentModal, setShowNewIncidentModal] = useState(false);

  // Form states for custom incidents
  const [title, setTitle] = useState('');
  const [service, setService] = useState('checkout-service');
  const [severity, setSeverity] = useState(IncidentSeverity.SEV1);
  const [priority, setPriority] = useState(IncidentPriority.P1);
  const [description, setDescription] = useState('');

  const handleCreateIncident = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim()) return;
    const newInc = await createNewIncident(title, description, service, severity, priority);
    setShowNewIncidentModal(false);
    // Reset form
    setTitle('');
    setDescription('');
    setService('checkout-service');
    setSeverity(IncidentSeverity.SEV1);
    setPriority(IncidentPriority.P1);
    // Auto navigate to the incidents view for the newly created alert
    setView('incidents', newInc.id);
  };

  const handleQuickDemo = async () => {
    const demoInc = await createNewIncident(
      'Database Connection Pool Saturated - pg_stat_activity spiked',
      'The checkout-service postgres pool is reporting 98% saturation with lock contentions detected on checkout transaction lines.',
      'checkout-service',
      IncidentSeverity.SEV0,
      IncidentPriority.P0
    );
    setView('incidents', demoInc.id);
  };

  const getViewTitle = () => {
    switch (currentView) {
      case 'dashboard': return 'Incident Overview';
      case 'incidents': return selectedIncidentId ? `Incident Analysis / ${selectedIncidentId}` : 'Incident Queue';
      case 'knowledge': return 'Knowledge Base & Vector Index';
      case 'reports': return 'Incident Post-Mortems';
      case 'analytics': return 'SRE Health Analytics';
      case 'settings': return 'Sentinel Preferences';
      default: return 'MastSentinel';
    }
  };

  return (
    <>
      <header id="top-navbar" className="h-16 bg-slate-900 border-b border-slate-800 px-6 flex items-center justify-between relative z-40 select-none">
        
        {/* Title and breadcrumbs */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-500 uppercase tracking-wider">Root</span>
          <span className="text-slate-700">/</span>
          <h2 className="font-sans font-semibold text-slate-100 text-sm tracking-tight capitalize">
            {getViewTitle()}
          </h2>
        </div>

        {/* Action controls */}
        <div className="flex items-center gap-4">
          
          {/* Quick Demo Button */}
          <button
            onClick={handleQuickDemo}
            className="hidden md:flex items-center gap-1.5 px-3 py-1.5 bg-rose-600/10 hover:bg-rose-600/20 text-rose-400 border border-rose-500/30 text-xs font-semibold rounded-lg font-mono tracking-wide transition-colors cursor-pointer"
          >
            <Play className="w-3.5 h-3.5" />
            SIMULATE SEV0
          </button>

          {/* Create custom alert button */}
          <button
            onClick={() => setShowNewIncidentModal(true)}
            className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3.5 py-2 rounded-lg shadow-sm shadow-blue-500/10 hover:shadow-blue-500/20 border border-blue-500 transition-all cursor-pointer font-sans"
          >
            <Plus className="w-3.5 h-3.5" />
            Trigger Alert
          </button>

          <div className="h-4 w-px bg-slate-800"></div>

          {/* Notification dropdown trigger */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-all relative cursor-pointer"
            >
              <Bell className="w-4 h-4" />
              {notifications.some(n => n.type === 'warn' || n.type === 'error') && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full ring-2 ring-slate-900"></span>
              )}
            </button>

            {/* Notifications panel overlay */}
            {showNotifications && (
              <div className="absolute right-0 mt-2.5 w-80 bg-slate-900 border border-slate-800 rounded-xl shadow-xl shadow-slate-950/80 z-50 overflow-hidden">
                <div className="p-3 border-b border-slate-800 bg-slate-950/30 flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-300 font-sans">SRE System Alerts</span>
                  <span className="text-[10px] font-mono text-slate-500">{notifications.length} logged</span>
                </div>
                <div className="max-h-64 overflow-y-auto divide-y divide-slate-800/60">
                  {notifications.map((not) => (
                    <div key={not.id} className="p-3 hover:bg-slate-800/40 transition-colors flex gap-2.5">
                      <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${
                        not.type === 'error' ? 'bg-rose-500' : not.type === 'warn' ? 'bg-amber-500' : 'bg-blue-500'
                      }`} />
                      <div>
                        <p className="text-xs text-slate-300 leading-relaxed font-sans">{not.text}</p>
                        <span className="text-[9px] text-slate-500 font-mono mt-0.5 block">
                          {new Date(not.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="h-4 w-px bg-slate-800"></div>

          {/* On-call SRE Profile Card */}
          <div className="flex items-center gap-3">
            <div className="hidden lg:flex flex-col text-right">
              <span className="text-xs font-bold text-slate-200">Elena Rostova</span>
              <span className="text-[9.5px] font-mono font-bold text-emerald-400 uppercase tracking-wider">Primary On-Call</span>
            </div>
            <img 
              src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=150&q=80" 
              alt="Avatar" 
              referrerPolicy="no-referrer"
              className="w-8 h-8 rounded-lg border border-slate-700 object-cover"
            />
          </div>

        </div>
      </header>

      {/* Trigger Incident Dialog Modal */}
      {showNewIncidentModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-xs flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-slate-800 w-full max-w-lg rounded-xl overflow-hidden shadow-2xl">
            <div className="p-4 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between">
              <h3 className="font-sans font-bold text-slate-200 text-sm">Simulate New Live Incident</h3>
              <button 
                onClick={() => setShowNewIncidentModal(false)}
                className="p-1 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-lg cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateIncident} className="p-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 font-sans">Alert Title</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Memory leak on auth-gateway service"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-hidden focus:border-blue-500 font-sans"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5 font-sans">Target Service / Resource</label>
                  <select
                    value={service}
                    onChange={(e) => setService(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-2 text-xs text-slate-200 focus:outline-hidden focus:border-blue-500 font-mono"
                  >
                    {serviceHealth.map(sh => (
                      <option key={sh.name} value={sh.name}>{sh.name}</option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1.5 font-sans">Severity</label>
                    <select
                      value={severity}
                      onChange={(e) => setSeverity(e.target.value as any)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-2 text-xs text-slate-200 focus:outline-hidden focus:border-blue-500 font-mono"
                    >
                      <option value={IncidentSeverity.SEV0}>SEV0 (Critical)</option>
                      <option value={IncidentSeverity.SEV1}>SEV1 (Major)</option>
                      <option value={IncidentSeverity.SEV2}>SEV2 (Minor)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1.5 font-sans">Priority</label>
                    <select
                      value={priority}
                      onChange={(e) => setPriority(e.target.value as any)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-2 text-xs text-slate-200 focus:outline-hidden focus:border-blue-500 font-mono"
                    >
                      <option value={IncidentPriority.P0}>P0</option>
                      <option value={IncidentPriority.P1}>P1</option>
                      <option value={IncidentPriority.P2}>P2</option>
                      <option value={IncidentPriority.P3}>P3</option>
                    </select>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 font-sans">Telemetry/Logs Summary Context</label>
                <textarea
                  required
                  rows={3}
                  placeholder="Paste alert payload or describe symptoms..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-hidden focus:border-blue-500 font-sans leading-relaxed"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowNewIncidentModal(false)}
                  className="px-4 py-2 text-xs text-slate-400 hover:text-slate-200 font-semibold hover:bg-slate-800 rounded-lg cursor-pointer transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-lg border border-blue-500 shadow-md shadow-blue-500/10 transition-all cursor-pointer"
                >
                  Trigger Incident
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
