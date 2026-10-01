import React from 'react';
import { Eye, Layers, BarChart3, Info } from 'lucide-react';
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
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-500">
        <Layers className="w-8 h-8 mx-auto mb-2 text-slate-600" />
        <p className="text-sm font-medium">RNFLT visualization unavailable for this input.</p>
        <p className="text-xs text-slate-600 mt-1">Upload an OCT study or select a research demo case.</p>
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
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 mb-6 gap-2">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
            <Eye className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">
              RNFL Thickness Structural Map
            </h3>
            <p className="text-xs text-slate-400">
              Quantitative peripapillary retinal nerve fiber layer OCT matrix
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 font-mono text-[11px] border border-slate-700/60">
            {dimensions[0]} &times; {dimensions[1]} pixels
          </span>
          <span className="px-2.5 py-1 rounded bg-teal-500/10 text-teal-300 font-medium text-[11px] border border-teal-500/20">
            Eye: {eye || 'OD'}
          </span>
          {patientId && (
            <span className="px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-300 font-medium text-[11px] border border-indigo-500/20">
              {patientId}
            </span>
          )}
        </div>
      </div>

      {/* Main Grid: Heatmap + Numerical Statistics */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        {/* Left Column: Visual RNFLT Heatmap */}
        <div className="lg:col-span-5 flex flex-col items-center">
          <div className="relative p-2 bg-slate-950 border border-slate-800 rounded-xl shadow-inner w-full max-w-[320px]">
            <img
              src={heatmap_image}
              alt="225x225 RNFLT Heatmap"
              className="w-full aspect-square object-contain rounded-lg border border-slate-900"
            />
            <div className="mt-2 text-center text-[11px] text-slate-400 font-medium">
              Real 225&times;225 Numerical Thickness Map (μm)
            </div>
          </div>
        </div>

        {/* Right Column: Quantitative Numerical Statistics */}
        <div className="lg:col-span-7">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {statsList.map((stat, idx) => (
              <div
                key={idx}
                className={`p-3.5 rounded-lg border ${
                  stat.highlight
                    ? 'bg-teal-950/20 border-teal-500/40'
                    : 'bg-slate-950/60 border-slate-800/80'
                }`}
              >
                <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                  {stat.label}
                </div>
                <div
                  className={`text-lg font-bold tracking-tight mt-1 font-mono ${
                    stat.highlight ? 'text-teal-400' : 'text-white'
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

          {/* Clinical Interpretation Notice */}
          <div className="mt-4 p-3 bg-slate-950/50 border border-slate-800 rounded-lg flex items-start space-x-2 text-xs text-slate-400">
            <Info className="w-4 h-4 text-teal-400 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-300">Preserved Raw Matrix: </span>
              GlaucoMap preserves all 50,625 discrete thickness measurements without reducing them to 4 quadrants. Central negative values (-1.0 to -2.0) demarcate the optic nerve cup scleral opening.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
