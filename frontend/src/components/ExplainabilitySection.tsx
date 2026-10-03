import React, { useState } from 'react';
import { Layers, Eye, Sparkles, Info } from 'lucide-react';
import { ExplainabilityData } from '../types';

interface ExplainabilitySectionProps {
  originalHeatmap?: string;
  explainability?: ExplainabilityData;
}

export const ExplainabilitySection: React.FC<ExplainabilitySectionProps> = ({
  originalHeatmap,
  explainability,
}) => {
  const [activeViewTab, setActiveViewTab] = useState<'3-panel' | 'original' | 'explanation' | 'overlay'>('3-panel');

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5">
      {/* 1. Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-4 gap-2">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-slate-900 tracking-tight">
                Visual Explainability (Grad-CAM Saliency)
              </h3>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-teal-50 text-teal-700 border border-teal-200">
                Spatial Attribution
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Identifies anatomical regions that influenced the model-estimated classification
            </p>
          </div>
        </div>

        {/* View Mode Tabs */}
        <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl text-xs">
          {(['3-panel', 'original', 'explanation', 'overlay'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveViewTab(tab)}
              className={`px-2.5 py-1 rounded-lg font-medium transition cursor-pointer capitalize ${
                activeViewTab === tab
                  ? 'bg-white text-slate-900 font-semibold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {tab === '3-panel' ? 'All 3 Views' : tab}
            </button>
          ))}
        </div>
      </div>

      {/* 2. Visual Saliency Views */}
      {activeViewTab === '3-panel' ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Panel 1: Original Quantitative RNFLT Map */}
          <div className="bg-slate-50/70 border border-slate-200 rounded-xl p-4 flex flex-col items-center">
            <div className="text-xs font-bold text-slate-800 mb-2.5 flex items-center space-x-1.5">
              <Eye className="w-3.5 h-3.5 text-teal-700" />
              <span>1. Original RNFLT Map</span>
            </div>
            <div className="w-full aspect-square max-w-[240px] rounded-xl border border-slate-200 bg-white flex items-center justify-center overflow-hidden shadow-xs">
              {explainability?.original_rnflt_image || originalHeatmap ? (
                <img
                  src={explainability?.original_rnflt_image || originalHeatmap}
                  alt="Original RNFLT Map"
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="text-center p-4 text-xs text-slate-400">
                  Awaiting study upload
                </div>
              )}
            </div>
            <div className="text-[11px] text-slate-500 mt-2 text-center font-mono">
              Quantitative Thickness Input
            </div>
          </div>

          {/* Panel 2: AI Explanation (Grad-CAM Heatmap) */}
          <div className="bg-slate-50/70 border border-slate-200 rounded-xl p-4 flex flex-col items-center">
            <div className="text-xs font-bold text-slate-800 mb-2.5 flex items-center space-x-1.5">
              <Sparkles className="w-3.5 h-3.5 text-teal-700" />
              <span>2. AI Explanation Map</span>
            </div>
            <div className="w-full aspect-square max-w-[240px] rounded-xl border border-slate-200 bg-white flex items-center justify-center overflow-hidden shadow-xs">
              {explainability?.gradcam_heatmap_image ? (
                <img
                  src={explainability.gradcam_heatmap_image}
                  alt="AI Explanation Map"
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="text-center p-4 text-xs text-slate-400">
                  Awaiting model execution
                </div>
              )}
            </div>
            <div className="text-[11px] text-slate-500 mt-2 text-center font-mono">
              Spatial Attribution Gradient
            </div>
          </div>

          {/* Panel 3: Combined Overlay */}
          <div className="bg-slate-50/70 border border-slate-200 rounded-xl p-4 flex flex-col items-center">
            <div className="text-xs font-bold text-slate-800 mb-2.5 flex items-center space-x-1.5">
              <Layers className="w-3.5 h-3.5 text-teal-700" />
              <span>3. Structural Overlay</span>
            </div>
            <div className="w-full aspect-square max-w-[240px] rounded-xl border border-slate-200 bg-white flex items-center justify-center overflow-hidden shadow-xs">
              {explainability?.gradcam_overlay_image ? (
                <img
                  src={explainability.gradcam_overlay_image}
                  alt="Structural Overlay"
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="text-center p-4 text-xs text-slate-400">
                  Awaiting overlay composite
                </div>
              )}
            </div>
            <div className="text-[11px] text-slate-500 mt-2 text-center font-mono">
              Anatomical Alignment
            </div>
          </div>
        </div>
      ) : (
        /* Single Tab Focused View */
        <div className="flex flex-col items-center justify-center p-6 bg-slate-50/70 border border-slate-200 rounded-xl">
          <div className="w-full max-w-sm aspect-square rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-sm flex items-center justify-center">
            {activeViewTab === 'original' && (
              <img
                src={explainability?.original_rnflt_image || originalHeatmap}
                alt="Original Map"
                className="w-full h-full object-cover"
              />
            )}
            {activeViewTab === 'explanation' && (
              <img
                src={explainability?.gradcam_heatmap_image}
                alt="AI Explanation"
                className="w-full h-full object-cover"
              />
            )}
            {activeViewTab === 'overlay' && (
              <img
                src={explainability?.gradcam_overlay_image}
                alt="Overlay"
                className="w-full h-full object-cover"
              />
            )}
          </div>
          <div className="mt-3 text-xs font-semibold text-slate-700 capitalize">
            {activeViewTab} View
          </div>
        </div>
      )}

      {/* 3. Clinical Attribution Disclaimer (Mandatory Safety Language) */}
      <div className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/60 flex items-start space-x-2.5 text-xs text-slate-600">
        <Info className="w-4 h-4 text-teal-700 flex-shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          Highlighted regions represent areas that influenced the model prediction. They do not independently establish a diagnosis.
        </p>
      </div>
    </div>
  );
};

export default ExplainabilitySection;
