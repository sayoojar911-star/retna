import React, { useState } from 'react';
import { FileText, Search, Plus, ArrowUpRight } from 'lucide-react';
import { ClinicalReport, ClinicalPatient } from '../types';

interface ReportsLibraryProps {
  reports: ClinicalReport[];
  patients?: ClinicalPatient[];
  onOpenAddReportModal: () => void;
  onSelectPatient: (patientId: string) => void;
}

export const ReportsLibrary: React.FC<ReportsLibraryProps> = ({
  reports,
  onOpenAddReportModal,
  onSelectPatient,
}) => {
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('ALL');

  const filteredReports = reports.filter((r) => {
    const matchesSearch =
      (r.patient_name || '').toLowerCase().includes(search.toLowerCase()) ||
      r.patient_id.toLowerCase().includes(search.toLowerCase()) ||
      r.report_type.toLowerCase().includes(search.toLowerCase()) ||
      r.file_name.toLowerCase().includes(search.toLowerCase());
    const matchesType = filterType === 'ALL' || r.report_type.includes(filterType);
    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center space-x-3 flex-1 max-w-md">
          <div className="relative w-full">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search reports by patient, document name, or type..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-teal-500 focus:bg-white transition"
            />
          </div>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-700 focus:outline-none focus:border-teal-500"
          >
            <option value="ALL">All Report Types</option>
            <option value="Visual Field">Visual Field (HVF)</option>
            <option value="Pachymetry">Pachymetry (CCT)</option>
            <option value="OCT">OCT Printout</option>
          </select>
        </div>

        <button
          onClick={onOpenAddReportModal}
          className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition flex items-center space-x-1.5 shadow-sm cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Upload Clinical Document</span>
        </button>
      </div>

      {/* Reports Table */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileText className="w-4 h-4 text-purple-700" />
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Clinical Document Repository
            </h3>
          </div>
          <span className="text-xs text-slate-500">
            {filteredReports.length} documents archived
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/70 text-slate-500 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-5">Date</th>
                <th className="py-3 px-4">Patient</th>
                <th className="py-3 px-4">Report Type</th>
                <th className="py-3 px-4">Eye</th>
                <th className="py-3 px-4">Document File</th>
                <th className="py-3 px-4">Clinical Summary</th>
                <th className="py-3 px-5 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredReports.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No clinical reports found.
                  </td>
                </tr>
              ) : (
                filteredReports.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3.5 px-5 font-mono text-slate-600 font-medium">
                      {r.report_date}
                    </td>
                    <td className="py-3.5 px-4">
                      <button
                        onClick={() => onSelectPatient(r.patient_id)}
                        className="text-slate-900 font-semibold hover:text-teal-700 text-left transition flex items-center space-x-1"
                      >
                        <span>{r.patient_name || r.patient_id}</span>
                        <ArrowUpRight className="w-3 h-3 text-slate-400" />
                      </button>
                      <div className="text-[10px] text-slate-400 font-mono">
                        ID: {r.patient_id}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-900">
                      {r.report_type}
                    </td>
                    <td className="py-3.5 px-4 font-mono font-bold text-teal-800">
                      {r.eye || 'OU'}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-slate-600 text-[11px]">
                      {r.file_name}
                    </td>
                    <td className="py-3.5 px-4 text-slate-500 italic max-w-xs truncate">
                      {r.notes || 'Routine documentation'}
                    </td>
                    <td className="py-3.5 px-5 text-right">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                        Archived
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ReportsLibrary;
