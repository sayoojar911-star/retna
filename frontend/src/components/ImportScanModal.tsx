import React, { useState } from 'react';
import { X, Upload, FileUp, AlertTriangle, CheckCircle2, ShieldCheck, Loader2 } from 'lucide-react';
import { ClinicalPatient } from '../types';

interface ImportScanModalProps {
  isOpen: boolean;
  onClose: () => void;
  patients: ClinicalPatient[];
  initialPatientId?: string;
  onAnalyze: (formData: FormData) => Promise<void>;
  loading: boolean;
}

export const ImportScanModal: React.FC<ImportScanModalProps> = ({
  isOpen,
  onClose,
  patients,
  initialPatientId,
  onAnalyze,
  loading,
}) => {
  const today = new Date().toISOString().split('T')[0];
  const [patientId, setPatientId] = useState(initialPatientId || (patients[0]?.id || 'GM-DEMO-01'));
  const [eye, setEye] = useState<'OD' | 'OS'>('OD');
  const [scanDate, setScanDate] = useState(today);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationStage, setValidationStage] = useState<'idle' | 'received' | 'checking' | 'verdict'>('idle');

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file: File) => {
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    const validExtensions = ['.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.dcm', '.npz'];

    if (!validExtensions.includes(ext)) {
      setError(`Unsupported format '${ext}'. Please upload an OCT scan image (PNG, JPG, JPEG, TIFF, or DICOM).`);
      setSelectedFile(null);
      return;
    }

    setError(null);
    setSelectedFile(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select or drop an OCT scan image to import.');
      return;
    }

    const currentPatient = patients.find((p) => p.id === patientId);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('patient_id', patientId);
    formData.append('eye', eye);
    formData.append('scan_date', scanDate);
    if (currentPatient?.age) {
      formData.append('age', currentPatient.age.toString());
    }

    setValidationStage('received');

    try {
      // Show staged feedback: "Scan received" -> "Checking scan quality..."
      setTimeout(() => setValidationStage('checking'), 400);
      await onAnalyze(formData);
      setValidationStage('verdict');
      setTimeout(() => {
        onClose();
        setValidationStage('idle');
      }, 700);
    } catch (err: any) {
      setValidationStage('idle');
      setError(err.message || 'Scan validation or analysis failed.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-xs">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
              <Upload className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Import OCT Scan</h3>
              <p className="text-xs text-slate-500">Optical Coherence Tomography Scan Ingestion</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-xs">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 flex items-start space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Validation Progress Stages Banner */}
          {loading && (
            <div className="p-4 bg-teal-50 border border-teal-200 rounded-xl space-y-2 text-teal-950">
              <div className="flex items-center space-x-2 text-xs font-bold text-teal-800">
                <Loader2 className="w-4 h-4 animate-spin text-teal-600" />
                <span>Processing OCT Scan Acquisition</span>
              </div>
              <div className="space-y-1 pl-6 text-[11px]">
                <div className="flex items-center space-x-1.5 font-medium text-teal-900">
                  <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
                  <span>Scan received</span>
                </div>
                <div className={`flex items-center space-x-1.5 font-medium ${validationStage === 'checking' || validationStage === 'verdict' ? 'text-teal-900' : 'text-slate-400'}`}>
                  {validationStage === 'checking' ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-teal-600" />
                  ) : validationStage === 'verdict' ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
                  ) : (
                    <div className="w-3.5 h-3.5 rounded-full border border-slate-300" />
                  )}
                  <span>Checking scan quality...</span>
                </div>
                <div className={`flex items-center space-x-1.5 font-medium ${validationStage === 'verdict' ? 'text-teal-900 font-bold' : 'text-slate-400'}`}>
                  {validationStage === 'verdict' ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
                  ) : (
                    <div className="w-3.5 h-3.5 rounded-full border border-slate-300" />
                  )}
                  <span>Scan quality: Valid</span>
                </div>
              </div>
            </div>
          )}

          {/* 1. Patient & Eye Selection */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-700 mb-1 font-semibold">Select Patient</label>
              <select
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white"
              >
                {patients.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} ({p.id})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-700 mb-1 font-semibold">Select Eye</label>
              <select
                value={eye}
                onChange={(e) => setEye(e.target.value as 'OD' | 'OS')}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white font-mono font-medium"
              >
                <option value="OD">Right Eye (OD)</option>
                <option value="OS">Left Eye (OS)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-slate-700 mb-1 font-semibold">Scan Date</label>
            <input
              type="date"
              value={scanDate}
              onChange={(e) => setScanDate(e.target.value)}
              required
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-slate-900 focus:outline-none focus:border-teal-500 focus:bg-white font-mono"
            />
          </div>

          {/* Upload Dropzone */}
          <div>
            <label className="block text-slate-700 mb-1 font-semibold">Upload OCT Scan Image</label>
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-2xl p-6 text-center transition cursor-pointer ${
                dragActive
                  ? 'border-teal-500 bg-teal-50/50'
                  : selectedFile
                  ? 'border-teal-400 bg-teal-50/30'
                  : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'
              }`}
              onClick={() => document.getElementById('scan-file-input')?.click()}
            >
              <input
                id="scan-file-input"
                type="file"
                className="hidden"
                accept=".png,.jpg,.jpeg,.tif,.tiff,.bmp,.dcm,.npz"
                onChange={handleFileChange}
              />
              <FileUp className="w-8 h-8 mx-auto text-teal-600 mb-2" />
              {selectedFile ? (
                <div>
                  <span className="font-mono text-xs text-teal-900 font-bold block">
                    {selectedFile.name}
                  </span>
                  <span className="text-[11px] text-slate-500 mt-0.5 block">
                    {(selectedFile.size / 1024).toFixed(1)} KB &bull; Click to change scan
                  </span>
                </div>
              ) : (
                <div>
                  <span className="text-xs text-slate-800 font-medium block">
                    Drop OCT Scan Image here, or browse files
                  </span>
                  <span className="text-[10px] text-slate-500 mt-1 block">
                    Supported: PNG, JPG, JPEG, TIFF, DICOM (.dcm)
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Clinical Workflow Explanation */}
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-[11px] text-slate-600 space-y-1">
            <div className="font-semibold text-slate-800 flex items-center space-x-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-teal-600 flex-shrink-0" />
              <span>Standard Clinical Pipeline</span>
            </div>
            <p className="leading-relaxed">
              Uploaded scan undergoes automated quality verification and modality detection. Legitimate RNFL thickness maps are calibrated and evaluated by the Harvard-GD CNN for glaucoma-associated classification and real Grad-CAM generation.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !selectedFile}
              className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold flex items-center space-x-2 shadow-sm transition disabled:opacity-50 cursor-pointer"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>{loading ? 'Checking scan quality...' : 'Upload OCT Scan'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ImportScanModal;
