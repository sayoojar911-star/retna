import React, { useState, useEffect, useCallback } from 'react';
import {
  ArrowLeft,
  Eye,
  Activity,
  FileText,
  TrendingDown,
  Clock,
  Upload,
  Sparkles,
  Info,
} from 'lucide-react';
import {
  PatientProfileResponse,
  ClinicalScan,
  OCTAnalysisResponse,
} from '../types';
import { PatientTimeline } from './PatientTimeline';
import { LongitudinalCharts } from './LongitudinalCharts';
import { VisitHistory } from './VisitHistory';
import { AddVisitModal } from './AddVisitModal';
import { AddIOPModal } from './AddIOPModal';
import { AddReportModal } from './AddReportModal';
import { AddVisualFieldModal } from './AddVisualFieldModal';
import { ModelResultCard } from './ModelResultCard';
import { ExplainabilitySection } from './ExplainabilitySection';
import { RNFLTAnalysisCard } from './RNFLTAnalysisCard';
import { RawOctResultCard } from './RawOctResultCard';
// ClinicalReportModal not used here; reports viewed via ReportsLibrary

interface PatientProfileProps {
  patientId: string;
  onBack: () => void;
  onSelectScanForAnalysis: (scan: ClinicalScan) => void;
  onOpenImportModalForPatient: (patientId: string) => void;
  apiBaseUrl: string;
  activeAnalysis?: OCTAnalysisResponse | null;
}

