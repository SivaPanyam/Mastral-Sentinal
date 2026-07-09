/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Sidebar } from './components/Sidebar';
import { TopNavbar } from './components/TopNavbar';

// Page Views
import { Dashboard } from './pages/Dashboard';
import { Incidents } from './pages/Incidents';
import { KnowledgeBase } from './pages/KnowledgeBase';
import { Reports } from './pages/Reports';
import { Analytics } from './pages/Analytics';
import { Settings } from './pages/Settings';
import { AICopilot } from './pages/AICopilot';

const AppContent: React.FC = () => {
  const { currentView } = useApp();

  const renderActiveView = () => {
    switch (currentView) {
      case 'dashboard':
        return <Dashboard />;
      case 'incidents':
        return <Incidents />;
      case 'knowledge':
        return <KnowledgeBase />;
      case 'reports':
        return <Reports />;
      case 'analytics':
        return <Analytics />;
      case 'settings':
        return <Settings />;
      case 'copilot':
        return <AICopilot />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div id="sentinel-app-root" className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans antialiased">
      {/* Persistent Left Sidebar: SRE Monitor and Core Navigation */}
      <Sidebar />

      {/* Main Panel */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Top Header Controls, Breadcrumbs, and Mock Telemetry Triggers */}
        <TopNavbar />

        {/* Scrollable Main Operations Deck */}
        <main className="flex-1 overflow-y-auto px-6 py-6 md:px-8 md:py-8 bg-slate-950/60 custom-scrollbar">
          <div className="max-w-7xl mx-auto w-full">
            {renderActiveView()}
          </div>
        </main>
      </div>
    </div>
  );
};

export default function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}
