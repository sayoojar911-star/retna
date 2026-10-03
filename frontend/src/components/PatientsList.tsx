import React, { useState } from 'react';
import { Users, Search, Plus, Eye, ChevronRight, Clock, CheckCircle2 } from 'lucide-react';
import { ClinicalPatient, ClinicalScan } from '../types';

interface PatientsListProps {
  patients: ClinicalPatient[];
  scans: ClinicalScan[];
  onSelectPatient: (patientId: string) => void;
  onOpenRegisterModal: () => void;
  onOpenImportModal: () => void;
  onSelectScanForAnalysis: (scan: ClinicalScan) => void;
}

export const PatientsList: React.FC<PatientsListProps> = ({
  patients,
  scans,
  onSelectPatient,
  onOpenRegisterModal,
  onOpenImportModal,
  onSelectScanForAnalysis,
}) => {
  const [search, setSearch] = useState('');
  const [filterEye, setFilterEye] = useState<string>('ALL');

  // Filter patients
  const filteredPatients = patients.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.id.toLowerCase().includes(search.toLowerCase());
    const matchesEye = filterEye === 'ALL' || p.eye_laterality === filterEye;
    return matchesSearch && matchesEye;
  });

  // Recent scans for dashboard summary
  const recentScans = scans.slice(0, 4);
  const pendingReviews = patients.filter(
    (p) =>
      p.status?.toLowerCase().includes('required') ||
      p.status?.toLowerCase().includes('pending')
  );
  const analyzedCount = patients.filter((p) => p.status === 'Analyzed').length;

  return (
    <div className="space-y-6">
      {/* 1. Doctor Dashboard Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {/* Active Patients */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center space-x-3.5 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
            <Users className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xl font-bold text-slate-900 font-mono">{patients.length}</div>
            <div className="text-[11px] text-slate-500 font-medium">Active Patients</div>
          </div>
        </div>

        {/* Recent Scans */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center space-x-3.5 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700">
            <Eye className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xl font-bold text-slate-900 font-mono">{scans.length}</div>
            <div className="text-[11px] text-slate-500 font-medium">Recent Scans</div>
          </div>
        </div>

        {/* Pending Reviews */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center space-x-3.5 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700">
            <Clock className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xl font-bold text-amber-800 font-mono">{pendingReviews.length}</div>
            <div className="text-[11px] text-slate-500 font-medium">Pending Reviews</div>
          </div>
        </div>

        {/* Completed Analyses */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4 flex items-center space-x-3.5 shadow-sm">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
            <CheckCircle2 className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xl font-bold text-emerald-800 font-mono">{analyzedCount}</div>
            <div className="text-[11px] text-slate-500 font-medium">Completed Analyses</div>
          </div>
        </div>
      </div>

      {/* 2. Search & Filter Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
        <div className="flex items-center space-x-3 flex-1 max-w-md">
          <div className="relative w-full">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by patient name or patient ID..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-teal-500 focus:bg-white transition"
            />
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Eye Laterality Filter */}
          <div className="flex items-center space-x-1 bg-slate-100 rounded-xl p-1 text-xs">
            {['ALL', 'OD', 'OS'].map((eye) => (
              <button
                key={eye}
                onClick={() => setFilterEye(eye)}
                className={`px-3 py-1 rounded-lg font-mono font-medium transition cursor-pointer ${
                  filterEye === eye
                    ? 'bg-white text-slate-900 shadow-xs font-semibold'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                {eye === 'ALL' ? 'All Eyes' : eye}
              </button>
            ))}
          </div>

          {/* Action Buttons */}
          <button
            onClick={onOpenRegisterModal}
            className="px-3.5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs transition flex items-center space-x-1.5 shadow-sm cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Register Patient</span>
          </button>
          <button
            onClick={onOpenImportModal}
            className="px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 font-medium text-xs transition flex items-center space-x-1.5 cursor-pointer"
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Import OCT</span>
          </button>
        </div>
      </div>

      {/* 3. Patients Table */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Users className="w-4 h-4 text-teal-700" />
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Patient Registry
            </h3>
          </div>
          <span className="text-xs text-slate-500">
            Showing {filteredPatients.length} of {patients.length} patients
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 uppercase text-[10px] tracking-wider font-semibold bg-slate-50/70">
                <th className="py-3 px-5">Patient Name</th>
                <th className="py-3 px-4">Patient ID</th>
                <th className="py-3 px-4">Age / Sex</th>
                <th className="py-3 px-4">Eye</th>
                <th className="py-3 px-4">Last Scan Date</th>
                <th className="py-3 px-4">Latest RNFLT</th>
                <th className="py-3 px-4">Analysis Status</th>
                <th className="py-3 px-5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredPatients.map((patient) => {
                const isAnalyzed = patient.status === 'Analyzed';
                const isExtractionRequired =
                  patient.status === 'RNFLT extraction required';

                return (
                  <tr
                    key={patient.id}
                    onClick={() => onSelectPatient(patient.id)}
                    className="hover:bg-slate-50/80 transition cursor-pointer group"
                  >
                    {/* Patient Photo (Rounded-square) & Name */}
                    <td className="py-3.5 px-5 flex items-center space-x-3">
                      {patient.photo_avatar ? (
                        <img
                          src={patient.photo_avatar}
                          alt={patient.name}
                          className="w-9 h-9 rounded-xl object-cover border border-slate-200 shadow-xs"
                        />
                      ) : (
                        <div className="w-9 h-9 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-800 font-bold text-xs">
                          {patient.name[0]}
                        </div>
                      )}
                      <div>
                        <div className="font-semibold text-slate-900 group-hover:text-teal-700 transition">
                          {patient.name}
                        </div>
                        {patient.is_demo && (
                          <span className="text-[9px] font-bold uppercase tracking-wider text-amber-700">
                            Research Demo
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Patient ID */}
                    <td className="py-3.5 px-4 font-mono font-medium text-slate-600 text-[11px]">
                      {patient.id}
                    </td>

                    {/* Age / Sex */}
                    <td className="py-3.5 px-4 text-slate-600">
                      {patient.age || 'Not recorded'} &bull; {patient.sex || 'Not recorded'}
                    </td>

                    {/* Eye Laterality */}
                    <td className="py-3.5 px-4 font-mono font-bold text-teal-800">
                      {patient.eye_laterality || 'OD'}
                    </td>

                    {/* Last Scan Date */}
                    <td className="py-3.5 px-4 text-slate-600 font-mono text-[11px]">
                      {patient.last_scan_date || 'Not recorded'}
                    </td>

                    {/* Latest RNFLT (Never fabricated) */}
                    <td className="py-3.5 px-4 font-mono font-semibold text-slate-900">
                      {patient.latest_rnflt_um !== null && patient.latest_rnflt_um !== undefined
                        ? `${patient.latest_rnflt_um} µm`
                        : <span className="text-slate-400 font-normal">Not recorded</span>}
                    </td>

                    {/* Analysis Status */}
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
                        {patient.status || 'Pending'}
                      </span>
                    </td>

                    {/* Action */}
                    <td className="py-3.5 px-5 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectPatient(patient.id);
                        }}
                        className="px-3 py-1 rounded-xl bg-slate-100 group-hover:bg-teal-600 group-hover:text-white text-slate-700 border border-slate-200 group-hover:border-teal-600 font-semibold text-xs transition inline-flex items-center space-x-1"
                      >
                        <span>Timeline</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. Recent Scans Quick Cards */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center space-x-2">
            <Eye className="w-4 h-4 text-teal-700" />
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Recent Scans Across Registry
            </h3>
          </div>
          <span className="text-xs text-slate-500">Latest imported studies</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {recentScans.map((scan) => (
            <div
              key={scan.id}
              className="bg-slate-50 hover:bg-slate-100/80 border border-slate-200 rounded-xl p-3.5 space-y-2 transition shadow-xs"
            >
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-900 truncate">
                  {scan.patient_name || scan.patient_id}
                </span>
                <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-white text-teal-800 border border-slate-200 font-bold">
                  {scan.eye}
                </span>
              </div>
              <div className="text-[11px] text-slate-500 font-mono">
                {scan.date} &bull; {scan.scan_type}
              </div>
              <div className="flex items-center justify-between pt-1">
                <span className="text-[11px] font-mono text-slate-700 font-bold">
                  {scan.mean_rnflt_um ? `${scan.mean_rnflt_um} µm` : '-'}
                </span>
                <button
                  onClick={() => onSelectScanForAnalysis(scan)}
                  className="text-xs text-teal-700 hover:text-teal-800 font-semibold"
                >
                  Analyze &rarr;
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PatientsList;