export const PatientProfile: React.FC<PatientProfileProps> = ({
  patientId,
  onBack,
  onSelectScanForAnalysis,
  onOpenImportModalForPatient,
  apiBaseUrl,
  activeAnalysis,
}) => {
  const [profileData, setProfileData] = useState<PatientProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [subTab, setSubTab] = useState<
    'timeline' | 'visits' | 'overview' | 'scans' | 'iop' | 'visual_field' | 'reports' | 'progression' | 'analysis'
  >('timeline');

  // Modals state
  const [isIopModalOpen, setIsIopModalOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isVisitOpen, setIsVisitOpen] = useState(false);
  const [isVfModalOpen, setIsVfModalOpen] = useState(false);
  // Report viewer state removed (unused)

  // Fetch full patient profile from backend
  const fetchProfile = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBaseUrl}/api/patients/${patientId}`).catch(() =>
        fetch(`${apiBaseUrl}/api/clinical/patients/${patientId}`)
      );
      if (!res.ok) {
        throw new Error(`Failed to load profile for ${patientId}`);
      }
      const data: PatientProfileResponse = await res.json();
      setProfileData(data);
    } catch (err: any) {
      setError(err.message || 'Error fetching profile');
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, patientId]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  if (loading && !profileData) {
    return (
      <div className="py-24 text-center text-slate-500 text-xs">
        <div className="inline-block animate-spin rounded-full h-7 w-7 border-b-2 border-teal-600 mb-3" />
        <p className="font-medium text-slate-700">Loading clinical patient record...</p>
      </div>
    );
  }

  if (error || !profileData) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-2xl p-6 text-rose-800 text-xs text-center space-y-3">
        <p>{error || 'Patient profile could not be found.'}</p>
        <button
          onClick={onBack}
          className="px-4 py-2 bg-slate-800 text-white rounded-xl hover:bg-slate-700 transition cursor-pointer"
        >
          Return to Patients
        </button>
      </div>
    );
  }

  const { patient, scans, iop_records, visual_field_records = [], reports } = profileData;

  // Key summaries from actual data (Never fabricate)
  const latestIop = iop_records.length > 0 ? iop_records[iop_records.length - 1] : null;
  const latestVf = visual_field_records.length > 0 ? visual_field_records[visual_field_records.length - 1] : null;
  const latestScan = scans.length > 0 ? scans[0] : null;

  return (
    <div className="space-y-6">
      {/* 1. Back Button & Header Context */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="inline-flex items-center space-x-1.5 text-xs text-slate-500 hover:text-slate-800 font-medium transition cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to All Patients</span>
        </button>

        <div className="flex items-center space-x-2">
          {patient.is_demo && (
            <span className="text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300">
              RESEARCH DEMO — NOT A REAL PATIENT
            </span>
          )}
          <span className="text-[11px] font-mono text-slate-500 bg-white px-2 py-0.5 rounded-lg border border-slate-200">
            ID: {patient.id}
          </span>
        </div>
      </div>

      {/* 2. Patient Information Header Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-5 pb-5 border-b border-slate-100">
          {/* Left: Rounded-square photo + Demographics */}
          <div className="flex items-center space-x-4">
            {patient.photo_avatar ? (
              <img
                src={patient.photo_avatar}
                alt={patient.name}
                className="w-16 h-16 rounded-2xl object-cover border border-slate-200 shadow-sm"
              />
            ) : (
              <div className="w-16 h-16 rounded-2xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-800 font-bold text-xl shadow-sm">
                {patient.name[0]}
              </div>
            )}
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-xl font-bold text-slate-900 tracking-tight">
                  {patient.name}
                </h2>
                <span className="text-xs font-mono px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200">
                  {patient.id}
                </span>
              </div>
              <div className="text-xs text-slate-500 mt-1 flex flex-wrap items-center gap-2">
                <span>Age: <strong className="text-slate-700">{patient.age || 'Not recorded'}</strong></span>
                <span>&bull;</span>
                <span>Sex: <strong className="text-slate-700">{patient.sex || 'Not recorded'}</strong></span>
                <span>&bull;</span>
                <span>Laterality: <strong className="text-slate-700 font-mono">{patient.eye_laterality || 'OD'}</strong></span>
                <span>&bull;</span>
                <span>Status: <strong className="text-teal-700">{patient.status || 'Active'}</strong></span>
              </div>
            </div>
          </div>

          {/* Right: Quick Study Actions */}
          <div className="flex items-center space-x-2 flex-wrap gap-1.5">
            <button
              onClick={() => onOpenImportModalForPatient(patient.id)}
              className="px-3.5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold shadow-sm transition flex items-center space-x-1.5 cursor-pointer"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Import OCT Study</span>
            </button>
            <button onClick={() => setIsVisitOpen(true)} className="px-3 py-2 rounded-xl bg-slate-900 hover:bg-black text-white text-xs font-semibold shadow-sm transition cursor-pointer">+ New Visit</button>
            <button
              onClick={() => setIsIopModalOpen(true)}
              className="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-xs font-medium transition cursor-pointer"
            >
              + Record IOP
            </button>
            <button
              onClick={() => setIsVfModalOpen(true)}
              className="px-3 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-xs font-medium transition cursor-pointer"
            >
              + Record VF
            </button>
          </div>
        </div>

        {/* Compact Clinical Summary Metrics Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          {/* Latest RNFLT */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Latest RNFLT
            </div>
            <div className="text-lg font-bold text-slate-900 font-mono mt-1">
              {patient.latest_rnflt_um !== null && patient.latest_rnflt_um !== undefined
                ? `${patient.latest_rnflt_um} µm`
                : 'Not recorded'}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Mean peripapillary</div>
          </div>

          {/* Latest IOP */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Latest IOP
            </div>
            <div className="text-lg font-bold text-teal-800 font-mono mt-1">
              {latestIop ? `${latestIop.iop_mmhg} mmHg` : 'Not recorded'}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">
              {latestIop ? latestIop.date : 'Goldmann target: ≤18'}
            </div>
          </div>

          {/* Visual Field MD */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Visual Field MD
            </div>
            <div className="text-lg font-bold text-amber-800 font-mono mt-1">
              {latestVf ? `${latestVf.md_db} dB` : 'Not recorded'}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">
              {latestVf ? latestVf.date : 'HVF 24-2 SITA-Fast'}
            </div>
          </div>

          {/* Last Scan Date */}
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Last Scan
            </div>
            <div className="text-base font-bold text-slate-900 font-mono mt-1">
              {patient.last_scan_date || (latestScan ? latestScan.date : 'Not recorded')}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-600"></span>
              <span>{scans.length} historical scans</span>
            </div>
          </div>
        </div>

        {/* 3. Compact Patient Navigation Pills */}
        <div className="pt-2">
          <nav className="flex items-center space-x-1 overflow-x-auto pb-1 border-t border-slate-100 pt-3">
            {[
              { id: 'timeline', label: 'Timeline', icon: Clock },
              { id: 'visits', label: 'Visits', icon: FileText },
              { id: 'overview', label: 'Overview', icon: Info },
              { id: 'scans', label: `Scans (${scans.length})`, icon: Eye },
              { id: 'analysis', label: 'AI Analysis', icon: Sparkles },
              { id: 'iop', label: `IOP (${iop_records.length})`, icon: Activity },
              { id: 'visual_field', label: `Visual Field (${visual_field_records.length})`, icon: FileText },
              { id: 'reports', label: `Reports (${reports.length})`, icon: FileText },
              { id: 'progression', label: 'Progression', icon: TrendingDown },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = subTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setSubTab(tab.id as any)}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
                    isActive
                      ? 'bg-teal-50 text-teal-800 border border-teal-200 shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-teal-700' : 'text-slate-400'}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* ========================================================= */}
      {/* 4. TAB CONTENTS                                           */}
      {/* ========================================================= */}

      {/* TAB A: MAIN PATIENT TIMELINE (DEFAULT) */}
      {subTab === 'timeline' && (
        <PatientTimeline
          patient={patient}
          scans={scans}
          iopRecords={iop_records}
          vfRecords={visual_field_records}
          reports={reports}
          onSelectScanForAnalysis={onSelectScanForAnalysis}
          onOpenImportModal={() => onOpenImportModalForPatient(patient.id)}
          onOpenAddIOPModal={() => setIsIopModalOpen(true)}
          onOpenAddVFModal={() => setIsVfModalOpen(true)}
          onOpenAddReportModal={() => setIsReportModalOpen(true)}
          onNavigateToTab={(tab) => setSubTab(tab)}
        />
      )}

      {/* TAB B: OVERVIEW */}
      {subTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Clinical History &amp; Diagnostics
            </h3>
            <div className="space-y-2.5 text-xs">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                <span className="font-semibold text-slate-700">Family History:</span>
                <p className="text-slate-600 mt-0.5">{patient.family_history || 'Not recorded'}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                <span className="font-semibold text-slate-700">Clinical Notes:</span>
                <p className="text-slate-600 mt-0.5">{patient.clinical_notes || 'No notes documented.'}</p>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80">
                <span className="font-semibold text-slate-700">Eye Laterality:</span>
                <p className="text-slate-600 mt-0.5 font-mono">{patient.eye_laterality || 'OD'}</p>
              </div>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Historical Records Summary
            </h3>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-center">
                <div className="text-2xl font-bold text-slate-900 font-mono">{scans.length}</div>
                <div className="text-slate-500 text-[11px] mt-0.5">OCT Scans</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-center">
                <div className="text-2xl font-bold text-teal-800 font-mono">{iop_records.length}</div>
                <div className="text-slate-500 text-[11px] mt-0.5">IOP Records</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-center">
                <div className="text-2xl font-bold text-amber-800 font-mono">{visual_field_records.length}</div>
                <div className="text-slate-500 text-[11px] mt-0.5">Visual Fields</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-center">
                <div className="text-2xl font-bold text-purple-800 font-mono">{reports.length}</div>
                <div className="text-slate-500 text-[11px] mt-0.5">Reports Uploaded</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB VISITS: longitudinal visit ledger */}
      {subTab === 'visits' && (
        <VisitHistory patientId={patient.id} apiBaseUrl={apiBaseUrl} onAddVisit={() => setIsVisitOpen(true)} />
      )}

      {/* TAB C: SCANS */}
      {subTab === 'scans' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">OCT / RNFLT Study Repository</h3>
              <p className="text-xs text-slate-500">Historical cross-sectional and thickness studies.</p>
            </div>
            <button
              onClick={() => onOpenImportModalForPatient(patient.id)}
              className="px-3.5 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition"
            >
              + Import OCT Study
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 uppercase text-[10px] tracking-wider font-semibold">
                  <th className="pb-2.5">Date</th>
                  <th className="pb-2.5">Eye</th>
                  <th className="pb-2.5">Type</th>
                  <th className="pb-2.5">RNFLT Mean</th>
                  <th className="pb-2.5">Analysis Status</th>
                  <th className="pb-2.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {scans.map((scan) => (
                  <tr key={scan.id} className="hover:bg-slate-50/60 transition">
                    <td className="py-3 font-mono font-medium text-slate-800">{scan.date}</td>
                    <td className="py-3 font-mono text-teal-800">{scan.eye}</td>
                    <td className="py-3">
                      <span className="font-mono text-[11px] bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                        {scan.scan_type}
                      </span>
                    </td>
                    <td className="py-3 font-mono text-slate-800">
                      {scan.mean_rnflt_um ? `${scan.mean_rnflt_um} µm` : 'Not recorded'}
                    </td>
                    <td className="py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                          scan.status === 'Analyzed'
                            ? 'bg-teal-50 text-teal-700 border-teal-200'
                            : scan.status === 'RNFLT extraction required'
                            ? 'bg-amber-50 text-amber-700 border-amber-200'
                            : 'bg-slate-100 text-slate-700 border-slate-200'
                        }`}
                      >
                        {scan.status}
                      </span>
                    </td>
                    <td className="py-3 text-right">
                      <button
                        onClick={() => onSelectScanForAnalysis(scan)}
                        className="px-2.5 py-1 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 text-xs font-semibold transition cursor-pointer"
                      >
                        Analyze
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB D: AI ANALYSIS */}
      {subTab === 'analysis' && (
        <div className="space-y-6">
          {(() => {
            const blocked = Boolean(activeAnalysis && (activeAnalysis.input_type === 'raw_oct' || activeAnalysis.ai_analysis?.rnflt_extraction?.available === false || activeAnalysis.model_result === null));
            if (blocked && activeAnalysis) {
              return (
                <RawOctResultCard
                  rawStudy={activeAnalysis.raw_oct_study}
                  aiAnalysis={activeAnalysis.ai_analysis}
                  patientContext={activeAnalysis.patient_context}
                  filename={activeAnalysis.filename}
                />
              );
            }
            if (activeAnalysis) {
              return (
                <>
                  <ModelResultCard
                    modelResult={activeAnalysis.model_result!}
                    patientContext={activeAnalysis.patient_context}
                    groundTruth={activeAnalysis.research_ground_truth}
                    staging={activeAnalysis.staging}
                  />
                  {activeAnalysis.is_valid && activeAnalysis.rnflt_analysis && activeAnalysis.model_result && (
                    <RNFLTAnalysisCard
                      analysis={activeAnalysis.rnflt_analysis}
                      patientId={patient.id}
                      eye={patient.eye_laterality || 'OD'}
                    />
                  )}
                  {activeAnalysis.rnflt_analysis && activeAnalysis.model_result && (
                    <ExplainabilitySection
                      originalHeatmap={activeAnalysis.rnflt_analysis?.heatmap_image}
                      explainability={activeAnalysis.explainability}
                    />
                  )}
                </>
              );
            }
            return null;
          })()}
          {!activeAnalysis && (
            <div className="p-10 bg-white border border-slate-200 rounded-2xl text-center space-y-3 shadow-sm">
              <Sparkles className="w-9 h-9 text-teal-600 mx-auto" />
              <h4 className="text-sm font-bold text-slate-900">No Active Analysis Loaded</h4>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Select a scan from the patient&apos;s timeline or scans repository to view structural AI classification and Grad-CAM visual explainability.
              </p>
              {scans.length > 0 && (
                <button
                  onClick={() => onSelectScanForAnalysis(scans[0])}
                  className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition cursor-pointer"
                >
                  Analyze Latest Scan ({scans[0].date})
                </button>
              )}
            </div>
          )}
        </div>
      )}
      {subTab === 'iop' && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Intraocular Pressure Registry</h3>
                <p className="text-xs text-slate-500">Tonometric measurements across clinical visits.</p>
              </div>
              <button
                onClick={() => setIsIopModalOpen(true)}
                className="px-3.5 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition cursor-pointer"
              >
                + Record IOP
              </button>
            </div>

            {iop_records.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500 uppercase text-[10px] tracking-wider font-semibold">
                      <th className="pb-2">Date</th>
                      <th className="pb-2">Eye</th>
                      <th className="pb-2">IOP</th>
                      <th className="pb-2">Method</th>
                      <th className="pb-2">Notes</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {iop_records.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-50/60">
                        <td className="py-2.5 font-mono text-slate-800">{r.date}</td>
                        <td className="py-2.5 font-mono text-teal-800">{r.eye}</td>
                        <td className="py-2.5 font-mono font-bold text-slate-900">{r.iop_mmhg} mmHg</td>
                        <td className="py-2.5 text-slate-600">{r.method || 'Goldmann'}</td>
                        <td className="py-2.5 text-slate-500 italic">{r.notes || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-slate-500">
                No longitudinal IOP data available.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB F: VISUAL FIELD */}
      {subTab === 'visual_field' && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Perimetric Visual Field History</h3>
                <p className="text-xs text-slate-500">Standard automated perimetry records (HVF 24-2).</p>
              </div>
              <button
                onClick={() => setIsVfModalOpen(true)}
                className="px-3.5 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition cursor-pointer"
              >
                + Record Visual Field
              </button>
            </div>

            {visual_field_records.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500 uppercase text-[10px] tracking-wider font-semibold">
                      <th className="pb-2">Date</th>
                      <th className="pb-2">Eye</th>
                      <th className="pb-2">Mean Deviation (MD)</th>
                      <th className="pb-2">Pattern SD</th>
                      <th className="pb-2">VFI</th>
                      <th className="pb-2">Reliability</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {visual_field_records.map((vf) => (
                      <tr key={vf.id} className="hover:bg-slate-50/60">
                        <td className="py-2.5 font-mono text-slate-800">{vf.date}</td>
                        <td className="py-2.5 font-mono text-teal-800">{vf.eye}</td>
                        <td className="py-2.5 font-mono font-bold text-amber-800">{vf.md_db} dB</td>
                        <td className="py-2.5 font-mono text-slate-700">
                          {vf.psd_db !== undefined && vf.psd_db !== null ? `${vf.psd_db} dB` : '-'}
                        </td>
                        <td className="py-2.5 font-mono text-slate-700">
                          {vf.vfi_pct !== undefined && vf.vfi_pct !== null ? `${vf.vfi_pct}%` : '-'}
                        </td>
                        <td className="py-2.5 text-slate-600">{vf.reliability || 'Reliable'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-slate-500">
                Visual-field data not available.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB G: REPORTS */}
      {subTab === 'reports' && (
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Clinical Reports &amp; Documents</h3>
              <p className="text-xs text-slate-500">Diagnostic summaries, external consults, and OCT printouts.</p>
            </div>
            <button
              onClick={() => setIsReportModalOpen(true)}
              className="px-3.5 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition cursor-pointer"
            >
              + Add Report
            </button>
          </div>

          {reports.length > 0 ? (
            <div className="divide-y divide-slate-100">
              {reports.map((rep) => (
                <div key={rep.id} className="py-3 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-slate-800">{rep.report_type}</div>
                    <div className="text-slate-500 text-[11px] mt-0.5">
                      Date: {rep.report_date} &bull; Eye: {rep.eye || 'OU'} &bull; File: {rep.file_name}
                    </div>
                    {rep.notes && <p className="text-slate-600 mt-1 italic">{rep.notes}</p>}
                  </div>
                  <span className="text-[11px] font-mono text-slate-500 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
                    Archived
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-slate-500">
              No reports uploaded for this patient.
            </div>
          )}
        </div>
      )}

      {/* TAB H: PROGRESSION */}
      {subTab === 'progression' && (
        <div className="space-y-6">
          <LongitudinalCharts
            patientId={patient.id}
            patientName={patient.name}
            eye={patient.eye_laterality || 'OD'}
            apiBaseUrl={apiBaseUrl}
            scans={scans}
            iopRecords={iop_records}
            visualFieldRecords={visual_field_records}
            longitudinalRnflt={profileData.longitudinal_rnflt}
          />
        </div>
      )}

      {/* Modals */}
      <AddVisitModal
        isOpen={isVisitOpen}
        onClose={() => setIsVisitOpen(false)}
        patientId={patient.id}
        apiBaseUrl={apiBaseUrl}
        defaultEye={patient.eye_laterality || 'OD'}
        onSuccess={() => {
          setIsVisitOpen(false);
          fetchProfile();
        }}
      />
      <AddIOPModal
        isOpen={isIopModalOpen}
        onClose={() => setIsIopModalOpen(false)}
        patientId={patient.id}
        patientName={patient.name}
        apiBaseUrl={apiBaseUrl}
        onSuccess={() => {
          setIsIopModalOpen(false);
          fetchProfile();
        }}
      />

      <AddVisualFieldModal
        isOpen={isVfModalOpen}
        onClose={() => setIsVfModalOpen(false)}
        patientId={patient.id}
        apiBaseUrl={apiBaseUrl}
        onSuccess={() => {
          setIsVfModalOpen(false);
          fetchProfile();
        }}
      />

      <AddReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        patientId={patient.id}
        patientName={patient.name}
        apiBaseUrl={apiBaseUrl}
        onSuccess={() => {
          setIsReportModalOpen(false);
          fetchProfile();
        }}
      />
    </div>
  );
};

export default PatientProfile;
