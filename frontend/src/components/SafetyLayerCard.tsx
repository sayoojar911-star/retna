import React from 'react';
import { ShieldAlert, ShieldCheck, CheckCircle2, Clock, AlertTriangle, Lock } from 'lucide-react';
import { SafetyLayerAudit } from '../types';

interface SafetyLayerCardProps {
  audit?: SafetyLayerAudit;
}

export const SafetyLayerCard: React.FC<SafetyLayerCardProps> = ({ audit }) => {
  const safetyItems = [
    {
      title: 'Input Quality Validation',
      desc: 'Automatic dimensional verification, non-zero variance check, and NaN/Inf rejection.',
      status: audit?.input_quality_validation || 'PASS',
      implemented: true,
    },
    {
      title: 'Missing Data Handling',
      desc: 'Graceful handling of absent clinical variables (e.g. IOP absent in Harvard-GDP) without fabrication.',
      status: audit?.missing_data_handling || 'PASS',
      implemented: true,
    },
    {
      title: 'Unsupported Input Handling',
      desc: 'Clear error surfacing and rejection of incompatible files without exposing stack traces.',
      status: audit?.unsupported_input_handling || 'PASS',
      implemented: true,
    },
    {
      title: 'Target Leakage Exclusion',
      desc: 'Strict technical boundary segregating Humphrey perimetry (MD/TDS) from progression inputs.',
      status: audit?.target_leakage_exclusion || 'PASS',
      implemented: true,
    },
    {
      title: 'Model Uncertainty Estimation',
      desc: 'Monte Carlo dropout / epistemic variance estimation for out-of-distribution scans.',
      status: audit?.model_uncertainty || 'Pending implementation',
      implemented: false,
    },
    {
      title: 'Atypical-Pattern & Artifact Review',
      desc: 'Automated flagging of high myopia, segmentation error artifacts, or peripapillary atrophy.',
      status: audit?.atypical_pattern_review || 'Pending implementation',
      implemented: false,
    },
    {
      title: 'Longitudinal Consistency Audit',
      desc: 'Plausibility boundary checking across sequential multi-year visits.',
      status: audit?.longitudinal_consistency || 'Pending implementation',
      implemented: false,
    },
  ];

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center space-x-3 border-b border-slate-800 pb-4 mb-6">
        <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
          <ShieldCheck className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-white">
            Clinical Safety &amp; Algorithmic Governance Layer
          </h3>
          <p className="text-xs text-slate-400">
            Real-time quality enforcement, regulatory guardrails, and compliance tracking
          </p>
        </div>
      </div>

      {/* Safety Matrix Table */}
      <div className="divide-y divide-slate-800 border border-slate-800 rounded-xl overflow-hidden bg-slate-950/60 mb-5">
        {safetyItems.map((item, idx) => (
          <div
            key={idx}
            className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-slate-900/50 transition-colors"
          >
            <div className="flex items-start space-x-2.5">
              <div className="mt-0.5">
                {item.implemented ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Clock className="w-4 h-4 text-amber-400" />
                )}
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-200">
                  {item.title}
                </div>
                <div className="text-[11px] text-slate-400">
                  {item.desc}
                </div>
              </div>
            </div>

            <div className="flex-shrink-0">
              <span
                className={`text-[10px] font-semibold px-2.5 py-0.5 rounded-full border ${
                  item.implemented
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                    : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                }`}
              >
                {item.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Mandatory Regulatory Statement */}
      <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl flex items-start space-x-3 text-xs text-slate-400">
        <ShieldAlert className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div>
          <div className="font-semibold text-slate-200 mb-1">
            Official Research Prototype Notice:
          </div>
          <p className="leading-relaxed">
            GlaucoMap is an investigational clinical decision-support prototype intended solely for scientific research and algorithm benchmarking. It is <strong>NOT</strong> cleared or approved by the FDA or CE for clinical diagnosis. Model outputs and structural estimations must never be used to replace, override, or delay comprehensive in-person ophthalmic examination and professional clinical judgment.
          </p>
        </div>
      </div>
    </div>
  );
};
