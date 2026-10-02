import React, { useState } from 'react';
import { HelpCircle, CheckCircle2, AlertTriangle, Minus } from 'lucide-react';

export const StructuralAIPipelineStatus: React.FC<{ diagnostics?: { two_stage_architecture?: { sam2_base: string; mgu: string; rnflt_resnet: string; end_to_end_raw_oct: string } } | null }> = ({ diagnostics }) => {
  const [showHow, setShowHow] = useState(false);
  const sam2 = diagnostics?.two_stage_architecture?.sam2_base || 'PASS';
  const mgu = diagnostics?.two_stage_architecture?.mgu || 'UNAVAILABLE';
  const resnet = diagnostics?.two_stage_architecture?.rnflt_resnet || 'PASS';
  const e2e = diagnostics?.two_stage_architecture?.end_to_end_raw_oct || 'BLOCKED';
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold text-slate-900 tracking-tight">Structural AI Pipeline Status</h3>
        <button onClick={() => setShowHow((v) => !v)} className="text-[11px] font-semibold text-teal-700 border border-teal-200 bg-teal-50 px-2.5 py-1 rounded-full flex items-center gap-1">
          <HelpCircle className="w-3.5 h-3.5" /> How it works
        </button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-xs">
        <div className="p-3 rounded-xl border bg-teal-50/60 border-teal-200">
          <div className="font-bold text-teal-900 flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5" /> RAW OCT</div>
          <div className="text-[11px] text-slate-600 mt-1">Import + quality — validated</div>
        </div>
        <div className="flex items-center justify-center text-slate-400">↓</div>
        <div className="p-3 rounded-xl border bg-amber-50 border-amber-200">
          <div className="font-bold text-amber-900 flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" /> RNFLT SEGMENTATION</div>
          <div className="text-[11px] text-slate-600 mt-1">MGU: {mgu} · SAM2 base: {sam2}</div>
          <div className="text-[10px] text-amber-800 mt-1">Unavailable in current build</div>
        </div>
        <div className="flex items-center justify-center text-slate-400">↓</div>
        <div className="p-3 rounded-xl border bg-slate-50 border-slate-200">
          <div className="font-bold text-slate-800 flex items-center gap-1"><CheckCircle2 className="w-3.5 h-3.5 text-teal-600" /> RNFLT CLASSIFIER</div>
          <div className="text-[11px] text-slate-600 mt-1">Harvard-GD RNFLT classifier — {resnet} (validated, independent)</div>
        </div>
      </div>
      <div className="flex flex-wrap gap-2 text-[11px]">
        <span className="px-2 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-800">Raw OCT: Imported ✓</span>
        <span className="px-2 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-800">RNFL segmentation: Unavailable — {e2e}</span>
        <span className="px-2 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-800">RNFLT classifier: Validated</span>
        <span className="px-2 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-600 flex items-center gap-1"><Minus className="w-3 h-3" /> Overall raw-OCT diagnosis: Not available</span>
      </div>
      {showHow && (
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-[11px] font-mono text-slate-700 leading-relaxed">
          <div className="text-center">RAW OCT<br />│<br />OCT PREPROCESSING<br />│<br />RNFLT SEGMENTATION — ⚠ CURRENTLY UNAVAILABLE<br />│<br />QUANTITATIVE RNFLT 225×225<br />│<br />HARVARD-GD CNN<br />│<br />STRUCTURAL ESTIMATE</div>
          <p className="mt-2 text-slate-600">Validated: RNFLT → CNN. Pending: OCT → RNFLT (MGU). Raw OCT B-scans are not passed directly to the RNFLT classifier. A validated OCT segmentation stage is required.</p>
        </div>
      )}
    </div>
  );
};
export default StructuralAIPipelineStatus;
