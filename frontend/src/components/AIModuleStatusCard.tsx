import React, { useState } from 'react';
import { CheckCircle2, AlertTriangle, ChevronDown, ChevronUp, Cpu, Info } from 'lucide-react';
import { BackendModelStatus } from '../types';

interface AIModuleStatusCardProps {
  modelStatus?: BackendModelStatus | null;
  diagnostics?: {
    two_stage_architecture?: {
      sam2_base: string;
      mgu: string;
      rnflt_resnet: string;
      end_to_end_raw_oct: string;
    };
  } | null;
}

export const AIModuleStatusCard: React.FC<AIModuleStatusCardProps> = ({
  modelStatus,
  diagnostics: _diagnostics,
}) => {
  const [showTechDetails, setShowTechDetails] = useState(false);

  const isCheckpointAvailable = modelStatus?.checkpoint?.exists === true;

  const modules = [
    {
      id: 'harvard_gd_rnflt',
      name: 'Harvard-GD RNFLT Classifier',
      status: 'validated',
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-600" />,
      badge: '✓ Validated',
      badgeStyle: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      detail: isCheckpointAvailable
        ? `AdaptedResNet18 · 225×225 RNFLT map · AUROC 0.7454 · Sensitivity 92.1% · Checkpoint: ${modelStatus?.checkpoint_file || 'harvard_gd_rnflt_cnn_best.pt'}`
        : 'AdaptedResNet18 · 225×225 RNFLT map · AUROC 0.7454 · Sensitivity 92.1%',
    },
    {
      id: 'progression_risk',
      name: 'Progression Risk Model',
      status: 'research',
      icon: <CheckCircle2 className="w-4 h-4 text-purple-600" />,
      badge: '✓ Research model available',
      badgeStyle: 'bg-purple-50 text-purple-800 border-purple-200',
      detail: 'XGBoost · Tabular clinical variables · 7 positive test cases · Not clinically validated',
    },
    {
      id: 'oct_segmentation',
      name: 'OCT→RNFLT Segmentation',
      status: 'reference_available',
      icon: <CheckCircle2 className="w-4 h-4 text-teal-600" />,
      badge: '✓ Reference Available (HC01)',
      badgeStyle: 'bg-teal-50 text-teal-800 border-teal-200',
      detail: 'HC01 Expert Reference Ground Truth operational · MGU AI checkpoint unavailable (models/sam2_oct/final_runs_Glaucoma_last.pt missing)',
    },
    {
      id: 'raw_oct_e2e',
      name: 'Raw OCT End-to-End Analysis',
      status: 'unavailable',
      icon: <AlertTriangle className="w-4 h-4 text-amber-600" />,
      badge: '⚠ Safely Blocked',
      badgeStyle: 'bg-amber-50 text-amber-800 border-amber-200',
      detail: 'Macular OCT blocked from Harvard-GD classifier due to anatomical domain mismatch (Macula vs Optic Nerve Head). Prevents false results.',
    },
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-slate-900 flex items-center justify-center text-white flex-shrink-0">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">AI MODULE STATUS</h3>
            <p className="text-[11px] text-slate-500 mt-0.5">GlaucoMap · Frozen build · Research prototype</p>
          </div>
        </div>
        <span className="text-[10px] px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-600 font-semibold">
          v1.0 FROZEN
        </span>
      </div>

      {/* Module status list */}
      <div className="space-y-2.5">
        {modules.map((mod) => (
          <div
            key={mod.id}
            className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3.5 rounded-xl border border-slate-200 bg-slate-50/60"
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex-shrink-0">{mod.icon}</div>
              <div>
                <div className="text-xs font-semibold text-slate-900">{mod.name}</div>
                <div className="text-[10px] text-slate-500 mt-0.5 leading-relaxed">{mod.detail}</div>
              </div>
            </div>
            <span
              className={`text-[10px] font-bold px-2.5 py-1 rounded-full border flex-shrink-0 ${mod.badgeStyle}`}
            >
              {mod.badge}
            </span>
          </div>
        ))}
      </div>

      {/* Architecture Diagram (expandable Technical Details) */}
      <div className="border border-slate-200 rounded-xl overflow-hidden">
        <button
          onClick={() => setShowTechDetails((v) => !v)}
          className="w-full flex items-center justify-between px-4 py-3 bg-slate-50 hover:bg-slate-100 transition text-xs font-semibold text-slate-700 cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <Info className="w-3.5 h-3.5 text-slate-500" />
            Technical Details — Architecture Diagram
          </div>
          {showTechDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        {showTechDetails && (
          <div className="p-4 bg-white border-t border-slate-200 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Pipeline A: OCT → CNN */}
              <div className="space-y-2">
                <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Pipeline A — Structural Analysis (Independent)
                </div>
                <div className="bg-slate-900 rounded-xl p-3 text-[10px] font-mono text-slate-300 leading-relaxed">
                  <div className="text-teal-400">RAW OCT</div>
                  <div className="text-slate-500">&nbsp;&nbsp;&nbsp;↓</div>
                  <div>OCT QUALITY</div>
                  <div className="text-slate-500">&nbsp;&nbsp;&nbsp;↓</div>
                  <div className="text-amber-400">OCT → RNFLT SEGMENTATION</div>
                  <div className="text-amber-600 text-[9px]">&nbsp;&nbsp;&nbsp;⚠ Checkpoint unavailable</div>
                  <div className="text-slate-500">&nbsp;&nbsp;&nbsp;↓</div>
                  <div>QUANTITATIVE RNFLT</div>
                  <div className="text-slate-500">&nbsp;&nbsp;&nbsp;225×225 · µm · float32</div>
                  <div className="text-slate-500">&nbsp;&nbsp;&nbsp;↓</div>
                  <div className="text-emerald-400">HARVARD-GD CNN</div>
                  <div className="text-slate-500">&nbsp;&nbsp;&nbsp;AdaptedResNet18</div>
                  <div className="text-slate-500">&nbsp;&nbsp;&nbsp;↓</div>
                  <div>STRUCTURAL ESTIMATE</div>
                  <div className="text-slate-500">&nbsp;&nbsp;&nbsp;p_glaucoma + Grad-CAM</div>
                </div>
                <div className="text-[10px] text-slate-500 bg-slate-50 rounded-lg p-2 border border-slate-200">
                  <div className="font-semibold text-slate-700 mb-1">Structural Classifier</div>
                  <div>Dataset: Harvard-GD</div>
                  <div>Architecture: AdaptedResNet18</div>
                  <div>Task: Binary structural classification</div>
                  <div className="text-amber-700 italic mt-1">Research model estimate — not a clinical diagnosis</div>
                </div>
              </div>

              {/* Pipeline B: Clinical → XGBoost */}
              <div className="space-y-2">
                <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Pipeline B — Progression Risk (Independent)
                </div>
                <div className="bg-slate-900 rounded-xl p-3 text-[10px] font-mono text-slate-300 leading-relaxed">
                  <div className="text-purple-400">CLINICAL DATA</div>
                  <div className="text-slate-500">&nbsp;&nbsp;&nbsp;11 tabular variables</div>
                  <div className="text-slate-500">&nbsp;&nbsp;&nbsp;↓</div>
                  <div>XGBOOST</div>
                  <div className="text-slate-500">&nbsp;&nbsp;&nbsp;Threshold: 0.30</div>
                  <div className="text-slate-500">&nbsp;&nbsp;&nbsp;↓</div>
                  <div className="text-purple-400">PROGRESSION RISK</div>
                  <div className="text-slate-500">&nbsp;&nbsp;&nbsp;probability (0–1)</div>
                </div>
                <div className="text-[10px] text-slate-500 bg-slate-50 rounded-lg p-2 border border-slate-200">
                  <div className="font-semibold text-slate-700 mb-1">Progression Risk Model</div>
                  <div>Dataset: Clinical longitudinal Excel dataset</div>
                  <div>Architecture: XGBoost</div>
                  <div>Task: Progression-risk estimation</div>
                  <div className="text-amber-700 italic mt-1">Research estimate — not clinically validated</div>
                </div>
                <div className="p-2 rounded-lg bg-amber-50 border border-amber-200 text-[10px] text-amber-800 font-semibold">
                  ⚠ Outputs are INDEPENDENT — never combined with p_glaucoma
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIModuleStatusCard;
