import React from 'react';
import { Activity, Server, Cpu, CheckCircle2, XCircle, RefreshCw } from 'lucide-react';

interface HeaderProps {
  backendConnected: boolean;
  backendChecking: boolean;
  gpuName: string;
  onRefresh: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  backendConnected,
  backendChecking,
  gpuName,
  onRefresh,
  activeTab,
  setActiveTab,
}) => {
  const tabs = [
    { id: 'dashboard', label: 'Analysis Dashboard' },
    { id: 'import', label: 'Import OCT Study' },
    { id: 'model', label: 'Model Status' },
    { id: 'safety', label: 'Safety & Validation' },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-50 px-6 py-3.5">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        {/* Brand and Project Badge */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400 shadow-sm shadow-teal-500/10">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight text-white">GlaucoMap</span>
              <span className="text-[11px] font-semibold uppercase px-2 py-0.5 rounded-full bg-teal-500/10 text-teal-400 border border-teal-500/30">
                10 PM Checkpoint
              </span>
            </div>
            <div className="text-xs text-slate-400">
              Clinical Decision-Support &amp; Structural Progression Prototype
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-1 bg-slate-900/80 border border-slate-800 rounded-lg p-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Hardware & Live Backend Status Indicators */}
        <div className="flex items-center space-x-2.5 text-xs">
          {/* Hardware Badge */}
          <div
            className="hidden lg:flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-300"
            title={gpuName}
          >
            <Cpu className="w-3.5 h-3.5 text-indigo-400" />
            <span className="truncate max-w-[170px] text-[11px]">RTX 4050 (6GB)</span>
          </div>

          {/* Backend Status Pill */}
          <div
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md border text-[11px] font-medium ${
              backendConnected
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                : 'bg-rose-500/10 border-rose-500/30 text-rose-400'
            }`}
          >
            <Server className="w-3.5 h-3.5" />
            <span>{backendConnected ? 'Backend Live' : 'Offline'}</span>
            {backendConnected ? (
              <CheckCircle2 className="w-3 h-3 text-emerald-400 ml-0.5" />
            ) : (
              <XCircle className="w-3 h-3 text-rose-400 ml-0.5" />
            )}
          </div>

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={backendChecking}
            className="p-1.5 rounded-md bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white transition disabled:opacity-50"
            title="Refresh System Status"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${backendChecking ? 'animate-spin text-teal-400' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};
