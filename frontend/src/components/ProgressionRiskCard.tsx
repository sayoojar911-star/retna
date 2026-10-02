import React, { useState } from 'react';
import { TrendingUp, ChevronDown, ChevronUp, AlertTriangle, Info } from 'lucide-react';

export const ProgressionRiskCard: React.FC<{ apiBaseUrl: string }> = ({ apiBaseUrl }) => {
  const [form, setForm] = useState({
    age: 60,
    iop: 17,
    cct: 540,
    total_visits: 3,
    rnflt_mean: 85,
    rnflt_superior: 100,
    rnflt_nasal: 80,
    rnflt_inferior: 110,
    rnflt_temporal: 70,
    vf_md: -2.0,
    vf_std: 1.5,
  });
  const [res, setRes] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showTechDetails, setShowTechDetails] = useState(false);
  const [showLimitations, setShowLimitations] = useState(false);

  const submit = async () => {
    setErr(null);
    setLoading(true);
    try {
      const r = await fetch(`${apiBaseUrl.replace(/\/$/, '')}/api/progression/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          age: form.age,
          iop: form.iop,
          cct: form.cct,
          total_visits: form.total_visits,
          rnflt_mean: form.rnflt_mean,
          rnflt_S: form.rnflt_superior,
          rnflt_N: form.rnflt_nasal,
          rnflt_I: form.rnflt_inferior,
          rnflt_T: form.rnflt_temporal,
          vf_md_proxy: form.vf_md,
          vf_std: form.vf_std,
        }),
      });
      if (!r.ok) throw new Error(await r.text());
      setRes(await r.json());
    } catch (e: any) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  const field = (k: keyof typeof form, label: string, step = 'any') => (
    <label key={k} className="space-y-1 text-xs">
      <span className="text-slate-600 font-medium">{label}</span>
      <input
        type="number"
        step={step}
        value={(form as any)[k]}
        onChange={(e) => setForm({ ...form, [k]: parseFloat(e.target.value) })}
        className="w-full border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-900 text-xs focus:outline-none focus:ring-2 focus:ring-teal-400"
      />
    </label>
  );

  const riskLevel =
    res == null
      ? null
      : res.probability >= 0.6
      ? { label: 'Higher Risk', color: 'text-rose-700', bg: 'bg-rose-50 border-rose-200' }
      : res.probability >= 0.3
      ? { label: 'Moderate Risk', color: 'text-amber-700', bg: 'bg-amber-50 border-amber-200' }
      : { label: 'Lower Risk', color: 'text-emerald-700', bg: 'bg-emerald-50 border-emerald-200' };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-purple-50 border border-purple-200 flex items-center justify-center text-purple-700 flex-shrink-0">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">PROGRESSION RISK</h3>
              <span className="text-[9px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 border border-purple-200">
                Module 2
              </span>
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Model: XGBoost · Input: clinical/tabular variables · Independent of RNFLT classifier
            </p>
          </div>
        </div>
        <span className="text-[10px] px-2.5 py-1.5 rounded-full bg-amber-50 border border-amber-200 text-amber-800 font-semibold self-start">
          Research estimate — not clinically validated
        </span>
      </div>

      {/* ── Research disclaimer ── */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-start gap-2.5 text-xs">
        <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-0.5">
          <div className="font-semibold text-amber-900">Research progression-risk estimate — not clinically validated.</div>
          <div className="text-amber-800 leading-relaxed">
            Evaluation includes only <strong>7 positive cases</strong> in the held-out test set; estimates are therefore uncertain.
            This model is <strong>not combined</strong> with the RNFLT structural classifier (p_glaucoma).
          </div>
        </div>
      </div>

      {/* ── Input grid ── */}
      <div>
        <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-3">
          Clinical / Tabular Input Variables
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {field('age', 'Age (years)', '1')}
          {field('iop', 'IOP (mmHg)')}
          {field('cct', 'CCT (µm)', '1')}
          {field('total_visits', 'Total Visits', '1')}
          {field('rnflt_mean', 'RNFLT Mean (µm)')}
          {field('rnflt_superior', 'RNFLT Superior (µm)')}
          {field('rnflt_nasal', 'RNFLT Nasal (µm)')}
          {field('rnflt_inferior', 'RNFLT Inferior (µm)')}
          {field('rnflt_temporal', 'RNFLT Temporal (µm)')}
          {field('vf_md', 'VF MD Proxy (dB)')}
          {field('vf_std', 'VF Std Dev')}
        </div>
      </div>

      <button
        onClick={submit}
        disabled={loading}
        className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 disabled:opacity-60 text-white text-xs font-semibold transition cursor-pointer"
      >
        {loading ? 'Estimating…' : 'Estimate Progression Probability'}
      </button>

      {err && (
        <div className="text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-xl p-3 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{err}</span>
        </div>
      )}

      {res && riskLevel && (
        <div className={`p-4 rounded-xl border ${riskLevel.bg} space-y-2`}>
          <div className="flex flex-wrap items-center gap-3">
            <div className="text-sm font-bold text-slate-900">
              Progression Probability:{' '}
              <span className={`font-mono ${riskLevel.color}`}>
                {(res.probability * 100).toFixed(1)}%
              </span>
            </div>
            <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full border ${riskLevel.bg} ${riskLevel.color}`}>
              {riskLevel.label}
            </span>
          </div>
          <div className="text-[11px] text-slate-600 space-y-0.5">
            <div>
              <span className="font-semibold">Classification:</span>{' '}
              <span className="font-mono">{res.classification_label}</span>
              {' '}(threshold: 0.30)
            </div>
            <div className="text-[10px] text-slate-500 italic">
              Module 2 — Research progression-risk estimate · Independent of RNFLT classifier · Not combined with p_glaucoma
            </div>
          </div>
        </div>
      )}

      {/* ── Technical Details (expandable) ── */}
      <div className="border border-slate-200 rounded-xl overflow-hidden">
        <button
          onClick={() => setShowTechDetails((v) => !v)}
          className="w-full flex items-center justify-between px-4 py-3 bg-slate-50 hover:bg-slate-100 transition text-xs font-semibold text-slate-700 cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <Info className="w-3.5 h-3.5 text-slate-500" />
            Technical Details
          </div>
          {showTechDetails ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        {showTechDetails && (
          <div className="p-4 bg-white space-y-3 text-xs text-slate-700 border-t border-slate-200">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <div className="font-semibold text-slate-900 text-[11px] uppercase tracking-wider">Progression Risk Model</div>
                <div><span className="text-slate-500">Dataset:</span> Clinical longitudinal Excel dataset</div>
                <div><span className="text-slate-500">Architecture:</span> XGBoost (binary:logistic)</div>
                <div><span className="text-slate-500">Task:</span> Progression-risk estimation</div>
                <div><span className="text-slate-500">Threshold:</span> 0.30 (validation-selected)</div>
                <div><span className="text-slate-500">Sensitivity @ 0.30:</span> 0.57 (95% CI: [0.16, 0.75])</div>
                <div><span className="text-slate-500">Specificity @ 0.30:</span> 0.91</div>
                <div><span className="text-slate-500">ROC-AUC:</span> 0.60</div>
              </div>
              <div className="space-y-1.5">
                <div className="font-semibold text-slate-900 text-[11px] uppercase tracking-wider">Input Features (11)</div>
                <div className="font-mono text-[10px] bg-slate-50 rounded-lg p-2 leading-relaxed border border-slate-200">
                  age, iop, cct, total_visits,<br />
                  rnflt_mean, rnflt_S, rnflt_N,<br />
                  rnflt_I, rnflt_T,<br />
                  vf_md_proxy, vf_std
                </div>
                <div className="text-[10px] text-amber-700 italic">
                  vf_md_proxy is NOT equivalent to clinical VF MD
                </div>
              </div>
            </div>
            <div className="p-2.5 bg-slate-900 rounded-lg text-[10px] font-mono text-slate-300 leading-relaxed">
              CLINICAL DATA<br />
              &nbsp;&nbsp;&nbsp;↓<br />
              MEDIAN IMPUTATION (train-only fitted)<br />
              &nbsp;&nbsp;&nbsp;↓<br />
              XGBOOST CLASSIFIER<br />
              &nbsp;&nbsp;&nbsp;↓<br />
              PROGRESSION-RISK PROBABILITY<br />
              &nbsp;&nbsp;&nbsp;&nbsp;(Independent of RNFLT classifier — outputs are NOT combined)
            </div>
          </div>
        )}
      </div>

      {/* ── Limitations Panel (expandable) ── */}
      <div className="border border-amber-200 rounded-xl overflow-hidden">
        <button
          onClick={() => setShowLimitations((v) => !v)}
          className="w-full flex items-center justify-between px-4 py-3 bg-amber-50 hover:bg-amber-100 transition text-xs font-semibold text-amber-800 cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            Current Limitations
          </div>
          {showLimitations ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
        {showLimitations && (
          <div className="p-4 bg-amber-50/50 border-t border-amber-200 space-y-1.5 text-xs text-amber-900">
            <ul className="space-y-1.5 list-none">
              {[
                'OCT→RNFLT segmentation checkpoint unavailable in current build',
                'Progression model has only 7 positive held-out test cases',
                'Progression model is not clinically validated',
                'No normal controls in the progression dataset',
                'vf_md_proxy is not equivalent to clinical VF MD',
                'No external validation on independent cohorts',
                'Current progression model uses baseline information only (no longitudinal change variables)',
              ].map((lim, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-amber-500 font-bold mt-0.5 flex-shrink-0">•</span>
                  <span>{lim}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressionRiskCard;
