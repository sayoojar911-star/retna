import React from 'react';
import {
  Eye,
  Search,
  Bell,
  Settings as SettingsIcon,
  ShieldCheck,
  Users,
  FileText,
  Activity,
  TrendingDown,
  BookOpen,
} from 'lucide-react';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onOpenSettings: () => void;
  selectedPatientName?: string | null;
  onQuickAction?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  searchQuery,
  onSearchChange,
  onOpenSettings,
}) => {
  const navItems = [
    { id: 'patients', label: 'Patients', icon: Users },
    { id: 'scans', label: 'Scans', icon: Eye },
    { id: 'reports', label: 'Reports', icon: FileText },
    { id: 'analysis', label: 'Analysis', icon: Activity },
    { id: 'progression', label: 'Progression', icon: TrendingDown },
    { id: 'demo-cases', label: 'Demo Cases', icon: BookOpen },
  ];

  return (
    <header className="border-b border-slate-200 bg-white/95 backdrop-blur-md sticky top-0 z-50 px-6 py-2.5 shadow-sm">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        {/* Brand & Subtitle */}
        <div
          className="flex items-center space-x-3 cursor-pointer select-none"
          onClick={() => setActiveTab('patients')}
        >
          <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700 shadow-sm">
            <Eye className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-base tracking-tight text-slate-900 font-mono">
                GLAUCOMAP
              </span>
              <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200 font-semibold flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" />
                Clinical Decision Support
              </span>
            </div>
            <div className="text-xs text-slate-500 font-normal leading-tight hidden sm:block">
              Ophthalmic Structural Analysis &amp; Longitudinal Monitoring
            </div>
          </div>
        </div>

        {/* Center / Top Navigation Pills */}
        <nav className="flex items-center space-x-1 bg-slate-100/80 p-1 rounded-xl border border-slate-200">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-white text-teal-700 shadow-sm border border-slate-200 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-white/60'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-teal-600' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Right Search, Notifications & Doctor Profile */}
        <div className="flex items-center space-x-3">
          {/* Quick Search */}
          <div className="relative hidden xl:block w-48">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search patient..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-3 py-1 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-teal-500 focus:bg-white transition"
            />
          </div>

          {/* Notifications */}
          <button
            className="relative p-2 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-500 hover:text-slate-700 transition"
            title="Clinical Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-teal-500 ring-2 ring-white"></span>
          </button>

          {/* Settings Modal Trigger */}
          <button
            onClick={onOpenSettings}
            className="p-2 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-500 hover:text-slate-700 transition"
            title="Workstation Diagnostics"
          >
            <SettingsIcon className="w-4 h-4" />
          </button>

          {/* Clinician Profile */}
          <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-teal-600 to-blue-600 flex items-center justify-center text-white text-xs font-semibold shadow-sm">
              DR
            </div>
            <div className="hidden lg:block text-left">
              <div className="text-xs font-semibold text-slate-900 leading-tight">
                Dr. Clinical Specialist
              </div>
              <div className="text-[10px] text-slate-500 leading-tight">Glaucoma Service</div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
