import React, { useState } from 'react';
import { Search, Plus, Eye, ArrowUpRight } from 'lucide-react';
import { ClinicalScan } from '../types';

interface ScansLibraryProps {
  scans: ClinicalScan[];
  onOpenImportModal: () => void;
  onSelectScanForAnalysis: (scan: ClinicalScan) => void;
  onSelectPatient: (patientId: string) => void;
}

export const ScansLibrary: React.FC<ScansLibraryProps> = ({
  scans,
  onOpenImportModal,
  onSelectScanForAnalysis,
  onSelectPatient,
}) => {
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('ALL');

  const filteredScans = scans.filter((s) => {
    const matchesSearch =
      (s.patient_name || '').toLowerCase().includes(search.toLowerCase()) ||
      s.patient_id.toLowerCase().includes(search.toLowerCase()) ||
      s.scan_type.toLowerCase().includes(search.toLowerCase());
    const matchesType = filterType === 'ALL' || s.scan_type.includes(filterType);
    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center space-x-3 flex-1 max-w-md">
          <div className="relative w-full">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search scans by patient name, ID, or scan type..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-teal-500 focus:bg-white transition"
            />
          </div>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-700 focus:outline-none focus:border-teal-500"
          >
            <option value="ALL">All Scan Types</option>
            <option value="RNFLT">RNFLT Map</option>
            <option value="OCT">Raw OCT B-Scan</option>
            <option value="Fundus">Fundus Photo</option>
          </select>
        </div>

        <button
          onClick={onOpenImportModal}
          className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition flex items-center space-x-1.5 shadow-sm cursor-pointer"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Import OCT Study</span>
        </button>
      </div>

      {/* Scans Table */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Eye className="w-4 h-4 text-teal-700" />
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Ophthalmic Scan Library
            </h3>
          </div>
          <span className="text-xs text-slate-500">
            {filteredScans.length} studies documented
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/70 text-slate-500 uppercase tracking-wider text-[10px] font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-5">Date</th>
                <th className="py-3 px-4">Patient</th>
                <th className="py-3 px-4">Eye</th>
                <th className="py-3 px-4">Modality</th>
                <th className="py-3 px-4">RNFLT Thickness</th>
                <th className="py-3 px-4">Analysis Status</th>
                <th className="py-3 px-5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredScans.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-500">
                    No ophthalmic scans found.
                  </td>
                </tr>
              ) : (
                filteredScans.map((s) => {
                  const isAnalyzed = s.status === 'Analyzed';
                  const isExtractionRequired =
                    s.status === 'RNFLT extraction required';

                  return (
                    <tr key={s.id} className="hover:bg-slate-50/80 transition">
                      <td className="py-3.5 px-5 font-mono text-slate-600 font-medium">
                        {s.date}
                      </td>
                      <td className="py-3.5 px-4">
                        <button
                          onClick={() => onSelectPatient(s.patient_id)}
                          className="text-slate-900 font-semibold hover:text-teal-700 text-left transition flex items-center space-x-1"
                        >
                          <span>{s.patient_name || s.patient_id}</span>
                          <ArrowUpRight className="w-3 h-3 text-slate-400" />
                        </button>
                        <div className="text-[10px] font-mono text-slate-400">
                          ID: {s.patient_id}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 font-mono font-bold text-teal-800">{s.eye}</td>
                      <td className="py-3.5 px-4">
                        <span className="font-mono text-[11px] bg-slate-100 px-2 py-0.5 rounded border border-slate-200 font-medium text-slate-700">
                          {s.scan_type}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 font-mono font-semibold text-slate-900">
                        {s.mean_rnflt_um ? `${s.mean_rnflt_um} µm` : <span className="text-slate-400 font-normal">Not recorded</span>}
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${
                            isAnalyzed
                              ? 'bg-teal-50 text-teal-700 border-teal-200'
                              : isExtractionRequired
                              ? 'bg-amber-50 text-amber-700 border-amber-200'
                              : 'bg-slate-100 text-slate-700 border-slate-200'
                          }`}
                        >
                          {s.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-5 text-right">
                        <button
                          onClick={() => onSelectScanForAnalysis(s)}
                          className="px-3 py-1 rounded-xl bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 font-semibold text-xs transition cursor-pointer"
                        >
                          {isAnalyzed ? 'View Analysis' : 'Run Analysis'}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ScansLibrary;
