import React from 'react';
import { Cpu, ArrowRight, Clock, AlertCircle, HardDrive, CheckCircle2 } from 'lucide-react';
import { BackendModelStatus } from '../types';

interface ModelStatusSectionProps {
  modelStatus?: BackendModelStatus | null;
}

export const ModelStatusSection: React.FC<ModelStatusSectionProps> = ({ modelStatus }) => {
  const pipelineSteps = [
    { name: 'Input RNFLT', desc: 'Raw 225x225 OCT thickness matrix', active: true },
    { name: 'Technical QA', desc: 'Dimensional & non-empty check', active: true },
    { name: 'Preprocessing', desc: 'Clamping & tensor normalization', active: true },
    { name: 'CNN Backbone', desc: 'Adapted ResNet18 / CompactRNFLT', pending: true },
    { name: 'Glaucoma Risk', desc: 'Calibrated binary estimate', pending: true },
    { name: 'Explainability', desc: 'Spatial Grad-CAM saliency', pending: true },
  ];

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 mb-6 gap-3">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">
              AI Model &amp; Training Infrastructure Status
            </h3>
            <p className="text-xs text-slate-400">
              Convolutional neural network lifecycle &amp; deployment tracking
            </p>
          </div>
        </div>

        {/* Status Pill */}
        <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 w-fit">
          <Clock className="w-3.5 h-3.5 animate-pulse" />
          <span>MODEL STATUS: Development / Training Pending</span>
        </div>
      </div>

      {/* System Infrastructure Pillars */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3.5 flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 flex-shrink-0">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-white">Training Infrastructure</div>
            <div className="text-[11px] text-emerald-400 font-mono mt-0.5">Ready &bull; Verified</div>
          </div>
        </div>

        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3.5 flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400 flex-shrink-0">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-white">Hardware Accelerator</div>
            <div className="text-[11px] text-indigo-300 font-mono mt-0.5 truncate">
              {modelStatus?.hardware.gpu_name || 'NVIDIA RTX 4050 (6GB)'}
            </div>
          </div>
        </div>

        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3.5 flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 flex-shrink-0">
            <HardDrive className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-white">Model Checkpoint</div>
            <div className="text-[11px] text-amber-300 font-mono mt-0.5">Pending Training</div>
          </div>
        </div>
      </div>

      {/* Model Pipeline Flowchart */}
      <div className="border border-slate-800/90 rounded-xl p-4 bg-slate-950/60 mb-5">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-3">
          End-to-End Processing &amp; Inference Pipeline
        </div>
        <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
          {pipelineSteps.map((step, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-lg border text-center flex flex-col justify-between ${
                step.active
                  ? 'bg-slate-900 border-teal-500/30'
                  : 'bg-slate-900/50 border-slate-800/80 opacity-75'
              }`}
            >
              <div>
                <div
                  className={`text-xs font-semibold ${
                    step.active ? 'text-teal-300' : 'text-slate-300'
                  }`}
                >
                  {step.name}
                </div>
                <div className="text-[10px] text-slate-500 mt-1 leading-tight">
                  {step.desc}
                </div>
              </div>
              <div className="mt-2.5">
                <span
                  className={`text-[9px] font-semibold uppercase px-1.5 py-0.5 rounded border ${
                    step.active
                      ? 'bg-teal-500/10 text-teal-400 border-teal-500/30'
                      : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  }`}
                >
                  {step.active ? 'Active' : 'Pending'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Truth in AI Notice */}
      <div className="p-3 bg-amber-950/20 border border-amber-900/40 rounded-lg flex items-start space-x-2.5 text-xs text-amber-300/90">
        <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-amber-200">Strict Scientific Integrity Policy: </span>
          GlaucoMap does NOT display simulated predictions, fabricated confidence intervals, or pseudo-Grad-CAM heatmaps. Model predictions will only become active once a genuine model training cycle has completed and a validated checkpoint file exists.
        </div>
      </div>
    </div>
  );
};
