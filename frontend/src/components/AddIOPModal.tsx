import React, { useState } from 'react';
import { X, Activity, Check } from 'lucide-react';

interface AddIOPModalProps {
  isOpen: boolean;
  onClose: () => void;
  patientId: string;
  patientName: string;
  onSuccess: () => void;
  apiBaseUrl: string;
}

export const AddIOPModal: React.FC<AddIOPModalProps> = ({
  isOpen,
  onClose,
  patientId,
  patientName,
  onSuccess,
  apiBaseUrl,
}) => {
  const today = new Date().toISOString().split('T')[0];
  const [date, setDate] = useState(today);
  const [eye, setEye] = useState<'OD' | 'OS'>('OD');
  const [iopValue, setIopValue] = useState<string>('18.0');
  const [method, setMethod] = useState<string>('Goldmann Applanation');
  const [notes, setNotes] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const val = parseFloat(iopValue);
    if (isNaN(val) || val <= 0 || val > 70) {
      setError('Please enter a valid IOP measurement (typically 5 to 60 mmHg).');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${apiBaseUrl}/api/clinical/patients/${patientId}/iop`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: patientId,
          date,
          eye,
          iop_mmhg: val,
          method,
          notes: notes || undefined,
        }),
      });

      if (!res.ok) {
        throw new Error('Failed to record IOP measurement.');
      }

      onSuccess();
      onClose();
    } catch (err: any) {
      setError(err.message || 'An error occurred while saving.');
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
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Record Tonometry (IOP)</h3>
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
              <label className="block text-slate-400 mb-1 font-medium">Measurement Date</label>
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Eye Laterality</label>
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

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">IOP Value (mmHg)</label>
              <input
                type="number"
                step="0.1"
                min="5"
                max="70"
                value={iopValue}
                onChange={(e) => setIopValue(e.target.value)}
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono text-sm focus:outline-none focus:border-teal-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Measurement Method</label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500"
              >
                <option value="Goldmann Applanation">Goldmann Applanation</option>
                <option value="Tonopen">Tonopen</option>
                <option value="Non-Contact Air-Puff">Non-Contact Air-Puff</option>
                <option value="Perkins Handheld">Perkins Handheld</option>
                <option value="Icare Rebound">Icare Rebound</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-medium">Clinical Notes (Optional)</label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Post-treatment morning check; target achieved."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500 resize-none"
            />
          </div>

          <div className="text-[11px] text-slate-500 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
            Note: IOP is stored as an independent longitudinal clinical parameter and is not passed to the structural RNFLT CNN.
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
              <span>{loading ? 'Saving...' : 'Save Measurement'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddIOPModal;
