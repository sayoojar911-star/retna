import React from 'react';
import { CheckCircle2 } from 'lucide-react';

export const ModelInfoPanel: React.FC = () => {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
      <h3 className="text-xs font-bold text-slate-900 tracking-wider">Model Information</h3>
      
      {/* Structural Classifier */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-3">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-teal-600" />
          <h4 className="font-bold text-slate-900">STRUCTURAL CLASSIFIER</h4>
          <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-teal-50 border border-teal-200 text-teal-700">RNFLT Structural Classifier</span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
          <div><span className="font-semibold">Model:</span> Harvard-GD AdaptedResNet18</div>
          <div><span className="font-semibold">Input:</span> 225×225 quantitative RNFLT (µm)</div>
          <div><span className="font-semibold">Task:</span> Binary structural classification</div>
          <div><span className="font-semibold">Classes:</span> 0=Normal/Suspect · 1=Glaucoma</div>
          <div><span className="font-semibold">Evaluation:</span> Held-out Harvard-GD test set</div>
          <div><span className="font-semibold">AUROC:</span> 0.849 (test), 0.853 (val)</div>
        </div>
        <p className="text-[10px] text-slate-500 italic">Operates on quantitative RNFLT maps only. Does NOT accept raw OCT B-scans directly.</p>
      </div>

      {/* Progression Model */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-3">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-teal-600" />
          <h4 className="font-bold text-slate-900">PROGRESSION MODEL</h4>
          <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-amber-50 border border-amber-200 text-amber-800">Research Progression Risk Estimate</span>
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
          <div><span className="font-semibold">Model:</span> XGBoost Binary Classifier</div>
          <div><span className="font-semibold">Input:</span> Clinical/tabular variables (RNFLT, VF, IOP, CCT, Age, Visits)</div>
          <div><span className="font-semibold">Task:</span> Progression-risk estimation (PLR2)</div>
          <div><span className="font-semibold">Dataset:</span> Clinical longitudinal Excel dataset (144 subjects)</div>
          <div><span className="font-semibold">AUROC:</span> 0.849 (test), 0.853 (val)</div>
          <div><span className="font-semibold">Sensitivity:</span> 0.43 @ 0.5 / 0.57 @ 0.3</div>
        </div>
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800">
          <strong>Research Progression Risk Estimate</strong> — not clinically validated.
          <br />Only 7 positive test cases (n=7). Sensitivity 95% CI: [0.16, 0.75].
          <br />VF MD proxy is derived from threshold mean (0-60 dB), not clinical VF MD.
        </div>
      </div>
    </div>
  );
};
export default ModelInfoPanel;