import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { QualityControlCard } from './components/QualityControlCard';
import { RNFLTAnalysisCard } from './components/RNFLTAnalysisCard';
import { ModelStatusSection } from './components/ModelStatusSection';
import { ExplainabilitySection } from './components/ExplainabilitySection';
import { ProgressionForecastSection } from './components/ProgressionForecastSection';
import { SafetyLayerCard } from './components/SafetyLayerCard';
import { ImportSection } from './components/ImportSection';
import { OCTAnalysisResponse, DemoCase, BackendModelStatus } from './types';
import { AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [backendConnected, setBackendConnected] = useState<boolean>(false);
  const [backendChecking, setBackendChecking] = useState<boolean>(false);
  const [modelStatus, setModelStatus] = useState<BackendModelStatus | null>(null);
  const [demoCases, setDemoCases] = useState<DemoCase[]>([]);
  const [currentAnalysis, setCurrentAnalysis] = useState<OCTAnalysisResponse | null>(null);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [globalError, setGlobalError] = useState<string | null>(null);

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // 1. Check Backend Health & Fetch Model Status + Demo Cases
  const refreshSystem = useCallback(async () => {
    setBackendChecking(true);
    setGlobalError(null);

    try {
      // Check /health
      const healthRes = await fetch(`${apiBaseUrl}/health`);
      if (healthRes.ok) {
        setBackendConnected(true);
      } else {
        setBackendConnected(false);
      }

      // Fetch model status
      try {
        const modelRes = await fetch(`${apiBaseUrl}/api/v1/model/status`);
        if (modelRes.ok) {
          const mData: BackendModelStatus = await modelRes.json();
          setModelStatus(mData);
        }
      } catch (e) {
        console.warn('Model status fetch failed:', e);
      }

      // Fetch demo cases
      try {
        const demoRes = await fetch(`${apiBaseUrl}/api/v1/oct/demo-cases`);
        if (demoRes.ok) {
          const dData: DemoCase[] = await demoRes.json();
          setDemoCases(dData);
        }
      } catch (e) {
        console.warn('Demo cases fetch failed:', e);
      }
    } catch (err: unknown) {
      setBackendConnected(false);
      if (err instanceof Error) {
        setGlobalError(`Backend connection failed: ${err.message}`);
      } else {
        setGlobalError('Unable to connect to GlaucoMap backend.');
      }
    } finally {
      setBackendChecking(false);
    }
  }, [apiBaseUrl]);

  // 2. Analyze Uploaded FormData
  const handleAnalyze = async (formData: FormData) => {
    setAnalyzing(true);
    setGlobalError(null);

    try {
      const response = await fetch(`${apiBaseUrl}/api/v1/oct/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server returned error ${response.status}`);
      }

      const data: OCTAnalysisResponse = await response.json();
      setCurrentAnalysis(data);
      setActiveTab('dashboard'); // Switch to analysis view
    } catch (err: unknown) {
      if (err instanceof Error) {
        setGlobalError(err.message);
      } else {
        setGlobalError('Analysis failed unexpectedly.');
      }
    } finally {
      setAnalyzing(false);
    }
  };

  // 3. Quick Load Demo Case
  const handleSelectDemoCase = async (demoId: string) => {
    const fd = new FormData();
    fd.append('demo_case_id', demoId);
    await handleAnalyze(fd);
  };

  // Initial load
  useEffect(() => {
    refreshSystem();
  }, [refreshSystem]);

  // Once backend is confirmed connected, auto-load first demo case if no analysis is present
  useEffect(() => {
    if (backendConnected && !currentAnalysis && demoCases.length > 0) {
      handleSelectDemoCase(demoCases[0].id);
    }
  }, [backendConnected, demoCases]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between selection:bg-teal-500 selection:text-white font-sans antialiased">
      {/* Navigation Header */}
      <Header
        backendConnected={backendConnected}
        backendChecking={backendChecking}
        gpuName={modelStatus?.hardware.gpu_name || 'NVIDIA RTX 4050 (6GB)'}
        onRefresh={refreshSystem}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      {/* Main Container */}
      <main className="max-w-7xl mx-auto w-full px-4 sm:px-6 py-8 flex-1 space-y-6">
        {/* Global Error Banner */}
        {globalError && (
          <div className="bg-rose-950/60 border border-rose-900 rounded-xl p-4 text-rose-300 text-xs flex items-start space-x-3 shadow-sm">
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-rose-200">System Notification</div>
              <div className="mt-0.5 text-slate-400">{globalError}</div>
            </div>
          </div>
        )}

        {/* VIEW 1: MAIN DASHBOARD & RECENT ANALYSIS */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Top Quick Status Bar */}
            <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-center space-x-2">
                <span className="text-slate-400">Active Study:</span>
                <span className="font-semibold text-white font-mono bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                  {currentAnalysis?.patient_context?.patient_id || 'Awaiting Study'}
                </span>
                <span className="text-slate-400 ml-2">Eye:</span>
                <span className="font-semibold text-teal-400 font-mono">
                  {currentAnalysis?.patient_context?.eye || 'OD'}
                </span>
              </div>

              <div className="flex items-center space-x-3 text-slate-400">
                <span>
                  Validation:{' '}
                  <strong className={currentAnalysis?.status === 'PASS' ? 'text-emerald-400' : 'text-rose-400'}>
                    {currentAnalysis?.quality_status || 'Pending'}
                  </strong>
                </span>
                <span>&bull;</span>
                <span>
                  Model:{' '}
                  <strong className="text-amber-400 font-normal">
                    Training Pending
                  </strong>
                </span>
                <button
                  onClick={() => setActiveTab('import')}
                  className="px-2.5 py-1 rounded bg-teal-500/10 text-teal-300 hover:bg-teal-500/20 border border-teal-500/30 transition text-[11px] font-medium"
                >
                  Import New Study
                </button>
              </div>
            </div>

            {/* Quality Control Card */}
            {currentAnalysis && (
              <QualityControlCard
                status={currentAnalysis.status}
                qualityStatus={currentAnalysis.quality_status}
                message={currentAnalysis.message}
                checks={currentAnalysis.validation_checks}
                issues={currentAnalysis.issues}
              />
            )}

            {/* RNFLT Quantitative Map Visualization */}
            {currentAnalysis?.is_valid && (
              <RNFLTAnalysisCard
                analysis={currentAnalysis.rnflt_analysis}
                patientId={currentAnalysis.patient_context?.patient_id}
                eye={currentAnalysis.patient_context?.eye}
              />
            )}

            {/* AI Model Status & Flowchart */}
            <ModelStatusSection modelStatus={modelStatus} />

            {/* Explainability (Grad-CAM Preparation) */}
            <ExplainabilitySection
              originalHeatmap={currentAnalysis?.rnflt_analysis?.heatmap_image}
            />

            {/* Progression Forecasting (Longitudinal) */}
            <ProgressionForecastSection />

            {/* Safety & Clinical Validation Layer */}
            <SafetyLayerCard audit={currentAnalysis?.safety_layer} />
          </div>
        )}

        {/* VIEW 2: IMPORT OCT STUDY */}
        {activeTab === 'import' && (
          <div className="space-y-6">
            <ImportSection
              onAnalyze={handleAnalyze}
              onSelectDemoCase={handleSelectDemoCase}
              demoCases={demoCases}
              loading={analyzing}
            />
          </div>
        )}

        {/* VIEW 3: AI MODEL DETAILS */}
        {activeTab === 'model' && (
          <div className="space-y-6">
            <ModelStatusSection modelStatus={modelStatus} />
            <ExplainabilitySection
              originalHeatmap={currentAnalysis?.rnflt_analysis?.heatmap_image}
            />
          </div>
        )}

        {/* VIEW 4: SAFETY & GOVERNANCE */}
        {activeTab === 'safety' && (
          <div className="space-y-6">
            <SafetyLayerCard audit={currentAnalysis?.safety_layer} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/60 py-4 px-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>GlaucoMap &copy; 2026 &bull; AI-Assisted Glaucoma Progression Mapping</span>
          <span className="text-[11px] text-slate-600">
            Research Demonstrator &bull; 10 PM Checkpoint Prototype &bull; Not for Clinical Diagnostic Use
          </span>
        </div>
      </footer>
    </div>
  );
};

export default App;
