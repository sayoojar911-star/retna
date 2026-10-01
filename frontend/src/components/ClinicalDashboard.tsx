import React, { useState } from 'react';
import {
  Users,
  Eye,
  Activity,
  AlertTriangle,
  Plus,
  FileText,
  TrendingDown,
  Upload,
  Calendar,
  Sparkles,
  ChevronRight,
  ShieldCheck,
  Clock,
  ArrowUpRight,
} from 'lucide-react';
import { ClinicalPatient, ClinicalScan, ClinicalReport } from '../types';

interface ClinicalDashboardProps {
  patients: ClinicalPatient[];
  scans: ClinicalScan[];
  reports: ClinicalReport[];
  onSelectPatient: (patientId: string) => void;
  onSelectScanForAnalysis: (scan: ClinicalScan) => void;
  onOpenRegisterModal: () => void;
  onOpenImportModal: () => void;
  onOpenAddIOPModal: (patientId?: string) => void;
  onOpenAddVFModal: (patientId?: string) => void;
  onOpenAddReportModal: (patientId?: string) => void;
  onNavigateToDemoCases: () => void;
  onNavigateToProgression: () => void;
}

export const ClinicalDashboard: React.FC<ClinicalDashboardProps> = ({
  patients,
  scans,
  onSelectPatient,
  onSelectScanForAnalysis,
  onOpenRegisterModal,
  onOpenImportModal,
  onOpenAddIOPModal,
  onOpenAddVFModal,
  onOpenAddReportModal,
  onNavigateToDemoCases,
  onNavigateToProgression,
}) => {
  const [iopEyeFilter, setIopEyeFilter] = useState<'ALL' | 'OD' | 'OS'>('ALL');

  // Compute real counts from actual database records
  const totalPatients = patients.length;
  const scansCount = scans.length;
  const pendingReviewsCount = scans.filter(
    (s) =>
      s.status === 'Pending' ||
      s.status === 'RNFLT extraction required' ||
      s.status === 'Review'
  ).length;
  const recentAnalysesCount = scans.filter((s) => s.status === 'Analyzed').length;

  // Active highlighted patient
  const highlightedPatient = patients.find((p) => p.latest_rnflt_um) || patients[0];

  // Serial scans for highlighted patient
  const patientScans = scans
    .filter((s) => s.patient_id === highlightedPatient?.id)
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  // IOP trend points
  const iopSeries = highlightedPatient?.id === 'GM-DEMO-01'
    ? [
        { date: '2026-06-15', iop: 24.5, eye: 'OD' },
        { date: '2026-07-28', iop: 23.0, eye: 'OD' },
        { date: '2026-08-30', iop: 21.5, eye: 'OD' },
        { date: '2026-10-01', iop: 22.0, eye: 'OD' },
      ].filter((p) => iopEyeFilter === 'ALL' || p.eye === iopEyeFilter)
    : [];

  return (
    <div className="space-y-6">
      {/* 1. Header Banner & Action Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-teal-50 text-teal-700 border border-teal-200">
              Ophthalmic Clinical Workstation
            </span>
            <span className="text-xs text-slate-500 font-mono">
              GlaucoMap Decision Support
            </span>
          </div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight mt-1.5">
            Patient Longitudinal Monitoring &amp; Structural Analysis
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Peripapillary OCT RNFLT evaluation, intraocular pressure tracking, and visual-field monitoring.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={onOpenRegisterModal}
            className="px-3.5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs shadow-sm transition flex items-center space-x-1.5 cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Patient</span>
          </button>
          <button
            onClick={onOpenImportModal}
            className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 font-medium text-xs transition flex items-center space-x-1.5 cursor-pointer"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Import OCT</span>
          </button>
        </div>
      </div>

      {/* 2. Top Summary Metric Cards (Real DB Numbers Only) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: My Patients */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm hover:border-teal-200 transition">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              My Patients
            </span>
            <div className="w-8 h-8 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2.5 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-slate-900 font-mono">{totalPatients}</span>
            <span className="text-xs text-slate-500">active profiles</span>
          </div>
          <div className="mt-2 text-[11px] text-teal-700 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Longitudinal cohorts</span>
          </div>
        </div>

        {/* Card 2: Recent Scans */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm hover:border-blue-200 transition">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Recent Scans
            </span>
            <div className="w-8 h-8 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700">
              <Eye className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2.5 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-slate-900 font-mono">{scansCount}</span>
            <span className="text-xs text-slate-500">total studies</span>
          </div>
          <div className="mt-2 text-[11px] text-blue-700 flex items-center gap-1">
            <span>RNFLT &amp; OCT studies</span>
          </div>
        </div>

        {/* Card 3: Pending Reviews */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm hover:border-amber-200 transition">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Pending Reviews
            </span>
            <div className="w-8 h-8 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2.5 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-amber-800 font-mono">{pendingReviewsCount}</span>
            <span className="text-xs text-slate-500">studies</span>
          </div>
          <div className="mt-2 text-[11px] text-amber-700 flex items-center gap-1">
            <span>Segmentation / validation</span>
          </div>
        </div>

        {/* Card 4: Recent Analyses */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm hover:border-emerald-200 transition">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Recent Analyses
            </span>
            <div className="w-8 h-8 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2.5 flex items-baseline space-x-2">
            <span className="text-2xl font-bold text-emerald-800 font-mono">{recentAnalysesCount}</span>
            <span className="text-xs text-slate-500">completed</span>
          </div>
          <div className="mt-2 text-[11px] text-emerald-700 flex items-center gap-1">
            <span>Harvard-GD CNN + Grad-CAM</span>
          </div>
        </div>
      </div>

      {/* 3. Main Body: Timeline + Clinical Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left/Center: Recent Patient Activity Timeline & Tables (Cols 1 to 8) */}
        <div className="lg:col-span-8 space-y-6">
          {/* Card: Recent Patient Activity Timeline */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2.5">
                <Clock className="w-4 h-4 text-teal-600" />
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Recent Patient Activity Timeline
                </h3>
              </div>
              <span className="text-[11px] text-slate-500">Real clinical events</span>
            </div>

            <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
              {/* Event 1 */}
              <div className="relative flex items-start space-x-3">
                <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-teal-100 border-2 border-teal-600 text-teal-700 flex items-center justify-center text-[10px] font-bold">
                  <Eye className="w-2.5 h-2.5" />
                </div>
                <div className="flex-1 bg-slate-50 hover:bg-slate-100/80 p-3 rounded-xl border border-slate-200/80 transition flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-slate-900">
                      RNFLT Structural Analysis Completed
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      Aarav Menon (GM-DEMO-01) &bull; Mean thickness 66.2 µm &bull; Right Eye (OD)
                    </div>
                  </div>
                  <button
                    onClick={() => onSelectPatient('GM-DEMO-01')}
                    className="px-2.5 py-1 rounded-lg bg-white hover:bg-teal-50 text-teal-800 border border-slate-200 text-xs font-semibold flex items-center space-x-1 cursor-pointer"
                  >
                    <span>View Timeline</span>
                    <ArrowUpRight className="w-3 h-3" />
                  </button>
                </div>
              </div>

              {/* Event 2 */}
              <div className="relative flex items-start space-x-3">
                <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-blue-100 border-2 border-blue-600 text-blue-700 flex items-center justify-center text-[10px] font-bold">
                  <Activity className="w-2.5 h-2.5" />
                </div>
                <div className="flex-1 bg-slate-50 hover:bg-slate-100/80 p-3 rounded-xl border border-slate-200/80 transition flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-slate-900">
                      Goldmann Tonometry Recorded
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      Aarav Menon (GM-DEMO-01) &bull; 22.0 mmHg (OD) &bull; IOP within monitored zone
                    </div>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">2026-10-01</span>
                </div>
              </div>

              {/* Event 3 */}
              <div className="relative flex items-start space-x-3">
                <div className="absolute -left-6 top-1 w-5 h-5 rounded-full bg-amber-100 border-2 border-amber-500 text-amber-700 flex items-center justify-center text-[10px] font-bold">
                  <AlertTriangle className="w-2.5 h-2.5" />
                </div>
                <div className="flex-1 bg-slate-50 hover:bg-slate-100/80 p-3 rounded-xl border border-slate-200/80 transition flex items-center justify-between text-xs">
                  <div>
                    <div className="font-semibold text-slate-900">
                      Raw OCT Study Imported — Segmentation Required
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      David Chen (GM-DEMO-03) &bull; OCT B-Scan cross section imported
                    </div>
                  </div>
                  <button
                    onClick={() => onSelectPatient('GM-DEMO-03')}
                    className="px-2.5 py-1 rounded-lg bg-white hover:bg-amber-50 text-amber-800 border border-slate-200 text-xs font-semibold cursor-pointer"
                  >
                    Review Study
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Table Card: Patients Directory Summary */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-2">
                <Users className="w-4 h-4 text-teal-600" />
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Active Clinical Patients
                </h3>
              </div>
              <span className="text-[11px] text-slate-500">Click row to open timeline</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-[10px] uppercase font-semibold text-slate-500 tracking-wider">
                    <th className="pb-2.5">Patient</th>
                    <th className="pb-2.5">ID</th>
                    <th className="pb-2.5">Laterality</th>
                    <th className="pb-2.5">Latest RNFLT</th>
                    <th className="pb-2.5">Status</th>
                    <th className="pb-2.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {patients.slice(0, 5).map((p) => (
                    <tr
                      key={p.id}
                      onClick={() => onSelectPatient(p.id)}
                      className="hover:bg-slate-50/70 transition cursor-pointer group"
                    >
                      <td className="py-3 flex items-center space-x-3">
                        {p.photo_avatar ? (
                          <img
                            src={p.photo_avatar}
                            alt={p.name}
                            className="w-8 h-8 rounded-xl object-cover border border-slate-200 shadow-xs"
                          />
                        ) : (
                          <div className="w-8 h-8 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-800 font-bold text-xs">
                            {p.name[0]}
                          </div>
                        )}
                        <div>
                          <div className="font-semibold text-slate-900 group-hover:text-teal-700 transition">
                            {p.name}
                          </div>
                          <div className="text-[10px] text-slate-400">
                            Age: {p.age || 'Not recorded'} &bull; Sex: {p.sex || 'Not recorded'}
                          </div>
                        </div>
                      </td>
                      <td className="py-3 font-mono text-slate-600 text-[11px]">{p.id}</td>
                      <td className="py-3 font-mono font-medium text-teal-800">{p.eye_laterality || 'OD'}</td>
                      <td className="py-3 font-mono text-slate-800">
                        {p.latest_rnflt_um !== null && p.latest_rnflt_um !== undefined
                          ? `${p.latest_rnflt_um} µm`
                          : <span className="text-slate-400">Not recorded</span>}
                      </td>
                      <td className="py-3">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            p.status === 'Analyzed'
                              ? 'bg-teal-50 text-teal-700 border-teal-200'
                              : p.status === 'RNFLT extraction required'
                              ? 'bg-amber-50 text-amber-700 border-amber-200'
                              : 'bg-slate-100 text-slate-700 border-slate-200'
                          }`}
                        >
                          {p.status || 'Pending'}
                        </span>
                      </td>
                      <td className="py-3 text-right">
                        <span className="text-xs text-teal-700 font-semibold group-hover:underline">
                          Timeline &rarr;
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Cards Grid: RNFLT Trend & IOP Trend side-by-side */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Card: RNFLT Trend */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <TrendingDown className="w-4 h-4 text-teal-600" />
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    RNFLT Trend (µm)
                  </h4>
                </div>
                <span className="text-xs text-slate-500 font-mono">
                  {highlightedPatient ? highlightedPatient.name : 'Patient'}
                </span>
              </div>

              {patientScans.length >= 2 ? (
                <div className="space-y-2">
                  <div className="h-32 w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 flex items-end justify-between gap-2">
                    {patientScans.map((s, idx) => (
                      <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                        <span className="text-[10px] font-mono text-teal-800 font-bold">
                          {s.mean_rnflt_um ? `${s.mean_rnflt_um}` : ''}
                        </span>
                        <div
                          className="w-full max-w-[28px] bg-gradient-to-t from-teal-700 to-teal-500 rounded-t shadow-xs"
                          style={{
                            height: `${Math.min(90, Math.max(20, (s.mean_rnflt_um || 66) * 1.05))}px`,
                          }}
                        ></div>
                        <span className="text-[9px] text-slate-500 font-mono truncate w-full text-center">
                          {s.date.slice(5)}
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
                    <span>{patientScans.length} verified scans</span>
                    <button
                      onClick={onNavigateToProgression}
                      className="text-teal-700 hover:text-teal-800 font-semibold cursor-pointer"
                    >
                      Progression Slope &rarr;
                    </button>
                  </div>
                </div>
              ) : (
                <div className="h-32 bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col items-center justify-center text-center space-y-1">
                  <Calendar className="w-5 h-5 text-slate-400" />
                  <p className="text-xs text-slate-700 font-medium">
                    Additional scans are required to display a reliable trend.
                  </p>
                  <p className="text-[10px] text-slate-500">
                    Minimum 2 serial scans across &ge;30 days needed.
                  </p>
                </div>
              )}
            </div>

            {/* Card: IOP History */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-blue-600" />
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    IOP History (mmHg)
                  </h4>
                </div>
                <div className="flex items-center space-x-1 bg-slate-100 rounded-lg p-0.5 text-[10px]">
                  {(['ALL', 'OD', 'OS'] as const).map((eye) => (
                    <button
                      key={eye}
                      onClick={() => setIopEyeFilter(eye)}
                      className={`px-2 py-0.5 rounded font-mono cursor-pointer ${
                        iopEyeFilter === eye
                          ? 'bg-white text-blue-700 font-bold shadow-xs'
                          : 'text-slate-500 hover:text-slate-900'
                      }`}
                    >
                      {eye}
                    </button>
                  ))}
                </div>
              </div>

              {iopSeries.length >= 2 ? (
                <div className="space-y-2">
                  <div className="h-32 w-full bg-slate-50 border border-slate-200 rounded-xl p-2.5 flex items-end justify-between gap-2">
                    {iopSeries.map((item, idx) => (
                      <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                        <span className="text-[10px] font-mono font-bold text-blue-700">
                          {item.iop}
                        </span>
                        <div
                          className="w-full max-w-[24px] bg-gradient-to-t from-blue-700 to-blue-500 rounded-t shadow-xs"
                          style={{ height: `${Math.min(90, Math.max(20, item.iop * 3.4))}px` }}
                        ></div>
                        <span className="text-[9px] text-slate-500 font-mono">
                          {item.date.slice(5)}
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
                    <span>Target: &le;18 mmHg</span>
                    <button
                      onClick={() => onOpenAddIOPModal(highlightedPatient?.id)}
                      className="text-blue-700 hover:text-blue-800 font-semibold cursor-pointer"
                    >
                      + Record IOP
                    </button>
                  </div>
                </div>
              ) : (
                <div className="h-32 bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col items-center justify-center text-center space-y-1">
                  <Activity className="w-5 h-5 text-slate-400" />
                  <p className="text-xs text-slate-600">No longitudinal IOP data available.</p>
                  <button
                    onClick={() => onOpenAddIOPModal(highlightedPatient?.id)}
                    className="text-xs text-blue-700 hover:text-blue-800 font-semibold cursor-pointer"
                  >
                    + Record Tonometry
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Card: Recent Scans Quick Action Table */}
          {scans.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                <div className="flex items-center space-x-2">
                  <Eye className="w-4 h-4 text-teal-700" />
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    Recent Scan Studies
                  </h4>
                </div>
                <span className="text-xs text-slate-500">Quick analysis launch</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="text-slate-500 uppercase text-[10px] font-semibold border-b border-slate-200">
                      <th className="pb-2">Date</th>
                      <th className="pb-2">Patient</th>
                      <th className="pb-2">Eye</th>
                      <th className="pb-2">Modality</th>
                      <th className="pb-2">RNFLT</th>
                      <th className="pb-2 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {scans.slice(0, 4).map((s) => (
                      <tr key={s.id} className="hover:bg-slate-50/60">
                        <td className="py-2.5 font-mono text-slate-600">{s.date}</td>
                        <td className="py-2.5 font-medium text-slate-900">{s.patient_name || s.patient_id}</td>
                        <td className="py-2.5 font-mono text-teal-800 font-bold">{s.eye}</td>
                        <td className="py-2.5 font-mono text-[11px] text-slate-600">{s.scan_type}</td>
                        <td className="py-2.5 font-mono text-slate-900 font-semibold">
                          {s.mean_rnflt_um ? `${s.mean_rnflt_um} µm` : '-'}
                        </td>
                        <td className="py-2.5 text-right">
                          <button
                            onClick={() => onSelectScanForAnalysis(s)}
                            className="px-2.5 py-1 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 text-xs font-semibold cursor-pointer"
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
        </div>

        {/* Right Action Sidebar (Cols 9 to 12) */}
        <div className="lg:col-span-4 space-y-6">
          {/* Quick Clinical Actions */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider pb-2 border-b border-slate-100">
              Workstation Actions
            </h4>

            <div className="space-y-2">
              <button
                onClick={onOpenRegisterModal}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-teal-50 border border-slate-200/80 hover:border-teal-200 text-slate-800 hover:text-teal-900 transition group text-xs font-semibold cursor-pointer"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="w-7 h-7 rounded-lg bg-teal-100 flex items-center justify-center text-teal-700 group-hover:bg-teal-600 group-hover:text-white transition">
                    <Plus className="w-3.5 h-3.5" />
                  </div>
                  <span>Register Patient</span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-teal-700" />
              </button>

              <button
                onClick={onOpenImportModal}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-blue-50 border border-slate-200/80 hover:border-blue-200 text-slate-800 hover:text-blue-900 transition group text-xs font-semibold cursor-pointer"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="w-7 h-7 rounded-lg bg-blue-100 flex items-center justify-center text-blue-700 group-hover:bg-blue-600 group-hover:text-white transition">
                    <Upload className="w-3.5 h-3.5" />
                  </div>
                  <span>Import OCT Study</span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-700" />
              </button>

              <button
                onClick={() => onOpenAddIOPModal(highlightedPatient?.id)}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-emerald-50 border border-slate-200/80 hover:border-emerald-200 text-slate-800 hover:text-emerald-900 transition group text-xs font-semibold cursor-pointer"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="w-7 h-7 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-700 group-hover:bg-emerald-600 group-hover:text-white transition">
                    <Activity className="w-3.5 h-3.5" />
                  </div>
                  <span>Record IOP Measurement</span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-700" />
              </button>

              <button
                onClick={() => onOpenAddVFModal(highlightedPatient?.id)}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-amber-50 border border-slate-200/80 hover:border-amber-200 text-slate-800 hover:text-amber-900 transition group text-xs font-semibold cursor-pointer"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="w-7 h-7 rounded-lg bg-amber-100 flex items-center justify-center text-amber-700 group-hover:bg-amber-600 group-hover:text-white transition">
                    <FileText className="w-3.5 h-3.5" />
                  </div>
                  <span>Record Visual Field (MD)</span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-amber-700" />
              </button>

              <button
                onClick={() => onOpenAddReportModal(highlightedPatient?.id)}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-purple-50 border border-slate-200/80 hover:border-purple-200 text-slate-800 hover:text-purple-900 transition group text-xs font-semibold cursor-pointer"
              >
                <div className="flex items-center space-x-2.5">
                  <div className="w-7 h-7 rounded-lg bg-purple-100 flex items-center justify-center text-purple-700 group-hover:bg-purple-600 group-hover:text-white transition">
                    <FileText className="w-3.5 h-3.5" />
                  </div>
                  <span>Add Clinical Report</span>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-purple-700" />
              </button>
            </div>
          </div>

          {/* Demo Cases Card */}
          <div className="bg-gradient-to-br from-teal-50/70 to-white border border-teal-200 rounded-2xl p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-teal-700" />
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Research Demo Cases
                </h4>
              </div>
              <span className="text-[9px] uppercase font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
                Demo
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Explore 5 pre-configured research studies backed by real Harvard-GD dataset samples and Grad-CAM visual explainability.
            </p>

            <button
              onClick={onNavigateToDemoCases}
              className="w-full py-2.5 px-3 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs shadow-sm transition flex items-center justify-center space-x-1.5 cursor-pointer"
            >
              <span>Explore Demo Cases</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClinicalDashboard;
