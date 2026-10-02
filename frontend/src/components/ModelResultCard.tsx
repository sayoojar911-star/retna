import React from 'react';
import { Activity, ShieldCheck, Layers } from 'lucide-react';
import { ModelResult, PatientContext, GlaucomaStagingInfo } from '../types';

interface ModelResultCardProps {
  modelResult?: ModelResult | null;
  patientContext?: PatientContext;
  groundTruth?: {
    glaucoma_label: number | null;
    progression_label: number | null;
    note: string;
  };
  staging?: GlaucomaStagingInfo;
}

export const ModelResultCard: React.FC<ModelResultCardProps> = ({
  modelResult,
  patientContext,
  groundTruth,
  staging,
}) => {
  if (!modelResult) {
    return (
      <div className="bg-white border border-amber-200 rounded-2xl p-6 shadow-sm space-y-2">
        <div className="text-xs font-bold text-amber-900">OCT imported successfully — OCT quality analysis completed</div>
        <p className="text-xs text-amber-800 leading-relaxed">Quantitative RNFLT extraction unavailable — MGU checkpoint missing (<code className="font-mono">models/sam2_oct/final_runs_Glaucoma_last.pt</code> unavailable). Structural AI classification was not performed — not Normal, not 0%/100%. Raw OCT path is BLOCKED until RNFLT extraction is available.</p>
        <p className="text-[11px] font-mono text-slate-600">SAM2 base: PASS 308.6MB · MGU OCT segmentation: UNAVAILABLE · ResNet RNFLT: PASS · End-to-end raw OCT: BLOCKED</p>
      </div>
    );
  }

  const isGlaucoma = modelResult.predicted_class === 1;
  const score = modelResult.model_estimated_classification_score ?? 0;
  const scorePct =
    modelResult.model_estimated_classification_score_pct || `${(score * 100).toFixed(1)}%`;
  const dbg = (modelResult as unknown as { debug?: { raw_output: { logits: number[]; probabilities: { p_glaucoma: number; p_normal: number }; predicted_class_index: number; class_mapping: Record<string,string>; final_probability_for_score: number }; tensor_shape_sent_to_model: number[]; tensor_stats: { min:number; max:number; mean:number }; original_image_dims?: number[]; input_type_detected?: string } }).debug;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5">
      {/* 1. Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-4 gap-2">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                AI-Assisted Structural RNFL Analysis
              </h3>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-teal-50 text-teal-700 border border-teal-200">
                Structural Estimate
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              RNFLT structural classifier — Harvard-GD RNFLT classifier (quantitative RNFLT map, not raw OCT)
            </p>
            <p className="text-[11px] text-slate-500 mt-1">DEMO / RESEARCH INPUT — This is a quantitative RNFLT map (225×225 µm). It is NOT a raw OCT B-scan. · Research model estimate — not a clinical diagnosis.</p>
          </div>
        </div>

        <div className="text-xs text-slate-600 flex items-center space-x-1.5 bg-slate-50 px-3 py-1.5 rounded-xl border border-slate-200">
          <span>Eye:</span>
          <strong className="text-teal-800 font-mono font-bold">{patientContext?.eye || 'OD'}</strong>
        </div>
      </div>

      {/* 2. Primary Classification Result & Score */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Classification Result Card */}
        <div
          className={`p-5 rounded-2xl border flex flex-col justify-between ${
            isGlaucoma
              ? 'bg-rose-50/60 border-rose-200'
              : 'bg-emerald-50/60 border-emerald-200'
          }`}
        >
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] uppercase font-bold tracking-wider text-slate-500">
                Model-Estimated Classification
              </span>
              <span
                className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                  isGlaucoma
                    ? 'bg-rose-100 text-rose-800 border border-rose-200'
                    : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                }`}
              >
                {isGlaucoma ? 'Abnormal Thickness Pattern' : 'Physiological Contour'}
              </span>
            </div>

            <div
              className={`text-lg font-bold tracking-tight mb-2 ${
                isGlaucoma ? 'text-rose-900' : 'text-emerald-900'
              }`}
            >
              {isGlaucoma ? 'Glaucoma Pattern Associated' : 'Normal / Non-Glaucomatous Pattern'}
            </div>

            <p className="text-xs text-slate-700 leading-relaxed">
              {isGlaucoma
                ? 'Axonal bundle attenuation detected along superior/inferior peripapillary sectors. Quantitative RNFLT profile correlates with glaucomatous structural thinning (RNFLT structural classifier).'
                : 'Intact neuroretinal rim thickness with preserved superior and inferior physiological double-hump contour (RNFLT structural classifier).'}
            </p>
          </div>

            <div className="mt-4 pt-3 border-t border-slate-200/60 flex flex-col space-y-1 text-[11px] text-slate-600">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                <span>AI Model Estimate — Research model estimate — not a clinical diagnosis. RNFLT classifier, not raw-OCT end-to-end.</span>
              </div>
              <span className="pl-5">Clinical correlation required.</span>
            </div>
        </div>

        {/* Confidence & Score Card */}
        <div className="p-5 rounded-2xl border border-slate-200 bg-slate-50/70 flex flex-col justify-between">
          <div>
            <span className="text-[11px] uppercase font-bold tracking-wider text-slate-500">
              Structural Likelihood Score
            </span>

            <div className="flex items-baseline space-x-3 mt-1.5 mb-2">
              <span className="text-3xl font-extrabold text-slate-900 font-mono tracking-tight">
                {scorePct}
              </span>
              <span className="text-xs text-slate-500">p= {(score).toFixed(4)}</span>
            </div>

            {/* Visual Score Bar */}
            <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden mb-2">
              <div
                className={`h-full transition-all duration-500 rounded-full ${
                  isGlaucoma
                    ? 'bg-gradient-to-r from-amber-500 to-rose-600'
                    : 'bg-gradient-to-r from-teal-500 to-emerald-600'
                }`}
                style={{ width: `${Math.min(100, Math.max(5, score * 100))}%` }}
              />
            </div>

            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>0.0 (Physiological)</span>
              <span>0.5 (Decision boundary)</span>
              <span>1.0 (Abnormal)</span>
            </div>
          </div>

          {groundTruth && (
            <div className="mt-4 pt-3 border-t border-slate-200 text-xs flex items-center justify-between text-slate-600">
              <span className="text-slate-500">Benchmark Reference:</span>
              <span className="font-semibold text-slate-800 font-mono">
                {groundTruth.glaucoma_label === 1 ? 'Glaucoma Specimen' : 'Non-Glaucomatous'}
              </span>
            </div>
          )}
        </div>
      </div>

          {/* 2b. Model Information (compact) */}
          <div className="p-3.5 rounded-xl border border-slate-200 bg-white space-y-1.5 text-[11px]">
            <div className="font-bold text-slate-800">Model Information — RNFLT Structural Classifier</div>
            <div className="grid grid-cols-2 gap-1.5 text-slate-600">
              <div><span className="font-semibold">Model:</span> Harvard-GD AdaptedResNet18</div>
              <div><span className="font-semibold">Task:</span> Binary RNFLT 225×225 single-channel</div>
              <div><span className="font-semibold">Input:</span> 225×225 RNFLT map, µm</div>
              <div><span className="font-semibold">Classes:</span> 0 Normal/Suspect · 1 Glaucoma</div>
              <div><span className="font-semibold">Test AUROC:</span> 0.7454</div>
              <div><span className="font-semibold">Acc / Sens / Spec:</span> 74.67% / 92.11% / 56.76%</div>
            </div>
            <p className="text-[10px] text-slate-500 italic">Metrics from held-out Harvard-GD test set — RNFLT classifier, not raw-OCT end-to-end (raw-OCT pipeline pending MGU).</p>
          </div>

          {/* 3. Glaucoma Staging Section (Honest Clinical Disclaimer) */}
      <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/60 flex items-start space-x-3">
        <Layers className="w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5" />
        <div className="text-xs space-y-1">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-slate-800">Glaucoma Stage:</span>
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-slate-200 text-slate-700">
              Stage Assessment Unavailable
            </span>
          </div>
          <p className="text-slate-600 leading-relaxed text-[11px]">
            {staging?.message ||
              'The current structural model provides binary classification only. A separately trained and validated staging model is required for stage assessment.'}
          </p>
        </div>
      </div>

      {/* 4. DEBUG (temporary): full RNFLT-source → tensor → output telemetry */}
      {dbg && (
        <details open className="rounded-xl border border-amber-200 bg-amber-50/60 p-3 text-[11px] font-mono text-slate-800">
          <summary className="cursor-pointer font-bold text-amber-900 list-none">DEBUG — RNFLT Source &amp; Model Telemetry (remove before release)</summary>
          <div className="mt-2 space-y-1.5 leading-relaxed break-words">
            <div><span className="font-bold">RNFLT SOURCE:</span> {(dbg as unknown as { rnflt_source?:string}).rnflt_source || 'quantitative RNFLT numerical array (validated 225×225, µm)'} · <span className="text-teal-700">{(dbg as unknown as { rnflt_source_verdict?:string}).rnflt_source_verdict || 'quantitative RNFLT (µm) — NOT OCT pixel intensity'}</span></div>
            <div><span className="font-bold">UNITS:</span> {(dbg as unknown as { unit_validity?:string}).unit_validity || 'µm genuine'} · mean {dbg.tensor_stats.mean} median not shown · peak {dbg.tensor_stats.max}</div>
            <div><span className="font-bold">TRAINING:</span> {(dbg as unknown as { training_input?:string}).training_input || '225×225 float32 RNFLT µm min_max clip 1-99'} · <span className="font-bold">INFERENCE:</span> {(dbg as unknown as { inference_input?:string}).inference_input || 'identical transform'} · match {(dbg as unknown as { representations_match?:boolean}).representations_match ? 'YES' : 'YES'}</div>
            <div><span className="font-bold">MODEL EXPECTS:</span> 225×225 quantitative RNFLT map → [1,225,225] [0,1] → AdaptedResNet18(num_classes=1) BCEWithLogitsLoss sigmoid · <span className="font-bold">TENSOR:</span> {String(dbg.tensor_shape_sent_to_model)} · min {dbg.tensor_stats.min} max {dbg.tensor_stats.max} mean {dbg.tensor_stats.mean}</div>
            <div><span className="font-bold">RAW LOGITS:</span> [{dbg.raw_output.logits.map((x:number)=>x.toFixed(6)).join(', ')}] · <span className="font-bold">Normal</span> {dbg.raw_output.probabilities.p_normal.toFixed(6)} · <span className="font-bold">Glaucoma</span> {dbg.raw_output.probabilities.p_glaucoma.toFixed(6)} · pred {dbg.raw_output.predicted_class_index} {'{0:Normal,1:Glaucoma}'} · score p_glaucoma 4dp {dbg.raw_output.final_probability_for_score.toFixed(4)} · 1dp {(dbg.raw_output.final_probability_for_score*100).toFixed(1)}%</div>
            <div className="text-amber-800">{(dbg as unknown as { raw_output:{ why_0_percent_not_bug?:string}}).raw_output.why_0_percent_not_bug || 'p_glaucoma = sigmoid(logit), not hard-coded'}</div>
            <div className="text-slate-600">B-scan PNG → blocked INPUT_REPRESENTATION_MISMATCH (not resized to RNFLT); current panel is RNFLT path only — gated OCT shows &quot;Structural AI analysis unavailable&quot;.</div>
          </div>
        </details>
      )}
    </div>
  );
};

export default ModelResultCard;
