import React from 'react';
import { Eye, Layers, Info } from 'lucide-react';
import { RNFLTAnalysis } from '../types';

interface RNFLTAnalysisCardProps {
  analysis?: RNFLTAnalysis;
  patientId?: string;
  eye?: string;
}

export const RNFLTAnalysisCard: React.FC<RNFLTAnalysisCardProps> = ({
  analysis,
  patientId,
  eye,
}) => {
  if (!analysis) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center text-slate-500 shadow-sm">
        <Layers className="w-8 h-8 mx-auto mb-2 text-slate-400" />
        <p className="text-xs font-semibold text-slate-700">RNFLT visualization unavailable for this input.</p>
        <p className="text-[11px] text-slate-500 mt-1">Upload an OCT study or select a research demo case.</p>
      </div>
    );
  }

  const {
    mean_thickness_um,
    phys_mean_thickness_um,
    min_thickness_um,
    max_thickness_um,
    median_thickness_um,
    optic_canal_ratio_pct,
    heatmap_image,
    dimensions,
  } = analysis;

  const statsList = [
    {
      label: 'Physiological Mean',
      value: `${phys_mean_thickness_um.toFixed(1)} μm`,
      sub: 'Excluding optic canal cup',
      highlight: true,
    },
    {
      label: 'Global Mean RNFLT',
      value: `${mean_thickness_um.toFixed(1)} μm`,
      sub: 'Full 225x225 grid average',
    },
    {
      label: 'Median Thickness',
      value: `${median_thickness_um.toFixed(1)} μm`,
      sub: '50th percentile',
    },
    {
      label: 'Peak Maximum',
      value: `${max_thickness_um.toFixed(1)} μm`,
      sub: 'Axonal nerve bundle peak',
    },
    {
      label: 'Array Minimum',
      value: `${min_thickness_um.toFixed(1)} μm`,
      sub: '-2.0/0.0 sentinel flag',
    },
    {
      label: 'Optic Canal Ratio',
      value: `${optic_canal_ratio_pct.toFixed(1)}%`,
      sub: 'Unsegmented cup pixels',
    },
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-4 gap-2">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
            <Eye className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              RNFL Thickness Structural Map
            </h3>
            <p className="text-xs text-slate-500">
              Quantitative peripapillary retinal nerve fiber layer OCT matrix
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-mono text-[11px] border border-slate-200">
            {dimensions[0]} &times; {dimensions[1]} pixels
          </span>
          <span className="px-2.5 py-1 rounded-lg bg-teal-50 text-teal-800 font-bold text-[11px] border border-teal-200">
            Eye: {eye || 'OD'}
          </span>
          {patientId && (
            <span className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 font-mono text-[11px] border border-slate-200">
              {patientId}
            </span>
          )}
        </div>
      </div>

      {/* Main Content Grid: Structural Heatmap on Left + Stats on Right */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
        {/* Heatmap Visualization */}
        <div className="md:col-span-5 flex flex-col items-center">
          <div className="relative p-2 rounded-2xl bg-slate-50 border border-slate-200 shadow-xs max-w-[280px] w-full aspect-square flex items-center justify-center overflow-hidden">
            <img
              src={heatmap_image}
              alt="Peripapillary RNFL Thickness Heatmap"
              className="w-full h-full object-contain rounded-xl"
            />
          </div>
          <div className="mt-2.5 flex items-center space-x-1.5 text-[11px] text-slate-500 text-center font-mono">
            <Info className="w-3.5 h-3.5 text-teal-700" />
            <span>Scale: 0 µm (thinning) to ≥150 µm (peak)</span>
          </div>
        </div>

        {/* Quantitative RNFLT Metrics */}
        <div className="md:col-span-7 grid grid-cols-2 gap-3">
          {statsList.map((stat, idx) => (
            <div
              key={idx}
              className={`p-3.5 rounded-xl border transition-all ${
                stat.highlight
                  ? 'bg-teal-50/60 border-teal-200 shadow-xs'
                  : 'bg-slate-50 border-slate-200'
              }`}
            >
              <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                {stat.label}
              </div>
              <div
                className={`text-xl font-bold font-mono tracking-tight mt-1 ${
                  stat.highlight ? 'text-teal-900' : 'text-slate-900'
                }`}
              >
                {stat.value}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5 truncate">
                {stat.sub}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RNFLTAnalysisCard;
