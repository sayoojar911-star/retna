import React, { useState } from 'react';
import { X, FileText, Check, Upload } from 'lucide-react';

interface AddReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  patientId: string;
  patientName: string;
  onSuccess: () => void;
  apiBaseUrl: string;
}

export const AddReportModal: React.FC<AddReportModalProps> = ({
  isOpen,
  onClose,
  patientId,
  patientName,
  onSuccess,
  apiBaseUrl,
}) => {
  const today = new Date().toISOString().split('T')[0];
  const [reportDate, setReportDate] = useState(today);
  const [reportType, setReportType] = useState('Humphrey Visual Field 24-2');
  const [eye, setEye] = useState<'OD' | 'OS' | 'OU'>('OD');
  const [fileName, setFileName] = useState('HVF_24-2_Clinical_Report.pdf');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${apiBaseUrl}/api/clinical/patients/${patientId}/reports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: patientId,
          report_date: reportDate,
          report_type: reportType,
          eye,
          file_name: fileName || 'clinical_document.pdf',
          notes: notes || undefined,
        }),
      });

      if (!res.ok) {
        throw new Error('Failed to attach clinical report.');
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'An error occurred while saving report.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-md overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Attach Clinical Report</h3>
              <p className="text-xs text-slate-400 font-mono">
                {patientName} ({patientId})
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
          {error && (
            <div className="p-3 bg-rose-950/60 border border-rose-900 rounded-lg text-rose-300">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Exam Date</label>
              <input
                type="date"
                value={reportDate}
                onChange={(e) => setReportDate(e.target.value)}
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Eye Laterality</label>
              <select
                value={eye}
                onChange={(e) => setEye(e.target.value as any)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500"
              >
                <option value="OD">Right Eye (OD)</option>
                <option value="OS">Left Eye (OS)</option>
                <option value="OU">Bilateral (OU)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-medium">Report / Study Type</label>
            <select
              value={reportType}
              onChange={(e) => {
                setReportType(e.target.value);
                setFileName(`${e.target.value.replace(/[^a-zA-Z0-9]/g, '_')}_${reportDate}.pdf`);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500"
            >
              <option value="Humphrey Visual Field 24-2">Humphrey Visual Field 24-2</option>
              <option value="Humphrey Visual Field 10-2">Humphrey Visual Field 10-2</option>
              <option value="Central Corneal Thickness (Pachymetry)">Central Corneal Thickness (Pachymetry)</option>
              <option value="Gonioscopy & Angle Assessment">Gonioscopy &amp; Angle Assessment</option>
              <option value="OCT Angiography (OCTA)">OCT Angiography (OCTA)</option>
              <option value="Fundus Photography Clinical Notes">Fundus Photography Clinical Notes</option>
              <option value="Specialist Consultation Letter">Specialist Consultation Letter</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-medium">Document / File Reference</label>
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={fileName}
                onChange={(e) => setFileName(e.target.value)}
                required
                className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono text-[11px] focus:outline-none focus:border-teal-500"
              />
              <button
                type="button"
                className="px-2.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg flex items-center space-x-1"
                title="Select local document"
              >
                <Upload className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-medium">Physician Notes / Summary (Optional)</label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Mild inferior arcuate defect noted on visual field."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500 resize-none"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-500 text-white font-medium flex items-center space-x-1.5 transition disabled:opacity-50"
            >
              <Check className="w-3.5 h-3.5" />
              <span>{loading ? 'Attaching...' : 'Attach Report'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddReportModal;
