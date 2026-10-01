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
      className={`rounded-2xl border p-5 transition-all shadow-sm ${
        isPass
          ? 'bg-white border-slate-200'
          : 'bg-rose-50/60 border-rose-200'
      }`}
    >
      {/* Header Banner */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
        <div className="flex items-center space-x-2.5">
          <div
            className={`w-8 h-8 rounded-xl flex items-center justify-center ${
              isPass
                ? 'bg-teal-50 text-teal-700 border border-teal-200'
                : 'bg-rose-100 text-rose-700 border border-rose-200'
            }`}
          >
            {isPass ? <ShieldCheck className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 tracking-tight">
              Study Quality Verification
            </h3>
            <p className="text-xs text-slate-500">
              Input integrity and acquisition quality validation
            </p>
          </div>
        </div>

        {/* Doctor-Friendly Quality Status Badge */}
        <div
          className={`flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${
            isPass
              ? 'bg-teal-50 text-teal-800 border-teal-200'
              : 'bg-rose-100 text-rose-800 border border-rose-200'
          }`}
        >
          {isPass ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
              <span>Scan quality: {qualityStatus || 'Valid'}</span>
            </>
          ) : (
            <>
              <XCircle className="w-3.5 h-3.5 text-rose-600" />
              <span>Quality Issue Detected</span>
            </>
          )}
        </div>
      </div>

      {/* Main Doctor-Friendly Message */}
      <div
        className={`p-3 rounded-xl text-xs font-medium mb-3 flex items-center space-x-2 ${
          isPass
            ? 'bg-teal-50/60 border border-teal-100 text-teal-900'
            : 'bg-rose-100/70 border border-rose-200 text-rose-900'
        }`}
      >
        {isPass ? (
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-teal-600" />
        ) : (
          <XCircle className="w-4 h-4 flex-shrink-0 text-rose-600" />
        )}
        <span>{isPass ? 'Scan quality: Valid. Study is suitable for quantitative analysis.' : (message || 'Scan could not be analyzed. Please review the uploaded study.')}</span>
      </div>

      {/* Issues Breakdown (if failed) */}
      {issues && issues.length > 0 && (
        <div className="mb-3 p-3 bg-white border border-rose-200 rounded-xl">
          <div className="text-[11px] font-bold text-rose-800 uppercase tracking-wider mb-1">
            Clinical Quality Notes:
          </div>
          <ul className="list-disc list-inside text-xs text-slate-700 space-y-0.5">
            {issues.map((issue, idx) => (
              <li key={idx} className="text-[11px] text-rose-700">
                {issue}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Verification Checks Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        {checks.map((chk, idx) => (
          <div
            key={idx}
            className="p-2.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs"
          >
            <span className="text-[11px] text-slate-700 font-medium truncate pr-1">
              {chk.name}
            </span>
            <span
              className={`text-[10px] font-bold px-1.5 py-0.2 rounded font-mono ${
                chk.status === 'PASS'
                  ? 'bg-teal-100 text-teal-800'
                  : 'bg-rose-100 text-rose-800'
              }`}
            >
              {chk.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default QualityControlCard;
