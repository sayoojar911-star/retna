import React from 'react';
import {
  LayoutDashboard,
  Users,
  Eye,
  FileText,
  Activity,
  TrendingDown,
  BookOpen,
  Settings as SettingsIcon,
  Plus,
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onOpenSettings: () => void;
  onOpenRegisterModal: () => void;
  onOpenImportModal: () => void;
  patientsCount: number;
  scansCount: number;
  reportsCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  onOpenSettings,
  onOpenRegisterModal,
  onOpenImportModal,
  patientsCount,
  scansCount,
  reportsCount,
}) => {
  const mainNav = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'patients', label: 'Patients', icon: Users, badge: patientsCount },
    { id: 'scans', label: 'Scans', icon: Eye, badge: scansCount },
    { id: 'reports', label: 'Reports', icon: FileText, badge: reportsCount },
    { id: 'analysis', label: 'Analysis', icon: Activity },
    { id: 'progression', label: 'Progression', icon: TrendingDown },
    { id: 'demo-cases', label: 'Demo Cases', icon: BookOpen },
  ];

  return (
    <aside className="w-60 bg-navy-900 border-r border-navy-750 flex flex-col justify-between py-4 px-3 flex-shrink-0 select-none">
      <div className="space-y-6">
        {/* Quick Action Clinical Shortcuts */}
        <div className="px-1 space-y-2">
          <button
            onClick={onOpenRegisterModal}
            className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium text-xs shadow-md shadow-cyan-950/50 transition-all cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Patient</span>
          </button>
          <button
            onClick={onOpenImportModal}
            className="w-full flex items-center justify-center space-x-2 py-1.5 px-3 rounded-lg bg-navy-850 hover:bg-navy-800 border border-navy-700 text-slate-300 hover:text-white font-medium text-xs transition-all cursor-pointer"
          >
            <Eye className="w-3.5 h-3.5 text-cyan-400" />
            <span>Import OCT Study</span>
          </button>
        </div>

        {/* Primary Navigation Menu */}
        <div>
          <div className="px-3 pb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Clinical Navigation
          </div>
          <nav className="space-y-1">
            {mainNav.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-navy-800 text-cyan-300 border-l-4 border-l-cyan-400 border-r border-t border-b border-navy-700/80 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-navy-850/60'
                  }`}
                >
                  <div className="flex items-center space-x-2.5">
                    <Icon
                      className={`w-4 h-4 ${
                        isActive ? 'text-cyan-400' : 'text-slate-400'
                      }`}
                    />
                    <span>{item.label}</span>
                  </div>
                  {item.badge !== undefined && item.badge > 0 && (
                    <span
                      className={`px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                        isActive
                          ? 'bg-cyan-500/20 text-cyan-300'
                          : 'bg-navy-800 text-slate-400 border border-navy-750'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Bottom Workstation Status & Settings */}
      <div className="space-y-2 pt-4 border-t border-navy-750 px-1">
        <button
          onClick={onOpenSettings}
          className="w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-navy-850/60 transition"
        >
          <SettingsIcon className="w-4 h-4 text-slate-400" />
          <span>Workstation Settings</span>
        </button>

        <div className="p-2.5 rounded-lg bg-navy-850/80 border border-navy-750 text-[11px] text-slate-400 space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Mode</span>
            <span className="text-cyan-400 font-medium">Decision-Support</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-400">Model</span>
            <span className="text-slate-300 font-mono">Harvard-GD CNN</span>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
