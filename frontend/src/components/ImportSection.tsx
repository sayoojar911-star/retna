import React, { useState } from 'react';
import { Upload, FileText, CheckCircle2, ArrowRight, ShieldAlert, Sparkles, FileImage, Cpu } from 'lucide-react';
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
  const [inputType, setInputType] = useState<'rnflt_numeric' | 'raw_oct'>('rnflt_numeric');
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

  const handleInputTypeSelect = (type: 'rnflt_numeric' | 'raw_oct') => {
    setInputType(type);
    setSelectedFile(null); // Clear previous file selection when switching modality
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    const fd = new FormData();
    fd.append('file', selectedFile);
    fd.append('input_type', inputType);
    if (patientId.trim()) fd.append('patient_id', patientId.trim());
    if (age.trim()) fd.append('age', age.trim());
    fd.append('eye', eye);
    if (iop.trim()) fd.append('iop', iop.trim());
    fd.append('family_history', familyHistory);

    await onAnalyze(fd);
  };

  const filteredDemoCases = demoCases.filter((c) => {
    if (inputType === 'raw_oct') {
      return c.input_type === 'raw_oct' || c.id.includes('raw');
    }
    return c.input_type === 'rnflt_numeric' || !c.id.includes('raw');
  });

  return (
    <div className="space-y-6">
      {/* 1. SELECT INPUT TYPE SECTION */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm space-y-4">
        <div className="border-b border-slate-800 pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              SELECT INPUT TYPE
            </h3>
            <p className="text-sm font-semibold text-white mt-0.5">
                Upload an OCT scan image to analyze
              </p>
          </div>
          <span className="text-[11px] font-mono px-2.5 py-1 rounded bg-teal-500/10 text-teal-300 border border-teal-500/20 w-fit">
            Modality Gate: {inputType === 'rnflt_numeric' ? 'RNFLT CNN Pipeline' : 'QA Validation Only'}
          </span>
        </div>

        {/* Input Type Selection Buttons */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          {/* Option A: RNFLT Numerical Map */}
          <button
            type="button"
            onClick={() => handleInputTypeSelect('rnflt_numeric')}
            className={`p-4 rounded-xl border text-left transition-all relative ${
              inputType === 'rnflt_numeric'
                ? 'bg-slate-950 border-teal-500 ring-2 ring-teal-500/20 shadow-md'
                : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 opacity-75 hover:opacity-100'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2.5">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    inputType === 'rnflt_numeric'
                      ? 'bg-teal-500/20 text-teal-400'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  <Cpu className="w-4 h-4" />
                </div>
                <span className="text-sm font-bold text-white">
                  RNFLT Numerical Map
                </span>
              </div>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${
                  inputType === 'rnflt_numeric'
                    ? 'bg-teal-500/10 text-teal-300 border-teal-500/30 font-semibold'
                    : 'bg-slate-800 text-slate-400 border-slate-700'
                }`}
              >
                Supported Formats: .npy, .npz
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed font-medium">
              &ldquo;Use a numerical RNFLT map compatible with the currently trained Harvard-GD model.&rdquo;
            </p>
            <div className="mt-3 pt-2.5 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center space-x-1.5">
              <span className="text-teal-400 font-semibold">&bull; End-to-end:</span>
              <span>Validation &rarr; Preprocessing &rarr; Harvard-GD CNN &rarr; Grad-CAM</span>
            </div>
          </button>

          {/* Option B: Raw / Digital OCT Study */}
          <button
            type="button"
            onClick={() => handleInputTypeSelect('raw_oct')}
            className={`p-4 rounded-xl border text-left transition-all relative ${
              inputType === 'raw_oct'
                ? 'bg-slate-950 border-sky-500 ring-2 ring-sky-500/20 shadow-md'
                : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 opacity-75 hover:opacity-100'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2.5">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                    inputType === 'raw_oct'
                      ? 'bg-sky-500/20 text-sky-400'
                      : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  <FileImage className="w-4 h-4" />
                </div>
                <span className="text-sm font-bold text-white">
                  Raw / Digital OCT Study
                </span>
              </div>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${
                  inputType === 'raw_oct'
                    ? 'bg-sky-500/10 text-sky-300 border-sky-500/30 font-semibold'
                    : 'bg-slate-800 text-slate-400 border-slate-700'
                }`}
              >
                Supported: .png, .jpg, .tif, .dcm
              </span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed font-medium">
              &ldquo;Raw OCT images require an OCT-to-RNFLT extraction/segmentation stage before they can be analyzed by the current RNFLT-trained model.&rdquo;
            </p>
            <div className="mt-3 pt-2.5 border-t border-slate-800/80 text-[11px] text-slate-400 flex items-center space-x-1.5">
              <span className="text-sky-400 font-semibold">&bull; Isolated:</span>
              <span>Technical validation only &bull; RNFLT extraction required &bull; CNN bypassed</span>
            </div>
          </button>
        </div>
      </div>

      {/* 2. Research Demo Case Quick Selector (Filtered by Selected Input Type) */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-3 mb-4 gap-2">
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
              <span>Verified Demo Cases (Quick Load)</span>
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                  inputType === 'rnflt_numeric'
                    ? 'bg-teal-500/10 text-teal-400 border-teal-500/20'
                    : 'bg-sky-500/10 text-sky-400 border-sky-500/20'
                }`}
              >
                {inputType === 'rnflt_numeric' ? 'HARVARD-GD NUMERICAL MAPS' : 'RAW DIGITAL OCT SCAN'}
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              {inputType === 'rnflt_numeric'
                ? 'One-click evaluation of real held-out Harvard-GD RNFLT test samples'
                : 'One-click evaluation of raw retinal B-scan cross-section technical validation'}
            </p>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800 w-fit">
            Showing {filteredDemoCases.length} compatible case{filteredDemoCases.length === 1 ? '' : 's'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filteredDemoCases.map((c) => {
            const isHarvardGD = c.id.includes('harvard_gd');
            const isNormal = c.id.includes('normal') || c.id.includes('0170');
            const isCorrupt = c.id.includes('corrupt');
            const isRawOct = c.id.includes('raw');

            return (
              <button
                key={c.id}
                onClick={() => onSelectDemoCase(c.id)}
                disabled={loading}
                className={`p-3.5 rounded-lg border text-left transition-all hover:scale-[1.01] ${
                  isRawOct
                    ? 'bg-slate-950/90 hover:bg-slate-950 border-sky-500/40 hover:border-sky-400 ring-1 ring-sky-500/20'
                    : isHarvardGD
                    ? 'bg-slate-950/90 hover:bg-slate-950 border-teal-500/40 hover:border-teal-400 ring-1 ring-teal-500/20'
                    : isNormal
                    ? 'bg-slate-950/80 hover:bg-slate-950 border-emerald-500/30 hover:border-emerald-400'
                    : isCorrupt
                    ? 'bg-slate-950/80 hover:bg-slate-950 border-rose-500/30 hover:border-rose-400'
                    : 'bg-slate-950/80 hover:bg-slate-950 border-indigo-500/30 hover:border-indigo-400'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-semibold text-white truncate flex items-center space-x-1.5">
                    {isHarvardGD && <Sparkles className="w-3 h-3 text-teal-400 flex-shrink-0" />}
                    {isRawOct && <FileImage className="w-3 h-3 text-sky-400 flex-shrink-0" />}
                    <span>{c.name}</span>
                  </span>
                  <span
                    className={`text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border ${
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
                <div className="mt-2.5 text-[10px] text-slate-400 flex items-center justify-between font-mono pt-2 border-t border-slate-900">
                  <span className={isRawOct ? 'text-sky-300 font-semibold' : 'text-teal-300 font-semibold'}>
                    {c.glaucoma_ground_truth}
                  </span>
                  <ArrowRight className="w-3 h-3 text-slate-400" />
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 3. IMPORT OCT STUDY FILE UPLOAD & CLINICAL INTAKE FORM */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-6 shadow-sm space-y-5">
        <div className="border-b border-slate-800 pb-3">
          <h3 className="text-sm font-semibold text-white">
            Import OCT Scan
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            {inputType === 'rnflt_numeric'
              ? 'Import quantitative 225×225 peripapillary RNFL thickness map (.npz or .npy)'
              : 'Import OCT scan image (.png, .jpg, .jpeg, .tif, .tiff, .bmp, .dcm)'}
          </p>
        </div>

        {/* Input Guidance Notice */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-lg p-3 text-xs text-slate-400 flex items-start space-x-2">
          <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="text-[11px] text-slate-300">
            {inputType === 'rnflt_numeric' ? (
              <span>
                <strong>RNFLT Numerical Input:</strong> The trained Harvard-GD ResNet-18 model will execute classification inference and generate real Grad-CAM visual saliency heatmaps based on layer4 activations.
              </span>
            ) : (
              <span>
                <strong>Raw OCT Study Input:</strong> Performs rigorous technical validation (file format, decoding, non-zero variance, absence of NaNs, and optical dimensions). Raw images are safely routed to <em>RNFLT Extraction Required</em> without passing into the thickness-trained CNN.
              </span>
            )}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* File Upload Drop Zone */}
          <div
            className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors bg-slate-950/50 ${
              inputType === 'rnflt_numeric'
                ? 'border-slate-700 hover:border-teal-500/60'
                : 'border-slate-700 hover:border-sky-500/60'
            }`}
          >
            <input
              type="file"
              id="octFileInput"
              accept={
                inputType === 'rnflt_numeric'
                  ? '.npz,.npy'
                  : '.png,.jpg,.jpeg,.tif,.tiff,.bmp,.dcm'
              }
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="octFileInput" className="cursor-pointer block">
              <Upload
                className={`w-8 h-8 mx-auto mb-2 ${
                  inputType === 'rnflt_numeric' ? 'text-teal-400' : 'text-sky-400'
                }`}
              />
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
                    Click to select or drag &amp; drop {inputType === 'rnflt_numeric' ? 'RNFLT numerical map' : 'OCT scan image'}
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1 font-mono">
                    {inputType === 'rnflt_numeric'
                      ? 'Supported formats: .npy, .npz (Harvard-GD compatible RNFLT map)'
                      : 'Supported formats: .png, .jpg, .jpeg, .tif, .tiff, .bmp, .dcm'}
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
                placeholder="e.g. HARVARD-0419"
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
                placeholder="e.g. 68"
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
                placeholder="e.g. 19.5"
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
              {inputType === 'rnflt_numeric'
                ? 'Processed through Harvard-GD ResNet-18 CNN with real Grad-CAM generation.'
                : 'Technically validated for format, dimensions, variance, and data integrity.'}
            </span>
            <button
              type="submit"
              disabled={!selectedFile || loading}
              className={`px-5 py-2 rounded-lg font-semibold text-xs transition disabled:opacity-40 flex items-center space-x-2 ${
                inputType === 'rnflt_numeric'
                  ? 'bg-teal-500 hover:bg-teal-400 text-slate-950'
                  : 'bg-sky-500 hover:bg-sky-400 text-slate-950'
              }`}
            >
              {loading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                    <span>Processing OCT Scan...</span>
                </>
              ) : (
                <>
                  <FileText className="w-3.5 h-3.5" />
                  <span>
                    {inputType === 'rnflt_numeric' ? 'Upload OCT Scan & Analyze' : 'Upload OCT Scan'}
                  </span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
