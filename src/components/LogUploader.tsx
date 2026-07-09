import React, { useState, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, Terminal } from 'lucide-react';
import { incidentService } from '../services/incidentService';

interface LogUploaderProps {
  incidentId: string;
}

export const LogUploader: React.FC<LogUploaderProps> = ({ incidentId }) => {
  const { addIncidentLog } = useApp();
  const [dragActive, setDragActive] = useState(false);
  const [manualLog, setManualLog] = useState('');
  const [manualSource, setManualSource] = useState('Nginx-Router');
  const [manualLevel, setManualLevel] = useState<'INFO' | 'WARN' | 'ERROR' | 'FATAL'>('ERROR');
  const [uploadStatus, setUploadStatus] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const processLogFile = async (file: File) => {
    try {
      const res = await incidentService.uploadBulkLogs(incidentId, file);
      if (res && res.status === 'success') {
        setUploadStatus({
          type: 'success',
          text: `Successfully injected ${res.logs_inserted} lines of telemetry logs from ${file.name}.`
        });
      } else {
        throw new Error('Upload failed');
      }
      setTimeout(() => setUploadStatus(null), 4000);
    } catch (err) {
      setUploadStatus({
        type: 'error',
        text: 'Failed to read log file. Ensure it is a valid CSV, JSON, or TXT document.'
      });
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await processLogFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      await processLogFile(e.target.files[0]);
    }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualLog.trim()) return;
    
    await addIncidentLog(incidentId, manualLog.trim(), manualSource, manualLevel);
    setManualLog('');
    setUploadStatus({
      type: 'success',
      text: 'Telemetry diagnostic log injected successfully.'
    });
    setTimeout(() => setUploadStatus(null), 3000);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xs select-none">
      <div className="p-4 border-b border-slate-800 bg-slate-950/40 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <UploadCloud className="w-4 h-4 text-blue-400" />
          <h3 className="font-sans font-bold text-slate-200 text-sm">Upload Diagnostic Telemetry</h3>
        </div>
        <span className="font-mono text-[9px] text-slate-500 bg-slate-950 border border-slate-800/60 px-1.5 py-0.5 rounded uppercase font-semibold">
          Sink: {incidentId}
        </span>
      </div>

      <div className="p-5 space-y-5">
        {/* Drag and Drop Zone */}
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border border-dashed rounded-xl p-6 text-center cursor-pointer transition-all flex flex-col items-center justify-center gap-2.5 ${
            dragActive 
              ? 'border-blue-500 bg-blue-600/5' 
              : 'border-slate-800 hover:border-slate-700 hover:bg-slate-950/20'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".txt,.log,.json"
            onChange={handleFileChange}
          />
          <UploadCloud className={`w-7 h-7 ${dragActive ? 'text-blue-400 animate-bounce' : 'text-slate-500'}`} />
          <div className="space-y-0.5">
            <p className="text-xs font-semibold text-slate-300 font-sans">
              Drag telemetry or log file here, or <span className="text-blue-400 hover:underline">browse</span>
            </p>
            <p className="text-[10px] text-slate-500 font-mono">
              Supports .log, .txt, .json (max 5MB)
            </p>
          </div>
        </div>

        {/* Manual Log Injection Form */}
        <form onSubmit={handleManualSubmit} className="space-y-3 pt-1">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold text-slate-500 uppercase tracking-wider">
              Or manually inject log entry
            </span>
            <div className="flex items-center gap-2">
              <select
                value={manualSource}
                onChange={(e) => setManualSource(e.target.value)}
                className="bg-slate-950 border border-slate-800/80 rounded px-1.5 py-0.5 text-[10px] text-slate-400 font-mono focus:outline-hidden"
              >
                <option value="Nginx-Router">Nginx-Router</option>
                <option value="Kubelet">Kubelet</option>
                <option value="postgresql-primary">PostgreSQL</option>
                <option value="checkout-service">checkout-service</option>
              </select>
              <select
                value={manualLevel}
                onChange={(e) => setManualLevel(e.target.value as any)}
                className="bg-slate-950 border border-slate-800/80 rounded px-1.5 py-0.5 text-[10px] text-slate-400 font-mono focus:outline-hidden"
              >
                <option value="INFO">INFO</option>
                <option value="WARN">WARN</option>
                <option value="ERROR">ERROR</option>
                <option value="FATAL">FATAL</option>
              </select>
            </div>
          </div>

          <div className="relative">
            <input
              type="text"
              required
              placeholder="e.g. pg_stat_activity connection capacity breached limits at..."
              value={manualLog}
              onChange={(e) => setManualLog(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-3 pr-20 py-2 text-xs text-slate-300 focus:outline-hidden focus:border-blue-500 font-mono"
            />
            <button
              type="submit"
              className="absolute right-1.5 top-1.5 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-[10px] font-mono px-2.5 py-1 rounded border border-blue-500 transition-all cursor-pointer"
            >
              Inject
            </button>
          </div>
        </form>

        {/* Upload Status Banner */}
        {uploadStatus && (
          <div className={`p-3 rounded-lg border flex items-start gap-2.5 ${
            uploadStatus.type === 'success' 
              ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
              : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
          }`}>
            {uploadStatus.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            )}
            <p className="text-[11px] font-medium leading-relaxed font-sans">{uploadStatus.text}</p>
          </div>
        )}
      </div>
    </div>
  );
};
