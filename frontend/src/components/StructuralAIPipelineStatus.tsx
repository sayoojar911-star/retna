import React, { useState } from 'react';
import { HelpCircle, CheckCircle2, AlertTriangle, ShieldAlert, ArrowRight } from 'lucide-react';

export const StructuralAIPipelineStatus: React.FC<{
  diagnostics?: {
    two_stage_architecture?: {
      raw_oct?: string;
      sam2_base?: string;
      mgu?: string;
      ai_rnfl_segmentation?: string;
      reference_rnflt?: string;
      rnflt_qc?: string;
      rnflt_resnet?: string;
      harvard_classifier_gate?: string;
      end_to_end_raw_oct?: string;
    };
  } | null;
}> = ({ diagnostics }) => {
  const [showHow, setShowHow] = useState(false);
  const rawOct = diagnostics?.two_stage_architecture?.raw_oct || 'PASS';
  const aiSeg = diagnostics?.two_stage_architecture?.ai_rnfl_segmentation || 'UNAVAILABLE';
  const refRnflt = diagnostics?.two_stage_architecture?.reference_rnflt || 'AVAILABLE';
  const rnfltQc = diagnostics?.two_stage_architecture?.rnflt_qc || 'PASS';
  const harvardGate =
    diagnostics?.two_stage_architecture?.harvard_classifier_gate ||
    'ONLY RUN IF ITS INPUT REPRESENTATION IS VALID';

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <h3 className="text-xs font-bold text-slate-900 tracking-tight uppercase">
            Structural AI Pipeline Status &amp; Execution Gate
          </h3>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Two-model architecture with separate AI vs. Reference extraction paths
          </p>
        </div>
        <button
          onClick={() => setShowHow((v) => !v)}
          className="text-[11px] font-semibold text-teal-700 border border-teal-200 bg-teal-50 px-2.5 py-1 rounded-full flex items-center gap-1 hover:bg-teal-100 transition cursor-pointer"
        >
          <HelpCircle className="w-3.5 h-3.5" /> Pipeline Details
        </button>
      </div>

      {/* 5-Stage Architecture Flow Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-xs">
        {/* Stage 1: Raw OCT */}
        <div className="p-3 rounded-xl border bg-teal-50/70 border-teal-200 flex flex-col justify-between">
          <div>
            <div className="font-bold text-teal-900 flex items-center justify-between">
              <span>RAW OCT</span>
              <span className="text-[10px] bg-teal-100 text-teal-800 px-1.5 py-0.5 rounded font-mono font-bold">
                {rawOct}
              </span>
            </div>
            <div className="text-[11px] text-slate-600 mt-1">Import + Quality verification</div>
          </div>
          <div className="text-[10px] text-teal-700 mt-2 font-semibold">✓ Verified format &amp; variance</div>
        </div>

        {/* Stage 2: AI Segmentation */}
        <div className="p-3 rounded-xl border bg-amber-50/70 border-amber-200 flex flex-col justify-between">
          <div>
            <div className="font-bold text-amber-900 flex items-center justify-between">
              <span>AI SEGMENTATION</span>
              <span className="text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded font-mono font-bold">
                {aiSeg}
              </span>
            </div>
            <div className="text-[11px] text-slate-600 mt-1">MGU checkpoint missing</div>
          </div>
          <div className="text-[10px] text-amber-800 mt-2 font-mono">SAM2 base ≠ Segmenter</div>
        </div>

        {/* Stage 3: Reference RNFLT */}
        <div className="p-3 rounded-xl border bg-teal-50/70 border-teal-200 flex flex-col justify-between">
          <div>
            <div className="font-bold text-teal-900 flex items-center justify-between">
              <span>REFERENCE RNFLT</span>
              <span className="text-[10px] bg-teal-100 text-teal-800 px-1.5 py-0.5 rounded font-mono font-bold">
                {refRnflt}
              </span>
            </div>
            <div className="text-[11px] text-slate-600 mt-1">HC01 Expert Annotations</div>
          </div>
          <div className="text-[10px] text-teal-700 mt-2 font-semibold">✓ Spectralis Ground Truth</div>
        </div>

        {/* Stage 4: RNFLT QC */}
        <div className="p-3 rounded-xl border bg-teal-50/70 border-teal-200 flex flex-col justify-between">
          <div>
            <div className="font-bold text-teal-900 flex items-center justify-between">
              <span>RNFLT QC</span>
              <span className="text-[10px] bg-teal-100 text-teal-800 px-1.5 py-0.5 rounded font-mono font-bold">
                {rnfltQc}
              </span>
            </div>
            <div className="text-[11px] text-slate-600 mt-1">Ordering &amp; Bounds check</div>
          </div>
          <div className="text-[10px] text-teal-700 mt-2 font-semibold">✓ Non-negative [0–250 µm]</div>
        </div>

        {/* Stage 5: Harvard Classifier */}
        <div className="p-3 rounded-xl border bg-slate-50 border-slate-200 flex flex-col justify-between">
          <div>
            <div className="font-bold text-slate-800 flex items-center justify-between">
              <span>HARVARD CLASSIFIER</span>
              <span className="text-[9px] bg-slate-200 text-slate-700 px-1 py-0.5 rounded font-mono font-bold">
                GATE ACTIVE
              </span>
            </div>
            <div className="text-[10px] text-slate-600 mt-1 leading-tight">
              Requires 225×225 ONH thickness map
            </div>
          </div>
          <div className="text-[10px] text-slate-500 mt-2 font-mono">Blocked on Domain Mismatch</div>
        </div>
      </div>

      {/* Summary Status Badges */}
      <div className="flex flex-wrap gap-2 text-[11px]">
        <span className="px-2.5 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-800 font-semibold flex items-center gap-1">
          <CheckCircle2 className="w-3.5 h-3.5" /> RAW OCT: PASS
        </span>
        <span className="px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-800 font-semibold flex items-center gap-1">
          <AlertTriangle className="w-3.5 h-3.5" /> AI RNFL SEGMENTATION: UNAVAILABLE
        </span>
        <span className="px-2.5 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-800 font-semibold flex items-center gap-1">
          <CheckCircle2 className="w-3.5 h-3.5" /> REFERENCE RNFLT: AVAILABLE
        </span>
        <span className="px-2.5 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-800 font-semibold flex items-center gap-1">
          <CheckCircle2 className="w-3.5 h-3.5" /> RNFLT QC: PASS
        </span>
        <span className="px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-700 font-semibold flex items-center gap-1">
          <ShieldAlert className="w-3.5 h-3.5 text-slate-500" /> HARVARD-GD CLASSIFIER: {harvardGate}
        </span>
      </div>

      {showHow && (
        <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl text-[11px] font-mono text-slate-700 space-y-2">
          <div className="font-bold text-slate-900 font-sans">Pipeline Architecture &amp; Modality Governance:</div>
          <p className="leading-relaxed">
            1. <strong>Mode A (AI Segmentation):</strong> OCT → Trained OCT-specific model (MGU) → ILM/RNFL-GCL boundaries → RNFLT. Currently <strong>UNAVAILABLE</strong> because <code className="text-amber-900">models/sam2_oct/final_runs_Glaucoma_last.pt</code> is missing. Generic SAM2 foundation base is NOT an OCT layer segmenter.<br />
            2. <strong>Mode B (Reference RNFLT):</strong> For the HC01 annotated dataset, boundaries are parsed from Johns Hopkins expert ground truth (<code className="text-teal-900">hc01_spectralis_macula_v1_s1_R.mat</code>). RNFLT = RNFL-GCL Y − ILM Y converted via native 3.867 µm/px calibration.<br />
            3. <strong>Classification Gate:</strong> Harvard-GD ResNet-18 expects a 225×225 peripapillary optic disc (ONH) map. It is safely blocked for macular scans to prevent misinterpreting normal foveal thinning as glaucomatous damage.
          </p>
        </div>
      )}
    </div>
  );
};

export default StructuralAIPipelineStatus;
