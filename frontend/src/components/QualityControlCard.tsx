import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, ShieldCheck } from 'lucide-react';
import { ValidationCheck } from '../types';

interface QualityControlCardProps {
  status: 'PASS' | 'FAIL';
  qualityStatus: string;
  message: string;
  checks: ValidationCheck[];
  issues?: string[];
}

export const QualityControlCard: React.FC<QualityControlCardProps> = ({
  status,
  qualityStatus,
  message,
  checks,
  issues,
}) => {
  const isPass = status === 'PASS';

  return (
    <div
      className={`rounded-xl border p-5 transition-all shadow-sm ${
        isPass
          ? 'bg-slate-900/90 border-emerald-500/40 shadow-emerald-500/5'
          : 'bg-slate-900/90 border-rose-500/40 shadow-rose-500/5'
      }`}
    >
      {/* Header Banner */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center space-x-2.5">
          <div
            className={`w-7 h-7 rounded-lg flex items-center justify-center ${
              isPass
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
            }`}
          >
            {isPass ? <ShieldCheck className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white tracking-tight">
              Technical Data Quality Control
            </h3>
            <p className="text-xs text-slate-400">
              Automated multi-point input verification gate
            </p>
          </div>
        </div>

        {/* Status Badge */}
        <div
          className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider border ${
            isPass
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
          }`}
        >
          {isPass ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>PASS &bull; {qualityStatus}</span>
            </>
          ) : (
            <>
              <XCircle className="w-3.5 h-3.5" />
              <span>FAIL &bull; {qualityStatus}</span>
            </>
          )}
        </div>
      </div>

      {/* Main Validation Message */}
      <div
        className={`p-3 rounded-lg text-xs font-medium mb-4 flex items-center space-x-2 ${
          isPass
            ? 'bg-emerald-950/40 border border-emerald-900/50 text-emerald-300'
            : 'bg-rose-950/40 border border-rose-900/50 text-rose-300'
        }`}
      >
        {isPass ? (
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-400" />
        ) : (
          <XCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
        )}
        <span>{message}</span>
      </div>

      {/* Issues Breakdown (if failed) */}
      {issues && issues.length > 0 && (
        <div className="mb-4 p-3 bg-slate-950 border border-rose-900/60 rounded-lg">
          <div className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider mb-1">
            Detected Technical Rejection Reasons:
          </div>
          <ul className="list-disc list-inside text-xs text-slate-300 space-y-0.5">
            {issues.map((issue, idx) => (
              <li key={idx} className="font-mono text-[11px] text-rose-200">
                {issue}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Verification Checklist Matrix */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
        {checks.map((check, idx) => {
          const pass = check.status === 'PASS';
          const fail = check.status === 'FAIL';
          return (
            <div
              key={idx}
              className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-2.5 flex items-start space-x-2"
            >
              <div className="mt-0.5">
                {pass && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
                {fail && <XCircle className="w-3.5 h-3.5 text-rose-400" />}
                {!pass && !fail && <AlertTriangle className="w-3.5 h-3.5 text-slate-500" />}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-200 truncate">
                    {check.name}
                  </span>
                  <span
                    className={`text-[10px] font-semibold px-1.5 py-0.2 rounded border ${
                      pass
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                        : fail
                        ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                        : 'bg-slate-800 text-slate-400 border-slate-700'
                    }`}
                  >
                    {check.status}
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 truncate mt-0.5 font-mono">
                  {check.detail}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
