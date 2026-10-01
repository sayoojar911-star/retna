import React, { useState } from 'react';
import { Upload, FileText, CheckCircle2, ArrowRight } from 'lucide-react';
import { DemoCase } from '../types';

interface ImportSectionProps {
  onAnalyze: (formData: FormData) => Promise<void>;
  onSelectDemoCase: (demoId: string) => Promise<void>;
  demoCases: DemoCase[];
  loading: boolean;
}

export const ImportSection: React.FC<ImportSectionProps> = ({
  onAnalyze,
  onSelectDemoCase,
  demoCases,
  loading,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [patientId, setPatientId] = useState('');
  const [age, setAge] = useState('');
  const [eye, setEye] = useState<'OD' | 'OS'>('OD');
  const [iop, setIop] = useState('');
  const [familyHistory, setFamilyHistory] = useState('unknown');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    const fd = new FormData();
    fd.append('file', selectedFile);
    if (patientId.trim()) fd.append('patient_id', patientId.trim());
    if (age.trim()) fd.append('age', age.trim());
    fd.append('eye', eye);
    if (iop.trim()) fd.append('iop', iop.trim());
    fd.append('family_history', familyHistory);

    await onAnalyze(fd);
  };

  return (
    <div className="space-y-6">
      {/* 1. Research Demo Case Quick Selector */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 mb-4 gap-2">
          <div>
            <h3 className="text-sm font-semibold text-white">
              Verified Research Demo Cases (Quick Load)
            </h3>
            <p className="text-xs text-slate-400">
              One-click validation of verified real Harvard-GDP samples &amp; QA test fixtures
            </p>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-teal-500/10 text-teal-300 border border-teal-500/20 w-fit">
            Deterministic Local Data
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {demoCases.map((c) => {
            const isNormal = c.id.includes('normal');
            const isCorrupt = c.id.includes('corrupt');
            return (
              <button
                key={c.id}
                onClick={() => onSelectDemoCase(c.id)}
                disabled={loading}
                className={`p-3.5 rounded-lg border text-left transition-all hover:scale-[1.01] ${
                  isNormal
                    ? 'bg-slate-950/80 hover:bg-slate-950 border-teal-500/30 hover:border-teal-400'
                    : isCorrupt
                    ? 'bg-slate-950/80 hover:bg-slate-950 border-rose-500/30 hover:border-rose-400'
                    : 'bg-slate-950/80 hover:bg-slate-950 border-indigo-500/30 hover:border-indigo-400'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-white truncate">{c.name}</span>
                  <span
                    className={`text-[9px] font-semibold uppercase px-1.5 py-0.5 rounded border ${
                      c.expected_quality === 'VALID'
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                        : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                    }`}
                  >
                    {c.expected_quality}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-snug line-clamp-2">
                  {c.description}
                </p>
                <div className="mt-2 text-[10px] text-slate-500 flex items-center justify-between font-mono">
                  <span>{c.glaucoma_ground_truth}</span>
                  <ArrowRight className="w-3 h-3 text-slate-400" />
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. File Upload & Clinical Intake Form */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="border-b border-slate-800 pb-3 mb-5">
          <h3 className="text-sm font-semibold text-white">
            Upload Custom OCT / RNFLT Study
          </h3>
          <p className="text-xs text-slate-400">
            Supports native NumPy archives (.npz, .npy) and volumetric cross-sections (.png, .jpg)
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* File Upload Drop Zone */}
          <div className="border-2 border-dashed border-slate-700 hover:border-teal-500/60 rounded-xl p-6 text-center transition-colors bg-slate-950/50">
            <input
              type="file"
              id="octFileInput"
              accept=".npz,.npy,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="octFileInput" className="cursor-pointer block">
              <Upload className="w-8 h-8 text-teal-400 mx-auto mb-2" />
              {selectedFile ? (
                <div>
                  <div className="text-xs font-semibold text-emerald-400 flex items-center justify-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>{selectedFile.name}</span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    {(selectedFile.size / 1024).toFixed(1)} KB &bull; Click to choose a different file
                  </div>
                </div>
              ) : (
                <div>
                  <div className="text-xs font-medium text-slate-300">
                    Click to select or drag &amp; drop OCT/RNFL study file
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1 font-mono">
                    Supported: .npz (Recommended 225x225 RNFLT), .npy, .png, .jpg
                  </div>
                </div>
              )}
            </label>
          </div>

          {/* Clinical Intake Fields */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3.5">
            {/* Patient ID */}
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Patient ID <span className="text-slate-500">(Optional)</span>
              </label>
              <input
                type="text"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                placeholder="e.g. SUB-042"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-teal-500/60"
              />
            </div>

            {/* Age */}
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Age <span className="text-slate-500">(Optional)</span>
              </label>
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                placeholder="e.g. 65"
                min="18"
                max="110"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-teal-500/60"
              />
            </div>

            {/* Eye Laterality */}
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Eye Laterality <span className="text-teal-400">*</span>
              </label>
              <select
                value={eye}
                onChange={(e) => setEye(e.target.value as 'OD' | 'OS')}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-teal-500/60"
              >
                <option value="OD">OD (Right Eye)</option>
                <option value="OS">OS (Left Eye)</option>
              </select>
            </div>

            {/* IOP */}
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                IOP (mmHg) <span className="text-slate-500">(Optional)</span>
              </label>
              <input
                type="number"
                step="0.1"
                value={iop}
                onChange={(e) => setIop(e.target.value)}
                placeholder="e.g. 18.5"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-teal-500/60"
              />
            </div>

            {/* Family History */}
            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">
                Family History <span className="text-slate-500">(Optional)</span>
              </label>
              <select
                value={familyHistory}
                onChange={(e) => setFamilyHistory(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-teal-500/60"
              >
                <option value="unknown">Unknown</option>
                <option value="yes">Yes (Positive)</option>
                <option value="no">No (Negative)</option>
              </select>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex items-center justify-between pt-2">
            <span className="text-[11px] text-slate-500">
              Files are processed in memory and validated against real technical quality bounds.
            </span>
            <button
              type="submit"
              disabled={!selectedFile || loading}
              className="px-5 py-2 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold text-xs transition disabled:opacity-40 flex items-center space-x-2"
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                  <span>Validating &amp; Processing...</span>
                </>
              ) : (
                <>
                  <FileText className="w-3.5 h-3.5" />
                  <span>Validate &amp; Analyze Study</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
