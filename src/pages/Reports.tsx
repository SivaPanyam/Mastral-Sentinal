import React from 'react';
import { useApp } from '../context/AppContext';
import { ReportCard } from '../components/ReportCard';
import { FileText } from 'lucide-react';

export const Reports: React.FC = () => {
  const { reports } = useApp();

  return (
    <div className="space-y-6 pb-12 select-none animate-fadeIn">
      {/* Page Header */}
      <div>
        <h3 className="font-sans font-bold text-slate-100 text-lg leading-tight">Incident Post-Mortems</h3>
        <p className="text-slate-400 text-xs font-sans mt-0.5">Comprehensive root-cause investigations, timelines, and remediation deliverables.</p>
      </div>

      {/* Reports collection */}
      <div className="space-y-4">
        {reports.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-slate-800 rounded-xl bg-slate-950/20">
            <FileText className="w-8 h-8 text-slate-600 mb-2.5" />
            <h4 className="font-sans font-bold text-slate-400 text-xs uppercase tracking-wider">No RCA Reports Filed</h4>
            <p className="text-[11px] text-slate-500 font-sans mt-0.5 max-w-xs mx-auto">
              Reports are auto-generated when you complete the <strong>RCA Report Agent</strong> step inside an active incident detail page.
            </p>
          </div>
        ) : (
          reports.map((rep) => (
            <ReportCard key={rep.id} report={rep} />
          ))
        )}
      </div>
    </div>
  );
};
