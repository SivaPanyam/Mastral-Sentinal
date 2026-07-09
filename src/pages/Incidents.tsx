import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { IncidentCard } from '../components/IncidentCard';
import { SearchBar } from '../components/SearchBar';
import { IncidentDetails } from './IncidentDetails';
import { IncidentStatus, IncidentSeverity } from '../types';
import { ShieldAlert, Inbox, CheckCircle2, AlertOctagon } from 'lucide-react';

export const Incidents: React.FC = () => {
  const { incidents, selectedIncidentId, setView } = useApp();
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'active' | 'resolved'>('all');
  const [severityFilter, setSeverityFilter] = useState<'ALL' | IncidentSeverity.SEV0 | IncidentSeverity.SEV1 | IncidentSeverity.SEV2>('ALL');

  // If we have a selected incident, render the details subview directly!
  if (selectedIncidentId) {
    return <IncidentDetails id={selectedIncidentId} />;
  }

  // Filter logic
  const filteredIncidents = incidents.filter(inc => {
    // 1. Text Search
    const matchesSearch = 
      inc.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.service.toLowerCase().includes(searchQuery.toLowerCase());

    // 2. Tab filtering
    let matchesTab = true;
    if (activeTab === 'active') {
      matchesTab = inc.status !== IncidentStatus.RESOLVED;
    } else if (activeTab === 'resolved') {
      matchesTab = inc.status === IncidentStatus.RESOLVED;
    }

    // 3. Severity filtering
    let matchesSeverity = true;
    if (severityFilter !== 'ALL') {
      matchesSeverity = inc.severity === severityFilter;
    }

    return matchesSearch && matchesTab && matchesSeverity;
  });

  return (
    <div className="space-y-6 select-none animate-fadeIn">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h3 className="font-sans font-bold text-slate-100 text-lg leading-tight">SRE Incident Queue</h3>
          <p className="text-slate-400 text-xs font-sans mt-0.5">Track system-level failures, diagnostic metrics, and automated agent resolutions.</p>
        </div>

        {/* Filter controls */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Severity Select */}
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5">
            <span>Severity:</span>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value as any)}
              className="bg-transparent border-none focus:outline-hidden font-bold text-slate-200 cursor-pointer"
            >
              <option value="ALL">ALL</option>
              <option value={IncidentSeverity.SEV0}>SEV0</option>
              <option value={IncidentSeverity.SEV1}>SEV1</option>
              <option value={IncidentSeverity.SEV2}>SEV2</option>
            </select>
          </div>
        </div>
      </div>

      {/* Search and Tabs Row */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
        {/* State Tabs */}
        <div className="bg-slate-900 border border-slate-800/80 rounded-xl p-1 flex gap-1 shrink-0">
          {(['all', 'active', 'resolved'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all cursor-pointer ${
                activeTab === tab
                  ? 'bg-slate-800 text-white'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Reusable search bar */}
        <SearchBar
          query={searchQuery}
          onChange={setSearchQuery}
          placeholder="Search incident codes, service logs, alerts..."
        />
      </div>

      {/* Grid List */}
      {filteredIncidents.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 border border-dashed border-slate-800 rounded-xl bg-slate-950/20 text-center">
          <Inbox className="w-9 h-9 text-slate-600 mb-3" />
          <h4 className="font-sans font-bold text-slate-400 text-sm">No Incidents Found</h4>
          <p className="text-[11px] text-slate-500 font-sans max-w-xs mt-1">
            Try adjusting your search criteria or trigger a mock incident alert from the top header panel.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredIncidents.map((inc) => (
            <IncidentCard
              key={inc.id}
              incident={inc}
              onClick={() => setView('incidents', inc.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
};
