import React, { useState } from 'react';

export const AddVisitModal: React.FC<{ isOpen: boolean; onClose: () => void; patientId: string; apiBaseUrl: string; defaultEye?: string; onSuccess: () => void }> = ({ isOpen, onClose, patientId, apiBaseUrl, defaultEye = 'OD', onSuccess }) => {
  const [visitDate, setVisitDate] = useState(new Date().toISOString().slice(0, 10));
  const [eye, setEye] = useState(defaultEye);
  const [qc, setQc] = useState('VALID');
  const [rnfl, setRnfl] = useState('');
  const [iop, setIop] = useState('');
  const [vfMd, setVfMd] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const submit = async () => {
    setError(null);
    if (!visitDate || !eye) { setError('visit_date and eye are required.'); return; }
    setSaving(true);
    try {
      const payload: any = {
        visit_date: visitDate,
        eye,
        qc_status: qc || null,
        rnfl_available: !!rnfl,
        mean_rnflt_um: rnfl ? parseFloat(rnfl) : null,
        iop_mmhg: iop ? parseFloat(iop) : null,
        vf_md_db: vfMd ? parseFloat(vfMd) : null,
        analysis_timestamp: visitDate,
      };
      const forBase = (b: string) => b.replace(/\/$/, '');
      const urls = [
        `${forBase(apiBaseUrl)}/api/patients/${patientId}/visits`,
        `${forBase(apiBaseUrl)}/api/v1/patients/${patientId}/visits`,
        `${forBase(apiBaseUrl)}/api/clinical/patients/${patientId}/visits`,
        `${forBase(apiBaseUrl)}/api/v1/clinical/patients/${patientId}/visits`,
      ];
      let ok = false;
      let last = '';
      for (const u of urls) {
        const r = await fetch(u, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
        if (r.ok) { ok = true; break; }
        last = `${r.status} ${await r.text()}`;
      }
      if (!ok) throw new Error(last || 'Failed to create visit');
      onSuccess();
    } catch (e: any) {
      setError(String(e?.message || e));
    } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xl w-full max-w-lg p-5 space-y-4">
        <h3 className="text-sm font-bold text-slate-900">Add Visit</h3>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <label className="space-y-1"><span className="text-slate-600">Visit date *</span><input type="date" value={visitDate} onChange={(e) => setVisitDate(e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-2" /></label>
          <label className="space-y-1"><span className="text-slate-600">Eye *</span><select value={eye} onChange={(e) => setEye(e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-2"><option>OD</option><option>OS</option><option>OU</option></select></label>
          <label className="space-y-1"><span className="text-slate-600">QC status</span><select value={qc} onChange={(e) => setQc(e.target.value)} className="w-full border border-slate-200 rounded-lg px-3 py-2"><option>VALID</option><option>INVALID</option><option>UNKNOWN</option></select></label>
          <label className="space-y-1"><span className="text-slate-600">RNFL mean (µm)</span><input value={rnfl} onChange={(e) => setRnfl(e.target.value)} placeholder="e.g. 82.4" className="w-full border border-slate-200 rounded-lg px-3 py-2" /></label>
          <label className="space-y-1"><span className="text-slate-600">IOP (mmHg)</span><input value={iop} onChange={(e) => setIop(e.target.value)} placeholder="e.g. 16" className="w-full border border-slate-200 rounded-lg px-3 py-2" /></label>
          <label className="space-y-1"><span className="text-slate-600">VF MD (dB)</span><input value={vfMd} onChange={(e) => setVfMd(e.target.value)} placeholder="e.g. -2.4" className="w-full border border-slate-200 rounded-lg px-3 py-2" /></label>
        </div>
        {error && <div className="text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-lg p-2.5">{error}</div>}
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-3.5 py-2 rounded-xl border border-slate-200 text-slate-700 text-xs">Cancel</button>
          <button onClick={submit} disabled={saving} className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold disabled:opacity-50">{saving ? 'Saving…' : 'Save Visit'}</button>
        </div>
      </div>
    </div>
  );
};
export default AddVisitModal;
