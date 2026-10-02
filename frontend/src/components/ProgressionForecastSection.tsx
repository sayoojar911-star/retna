import React from 'react';
import { Activity, Clock, AlertCircle, Calendar } from 'lucide-react';

export const ProgressionForecastSection: React.FC = () => {
  const horizons = [
    { label: 'Baseline', time: 'Month 0', status: 'Observed Exam', active: true },
    { label: '6 Months', time: 'Month +6', status: 'Forecast Pending', active: false },
    { label: '12 Months', time: 'Month +12', status: 'Forecast Pending', active: false },
    { label: '18 Months', time: 'Month +18', status: 'Forecast Pending', active: false },
    { label: '24 Months', time: 'Month +24', status: 'Forecast Pending', active: false },
  ];

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 mb-6 gap-2">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">
              Longitudinal Progression Trajectory &amp; Forecast
            </h3>
            <p className="text-xs text-slate-400">
              Structural RNFL thinning rate &amp; multi-horizon progression projection
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700 w-fit">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span>Longitudinal Model Pending</span>
        </div>
      </div>

      {/* Multi-Horizon Timeline Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 mb-5">
        {horizons.map((h, idx) => (
          <div
            key={idx}
            className={`rounded-xl border p-4 flex flex-col justify-between ${
              h.active
                ? 'bg-slate-950 border-teal-500/40 shadow-sm'
                : 'bg-slate-950/40 border-slate-800/80 opacity-60'
            }`}
          >
            <div>
              <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
                <span className="font-semibold text-slate-300">{h.label}</span>
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
              </div>
              <div className="text-sm font-bold text-white font-mono">{h.time}</div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-900">
              <span
                className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                  h.active
                    ? 'bg-teal-500/10 text-teal-400 border-teal-500/30'
                    : 'bg-slate-800 text-slate-400 border-slate-700'
                }`}
              >
                {h.status}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Trajectory Placeholder Chart Box */}
      <div className="border border-dashed border-slate-800 bg-slate-950/40 rounded-xl p-8 text-center flex flex-col items-center justify-center mb-4">
        <Clock className="w-8 h-8 text-slate-600 mb-2" />
        <h4 className="text-sm font-semibold text-slate-300">
          Longitudinal Forecast Inactive
        </h4>
        <p className="text-xs text-slate-500 max-w-md mt-1">
          24-month forecast unavailable — validated progression model not currently connected. Additional longitudinal data and a validated progression model are required.
        </p>
        <span className="text-[11px] text-slate-600 font-mono mt-2">
          Strict policy: No synthetic trajectories or fabricated forecast data.
        </span>
      </div>

      {/* Clinical Disclaimer */}
      <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-start space-x-2 text-xs text-slate-400">
        <AlertCircle className="w-4 h-4 text-teal-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-300">Progression Forecasting Gate: </span>
          Real glaucoma progression slopes require verified temporal Humphrey visual field MD/VFI decline rates over multi-year monitoring. Target leakage protections strictly segregate functional perimetry from baseline structural inputs.
        </div>
      </div>
    </div>
  );
};
