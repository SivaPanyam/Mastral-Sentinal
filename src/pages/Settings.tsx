import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { Settings as SettingsIcon, Shield, Server, Cpu, Database, Eye, CheckCircle2 } from 'lucide-react';

export const Settings: React.FC = () => {
  const { addNotification } = useApp();
  const [geminiModel, setGeminiModel] = useState('gemini-2.5-flash');
  const [temperature, setTemperature] = useState(0.2);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  // Enkrypt AI Security middleware settings
  const [enableInjectionFilter, setEnableInjectionFilter] = useState(true);
  const [enableSecretFilter, setEnableSecretFilter] = useState(true);
  const [enablePIIFilter, setEnablePIIFilter] = useState(true);
  const [enableJailbreakBlock, setEnableJailbreakBlock] = useState(true);
  const [failureAction, setFailureAction] = useState<'BLOCK' | 'ANONYMIZE' | 'AUDIT_ONLY'>('BLOCK');

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveStatus('Saving changes to Sentinel configuration daemon...');
    
    setTimeout(() => {
      setSaveStatus('Settings updated successfully.');
      addNotification('Sentinel core preferences and model configurations re-initialised.', 'info');
      setTimeout(() => setSaveStatus(null), 3000);
    }, 1200);
  };

  return (
    <div className="space-y-6 pb-12 select-none animate-fadeIn">
      {/* Page Header */}
      <div>
        <h3 className="font-sans font-bold text-slate-100 text-lg leading-tight">Sentinel Preferences</h3>
        <p className="text-slate-400 text-xs font-sans mt-0.5">Configure autonomous SRE runtime parameters, LLM thresholds, and Enkrypt AI firewall rules.</p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Section A: Gemini Core Configuration */}
          <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
              <Cpu className="w-4 h-4 text-blue-400" />
              <h4 className="font-sans font-bold text-slate-200 text-xs uppercase tracking-wider">Mastra Agent Reasoning Engine</h4>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 font-sans">Primary Gemini LLM</label>
                <select
                  value={geminiModel}
                  onChange={(e) => setGeminiModel(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-2 text-xs text-slate-200 focus:outline-hidden focus:border-blue-500 font-mono"
                >
                  <option value="gemini-2.5-flash">gemini-2.5-flash (Fast & Cost-Efficient)</option>
                  <option value="gemini-2.5-pro">gemini-2.5-pro (High Analytical Capability)</option>
                  <option value="gemini-1.5-flash">gemini-1.5-flash (Legacy Sandbox)</option>
                </select>
                <span className="block text-[10px] text-slate-500 font-sans mt-1">Recommended for automated SRE summarizations and diagnostic matching.</span>
              </div>

              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-xs font-medium text-slate-400 font-sans">LLM Temperature</label>
                  <span className="font-mono text-xs font-bold text-blue-400">{temperature}</span>
                </div>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.05"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full h-1 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-blue-500"
                />
                <span className="block text-[10px] text-slate-500 font-sans mt-1">Lower temperatures yield deterministic, repeatable CLI mitigation inputs.</span>
              </div>
            </div>
          </div>

          {/* Section B: Qdrant Vector Storage Configuration */}
          <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
              <Database className="w-4 h-4 text-indigo-400" />
              <h4 className="font-sans font-bold text-slate-200 text-xs uppercase tracking-wider">Qdrant Context Retrieval parameters</h4>
            </div>

            <div className="space-y-3.5 text-xs font-mono">
              <div className="flex items-center justify-between p-2.5 bg-slate-950/40 border border-slate-800/60 rounded-lg">
                <span className="text-slate-400">Embedding Dimensions</span>
                <span className="text-slate-200 font-bold">1536 (Cosine Similarity)</span>
              </div>

              <div className="flex items-center justify-between p-2.5 bg-slate-950/40 border border-slate-800/60 rounded-lg">
                <span className="text-slate-400">Max Search Matches (K)</span>
                <span className="text-slate-200 font-bold">3 Playbook Records</span>
              </div>

              <div className="flex items-center justify-between p-2.5 bg-slate-950/40 border border-slate-800/60 rounded-lg">
                <span className="text-slate-400">RAG Relevance Threshold</span>
                <span className="text-slate-200 font-bold">0.78 confidence minimum</span>
              </div>
            </div>
          </div>

          {/* Section C: Enkrypt AI Security Architecture Firewall */}
          <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-4 lg:col-span-2">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-rose-400" />
                <h4 className="font-sans font-bold text-slate-200 text-xs uppercase tracking-wider">Enkrypt AI Security Middleware Filters</h4>
              </div>
              <span className="text-[9px] font-mono font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                INLINE REQUEST FIREWALL
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-slate-950/40 border border-slate-800/60 rounded-xl">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-slate-200 font-sans">Prompt Injection Filtering</span>
                    <p className="text-[10px] text-slate-500 font-sans">Blocks LLM hijack vectors and override prompts.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={enableInjectionFilter}
                    onChange={(e) => setEnableInjectionFilter(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded bg-slate-950 border-slate-800 focus:ring-blue-500 cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between p-3 bg-slate-950/40 border border-slate-800/60 rounded-xl">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-slate-200 font-sans">Secret Leak Protection</span>
                    <p className="text-[10px] text-slate-500 font-sans">Detects AWS, Stripe, and Postgres API keys.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={enableSecretFilter}
                    onChange={(e) => setEnableSecretFilter(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded bg-slate-950 border-slate-800 focus:ring-blue-500 cursor-pointer"
                  />
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-slate-950/40 border border-slate-800/60 rounded-xl">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-slate-200 font-sans">PII Scrubbing</span>
                    <p className="text-[10px] text-slate-500 font-sans">Anonymizes emails, IPs, and system credentials.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={enablePIIFilter}
                    onChange={(e) => setEnablePIIFilter(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded bg-slate-950 border-slate-800 focus:ring-blue-500 cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between p-3 bg-slate-950/40 border border-slate-800/60 rounded-xl">
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-slate-200 font-sans">Jailbreak Guard</span>
                    <p className="text-[10px] text-slate-500 font-sans">Blocks system exploitation and unauthorized scripts.</p>
                  </div>
                  <input
                    type="checkbox"
                    checked={enableJailbreakBlock}
                    onChange={(e) => setEnableJailbreakBlock(e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded bg-slate-950 border-slate-800 focus:ring-blue-500 cursor-pointer"
                  />
                </div>
              </div>
            </div>

            {/* Failure handling and risk score placements */}
            <div className="pt-3 border-t border-slate-800/80 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5 font-sans">Security Breach Action</label>
                <select
                  value={failureAction}
                  onChange={(e) => setFailureAction(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-2 text-xs text-slate-200 focus:outline-hidden focus:border-blue-500 font-mono"
                >
                  <option value="BLOCK">BLOCK (Hard Refusal & Log Audit)</option>
                  <option value="ANONYMIZE">ANONYMIZE (Scrub & Proceed)</option>
                  <option value="AUDIT_ONLY">AUDIT ONLY (Log warning events)</option>
                </select>
              </div>

              <div>
                <span className="block text-xs font-medium text-slate-400 mb-1.5 font-sans">Middleware Placement Lifecycle</span>
                <p className="text-[11.5px] text-slate-400 leading-relaxed font-sans bg-slate-950/30 p-2.5 border border-slate-800/60 rounded-lg">
                  Enkrypt AI executes interceptors directly at the <strong>Inbound Prompt Router</strong> and the <strong>Outbound Validation proxy</strong> to defend LLM boundary zones.
                </p>
              </div>
            </div>

          </div>

          {/* Section D: Audit Logs */}
          <div className="p-5 bg-slate-900 border border-slate-800 rounded-xl space-y-4 lg:col-span-2">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-emerald-400" />
                <h4 className="font-sans font-bold text-slate-200 text-xs uppercase tracking-wider">Security Audit Logs</h4>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left font-mono text-[10px] text-slate-400">
                <thead className="bg-slate-950/40 text-slate-500 uppercase">
                  <tr>
                    <th className="p-2 border-b border-slate-800">Timestamp</th>
                    <th className="p-2 border-b border-slate-800">User</th>
                    <th className="p-2 border-b border-slate-800">Action</th>
                    <th className="p-2 border-b border-slate-800">Details</th>
                  </tr>
                </thead>
                <tbody>
                  {useApp().auditLogs?.map(log => (
                    <tr key={log.id} className="border-b border-slate-800/50 hover:bg-slate-800/20">
                      <td className="p-2">{new Date(log.timestamp).toLocaleString()}</td>
                      <td className="p-2">{log.userName}</td>
                      <td className="p-2 font-bold text-blue-400">{log.action}</td>
                      <td className="p-2">{log.details}</td>
                    </tr>
                  ))}
                  {(!useApp().auditLogs || useApp().auditLogs.length === 0) && (
                    <tr>
                      <td colSpan={4} className="p-4 text-center text-slate-600 italic">No audit logs found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

        </div>

        {/* Submit Save Button */}
        <div className="flex items-center justify-end gap-4">
          {saveStatus && (
            <span className="text-xs font-mono font-semibold text-blue-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 animate-pulse" />
              {saveStatus}
            </span>
          )}

          <button
            type="submit"
            className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-5 py-2.5 rounded-lg border border-blue-500 shadow-md shadow-blue-500/10 transition-all cursor-pointer"
          >
            Save Configurations
          </button>
        </div>

      </form>
    </div>
  );
};
