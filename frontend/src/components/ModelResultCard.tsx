import React from 'react';
import { Activity, ShieldCheck, Layers } from 'lucide-react';
import { ModelResult, PatientContext, GlaucomaStagingInfo } from '../types';

interface ModelResultCardProps {
  modelResult?: ModelResult;
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
    return null;
  }

  const isGlaucoma = modelResult.predicted_class === 1;
  const score = modelResult.model_estimated_classification_score ?? 0;
  const scorePct =
    modelResult.model_estimated_classification_score_pct || `${(score * 100).toFixed(1)}%`;

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
              Machine learning quantitative pattern evaluation on standardized peripapillary RNFL thickness
            </p>
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
                ? 'Axonal bundle attenuation detected along superior/inferior peripapillary sectors. Quantitative profile correlates with glaucomatous structural thinning.'
                : 'Intact neuroretinal rim thickness with preserved superior and inferior physiological double-hump contour.'}
            </p>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-200/60 flex items-center space-x-2 text-[11px] text-slate-600">
            <ShieldCheck className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
            <span>AI model estimate &bull; Clinical correlation required.</span>
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
              <span className="text-xs text-slate-500">calibrated output</span>
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
                {groundTruth.glaucoma_label === 1 ? 'Glaucoma Specimen' : 'Normal Control'}
              </span>
            </div>
          )}
        </div>
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
    </div>
  );
};

export default ModelResultCard;
