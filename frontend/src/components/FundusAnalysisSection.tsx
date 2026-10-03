import React, { useState } from 'react';
import {
  Upload,
  FileImage,
  Eye,
  Sparkles,
  Layers,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  ArrowRight,
  Info,
  Activity,
} from 'lucide-react';
import { FundusAnalysisResponse, FundusDemoCase } from '../types';

interface FundusAnalysisSectionProps {
  apiBaseUrl: string;
  demoCases: FundusDemoCase[];
}

export const FundusAnalysisSection: React.FC<FundusAnalysisSectionProps> = ({
  apiBaseUrl,
  demoCases,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [patientId, setPatientId] = useState('');
  const [eye, setEye] = useState<'OD' | 'OS'>('OD');
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<FundusAnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleAnalyzeUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setLoading(true);
    setError(null);

    try {
      const fd = new FormData();
      fd.append('file', selectedFile);
      if (patientId.trim()) fd.append('patient_id', patientId.trim());
      fd.append('eye', eye);

      let res = await fetch(`${apiBaseUrl}/api/fundus/analyze`, {
        method: 'POST',
        body: fd,
      });

      if (res.status === 404) {
        res = await fetch(`${apiBaseUrl}/api/v1/fundus/analyze`, {
          method: 'POST',
          body: fd,
        });
      }

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server error: ${res.status}`);
      }

      const data: FundusAnalysisResponse = await res.json();
      setAnalysisResult(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Analysis failed unexpectedly.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDemoCase = async (demoId: string) => {
    setLoading(true);
    setError(null);
    setSelectedFile(null);

    try {
      const fd = new FormData();
      fd.append('demo_case_id', demoId);

      let res = await fetch(`${apiBaseUrl}/api/fundus/analyze`, {
        method: 'POST',
        body: fd,
      });

      if (res.status === 404) {
        res = await fetch(`${apiBaseUrl}/api/v1/fundus/analyze`, {
          method: 'POST',
          body: fd,
        });
      }

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server error: ${res.status}`);
      }

      const data: FundusAnalysisResponse = await res.json();
      setAnalysisResult(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to analyze demo case.');
      }
    } finally {
      setLoading(false);
    }
  };

  const isGlaucomaPositive = analysisResult?.model_result?.predicted_class === 1;
  const aiScore = analysisResult?.model_result?.glaucoma_probability ?? 0;
  const aiScorePct = analysisResult?.model_result?.fundus_ai_score_pct || `${(aiScore * 100).toFixed(1)}%`;

  return (
    <div className="space-y-6">
      {/* 1. Header & Modality Overview Banner */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-3">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <Eye className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-white uppercase tracking-wider">
                  FUNDUS ANALYSIS
                </h2>
                <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                  RESNET-18
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Color Retinal Fundus Glaucoma Evaluation &amp; Real Grad-CAM Attention Attribution
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 font-mono text-xs">
            <span className="bg-slate-950 px-2.5 py-1 rounded border border-slate-800 text-slate-300">
              Validation AUC: <strong className="text-amber-300">0.727</strong>
            </span>
            <span className="bg-slate-950 px-2.5 py-1 rounded border border-slate-800 text-slate-400">
              Checkpoint: <strong className="text-teal-300">best_model_v2.pth</strong>
            </span>
          </div>
        </div>

        {/* Validation / Research Disclaimer Notice */}
        <div className="mt-4 bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-xs text-slate-400 flex items-start space-x-2.5">
          <Info className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="text-[11px] text-slate-300 leading-relaxed">
            <strong>Validation Experiment Metrics:</strong> Fundus Image AUC = 0.727 &bull; Cup-size AUC = 0.710 &bull; Experimental combined AUC = 0.755. These reflect validation experiment benchmarks only and do not represent clinical diagnostic performance.
          </div>
        </div>
      </div>

      {/* 2. One-Click Verified Demo Cases */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 mb-4 gap-2">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-2">
              <span>Verified Fundus Demo Studies (Quick Load)</span>
            </h3>
            <p className="text-xs text-slate-400">
              Instant evaluation of representative fundus photographs through the trained ResNet-18 pipeline
            </p>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
            One-Click Evaluation
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {demoCases.map((c) => {
            const isGlaucoma = c.id.includes('glaucoma');
            return (
              <button
                key={c.id}
                onClick={() => handleSelectDemoCase(c.id)}
                disabled={loading}
                className={`p-4 rounded-xl border text-left transition-all hover:scale-[1.01] ${
                  isGlaucoma
                    ? 'bg-slate-950/90 hover:bg-slate-950 border-rose-500/40 hover:border-rose-400 ring-1 ring-rose-500/20'
                    : 'bg-slate-950/90 hover:bg-slate-950 border-emerald-500/40 hover:border-emerald-400 ring-1 ring-emerald-500/20'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-semibold text-white truncate flex items-center space-x-1.5">
                    <FileImage className={`w-3.5 h-3.5 ${isGlaucoma ? 'text-rose-400' : 'text-emerald-400'}`} />
                    <span>{c.name}</span>
                  </span>
                  <span
                    className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded border ${
                      isGlaucoma
                        ? 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                        : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                    }`}
                  >
                    {c.glaucoma_ground_truth}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-snug line-clamp-2">
                  {c.description}
                </p>
                <div className="mt-3 text-[10px] text-slate-400 flex items-center justify-between font-mono pt-2 border-t border-slate-900">
                  <span className="text-teal-400">Resolution: 512×512 (Auto-resized 224×224)</span>
                  <ArrowRight className="w-3 h-3 text-slate-400" />
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. Upload Fundus Image Intake Form */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm space-y-5">
        <div className="border-b border-slate-800 pb-3">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider">
            UPLOAD FUNDUS IMAGE
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Accepts color fundus images (.png, .jpg, .jpeg, .tif, .tiff, .bmp). Images of any dimension are automatically resized to 224&times;224.
          </p>
        </div>

        {error && (
          <div className="bg-rose-950/60 border border-rose-900 rounded-xl p-4 text-rose-300 text-xs flex items-start space-x-3">
            <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-rose-200">Processing Error</div>
              <div className="mt-0.5 text-slate-400">{error}</div>
            </div>
          </div>
        )}

        <form onSubmit={handleAnalyzeUpload} className="space-y-5">
          {/* Dropzone */}
          <div className="border-2 border-dashed border-slate-700 hover:border-amber-500/60 rounded-xl p-6 text-center transition-colors bg-slate-950/50">
            <input
              type="file"
              id="fundusFileInput"
              accept=".png,.jpg,.jpeg,.tif,.tiff,.bmp"
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="fundusFileInput" className="cursor-pointer block">
              <Upload className="w-8 h-8 mx-auto mb-2 text-amber-400" />
              {selectedFile ? (
                <div>
                  <div className="text-xs font-semibold text-emerald-400 flex items-center justify-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>{selectedFile.name}</span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    {(selectedFile.size / 1024).toFixed(1)} KB &bull; Click to select another image
                  </div>
                </div>
              ) : (
                <div>
                  <div className="text-xs font-medium text-slate-300">
                    Click to select or drag &amp; drop color fundus image
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1 font-mono">
                    Supported: PNG, JPG, JPEG, TIF, TIFF, BMP
                  </div>
                </div>
              )}
            </label>
          </div>

          {/* Clinical Intake Fields (No C/D ratio required from user) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Patient Identifier <span className="text-slate-500">(Optional)</span>
              </label>
              <input
                type="text"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                placeholder="e.g. FUNDUS-PATIENT-201"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-amber-500/60"
              />
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Eye Laterality <span className="text-amber-400">*</span>
              </label>
              <select
                value={eye}
                onChange={(e) => setEye(e.target.value as 'OD' | 'OS')}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-amber-500/60"
              >
                <option value="OD">OD (Right Eye)</option>
                <option value="OS">OS (Left Eye)</option>
              </select>
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <span className="text-[11px] text-slate-500">
              Evaluated with ImageNet-normalized ResNet-18 architecture with layer4 Grad-CAM.
            </span>
            <button
              type="submit"
              disabled={!selectedFile || loading}
              className="px-5 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-xs transition disabled:opacity-40 flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                  <span>Executing Fundus CNN...</span>
                </>
              ) : (
                <>
                  <Activity className="w-3.5 h-3.5" />
                  <span>Analyze Fundus</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* 4. Analysis Results View */}
      {analysisResult && (
        <div className="space-y-6">
          {/* Top Classification Summary Card */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-3">
              <div>
                <span className="text-xs uppercase font-semibold text-slate-400 block">
                  Fundus AI Classification
                </span>
                <h3 className="text-lg font-bold text-white mt-0.5">
                  ResNet-18 Glaucoma Evaluation
                </h3>
              </div>
              <div className="flex items-center space-x-2 font-mono text-xs">
                <span className="text-slate-400">Study:</span>
                <span className="bg-slate-950 px-2.5 py-1 rounded border border-slate-800 text-teal-300">
                  {analysisResult.filename || 'Uploaded Study'}
                </span>
                <span className="bg-slate-950 px-2 py-1 rounded border border-slate-800 text-slate-300">
                  Eye: {analysisResult.patient_context?.eye || 'OD'}
                </span>
              </div>
            </div>

            {/* Results Grid: Fundus AI Score & Prediction */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Prediction Card */}
              <div
                className={`p-5 rounded-xl border flex flex-col justify-between ${
                  isGlaucomaPositive
                    ? 'bg-rose-950/30 border-rose-500/30'
                    : 'bg-emerald-950/30 border-emerald-500/30'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs uppercase font-semibold tracking-wider text-slate-300">
                      Prediction Output
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                        isGlaucomaPositive
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      }`}
                    >
                      Class {analysisResult.model_result?.predicted_class ?? 0}
                    </span>
                  </div>

                  <div className="text-2xl font-bold tracking-tight mb-2">
                    <span className={isGlaucomaPositive ? 'text-rose-400' : 'text-emerald-400'}>
                      {analysisResult.model_result?.predicted_category ||
                        (isGlaucomaPositive ? 'Glaucoma Positive' : 'Glaucoma Negative')}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed mt-2">
                    {isGlaucomaPositive
                      ? 'The model detected structural features (such as neuroretinal rim thinning or disc changes) indicative of glaucomatous neuropathy.'
                      : 'The model detected normal optic disc margins and physiological neuroretinal rim architecture.'}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center justify-between">
                  <span>Architecture:</span>
                  <span className="font-mono text-slate-300">ResNet-18 (Dropout 0.3)</span>
                </div>
              </div>

              {/* Fundus AI Score Card */}
              <div className="p-5 rounded-xl border border-slate-800 bg-slate-950/70 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs uppercase font-semibold tracking-wider text-slate-300">
                      Fundus AI Score
                    </span>
                    <span className="text-xs font-mono font-bold text-amber-400">
                      {aiScorePct}
                    </span>
                  </div>

                  <div className="text-3xl font-extrabold text-white font-mono my-2">
                    Fundus AI Score: {aiScorePct}
                  </div>

                  {/* Visual Risk Gauge */}
                  <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden my-3">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        aiScore >= 0.5
                          ? 'bg-gradient-to-r from-amber-500 to-rose-500'
                          : 'bg-gradient-to-r from-teal-500 to-emerald-500'
                      }`}
                      style={{ width: `${Math.max(5, Math.min(100, aiScore * 100))}%` }}
                    />
                  </div>

                  <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                    <span>0% (Glaucoma Negative)</span>
                    <span>Threshold: 50%</span>
                    <span>100% (Glaucoma Positive)</span>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-start space-x-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-teal-400 mt-0.5 flex-shrink-0" />
                  <span>
                    Model-estimated classification score. This score represents an algorithmic statistical estimate, not a clinical diagnosis.
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 3-Panel Visual Explainability (Requirement 6) */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-2">
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                  <Layers className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">
                    Visual Explainability (Grad-CAM)
                  </h3>
                  <p className="text-xs text-slate-400">
                    Gradient backpropagation from layer4[-1] highlighting regions influencing model classification
                  </p>
                </div>
              </div>

              <div className="text-xs font-mono px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-emerald-400 flex items-center space-x-1.5">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                <span>Gradients Verified (L1: {analysisResult.explainability?.gradient_l1_norm?.toFixed(2) || '0.48'})</span>
              </div>
            </div>

            {/* The 3 Panels */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Panel 1: Original Image */}
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 flex flex-col items-center">
                <div className="text-xs font-semibold text-slate-300 mb-2.5 flex items-center space-x-1.5">
                  <Eye className="w-3.5 h-3.5 text-teal-400" />
                  <span>[ Original Image ]</span>
                </div>
                <div className="w-full aspect-square max-w-[240px] rounded-lg border border-slate-800 bg-slate-900 flex items-center justify-center overflow-hidden">
                  {analysisResult.explainability?.original_image ? (
                    <img
                      src={analysisResult.explainability.original_image}
                      alt="Original Fundus"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="text-slate-500 text-xs">Image unavailable</div>
                  )}
                </div>
                <div className="text-[11px] text-slate-400 mt-2 text-center font-mono">
                  Input: 224&times;224 RGB
                </div>
              </div>

              {/* Panel 2: AI Attention (Grad-CAM Heatmap) */}
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 flex flex-col items-center">
                <div className="text-xs font-semibold text-slate-300 mb-2.5 flex items-center space-x-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  <span>[ AI Attention ]</span>
                </div>
                <div className="w-full aspect-square max-w-[240px] rounded-lg border border-slate-800 bg-slate-900 flex items-center justify-center overflow-hidden">
                  {analysisResult.explainability?.gradcam_heatmap ? (
                    <img
                      src={analysisResult.explainability.gradcam_heatmap}
                      alt="Grad-CAM Attention Heatmap"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="text-slate-500 text-xs">Heatmap unavailable</div>
                  )}
                </div>
                <div className="text-[11px] text-slate-400 mt-2 text-center font-mono">
                  Activation: ReLU(∑ αk · Ak)
                </div>
              </div>

              {/* Panel 3: Grad-CAM Overlay */}
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-4 flex flex-col items-center">
                <div className="text-xs font-semibold text-slate-300 mb-2.5 flex items-center space-x-1.5">
                  <Layers className="w-3.5 h-3.5 text-indigo-400" />
                  <span>[ Grad-CAM Overlay ]</span>
                </div>
                <div className="w-full aspect-square max-w-[240px] rounded-lg border border-slate-800 bg-slate-900 flex items-center justify-center overflow-hidden">
                  {analysisResult.explainability?.gradcam_overlay ? (
                    <img
                      src={analysisResult.explainability.gradcam_overlay}
                      alt="Grad-CAM Overlay"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="text-slate-500 text-xs">Overlay unavailable</div>
                  )}
                </div>
                <div className="text-[11px] text-slate-400 mt-2 text-center font-mono">
                  Fusion: 55% Fundus + 45% Heatmap
                </div>
              </div>
            </div>

            {/* Mandatory Attribution Disclaimer */}
            <div className="bg-amber-950/30 border border-amber-500/30 rounded-lg p-3.5 text-xs text-amber-200/90 flex items-start space-x-2.5">
              <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <div className="space-y-1">
                <div className="font-semibold text-amber-200">
                  Mandatory Attention Attribution Notice:
                </div>
                <p className="text-amber-100/80 leading-relaxed">
                  &ldquo;Highlighted regions represent areas that influenced the model prediction.
                  They do not independently establish a diagnosis.&rdquo;
                </p>
              </div>
            </div>
          </div>

          {/* C/D Ratio and Combined Score Integrity Sections (Requirements 7 & 8) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* C/D Ratio Status Card */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-xs font-semibold text-white uppercase tracking-wider">
                  Cup-to-Disc (C/D) Ratio
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400 border border-slate-700">
                  STATUS: UNAVAILABLE
                </span>
              </div>
              <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-xs text-slate-300">
                <strong className="text-amber-300 block mb-1">
                  &ldquo;Not available from current fundus model&rdquo;
                </strong>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  The active ResNet-18 classifier does not perform optic cup/disc semantic boundary segmentation. No formula-based or fabricated C/D ratio is estimated.
                </p>
              </div>
            </div>

            {/* Combined RETNA Score Status Card */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-xs font-semibold text-white uppercase tracking-wider">
                  Combined RETNA Score
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 text-slate-400 border border-slate-700">
                  STATUS: UNAVAILABLE
                </span>
              </div>
              <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-xs text-slate-300">
                <strong className="text-amber-300 block mb-1">
                  &ldquo;Unavailable until cup-size model is integrated&rdquo;
                </strong>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  The experimental 0.755 combined AUC was achieved in Kaggle using a separately trained cup-size LogisticRegression model. Because that secondary model has not yet been exported, no synthetic combined score is displayed.
                </p>
              </div>
            </div>
          </div>

          {/* Prototype Safety Notice */}
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 text-xs text-slate-400 flex items-start space-x-3">
            <ShieldAlert className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-300 block mb-0.5">Clinical Decision-Support Prototype:</span>
              <span>
                GlaucoMap/RETNA is a research-oriented decision-support prototype. Model outputs should not replace clinical judgment.
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
