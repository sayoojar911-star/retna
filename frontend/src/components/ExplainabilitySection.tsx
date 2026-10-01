import React from 'react';
import { Layers, Clock, AlertCircle, Eye } from 'lucide-react';

interface ExplainabilitySectionProps {
  originalHeatmap?: string;
  hasTrainedModel?: boolean;
}

export const ExplainabilitySection: React.FC<ExplainabilitySectionProps> = ({
  originalHeatmap,
  hasTrainedModel = false,
}) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 mb-6 gap-2">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">
              Visual Explainability (Grad-CAM Preparation)
            </h3>
            <p className="text-xs text-slate-400">
              Convolutional gradient-weighted class activation mapping layout
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700 w-fit">
          <Clock className="w-3.5 h-3.5 text-slate-500" />
          <span>Awaiting Trained Checkpoint</span>
        </div>
      </div>

      {/* 3-Panel Visual Saliency Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        {/* Panel 1: Original Quantitative OCT RNFLT */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 flex flex-col items-center">
          <div className="text-xs font-semibold text-slate-300 mb-2.5 flex items-center space-x-1.5">
            <Eye className="w-3.5 h-3.5 text-teal-400" />
            <span>1. Original RNFLT Matrix</span>
          </div>
          <div className="w-full aspect-square max-w-[220px] rounded-lg border border-slate-800 bg-slate-900 flex items-center justify-center overflow-hidden">
            {originalHeatmap ? (
              <img
                src={originalHeatmap}
                alt="Original RNFLT Map"
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="text-center p-4 text-xs text-slate-500">
                Awaiting study upload
              </div>
            )}
          </div>
          <div className="text-[11px] text-slate-400 mt-2 text-center font-mono">
            Input: 225&times;225 Numerical Map
          </div>
        </div>

        {/* Panel 2: Grad-CAM Saliency Heatmap */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 flex flex-col items-center">
          <div className="text-xs font-semibold text-slate-300 mb-2.5 flex items-center space-x-1.5">
            <Layers className="w-3.5 h-3.5 text-purple-400" />
            <span>2. Feature Saliency Map</span>
          </div>
          <div className="w-full aspect-square max-w-[220px] rounded-lg border border-dashed border-slate-800 bg-slate-900/60 flex flex-col items-center justify-center p-4 text-center">
            <Clock className="w-6 h-6 text-slate-600 mb-2" />
            <span className="text-xs font-medium text-slate-400">
              Grad-CAM visualization will appear after model training
            </span>
            <span className="text-[10px] text-slate-500 mt-1">
              Zero fake saliency generated
            </span>
          </div>
          <div className="text-[11px] text-slate-400 mt-2 text-center font-mono">
            Backbone: Layer4 Feature Gradients
          </div>
        </div>

        {/* Panel 3: Anatomical Overlay */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 flex flex-col items-center">
          <div className="text-xs font-semibold text-slate-300 mb-2.5 flex items-center space-x-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span>3. Clinician Overlay</span>
          </div>
          <div className="w-full aspect-square max-w-[220px] rounded-lg border border-dashed border-slate-800 bg-slate-900/60 flex flex-col items-center justify-center p-4 text-center">
            <Clock className="w-6 h-6 text-slate-600 mb-2" />
            <span className="text-xs font-medium text-slate-400">
              Awaiting trained model overlay
            </span>
            <span className="text-[10px] text-slate-500 mt-1">
              Preserves anatomical fidelity
            </span>
          </div>
          <div className="text-[11px] text-slate-400 mt-2 text-center font-mono">
            Fusion: α = 0.5 RNFLT + Gradient
          </div>
        </div>
      </div>

      {/* Mandatory Clinical Notice */}
      <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-start space-x-2 text-xs text-slate-400">
        <AlertCircle className="w-4 h-4 text-purple-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-300">Clinician Saliency Notice: </span>
          Highlighted regions represent areas that influenced the trained model&apos;s prediction. They do not independently establish a diagnosis. Saliency representations are visual debugging aids and must be correlated with clinical ophthalmoscopy and perimetry.
        </div>
      </div>
    </div>
  );
};
