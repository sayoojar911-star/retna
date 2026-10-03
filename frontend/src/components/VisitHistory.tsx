import React, { useEffect, useState } from 'react';

interface VisitRecord {
  visit_id: string;
  visit_date: string;
  eye: string;
  qc_status?: string | null;
  mean_rnflt_um?: number | null;
  iop_mmhg?: number | null;
  vf_md_db?: number | null;
  model_version?: string | null;
  predicted_category?: string | null;
  classification_score?: number | null;
  analysis_timestamp?: string | null;
}

export const VisitHistory: React.FC<{ patientId: string; apiBaseUrl: string; onAddVisit: () => void }> = ({ patientId, apiBaseUrl, onAddVisit }) => {
  const [visits, setVisits] = useState<VisitRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const forBase = (b: string) => b.replace(/\/$/, '');
        const tryUrls = [
          `${forBase(apiBaseUrl)}/api/patients/${patientId}/visits`,
          `${forBase(apiBaseUrl)}/api/v1/patients/${patientId}/visits`,
          `${forBase(apiBaseUrl)}/api/clinical/patients/${patientId}/visits`,
          `${forBase(apiBaseUrl)}/api/v1/clinical/patients/${patientId}/visits`,
        ];
        let lastErr = '';
        for (const u of tryUrls) {
          try {
            const r = await fetch(u);
            if (r.ok) {
              const j = await r.json();
              if (!cancelled) setVisits(Array.isArray(j) ? j : j.visits || []);
              return;
            }
            lastErr = `${r.status} ${await r.text()}`;
          } catch (e: any) {
            lastErr = String(e?.message || e);
          }
        }
        if (!cancelled) setError(lastErr || 'Failed to load visits');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [patientId, apiBaseUrl]);

  if (loading) return <div className="p-8 text-center text-xs text-slate-500">Loading visits…</div>;
  if (error) return <div className="p-6 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800">{error}</div>;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-900">Visit History</h3>
          <p className="text-xs text-slate-500">Longitudinal visits — one row per encounter. No overwrite of prior visits.</p>
        </div>
        <button onClick={onAddVisit} className="px-3 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold">+ New Visit</button>
      </div>
      {visits.length === 0 ? (
        <div className="p-8 text-center text-xs text-slate-500 border border-dashed border-slate-200 rounded-xl">No visits yet. Add a visit to start longitudinal tracking.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead><tr className="border-b border-slate-200 text-[10px] tracking-wider uppercase font-semibold text-slate-500">
              <th className="pb-2">Visit date</th><th className="pb-2">Eye</th><th className="pb-2">RNFL mean</th><th className="pb-2">IOP</th><th className="pb-2">VF MD</th><th className="pb-2">Model</th><th className="pb-2">QC</th></tr></thead>
            <tbody className="divide-y divide-slate-100">
              {visits.map((v) => (
                <tr key={v.visit_id} className="hover:bg-slate-50/60">
                  <td className="py-2.5 font-mono text-slate-800">{v.visit_date}</td>
                  <td className="py-2.5 font-mono">{v.eye}</td>
                  <td className="py-2.5 font-mono">{v.mean_rnflt_um != null ? `${v.mean_rnflt_um} µm` : '—'}</td>
                  <td className="py-2.5 font-mono">{v.iop_mmhg != null ? `${v.iop_mmhg} mmHg` : '—'}</td>
                  <td className="py-2.5 font-mono">{v.vf_md_db != null ? `${v.vf_md_db} dB` : '—'}</td>
                  <td className="py-2.5 text-[11px] text-slate-600">{v.predicted_category || v.model_version || '—'}{v.classification_score != null ? ` · ${(v.classification_score * 100).toFixed(1)}%` : ''}</td>
                  <td className="py-2.5 text-[11px]">{v.qc_status || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
export default VisitHistory;
