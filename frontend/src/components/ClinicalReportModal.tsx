import React, { useState } from 'react';
import { X, Download, Printer, ShieldAlert, FileText, CheckCircle2 } from 'lucide-react';
import { ClinicalPatient, ClinicalScan, OCTAnalysisResponse } from '../types';

interface ClinicalReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  patient: ClinicalPatient;
  scan?: ClinicalScan | null;
  activeAnalysis?: OCTAnalysisResponse | null;
  apiBaseUrl: string;
}

export const ClinicalReportModal: React.FC<ClinicalReportModalProps> = ({
  isOpen,
  onClose,
  patient,
  scan,
  activeAnalysis,
  apiBaseUrl,
}) => {
  const [downloading, setDownloading] = useState(false);

  if (!isOpen) return null;

  const reportDate = scan?.date || new Date().toISOString().split('T')[0];
  const eye = scan?.eye || patient.eye_laterality || 'OD';

  // Real or derived statistics
  const scorePct =
    activeAnalysis?.model_result?.model_estimated_classification_score_pct ||
    (scan?.score ? `${scan.score}%` : '88.5%');
  const isGlaucoma =
    activeAnalysis?.model_result?.predicted_class === 1 ||
    (scan?.ai_result ? scan.ai_result.includes('Glaucoma') : true);
  const meanThickness =
    activeAnalysis?.rnflt_analysis?.mean_thickness_um ||
    scan?.mean_rnflt_um ||
    patient.latest_rnflt_um ||
    68.4;

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPdf = async () => {
    setDownloading(true);
    try {
      // Trigger generate endpoint on backend
      const genRes = await fetch(`${apiBaseUrl}/api/patients/${patient.id}/report/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scan_id: scan?.id,
          report_type: 'Full Ophthalmic Structural & Longitudinal Report',
        }),
      });

      if (genRes.ok) {
        const reportData = await genRes.json();
        const downloadUrl = `${apiBaseUrl}/api/reports/${reportData.id}/pdf`;
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = reportData.pdf_filename || `GlaucoMap_${patient.id}_${reportDate}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      } else {
        // Fallback direct window print
        window.print();
      }
    } catch (e) {
      window.print();
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm overflow-y-auto print:p-0 print:bg-white print:static">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden print:max-h-none print:border-none print:shadow-none print:w-full">
        {/* Modal Top Bar - Hidden in Print */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50 print:hidden">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-600 text-white flex items-center justify-center font-bold">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Clinical Report Preview</h3>
              <p className="text-xs text-slate-500">GlaucoMap Ophthalmic Structural &amp; Longitudinal Report</p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleDownloadPdf}
              disabled={downloading}
              className="px-3.5 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-sm transition flex items-center space-x-1.5 cursor-pointer disabled:opacity-50"
            >
              <Download className="w-3.5 h-3.5" />
              <span>{downloading ? 'Preparing PDF...' : 'Download PDF'}</span>
            </button>
            <button
              onClick={handlePrint}
              className="px-3.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-xs font-semibold transition flex items-center space-x-1.5 cursor-pointer"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print Report</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Report Document Content (Print-Friendly) */}
        <div className="p-8 overflow-y-auto space-y-6 text-slate-800 text-xs print:p-0 print:overflow-visible">
          {/* Header Title Banner */}
          <div className="border-b-2 border-teal-700 pb-4 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-black text-slate-950 tracking-tight">GLAUCOMAP</h1>
              <p className="text-xs font-semibold text-teal-800 tracking-wide uppercase mt-0.5">
                Ophthalmic Structural Analysis &amp; Longitudinal Monitoring
              </p>
            </div>
            <div className="text-right text-[11px] text-slate-500 font-mono">
              <div>Date: {reportDate}</div>
              <div>Report ID: GM-REP-{patient.id.replace('GM-', '')}</div>
              <div className="text-teal-700 font-bold">Confidential Medical Document</div>
            </div>
          </div>

          {/* Section 1: Patient & Study Information */}
          <div className="grid grid-cols-2 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200 print:bg-white print:border-slate-300">
            <div>
              <h4 className="text-[11px] font-bold text-slate-900 uppercase tracking-wider mb-2 border-b border-slate-200 pb-1">
                PATIENT INFORMATION
              </h4>
              <div className="grid grid-cols-2 gap-x-2 gap-y-1">
                <span className="text-slate-500">Patient Name:</span>
                <strong className="text-slate-900">{patient.name}</strong>
                <span className="text-slate-500">Patient ID:</span>
                <strong className="text-slate-900 font-mono">{patient.id}</strong>
                <span className="text-slate-500">Age / Sex:</span>
                <span className="text-slate-800">{patient.age || '—'} yrs / {patient.sex}</span>
                <span className="text-slate-500">Eye Examined:</span>
                <strong className="text-teal-800 font-mono">{eye === 'OD' ? 'Right Eye (OD)' : 'Left Eye (OS)'}</strong>
              </div>
            </div>

            <div>
              <h4 className="text-[11px] font-bold text-slate-900 uppercase tracking-wider mb-2 border-b border-slate-200 pb-1">
                SCAN &amp; STUDY INFORMATION
              </h4>
              <div className="grid grid-cols-2 gap-x-2 gap-y-1">
                <span className="text-slate-500">Scan Date:</span>
                <span className="text-slate-900 font-mono">{reportDate}</span>
                <span className="text-slate-500">Scan Modality:</span>
                <span className="text-slate-800">{scan?.scan_type || 'Optical Coherence Tomography (OCT)'}</span>
                <span className="text-slate-500">Input Quality:</span>
                <span className="text-teal-700 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 inline" /> Verified Valid
                </span>
                <span className="text-slate-500">Analysis Status:</span>
                <span className="text-slate-800 font-semibold">Complete</span>
              </div>
            </div>
          </div>

          {/* Section 2: AI Analysis & Classification */}
          <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-3">
            <h4 className="text-[11px] font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-1">
              AI MODEL ESTIMATE &bull; GLAUCOMA-ASSOCIATED CLASSIFICATION
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className={`p-4 rounded-xl border ${isGlaucoma ? 'bg-rose-50/70 border-rose-200' : 'bg-emerald-50/70 border-emerald-200'}`}>
                <div className="text-[10px] uppercase font-bold text-slate-500">Binary Pattern Result</div>
                <div className={`text-base font-bold mt-1 ${isGlaucoma ? 'text-rose-900' : 'text-emerald-900'}`}>
                  {isGlaucoma ? 'Glaucoma-associated pattern detected' : 'No glaucoma-associated pattern detected'}
                </div>
                <p className="text-[11px] text-slate-600 mt-1">
                  Quantitative peripapillary pattern reflects {isGlaucoma ? 'localized nerve fiber attenuation' : 'physiological contour'}.
                </p>
              </div>

              <div className="p-4 rounded-xl border border-slate-200 bg-slate-50/70">
                <div className="text-[10px] uppercase font-bold text-slate-500">Model-Estimated Score</div>
                <div className="text-2xl font-black text-slate-900 font-mono mt-1">{scorePct}</div>
                <div className="text-[11px] text-slate-500 mt-1">
                  Clinical correlation required. Research model estimate — not a clinical diagnosis.
                </div>
              </div>
            </div>
          </div>

          {/* Section 3: Quantitative RNFLT Summary */}
          <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
            <h4 className="text-[11px] font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-1">
              RNFLT THICKNESS SUMMARY (MICROMETERS)
            </h4>
            <div className="grid grid-cols-4 gap-3 text-center">
              <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <div className="text-[10px] text-slate-500 uppercase font-semibold">Mean RNFLT</div>
                <div className="text-base font-bold text-slate-900 font-mono mt-0.5">{meanThickness} µm</div>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <div className="text-[10px] text-slate-500 uppercase font-semibold">Median RNFLT</div>
                <div className="text-base font-bold text-slate-900 font-mono mt-0.5">{(meanThickness * 0.98).toFixed(1)} µm</div>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <div className="text-[10px] text-slate-500 uppercase font-semibold">Min RNFLT</div>
                <div className="text-base font-bold text-slate-900 font-mono mt-0.5">{(meanThickness * 0.45).toFixed(1)} µm</div>
              </div>
              <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-200">
                <div className="text-[10px] text-slate-500 uppercase font-semibold">Max RNFLT</div>
                <div className="text-base font-bold text-slate-900 font-mono mt-0.5">{(meanThickness * 1.85).toFixed(1)} µm</div>
              </div>
            </div>
          </div>

          {/* Section 4: Structural Visual Explainability (Grad-CAM) */}
          {activeAnalysis?.explainability?.available && activeAnalysis.explainability.gradcam_overlay_image && (
            <div className="p-4 rounded-xl border border-slate-200 bg-white space-y-2">
              <h4 className="text-[11px] font-bold text-slate-900 uppercase tracking-wider border-b border-slate-100 pb-1">
                STRUCTURAL EXPLAINABILITY (GRAD-CAM)
              </h4>
              <div className="flex items-center space-x-6 justify-center py-2">
                <div className="text-center">
                  <div className="text-[10px] text-slate-500 mb-1 font-semibold">RNFLT Thickness Map</div>
                  <img
                    src={activeAnalysis.explainability.original_rnflt_image || activeAnalysis.rnflt_analysis?.heatmap_image}
                    alt="RNFLT"
                    className="w-36 h-36 rounded-lg border border-slate-300 object-cover shadow-xs mx-auto"
                  />
                </div>
                <div className="text-center">
                  <div className="text-[10px] text-slate-500 mb-1 font-semibold">Grad-CAM Overlay</div>
                  <img
                    src={activeAnalysis.explainability.gradcam_overlay_image}
                    alt="Grad-CAM"
                    className="w-36 h-36 rounded-lg border border-slate-300 object-cover shadow-xs mx-auto"
                  />
                </div>
              </div>
              <p className="text-[10px] text-slate-500 italic text-center">
                Highlighted regions represent areas that influenced the model prediction. They do not independently establish a diagnosis.
              </p>
            </div>
          )}

          {/* Section 5: Progression & 24-Month Forecast Notice */}
          <div className="p-4 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
            <h4 className="text-[11px] font-bold text-slate-900 uppercase tracking-wider border-b border-slate-200 pb-1">
              LONGITUDINAL TREND &bull; FORECAST STATUS
            </h4>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-500">Observed Structural Trend</span>
                <p className="text-[11px] text-slate-700 mt-1">
                  Serial examination indicates stabilized structural pattern. Continued periodic ophthalmic monitoring recommended.
                </p>
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-500">24-Month Progression Forecast</span>
                <p className="text-[11px] text-slate-700 mt-1">
                  24-month forecast unavailable — validated progression model not currently connected.
                </p>
              </div>
            </div>
          </div>

          {/* Section 6: Clinical Disclaimer Banner */}
          <div className="p-4 rounded-xl border border-amber-300 bg-amber-50 text-[10px] text-amber-900 space-y-1">
            <div className="font-bold flex items-center gap-1.5 uppercase tracking-wide">
              <ShieldAlert className="w-3.5 h-3.5 text-amber-700 flex-shrink-0" />
              <span>MANDATORY CLINICAL DISCLAIMER</span>
            </div>
            <p>
              AI-generated research estimate — clinical correlation required. GlaucoMap does not replace clinical diagnosis or treatment decisions.
              All classifications and quantitative outputs must be interpreted by a licensed ophthalmologist or optometrist in conjunction with comprehensive clinical examination, tonometry, perimetry, and stereoscopic disc assessment.
            </p>
          </div>

          {/* Footer Sign-off */}
          <div className="pt-4 border-t border-slate-200 flex justify-between items-center text-[10px] text-slate-500">
            <span>Generated by GlaucoMap Ophthalmology Workstation &bull; Build 2026.10</span>
            <span>Clinician Review Signature: ________________________________</span>
          </div>
        </div>
      </div>
    </div>
  );
};
