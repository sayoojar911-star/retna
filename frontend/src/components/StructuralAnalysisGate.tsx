import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { OCTAnalysisResponse } from '../types';

export const StructuralAnalysisGate: React.FC<{ analysis: OCTAnalysisResponse | null }> = ({ analysis }) => {
  if (!analysis) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center text-slate-500 shadow-sm">
        <p className="text-xs font-semibold">No analysis loaded.</p>
      </div>
    );
  }
  const blocked = analysis.ai_analysis?.rnflt_extraction?.available === false || analysis.model_result === null;
  if (blocked && analysis.input_type === 'raw_oct') {
    return (
      <div className="bg-white border border-amber-200 rounded-2xl p-6 shadow-sm space-y-3" data-testid="structural-unavailable">
        <div className="flex items-center space-x-2 text-amber-900">
          <AlertTriangle className="w-4 h-4" />
          <h3 className="text-sm font-bold">STRUCTURAL ANALYSIS UNAVAILABLE</h3>
        </div>
        <div className="text-xs text-slate-700 space-y-1.5" data-testid="structural-unavailable-details">
          <div className="flex items-center space-x-1.5"><span className="text-teal-600">✓</span><span>OCT imported successfully</span></div>
          <div className="flex items-center space-x-1.5"><span className="text-teal-600">✓</span><span>OCT quality analysis completed</span></div>
          <div className="flex items-center space-x-1.5 text-amber-800"><span>⚠</span><span>Quantitative RNFLT extraction unavailable</span></div>
          <p>The OCT→RNFLT segmentation model is not available in this build. Structural AI classification was not performed.</p>
        </div>
      </div>
    );
  }
  return null;
};
export default StructuralAnalysisGate;
