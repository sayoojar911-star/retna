import React, { useState } from 'react';
import {
  Eye,
  Activity,
  FileText,
  Calendar,
  Plus,
  Sparkles,
  ChevronRight,
  Clock,
  CheckCircle2,
} from 'lucide-react';
import {
  ClinicalPatient,
  ClinicalScan,
  IOPRecord,
  VisualFieldRecord,
  ClinicalReport,
} from '../types';

interface PatientTimelineProps {
  patient: ClinicalPatient;
  scans: ClinicalScan[];
  iopRecords: IOPRecord[];
  vfRecords: VisualFieldRecord[];
  reports: ClinicalReport[];
  onSelectScanForAnalysis: (scan: ClinicalScan) => void;
  onOpenImportModal: () => void;
  onOpenAddIOPModal: () => void;
  onOpenAddVFModal: () => void;
  onOpenAddReportModal: () => void;
  onNavigateToTab: (tab: any) => void;
}

interface TimelineItem {
  id: string;
  date: string;
  type: 'scan' | 'iop' | 'vf' | 'report';
  title: string;
  eye?: string;
  data: any;
}

export const PatientTimeline: React.FC<PatientTimelineProps> = ({
  scans,
  iopRecords,
  vfRecords,
  reports,
  onSelectScanForAnalysis,
  onOpenImportModal,
  onOpenAddIOPModal,
  onOpenAddVFModal,
  onOpenAddReportModal,
  onNavigateToTab,
}) => {
  const [filterType, setFilterType] = useState<'ALL' | 'SCAN' | 'IOP' | 'VF' | 'REPORT'>('ALL');

  // Collate all real clinical events
  const events: TimelineItem[] = [];

  scans.forEach((scan) => {
    events.push({
      id: `scan-${scan.id}`,
      date: scan.date,
      type: 'scan',
      title: scan.scan_type === 'RNFLT' ? 'OCT RNFLT Study' : 'Digital OCT Study',
      eye: scan.eye,
      data: scan,
    });
  });

  iopRecords.forEach((iop) => {
    events.push({
      id: `iop-${iop.id}`,
      date: iop.date,
      type: 'iop',
      title: 'IOP Tonometry',
      eye: iop.eye,
      data: iop,
    });
  });

  vfRecords.forEach((vf) => {
    events.push({
      id: `vf-${vf.id}`,
      date: vf.date,
      type: 'vf',
      title: 'Visual Field HVF 24-2',
      eye: vf.eye,
      data: vf,
    });
  });

  reports.forEach((rep) => {
    events.push({
      id: `report-${rep.id}`,
      date: rep.report_date,
      type: 'report',
      title: rep.report_type || 'Clinical Report',
      eye: rep.eye,
      data: rep,
    });
  });

  // Sort descending by date
  events.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

  // Filter items
  const filteredEvents = events.filter((ev) => {
    if (filterType === 'ALL') return true;
    if (filterType === 'SCAN') return ev.type === 'scan';
    if (filterType === 'IOP') return ev.type === 'iop';
    if (filterType === 'VF') return ev.type === 'vf';
    if (filterType === 'REPORT') return ev.type === 'report';
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Timeline Controls & Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white p-3.5 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 sm:pb-0">
          <span className="text-xs font-semibold text-slate-700 mr-1.5 flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-teal-600" />
            Events:
          </span>
          {(['ALL', 'SCAN', 'IOP', 'VF', 'REPORT'] as const).map((ft) => (
            <button
              key={ft}
              onClick={() => setFilterType(ft)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer ${
                filterType === ft
                  ? 'bg-teal-50 text-teal-800 border border-teal-200 font-semibold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              {ft === 'ALL'
                ? `All (${events.length})`
                : ft === 'SCAN'
                ? `Scans (${scans.length})`
                : ft === 'IOP'
                ? `IOP (${iopRecords.length})`
                : ft === 'VF'
                ? `Visual Field (${vfRecords.length})`
                : `Reports (${reports.length})`}
            </button>
          ))}
        </div>

        {/* Quick Action Clinical Buttons */}
        <div className="flex items-center space-x-2">
          <button
            onClick={onOpenImportModal}
            className="px-3 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-medium transition flex items-center space-x-1.5 shadow-sm cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Import OCT</span>
          </button>
          <button
            onClick={onOpenAddIOPModal}
            className="px-2.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-xs font-medium transition cursor-pointer"
          >
            <span>+ IOP</span>
          </button>
          <button
            onClick={onOpenAddVFModal}
            className="px-2.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-xs font-medium transition cursor-pointer"
          >
            <span>+ VF</span>
          </button>
          <button
            onClick={onOpenAddReportModal}
            className="px-2.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 text-xs font-medium transition cursor-pointer"
          >
            <span>+ Report</span>
          </button>
        </div>
      </div>

      {/* Connected Longitudinal Timeline Container */}
      <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
        {/* Next Scheduled Follow-up Node */}
        <div className="relative flex items-start space-x-4">
          <div className="absolute -left-6 sm:-left-8 top-1 w-6 h-6 rounded-full bg-teal-100 border-2 border-teal-600 flex items-center justify-center text-teal-700 shadow-xs">
            <Calendar className="w-3 h-3" />
          </div>
          <div className="flex-1 bg-gradient-to-r from-teal-50/60 to-white border border-teal-200/80 rounded-2xl p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-teal-100 text-teal-800">
                  Target Review
                </span>
                <span className="text-xs font-semibold text-slate-800">
                  Follow-up Structural &amp; Functional Assessment
                </span>
              </div>
              <span className="text-xs font-mono text-teal-800 font-semibold">
                Scheduled ~Dec 2026
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">
              Recommended 3-month follow-up for repeat peripapillary RNFLT OCT and Goldmann tonometry to monitor longitudinal stability.
            </p>
          </div>
        </div>

        {/* Real Recorded Events in Chronological Sequence */}
        {filteredEvents.map((item) => {
          if (item.type === 'scan') {
            const scan: ClinicalScan = item.data;
            const isAnalyzed = scan.status === 'Analyzed';
            const isExtractionRequired = scan.status === 'RNFLT extraction required';

            return (
              <div key={item.id} className="relative flex items-start space-x-4">
                {/* Timeline Node */}
                <div
                  className={`absolute -left-6 sm:-left-8 top-3.5 w-6 h-6 rounded-full border-2 flex items-center justify-center shadow-xs bg-white ${
                    isAnalyzed
                      ? 'border-teal-600 text-teal-700'
                      : isExtractionRequired
                      ? 'border-amber-500 text-amber-600'
                      : 'border-slate-400 text-slate-500'
                  }`}
                >
                  <Eye className="w-3 h-3" />
                </div>

                {/* Floating Clinical Card */}
                <div className="flex-1 bg-white border border-slate-200 hover:border-teal-300 rounded-2xl p-5 shadow-sm transition-all hover:shadow-md space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                    <div className="flex items-center space-x-2.5">
                      <span className="text-xs font-bold text-slate-900">{item.title}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200">
                        Eye: {scan.eye}
                      </span>
                      <span
                        className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border ${
                          isAnalyzed
                            ? 'bg-teal-50 text-teal-700 border-teal-200'
                            : isExtractionRequired
                            ? 'bg-amber-50 text-amber-700 border-amber-200'
                            : 'bg-slate-100 text-slate-700 border-slate-200'
                        }`}
                      >
                        {scan.status}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 text-xs text-slate-500 font-mono">
                      <Calendar className="w-3.5 h-3.5 text-slate-400" />
                      <span>{scan.date}</span>
                    </div>
                  </div>

                  {/* Quantitative Findings */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                      <div className="text-[11px] text-slate-500">Modality</div>
                      <div className="font-semibold text-slate-800 mt-0.5 font-mono">
                        {scan.scan_type}
                      </div>
                    </div>

                    <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                      <div className="text-[11px] text-slate-500">RNFLT Mean</div>
                      <div className="font-semibold text-teal-800 mt-0.5 font-mono">
                        {scan.mean_rnflt_um ? `${scan.mean_rnflt_um} µm` : 'Not recorded'}
                      </div>
                    </div>

                    <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                      <div className="text-[11px] text-slate-500">Status</div>
                      <div className="font-semibold text-slate-800 mt-0.5 truncate">
                        {scan.status}
                      </div>
                    </div>

                    <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                      <div className="text-[11px] text-slate-500">Classification</div>
                      <div className="font-semibold text-slate-800 mt-0.5 flex items-center gap-1">
                        {isAnalyzed ? (
                          <>
                            <CheckCircle2 className="w-3 h-3 text-teal-600" />
                            <span>Estimated</span>
                          </>
                        ) : isExtractionRequired ? (
                          <span className="text-amber-700">Segmentation Req.</span>
                        ) : (
                          <span>Awaiting analysis</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Card Action Buttons */}
                  <div className="flex items-center justify-between pt-1">
                    <div className="text-[11px] text-slate-500">
                      {isExtractionRequired
                        ? 'Raw OCT cross-section; segmentation extraction interface ready.'
                        : 'Real Harvard-GD trained CNN structural evaluation.'}
                    </div>

                    <button
                      onClick={() => onSelectScanForAnalysis(scan)}
                      className="px-3 py-1.5 rounded-xl bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 text-xs font-semibold flex items-center space-x-1.5 transition cursor-pointer"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-teal-600" />
                      <span>{isAnalyzed ? 'View AI Analysis & Grad-CAM' : 'Open Study Analysis'}</span>
                      <ChevronRight className="w-3 h-3 text-teal-600" />
                    </button>
                  </div>
                </div>
              </div>
            );
          }

          if (item.type === 'iop') {
            const iop: IOPRecord = item.data;
            return (
              <div key={item.id} className="relative flex items-start space-x-4">
                {/* Timeline Node */}
                <div className="absolute -left-6 sm:-left-8 top-3.5 w-6 h-6 rounded-full border-2 border-blue-600 text-blue-700 bg-white flex items-center justify-center shadow-xs">
                  <Activity className="w-3 h-3" />
                </div>

                {/* Floating Card */}
                <div className="flex-1 bg-white border border-slate-200 hover:border-blue-300 rounded-2xl p-4 shadow-sm transition space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-slate-900">Intraocular Pressure</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
                        Eye: {iop.eye}
                      </span>
                    </div>
                    <span className="text-xs font-mono text-slate-500">{iop.date}</span>
                  </div>

                  <div className="flex items-center justify-between bg-blue-50/50 p-3 rounded-xl border border-blue-100">
                    <div>
                      <div className="text-[11px] text-slate-500">Measured Tonometry</div>
                      <div className="text-base font-bold text-blue-800 font-mono mt-0.5">
                        {iop.iop_mmhg} mmHg
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-[11px] text-slate-500">Method</div>
                      <div className="text-xs font-medium text-slate-700 mt-0.5">
                        {iop.method || 'Goldmann Applanation'}
                      </div>
                    </div>
                  </div>

                  {iop.notes && (
                    <p className="text-[11px] text-slate-600 italic">Notes: {iop.notes}</p>
                  )}

                  <div className="flex justify-end pt-1">
                    <button
                      onClick={() => onNavigateToTab('iop')}
                      className="text-xs text-blue-700 hover:text-blue-800 font-medium flex items-center space-x-1 cursor-pointer"
                    >
                      <span>View Longitudinal IOP History</span>
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            );
          }

          if (item.type === 'vf') {
            const vf: VisualFieldRecord = item.data;
            return (
              <div key={item.id} className="relative flex items-start space-x-4">
                {/* Timeline Node */}
                <div className="absolute -left-6 sm:-left-8 top-3.5 w-6 h-6 rounded-full border-2 border-amber-500 text-amber-600 bg-white flex items-center justify-center shadow-xs">
                  <FileText className="w-3 h-3" />
                </div>

                {/* Floating Card */}
                <div className="flex-1 bg-white border border-slate-200 hover:border-amber-300 rounded-2xl p-4 shadow-sm transition space-y-2.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-slate-900">Perimetric Visual Field</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200 font-semibold">
                        Eye: {vf.eye}
                      </span>
                    </div>
                    <span className="text-xs font-mono text-slate-500">{vf.date}</span>
                  </div>

                  <div className="grid grid-cols-3 gap-2 bg-amber-50/40 p-3 rounded-xl border border-amber-100 text-xs">
                    <div>
                      <div className="text-[11px] text-slate-500">Mean Deviation (MD)</div>
                      <div className="font-bold text-amber-900 font-mono mt-0.5">
                        {vf.md_db} dB
                      </div>
                    </div>
                    <div>
                      <div className="text-[11px] text-slate-500">Pattern SD (PSD)</div>
                      <div className="font-semibold text-slate-800 font-mono mt-0.5">
                        {vf.psd_db !== undefined && vf.psd_db !== null
                          ? `${vf.psd_db} dB`
                          : 'Not recorded'}
                      </div>
                    </div>
                    <div>
                      <div className="text-[11px] text-slate-500">Visual Field Index</div>
                      <div className="font-semibold text-slate-800 font-mono mt-0.5">
                        {vf.vfi_pct !== undefined && vf.vfi_pct !== null ? `${vf.vfi_pct}%` : 'Not recorded'}
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end pt-1">
                    <button
                      onClick={() => onNavigateToTab('visual_field')}
                      className="text-xs text-amber-800 hover:text-amber-900 font-medium flex items-center space-x-1 cursor-pointer"
                    >
                      <span>View Visual Field Trend</span>
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            );
          }

          if (item.type === 'report') {
            const rep: ClinicalReport = item.data;
            return (
              <div key={item.id} className="relative flex items-start space-x-4">
                {/* Timeline Node */}
                <div className="absolute -left-6 sm:-left-8 top-3.5 w-6 h-6 rounded-full border-2 border-purple-500 text-purple-600 bg-white flex items-center justify-center shadow-xs">
                  <FileText className="w-3 h-3" />
                </div>

                {/* Floating Card */}
                <div className="flex-1 bg-white border border-slate-200 hover:border-purple-300 rounded-2xl p-4 shadow-sm transition space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-bold text-slate-900">{item.title}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200 font-semibold">
                        {rep.eye || 'OU'}
                      </span>
                    </div>
                    <span className="text-xs font-mono text-slate-500">{rep.report_date}</span>
                  </div>

                  {rep.notes && (
                    <p className="text-xs text-slate-600 leading-relaxed">{rep.notes}</p>
                  )}

                  <div className="flex items-center justify-between pt-1 text-xs">
                    <span className="text-[11px] text-slate-500 font-mono">
                      File: {rep.file_name}
                    </span>
                    <button
                      onClick={() => onNavigateToTab('reports')}
                      className="text-xs text-purple-700 hover:text-purple-800 font-medium flex items-center space-x-1 cursor-pointer"
                    >
                      <span>Open Document Record</span>
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            );
          }

          return null;
        })}

        {/* Empty State */}
        {filteredEvents.length === 0 && (
          <div className="p-8 bg-white border border-dashed border-slate-300 rounded-2xl text-center space-y-2">
            <Clock className="w-8 h-8 text-slate-400 mx-auto" />
            <h4 className="text-xs font-semibold text-slate-800">No Events Recorded</h4>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              No clinical events recorded for this patient under the selected filter.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PatientTimeline;
