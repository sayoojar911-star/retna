import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { ClinicalDashboard } from './components/ClinicalDashboard';
import { PatientProfile } from './components/PatientProfile';
import { ScansLibrary } from './components/ScansLibrary';
import { ReportsLibrary } from './components/ReportsLibrary';
import { DemoCasesPage } from './components/DemoCasesPage';
import { RegisterPatientModal } from './components/RegisterPatientModal';
import { ImportScanModal } from './components/ImportScanModal';
import { SettingsModal } from './components/SettingsModal';
import { AddIOPModal } from './components/AddIOPModal';
import { AddVisualFieldModal } from './components/AddVisualFieldModal';
import { AddReportModal } from './components/AddReportModal';
import { QualityControlCard } from './components/QualityControlCard';
import { ModelResultCard } from './components/ModelResultCard';
import { RNFLTAnalysisCard } from './components/RNFLTAnalysisCard';
import { ExplainabilitySection } from './components/ExplainabilitySection';
import { RawOctResultCard } from './components/RawOctResultCard';
import { ReferenceOctResultCard } from './components/ReferenceOctResultCard';
import { SafetyLayerCard } from './components/SafetyLayerCard';
import { StructuralAIPipelineStatus } from './components/StructuralAIPipelineStatus';
import { ModelInfoPanel } from './components/ModelInfoPanel';
import { AIModuleStatusCard } from './components/AIModuleStatusCard';
import {
  OCTAnalysisResponse,
  BackendModelStatus,
  ClinicalPatient,
  ClinicalScan,
  ClinicalReport,
} from './types';
import { AlertCircle, Upload, Sparkles } from 'lucide-react';
import { ProgressionRiskCard } from './components/ProgressionRiskCard';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('patients');
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Clinical data states
  const [patients, setPatients] = useState<ClinicalPatient[]>([]);
  const [scans, setScans] = useState<ClinicalScan[]>([]);
  const [reports, setReports] = useState<ClinicalReport[]>([]);

  // System and analysis states
  const [backendConnected, setBackendConnected] = useState<boolean>(false);
  const [modelStatus, setModelStatus] = useState<BackendModelStatus | null>(null);
  const [currentAnalysis, setCurrentAnalysis] = useState<OCTAnalysisResponse | null>(null);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [globalError, setGlobalError] = useState<string | null>(null);

  // Modal controls
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState<boolean>(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState<boolean>(false);
  const [importInitialPatientId, setImportInitialPatientId] = useState<string | undefined>(undefined);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState<boolean>(false);
  const [isIopModalOpen, setIsIopModalOpen] = useState<boolean>(false);
  const [isVfModalOpen, setIsVfModalOpen] = useState<boolean>(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState<boolean>(false);
  const [modalTargetPatientId, setModalTargetPatientId] = useState<string>('GM-DEMO-01');

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  const [diagnostics, setDiagnostics] = useState<{ two_stage_architecture?: { sam2_base: string; mgu: string; rnflt_resnet: string; end_to_end_raw_oct: string } } | null>(null);

  // 1. Fetch Clinical Data and System Status
  const refreshSystem = useCallback(async () => {
    setGlobalError(null);

    try {
      // Check /health
      const healthRes = await fetch(`${apiBaseUrl}/health`);
      setBackendConnected(healthRes.ok);

      // Fetch patients
      try {
        const patRes = await fetch(`${apiBaseUrl}/api/patients`).catch(() =>
          fetch(`${apiBaseUrl}/api/clinical/patients`)
        );
        if (patRes.ok) {
          const pData: ClinicalPatient[] = await patRes.json();
          setPatients(pData);
        }
      } catch (e) {
        console.warn('Patients fetch notice:', e);
      }

      // Fetch scans
      try {
        const scanRes = await fetch(`${apiBaseUrl}/api/scans`).catch(() =>
          fetch(`${apiBaseUrl}/api/clinical/scans`)
        );
        if (scanRes.ok) {
          const sData: ClinicalScan[] = await scanRes.json();
          setScans(sData);
        }
      } catch (e) {
        console.warn('Scans fetch notice:', e);
      }

      // Fetch reports
      try {
        const repRes = await fetch(`${apiBaseUrl}/api/reports`).catch(() =>
          fetch(`${apiBaseUrl}/api/clinical/reports`)
        );
        if (repRes.ok) {
          const rData: ClinicalReport[] = await repRes.json();
          setReports(rData);
        }
      } catch (e) {
        console.warn('Reports fetch notice:', e);
      }

      // Fetch model status
      try {
        const modelRes = await fetch(`${apiBaseUrl}/api/model/status`).catch(() =>
          fetch(`${apiBaseUrl}/api/v1/model/status`)
        );
        if (modelRes.ok) {
          const mData: BackendModelStatus = await modelRes.json();
          setModelStatus(mData);
        }
      } catch (e) {
        console.warn('Model status fetch notice:', e);
      }
      // Fetch diagnostics for pipeline status (SAM2/MGU/ResNet)
      try {
        const dRes = await fetch(`${apiBaseUrl}/api/model/diagnostics`).catch(() => fetch(`${apiBaseUrl}/api/v1/model/diagnostics`));
        if (dRes.ok) setDiagnostics(await dRes.json() as typeof diagnostics);
      } catch {}
    } catch (err: unknown) {
      setBackendConnected(false);
      if (err instanceof Error) {
        setGlobalError(`Backend service notice: ${err.message}`);
      } else {
        setGlobalError('Unable to connect to GlaucoMap backend.');
      }
    }
  }, [apiBaseUrl]);

  // Initial load
  useEffect(() => {
    refreshSystem();
  }, [refreshSystem]);

  // 2. Analyze Uploaded Study
  const handleAnalyze = async (formData: FormData) => {
    setAnalyzing(true);
    setGlobalError(null);
    // DEMO DATA SAFETY: Clear any previous analysis before running a new one
    // This prevents stale RNFLT / demo data from leaking between modalities
    setCurrentAnalysis(null);

    try {
      let response = await fetch(`${apiBaseUrl}/api/analyze`, {
        method: 'POST',
        body: formData,
      });

      if (response.status === 404) {
        response = await fetch(`${apiBaseUrl}/api/v1/oct/analyze`, {
          method: 'POST',
          body: formData,
        });
      }

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || `Server returned error ${response.status}`);
      }

      const data: OCTAnalysisResponse = await response.json();
      setCurrentAnalysis(data);
      setActiveTab('analysis'); // Switch cleanly to analysis view
      refreshSystem(); // Refresh clinical registries
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

  // 4. Select Scan for Analysis
  const handleSelectScanForAnalysis = async (scan: ClinicalScan) => {
    if (scan.demo_case_id) {
      await handleSelectDemoCase(scan.demo_case_id);
    } else {
      setActiveTab('analysis');
    }
  };

  // 5. Open Import Modal for Specific Patient
  const handleOpenImportModalForPatient = (patientId: string) => {
    setImportInitialPatientId(patientId);
    setIsImportModalOpen(true);
  };

  // Filtered patients for search query
  const displayedPatients = searchQuery
    ? patients.filter(
        (p) =>
          p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          p.id.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : patients;

  return (
    <div className="min-h-screen bg-slate-100/90 text-slate-800 flex flex-col justify-between font-sans antialiased selection:bg-teal-500 selection:text-white">
      {/* Top Application Bar */}
      <Header
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
          if (tab !== 'patients') {
            // keep state clean
          }
        }}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onOpenSettings={() => setIsSettingsModalOpen(true)}
        onQuickAction={() => setIsRegisterModalOpen(true)}
      />

      {/* Main Clinical Workspace Shell */}
      <main className="max-w-7xl mx-auto w-full px-4 sm:px-6 py-6 flex-1 space-y-6">
        {/* Global Error Banner */}
        {globalError && (
          <div className="bg-rose-50 border border-rose-200 rounded-2xl p-4 text-rose-800 text-xs flex items-start space-x-3 shadow-sm">
            <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-semibold text-rose-900">Workstation Notice</div>
              <div className="mt-0.5 text-slate-600">{globalError}</div>
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* 1. PATIENTS / HOME TIMELINE DASHBOARD                     */}
        {/* ========================================================= */}
        {activeTab === 'patients' && (
          <div>
            {selectedPatientId ? (
              <PatientProfile
                patientId={selectedPatientId}
                onBack={() => setSelectedPatientId(null)}
                onSelectScanForAnalysis={handleSelectScanForAnalysis}
                onOpenImportModalForPatient={handleOpenImportModalForPatient}
                apiBaseUrl={apiBaseUrl}
                activeAnalysis={currentAnalysis}
              />
            ) : (
              <ClinicalDashboard
                patients={displayedPatients}
                scans={scans}
                reports={reports}
                onSelectPatient={(pId) => setSelectedPatientId(pId)}
                onSelectScanForAnalysis={handleSelectScanForAnalysis}
                onOpenRegisterModal={() => setIsRegisterModalOpen(true)}
                onOpenImportModal={() => {
                  setImportInitialPatientId(undefined);
                  setIsImportModalOpen(true);
                }}
                onOpenAddIOPModal={(pId) => {
                  setModalTargetPatientId(pId || patients[0]?.id || 'GM-DEMO-01');
                  setIsIopModalOpen(true);
                }}
                onOpenAddVFModal={(pId) => {
                  setModalTargetPatientId(pId || patients[0]?.id || 'GM-DEMO-01');
                  setIsVfModalOpen(true);
                }}
                onOpenAddReportModal={(pId) => {
                  setModalTargetPatientId(pId || patients[0]?.id || 'GM-DEMO-01');
                  setIsReportModalOpen(true);
                }}
                onNavigateToDemoCases={() => setActiveTab('demo-cases')}
                onNavigateToProgression={() => setActiveTab('progression')}
              />
            )}
          </div>
        )}

        {/* ========================================================= */}
        {/* 2. SCANS LIBRARY                                          */}
        {/* ========================================================= */}
        {activeTab === 'scans' && (
          <ScansLibrary
            scans={scans}
            onOpenImportModal={() => {
              setImportInitialPatientId(undefined);
              setIsImportModalOpen(true);
            }}
            onSelectScanForAnalysis={handleSelectScanForAnalysis}
            onSelectPatient={(pId) => {
              setSelectedPatientId(pId);
              setActiveTab('patients');
            }}
          />
        )}

        {/* ========================================================= */}
        {/* 3. REPORTS LIBRARY                                        */}
        {/* ========================================================= */}
        {activeTab === 'reports' && (
          <ReportsLibrary
            reports={reports}
            patients={patients}
            onOpenAddReportModal={() => {
              setModalTargetPatientId(patients[0]?.id || 'GM-DEMO-01');
              setIsReportModalOpen(true);
            }}
            onSelectPatient={(pId) => {
              setSelectedPatientId(pId);
              setActiveTab('patients');
            }}
          />
        )}

        {/* ========================================================= */}
        {/* 4. AI STRUCTURAL ANALYSIS VIEW                            */}
        {/* ========================================================= */}
        {activeTab === 'analysis' && (
          <div className="space-y-6">
            {currentAnalysis ? (
              <>
                {/* Clinical Context Bar */}
                <div className="bg-white border border-slate-200 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs shadow-sm">
                  <div className="flex flex-wrap items-center gap-2">
                    {(() => {
                      const srcBadge = currentAnalysis.input_type === 'raw_oct' ? 'RAW OCT' : (currentAnalysis.input_type === 'rnflt_numeric' || currentAnalysis.rnflt_analysis) && (currentAnalysis as unknown as { input_source?:string}).input_source === 'demo_rnflt' ? 'DEMO RNFLT' : currentAnalysis.rnflt_analysis ? 'RNFLT structural classifier' : 'Awaiting study';
                      const srcTone = srcBadge === 'RAW OCT' ? 'bg-amber-100 text-amber-800 border-amber-200' : srcBadge === 'DEMO RNFLT' ? 'bg-teal-100 text-teal-800 border-teal-200' : 'bg-slate-100 text-slate-700 border-slate-200';
                      return <span className={`text-[10px] font-bold tracking-wider px-2.5 py-1 rounded-full border ${srcTone}`}>Input type: {srcBadge}</span>;
                    })()}
                    <span className="text-slate-500 font-medium">Modality:</span>
                    <span className="font-semibold text-slate-900 font-mono bg-slate-100 px-2.5 py-0.5 rounded-lg border border-slate-200">
                      {currentAnalysis.input_type_display ||
                        (currentAnalysis.input_type === 'raw_oct'
                          ? 'Raw / Digital OCT Study'
                          : currentAnalysis.input_type === 'rnflt_numeric' ? 'Harvard-GD RNFLT classifier — Quantitative 225×225 RNFLT map' : 'RNFLT structural classifier — 225×225 RNFLT map')}
                    </span>
                    <span className="text-slate-500 font-medium ml-2">Patient ID:</span>
                    <span className="font-semibold text-teal-800 font-mono bg-teal-50 px-2.5 py-0.5 rounded-lg border border-teal-200">
                      {currentAnalysis.patient_context?.patient_id || 'Awaiting Study'}
                    </span>
                    <span className="text-slate-500 font-medium ml-2">Eye:</span>
                    <span className="font-bold text-teal-800 font-mono">
                      {currentAnalysis.patient_context?.eye || 'OD'}
                    </span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setIsImportModalOpen(true)}
                      className="px-3.5 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-sm transition flex items-center space-x-1.5 cursor-pointer"
                    >
                      <Upload className="w-3.5 h-3.5" />
                      <span>Import Another Scan</span>
                    </button>
                  </div>
                </div>

                {/* Quality Verification Card */}
                <QualityControlCard
                  status={currentAnalysis.status}
                  qualityStatus={currentAnalysis.quality_status}
                  message={currentAnalysis.message}
                  checks={currentAnalysis.validation_checks}
                  issues={currentAnalysis.issues}
                />

                {/* Generate Report Button (RNFLT Path Only) */}
                {currentAnalysis.input_type !== 'raw_oct' && currentAnalysis.is_valid && (
                  <div className="flex flex-wrap items-center justify-end gap-2">
                    <button
                      onClick={() => setActiveTab('reports')}
                      className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs shadow-sm transition cursor-pointer"
                    >
                      Generate Report
                    </button>
                  </div>
                )}

                <StructuralAIPipelineStatus diagnostics={diagnostics} />

                <ModelInfoPanel />

                <AIModuleStatusCard modelStatus={modelStatus} diagnostics={diagnostics} />

                {/* Conditional Rendering — strict gate: raw_oct with unavailable extraction MUST NOT leak demo RNFLT */}
                {(() => {
                  if (currentAnalysis.input_type === 'reference_oct_rnflt') {
                    return <ReferenceOctResultCard analysis={currentAnalysis} />;
                  }
                  const isRawOctBlocked =
                    currentAnalysis.input_type === 'raw_oct' ||
                    currentAnalysis.ai_analysis?.rnflt_extraction?.available === false ||
                    currentAnalysis.model_result === null && !currentAnalysis.rnflt_analysis;
                  if (isRawOctBlocked && (currentAnalysis.input_type === 'raw_oct' || !currentAnalysis.rnflt_analysis)) {
                    return (
                      <RawOctResultCard
                        rawStudy={currentAnalysis.raw_oct_study}
                        aiAnalysis={currentAnalysis.ai_analysis}
                        patientContext={currentAnalysis.patient_context}
                        filename={currentAnalysis.filename}
                      />
                    );
                  }
                  return (
                    <>
                      <ModelResultCard
                        modelResult={currentAnalysis.model_result}
                        patientContext={currentAnalysis.patient_context}
                        groundTruth={currentAnalysis.research_ground_truth}
                        staging={currentAnalysis.staging}
                      />

                      {currentAnalysis.is_valid && currentAnalysis.rnflt_analysis && currentAnalysis.model_result && (
                        <RNFLTAnalysisCard
                          analysis={currentAnalysis.rnflt_analysis}
                          patientId={currentAnalysis.patient_context?.patient_id}
                          eye={currentAnalysis.patient_context?.eye}
                        />
                      )}

                      {currentAnalysis.rnflt_analysis && (
                        <ExplainabilitySection
                          originalHeatmap={currentAnalysis.rnflt_analysis?.heatmap_image}
                          explainability={currentAnalysis.explainability}
                        />
                      )}

                      {currentAnalysis.safety_layer && <SafetyLayerCard audit={currentAnalysis.safety_layer} />}
                    </>
                  );
                })()}
              </>
            ) : (
              /* Empty Analysis State */
              <div className="p-12 border border-slate-200 rounded-2xl text-center bg-white space-y-4 shadow-sm">
                <Sparkles className="w-10 h-10 text-teal-600 mx-auto" />
                <h3 className="text-base font-bold text-slate-900">No Scan Currently in Active Analysis</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                  Select a research demo study or import a clinical OCT scan to run real-time
                  structural classification and Grad-CAM visual explainability.
                </p>
                <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
                  <button
                    onClick={() => setActiveTab('demo-cases')}
                    className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs shadow-sm transition cursor-pointer"
                  >
                    Select a Demo Case
                  </button>
                  <button
                    onClick={() => setIsImportModalOpen(true)}
                    className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 font-medium text-xs transition flex items-center space-x-1.5 cursor-pointer"
                  >
                    <Upload className="w-3.5 h-3.5" />
                    <span>Import OCT Scan</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* =========================================================
        {/* NOTE: ProgressionRiskCard is rendered only on the 'progression' tab
             to keep it clearly separate from the structural analysis tab.
             This enforces the rule: never combine p_glaucoma with progression risk.
        ========================================================= */}

        {/* ========================================================= */}
        {/* 5. LONGITUDINAL PROGRESSION WORKSTATION                   */}
        {/* ========================================================= */}
        {activeTab === 'progression' && selectedPatientId && (
          <PatientProfile
            patientId={selectedPatientId}
            onBack={() => setSelectedPatientId(null)}
            onSelectScanForAnalysis={handleSelectScanForAnalysis}
            onOpenImportModalForPatient={handleOpenImportModalForPatient}
            apiBaseUrl={apiBaseUrl}
            activeAnalysis={currentAnalysis}
          />
        )}
        {activeTab === 'progression' && !selectedPatientId && (
          <div className="space-y-6">
            <div className="p-12 border border-slate-200 rounded-2xl text-center bg-white space-y-4 shadow-sm">
              <h3 className="text-base font-bold text-slate-900">Select a Patient to View Progression</h3>
              <p className="text-xs text-slate-500 max-w-md mx-auto leading-relaxed">
                Please select a patient from the Patients tab to view their longitudinal progression with real IOP, Visual Field, RNFLT, and AI score trends.
              </p>
              <button
                onClick={() => setActiveTab('patients')}
                className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs shadow-sm transition cursor-pointer"
              >
                Go to Patients
              </button>
            </div>
            {/* PROGRESSION RISK MODULE — shown only here, never on the structural analysis tab.
                Rule: p_glaucoma (Module 1) and progression probability (Module 2) are NEVER combined. */}
            <ProgressionRiskCard apiBaseUrl={apiBaseUrl} />
          </div>
        )}

        {/* ========================================================= */}
        {/* 6. DEMO CASES LIBRARY                                     */}
        {/* ========================================================= */}
        {activeTab === 'demo-cases' && (
          <DemoCasesPage
            patients={patients}
            onSelectPatient={(pId) => {
              setSelectedPatientId(pId);
              setActiveTab('patients');
            }}
            onSelectDemoCase={async (demoId) => {
              await handleSelectDemoCase(demoId);
            }}
          />
        )}
      </main>

      {/* Doctor-Facing Clinical Workstation Modals */}
      <RegisterPatientModal
        isOpen={isRegisterModalOpen}
        onClose={() => setIsRegisterModalOpen(false)}
        onSuccess={(newPatient) => {
          refreshSystem();
          setSelectedPatientId(newPatient.id);
          setActiveTab('patients');
        }}
        apiBaseUrl={apiBaseUrl}
      />

      <ImportScanModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        patients={patients}
        initialPatientId={importInitialPatientId}
        onAnalyze={handleAnalyze}
        loading={analyzing}
      />

      <SettingsModal
        isOpen={isSettingsModalOpen}
        onClose={() => setIsSettingsModalOpen(false)}
        backendConnected={backendConnected}
        modelStatus={modelStatus}
        onRefresh={refreshSystem}
      />

      <AddIOPModal
        isOpen={isIopModalOpen}
        onClose={() => setIsIopModalOpen(false)}
        patientId={modalTargetPatientId}
        patientName={patients.find((p) => p.id === modalTargetPatientId)?.name || 'Patient'}
        apiBaseUrl={apiBaseUrl}
        onSuccess={() => {
          setIsIopModalOpen(false);
          refreshSystem();
        }}
      />

      <AddVisualFieldModal
        isOpen={isVfModalOpen}
        onClose={() => setIsVfModalOpen(false)}
        patientId={modalTargetPatientId}
        apiBaseUrl={apiBaseUrl}
        onSuccess={() => {
          setIsVfModalOpen(false);
          refreshSystem();
        }}
      />

      <AddReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        patientId={modalTargetPatientId}
        patientName={patients.find((p) => p.id === modalTargetPatientId)?.name || 'Patient'}
        apiBaseUrl={apiBaseUrl}
        onSuccess={() => {
          setIsReportModalOpen(false);
          refreshSystem();
        }}
      />

      {/* Calm Clinical Footer */}
      <footer className="border-t border-slate-200 bg-white/90 py-4 px-6 text-xs text-slate-500 shadow-xs">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-700">GlaucoMap</span>
            <span>&bull;</span>
            <span>Ophthalmic Structural Analysis &amp; Longitudinal Monitoring</span>
          </div>
          <span className="text-[11px] text-slate-500">
            Clinical Decision-Support &amp; Research Prototype &bull; Not for Independent Diagnostic Use
          </span>
        </div>
      </footer>
    </div>
  );
};

export default App;
