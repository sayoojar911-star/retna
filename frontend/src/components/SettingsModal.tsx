import React from 'react';
import { X, Settings as SettingsIcon, CheckCircle2 } from 'lucide-react';
import { BackendModelStatus } from '../types';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  backendConnected: boolean;
  modelStatus: BackendModelStatus | null;
  onRefresh: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  backendConnected,
  modelStatus,
  onRefresh,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-lg overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
              <SettingsIcon className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Workstation Diagnostics</h3>
              <p className="text-xs text-slate-400">Infrastructure configuration &amp; verification</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 text-xs">
          <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 space-y-2">
            <div className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
              System Service Status
            </div>
            <div className="flex justify-between items-center text-slate-300">
              <span>Backend Connectivity:</span>
              <span className={`font-medium flex items-center ${backendConnected ? 'text-emerald-400' : 'text-rose-400'}`}>
                <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                {backendConnected ? 'Online (HTTP 200)' : 'Disconnected'}
              </span>
            </div>
            <div className="flex justify-between items-center text-slate-300">
              <span>Model Checkpoint Status:</span>
              <span className="font-mono text-emerald-400 font-medium">
                {modelStatus?.status === 'TRAINED' ? 'Harvard-GD ResNet-18 (Verified)' : 'Ready'}
              </span>
            </div>
          </div>

          <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 space-y-2">
            <div className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
              Clinical Safety Notice
            </div>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              GlaucoMap is a clinical decision-support and research prototype. Model outputs are mathematical
              estimates intended to assist qualified ophthalmologists and do not replace comprehensive clinical examinations.
            </p>
          </div>

          <div className="flex items-center justify-between pt-2 border-t border-slate-800">
            <button
              onClick={onRefresh}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition text-xs font-medium"
            >
              Verify Connections
            </button>
            <button
              onClick={onClose}
              className="px-4 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white transition text-xs font-medium"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
export default SettingsModal;
