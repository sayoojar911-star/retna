import React, { useState } from 'react';
import { X, Check, Activity } from 'lucide-react';
import { VisualFieldRecord } from '../types';

interface AddVisualFieldModalProps {
  isOpen: boolean;
  onClose: () => void;
  patientId: string;
  onSuccess: (record: VisualFieldRecord) => void;
  apiBaseUrl: string;
}

export const AddVisualFieldModal: React.FC<AddVisualFieldModalProps> = ({
  isOpen,
  onClose,
  patientId,
  onSuccess,
  apiBaseUrl,
}) => {
  const today = new Date().toISOString().split('T')[0];
  const [date, setDate] = useState(today);
  const [eye, setEye] = useState<'OD' | 'OS'>('OD');
  const [mdDb, setMdDb] = useState<number | ''>(-4.5);
  const [psdDb, setPsdDb] = useState<number | ''>(3.5);
  const [vfiPct, setVfiPct] = useState<number | ''>(92.0);
  const [reliability, setReliability] = useState('Reliable');
  const [notes, setNotes] = useState('');
  const [fileName, setFileName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (mdDb === '') {
      setError('Mean Deviation (MD) is required.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${apiBaseUrl}/api/patients/${patientId}/visual-field`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: patientId,
          date,
          eye,
          md_db: Number(mdDb),
          psd_db: psdDb !== '' ? Number(psdDb) : null,
          vfi_pct: vfiPct !== '' ? Number(vfiPct) : null,
          reliability,
          notes: notes.trim() || undefined,
          file_name: fileName.trim() || undefined,
        }),
      });

      if (!res.ok) {
        throw new Error('Failed to record visual field measurement.');
      }

      const data = await res.json();
      onSuccess(data.record);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Error recording visual field.');
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
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Record Visual Field (HVF 24-2)</h3>
              <p className="text-xs text-slate-400">Perimetric indices &amp; defect tracking</p>
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
              <label className="block text-slate-400 mb-1 font-medium">Test Date</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500 font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Eye</label>
              <select
                value={eye}
                onChange={(e) => setEye(e.target.value as 'OD' | 'OS')}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500"
              >
                <option value="OD">Right Eye (OD)</option>
                <option value="OS">Left Eye (OS)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Mean Dev (MD) *</label>
              <div className="relative">
                <input
                  type="number"
                  step="0.1"
                  value={mdDb}
                  onChange={(e) => setMdDb(e.target.value === '' ? '' : Number(e.target.value))}
                  placeholder="-4.5"
                  required
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-teal-500"
                />
                <span className="absolute right-2.5 top-2 text-[10px] text-slate-500 font-mono">dB</span>
              </div>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">Pattern SD (PSD)</label>
              <div className="relative">
                <input
                  type="number"
                  step="0.1"
                  value={psdDb}
                  onChange={(e) => setPsdDb(e.target.value === '' ? '' : Number(e.target.value))}
                  placeholder="3.5"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-teal-500"
                />
                <span className="absolute right-2.5 top-2 text-[10px] text-slate-500 font-mono">dB</span>
              </div>
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-medium">VFI (%)</label>
              <div className="relative">
                <input
                  type="number"
                  step="1"
                  min="0"
                  max="100"
                  value={vfiPct}
                  onChange={(e) => setVfiPct(e.target.value === '' ? '' : Number(e.target.value))}
                  placeholder="92"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-teal-500"
                />
                <span className="absolute right-2.5 top-2 text-[10px] text-slate-500 font-mono">%</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Test Reliability</label>
              <select
                value={reliability}
                onChange={(e) => setReliability(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500"
              >
                <option value="Reliable">Reliable (&lt;15% fixation losses)</option>
                <option value="Borderline">Borderline Reliability</option>
                <option value="Unreliable">Unreliable (High FL/FN/FP)</option>
              </select>
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Report File (Optional)</label>
              <input
                type="text"
                value={fileName}
                onChange={(e) => setFileName(e.target.value)}
                placeholder="e.g. HVF_24_2.pdf"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-medium">Clinical Notes</label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Superior paracentral scotoma correlating with inferior RNFL loss."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500 resize-none"
            />
          </div>

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
              <span>{loading ? 'Recording...' : 'Record Visual Field'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
export default AddVisualFieldModal;
