import React, { useState } from 'react';
import { X, UserPlus, Check, Image as ImageIcon } from 'lucide-react';
import { ClinicalPatient } from '../types';

interface RegisterPatientModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (newPatient: ClinicalPatient) => void;
  apiBaseUrl: string;
}

export const RegisterPatientModal: React.FC<RegisterPatientModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  apiBaseUrl,
}) => {
  const [name, setName] = useState('');
  const [patientId, setPatientId] = useState('');
  const [age, setAge] = useState<number | ''>(55);
  const [dob, setDob] = useState('');
  const [sex, setSex] = useState('Female');
  const [eyeLaterality, setEyeLaterality] = useState('OD');
  const [familyHistory, setFamilyHistory] = useState('No known family history of glaucoma');
  const [clinicalNotes, setClinicalNotes] = useState('');
  const [photoAvatar, setPhotoAvatar] = useState<string | null>(null);
  const [isDemo, setIsDemo] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const reader = new FileReader();
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          setPhotoAvatar(reader.result);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Patient name is required.');
      return;
    }
    if (!age || Number(age) <= 0 || Number(age) > 120) {
      setError('Please provide a valid patient age.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${apiBaseUrl}/api/patients`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name.trim(),
          patient_id: patientId.trim() || undefined,
          age: Number(age),
          dob: dob || undefined,
          sex,
          eye_laterality: eyeLaterality,
          family_history: familyHistory.trim(),
          clinical_notes: clinicalNotes.trim(),
          photo_avatar: photoAvatar || undefined,
          is_demo: isDemo,
        }),
      });

      if (!res.ok) {
        throw new Error('Failed to register patient in workstation.');
      }

      const created: ClinicalPatient = await res.json();
      onSuccess(created);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Error creating patient.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-lg overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
              <UserPlus className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Register Clinical Patient</h3>
              <p className="text-xs text-slate-400">Add biodata, photo, and clinical baseline</p>
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
        <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs max-h-[80vh] overflow-y-auto">
          {error && (
            <div className="p-3 bg-rose-950/60 border border-rose-900 rounded-lg text-rose-300">
              {error}
            </div>
          )}

          {/* Photo Upload Row */}
          <div className="flex items-center space-x-4 bg-slate-950/60 p-3 rounded-lg border border-slate-800">
            <div className="w-14 h-14 rounded-lg bg-slate-900 border border-slate-700/80 overflow-hidden flex items-center justify-center flex-shrink-0">
              {photoAvatar ? (
                <img src={photoAvatar} alt="Preview" className="w-full h-full object-cover" />
              ) : (
                <ImageIcon className="w-6 h-6 text-slate-600" />
              )}
            </div>
            <div className="flex-1">
              <label className="block text-slate-300 text-xs font-medium mb-1">
                Patient Photo / Avatar
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={handlePhotoUpload}
                className="text-[11px] text-slate-400 file:mr-2 file:py-1 file:px-2.5 file:rounded-md file:border-0 file:text-[11px] file:bg-slate-800 file:text-slate-200 hover:file:bg-slate-700 cursor-pointer"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Patient Full Name *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Ramesh Patel"
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Patient ID (Auto if blank)</label>
              <input
                type="text"
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                placeholder="e.g. GM-006"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-teal-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Age *</label>
              <input
                type="number"
                min="1"
                max="120"
                value={age}
                onChange={(e) => setAge(e.target.value === '' ? '' : Number(e.target.value))}
                required
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-teal-500"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Date of Birth</label>
              <input
                type="date"
                value={dob}
                onChange={(e) => setDob(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500 font-mono"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Sex</label>
              <select
                value={sex}
                onChange={(e) => setSex(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500"
              >
                <option value="Female">Female</option>
                <option value="Male">Male</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Primary Eye Laterality</label>
              <select
                value={eyeLaterality}
                onChange={(e) => setEyeLaterality(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500"
              >
                <option value="OD">Right Eye (OD)</option>
                <option value="OS">Left Eye (OS)</option>
                <option value="OU">Bilateral (OU)</option>
              </select>
            </div>
            <div>
              <label className="block text-slate-400 mb-1 font-medium">Family History of Glaucoma</label>
              <input
                type="text"
                value={familyHistory}
                onChange={(e) => setFamilyHistory(e.target.value)}
                placeholder="e.g. Maternal grandmother diagnosed"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-medium">Clinical Notes &amp; History</label>
            <textarea
              rows={2}
              value={clinicalNotes}
              onChange={(e) => setClinicalNotes(e.target.value)}
              placeholder="e.g. Borderline cup-to-disc ratio noted during routine optometry exam."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-teal-500 resize-none"
            />
          </div>

          {/* Research Demo Marker Checkbox */}
          <div className="flex items-center space-x-2 pt-1">
            <input
              type="checkbox"
              id="is_demo"
              checked={isDemo}
              onChange={(e) => setIsDemo(e.target.checked)}
              className="rounded bg-slate-950 border-slate-800 text-teal-600 focus:ring-teal-500"
            />
            <label htmlFor="is_demo" className="text-slate-400 text-xs cursor-pointer">
              Mark as <strong className="text-amber-300">Research Demo — Not a Real Patient</strong>
            </label>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end space-x-2 pt-3 border-t border-slate-800">
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
              <span>{loading ? 'Registering...' : 'Register Patient'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
export default RegisterPatientModal;
