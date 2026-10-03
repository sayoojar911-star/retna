import React, { useState, useEffect } from 'react';
import { TrendingDown, Info, Calendar, ArrowRightLeft, Layers, ShieldAlert } from 'lucide-react';
import {
  IOPRecord,
  LongitudinalRNFLT,
  VisualFieldRecord,
  PatientProgressionResponse,
  ClinicalComparisonResponse,
  ClinicalScan,
} from '../types';

interface LongitudinalChartsProps {
  longitudinalRnflt?: LongitudinalRNFLT[];
  iopRecords?: IOPRecord[];
  visualFieldRecords?: VisualFieldRecord[];
  patientId: string;
  patientName?: string;
  eye?: string;
  apiBaseUrl?: string;
  scans?: ClinicalScan[];
}

export const LongitudinalCharts: React.FC<LongitudinalChartsProps> = ({
  longitudinalRnflt = [],
  iopRecords = [],
  visualFieldRecords = [],
  patientId,
  patientName = 'Patient',
  eye = 'OD',
  apiBaseUrl = 'http://localhost:8000',
  scans = [],
}) => {
  const [selectedEye, setSelectedEye] = useState<'ALL' | 'OD' | 'OS'>('ALL');
  const [dateFilter, setDateFilter] = useState<'ALL' | '7D' | '30D' | '3M' | '6M' | '12M'>('ALL');
  const [progressionData, setProgressionData] = useState<PatientProgressionResponse | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [_comparisonData, setComparisonData] = useState<ClinicalComparisonResponse | null>(null);
  const [prevScanIdx, setPrevScanIdx] = useState<number>(1);
  const [currScanIdx, setCurrScanIdx] = useState<number>(0);

  // Fetch progression rate calculation and serial comparison from backend
  useEffect(() => {
    let isMounted = true;
    const fetchProgression = async () => {
      try {
        const res = await fetch(`${apiBaseUrl}/api/patients/${patientId}/progression`);
        if (res.ok && isMounted) {
          const data = await res.json();
          setProgressionData(data);
        }
      } catch (e) {
        // Fallback
      }

      try {
        const resComp = await fetch(`${apiBaseUrl}/api/patients/${patientId}/comparison`);
        if (resComp.ok && isMounted) {
          const comp = await resComp.json();
          setComparisonData(comp);
        }
      } catch (e) {
        // Fallback
      }
    };

    fetchProgression();
    return () => {
      isMounted = false;
    };
  }, [patientId, apiBaseUrl]);

  // Date filter helper
  const isWithinDateFilter = (dateStr: string) => {
    if (dateFilter === 'ALL') return true;
    const itemDate = new Date(dateStr).getTime();
    const now = new Date('2026-10-02').getTime(); // anchored to reference demo time
    const diffDays = (now - itemDate) / (1000 * 3600 * 24);

    if (dateFilter === '7D') return diffDays <= 7;
    if (dateFilter === '30D') return diffDays <= 30;
    if (dateFilter === '3M') return diffDays <= 92;
    if (dateFilter === '6M') return diffDays <= 183;
    if (dateFilter === '12M') return diffDays <= 365;
    return true;
  };

  // Derive RNFLT points from scans or longitudinalRnflt
  const rnfltPoints: Array<{ date: string; mean_rnflt_um: number; eye: string; score?: number; score_pct?: string }> = [];
  if (scans.length > 0) {
    scans.forEach((s) => {
      if (s.mean_rnflt_um !== null && s.mean_rnflt_um !== undefined) {
        rnfltPoints.push({
          date: s.date,
          mean_rnflt_um: s.mean_rnflt_um,
          eye: s.eye,
          score: s.score ?? 50,
          score_pct: s.score_pct || (s.score != null ? `${s.score}%` : 'N/A'),
        });
      }
    });
  } else if (longitudinalRnflt.length > 0) {
    longitudinalRnflt.forEach((r) => {
      rnfltPoints.push({
        date: r.date,
        mean_rnflt_um: r.mean_rnflt_um,
        eye: r.eye,
          score: (r.score as unknown as number | undefined) ?? undefined,
          score_pct: (r.score_pct as unknown as string | undefined) || 'N/A',
      });
    });
  }

  const filteredRnflt = rnfltPoints
    .filter((r) => (selectedEye === 'ALL' ? true : r.eye === selectedEye))
    .filter((r) => isWithinDateFilter(r.date))
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  // Model score trend points
  const filteredScores = filteredRnflt
    .filter((r) => r.score !== undefined)
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  // Filter IOP points: fall back to progression API data when explicit props are empty
  // (prevents "No longitudinal IOP data available" when records exist in the backend)
  const apiIop = (progressionData as any)?.iop_trend || [];
  const effectiveIop: IOPRecord[] =
    iopRecords.length > 0
      ? iopRecords
      : apiIop.map((p: any, idx: number) => ({
          id: `api-iop-${idx}`,
          patient_id: patientId,
          date: p.date,
          eye: selectedEye === 'ALL' ? (p.eye || eye) : (p.eye || eye),
          iop_mmhg: p.iop_mmhg,
          method: p.method || 'Goldmann Applanation',
        }));
  const filteredIop = effectiveIop
    .filter((i) => (selectedEye === 'ALL' ? true : i.eye === selectedEye))
    .filter((i) => isWithinDateFilter(i.date))
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  // Filter Visual Field points: same fallback to progression API response
  const apiVf = (progressionData as any)?.vf_trend || [];
  const effectiveVf: VisualFieldRecord[] =
    visualFieldRecords.length > 0
      ? visualFieldRecords
      : apiVf.map((p: any, idx: number) => ({
          id: `api-vf-${idx}`,
          patient_id: patientId,
          date: p.date,
          eye: p.eye || eye,
          md_db: p.md_db,
          reliability: 'Reliable',
        }));
  const filteredVf = effectiveVf
    .filter((v) => (selectedEye === 'ALL' ? true : v.eye === selectedEye))
    .filter((v) => isWithinDateFilter(v.date))
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  // Top Longitudinal Summary calculations
  const totalScansCount = filteredRnflt.length;
  const dateRangeDisplay =
    filteredRnflt.length > 0
      ? `${filteredRnflt[0].date} — ${filteredRnflt[filteredRnflt.length - 1].date}`
      : 'No scans in range';
  const rnfltChangeDisplay =
    filteredRnflt.length >= 2
      ? `${(filteredRnflt[filteredRnflt.length - 1].mean_rnflt_um - filteredRnflt[0].mean_rnflt_um).toFixed(1)} µm`
      : 'Baseline';
  const aiScoreChangeDisplay =
    filteredScores.length >= 2 && filteredScores[0].score !== undefined && filteredScores[filteredScores.length - 1].score !== undefined
      ? `${(filteredScores[filteredScores.length - 1].score! - filteredScores[0].score!).toFixed(1)}%`
      : 'Baseline';
  const iopChangeDisplay =
    filteredIop.length >= 2
      ? `${(filteredIop[filteredIop.length - 1].iop_mmhg - filteredIop[0].iop_mmhg).toFixed(1)} mmHg`
      : filteredIop.length === 1
      ? `${filteredIop[0].iop_mmhg} mmHg`
      : 'Unavailable';
  const vfChangeDisplay =
    filteredVf.length >= 2
      ? `${(filteredVf[filteredVf.length - 1].md_db - filteredVf[0].md_db).toFixed(1)} dB`
      : filteredVf.length === 1
      ? `${filteredVf[0].md_db} dB`
      : 'Unavailable';

  // Helper: SVG Line Chart for RNFLT (µm vs Date)
  const renderRnfltChart = () => {
    if (filteredRnflt.length < 2) {
      return (
        <div className="h-52 flex flex-col items-center justify-center border border-dashed border-slate-300 rounded-xl p-6 text-center bg-slate-50/50">
          <Info className="w-5 h-5 text-slate-400 mb-2" />
          <p className="text-xs text-slate-700 font-semibold">
            Additional scans are required to estimate a reliable structural trend.
          </p>
          <p className="text-[11px] text-slate-500 mt-1 max-w-sm">
            {filteredRnflt.length === 1
              ? `Only 1 scan recorded (${filteredRnflt[0].date}: ${filteredRnflt[0].mean_rnflt_um} µm). Minimum 2 serial scans required.`
              : 'No quantitative RNFLT records available for the selected filters.'}
          </p>
        </div>
      );
    }

    const minVal = 40;
    const maxVal = 120;
    const width = 500;
    const height = 180;
    const padX = 45;
    const padY = 20;

    const points = filteredRnflt.map((item, idx) => {
      const x = padX + (idx / (filteredRnflt.length - 1)) * (width - 2 * padX);
      const normalizedY = (item.mean_rnflt_um - minVal) / (maxVal - minVal);
      const y = height - padY - normalizedY * (height - 2 * padY);
      return { x, y, ...item };
    });

    const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

    return (
      <div className="space-y-2">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-52 overflow-visible select-none">
          {/* Physiological range shaded band (80-110 µm) */}
          <rect
            x={padX}
            y={height - padY - ((110 - minVal) / (maxVal - minVal)) * (height - 2 * padY)}
            width={width - 2 * padX}
            height={((110 - 80) / (maxVal - minVal)) * (height - 2 * padY)}
            fill="#0d9488"
            fillOpacity="0.08"
          />
          <line
            x1={padX}
            y1={height - padY - ((80 - minVal) / (maxVal - minVal)) * (height - 2 * padY)}
            x2={width - padX}
            y2={height - padY - ((80 - minVal) / (maxVal - minVal)) * (height - 2 * padY)}
            stroke="#94a3b8"
            strokeDasharray="3 3"
          />
          <text x={padX - 8} y={height - padY - ((80 - minVal) / (maxVal - minVal)) * (height - 2 * padY) + 3} fill="#64748b" fontSize="9" textAnchor="end">
            80µm
          </text>
          <text x={padX - 8} y={height - padY - ((100 - minVal) / (maxVal - minVal)) * (height - 2 * padY) + 3} fill="#64748b" fontSize="9" textAnchor="end">
            100µm
          </text>

          <path d={pathD} fill="none" stroke="#0d9488" strokeWidth="2.5" strokeLinecap="round" />

          {points.map((p, idx) => (
            <g key={idx}>
              <circle cx={p.x} cy={p.y} r="4.5" fill="#ffffff" stroke="#0d9488" strokeWidth="2.5" />
              <text x={p.x} y={p.y - 8} fill="#0f172a" fontSize="10" fontWeight="bold" textAnchor="middle">
                {p.mean_rnflt_um} µm
              </text>
              <text x={p.x} y={height - 2} fill="#64748b" fontSize="9" textAnchor="middle">
                {p.date.split('-').slice(1).join('/')}
              </text>
            </g>
          ))}
        </svg>
      </div>
    );
  };

  // Helper: SVG Line Chart for AI Model Score (0-100% vs Date)
  const renderScoreChart = () => {
    if (filteredScores.length < 2) {
      return (
        <div className="h-52 flex flex-col items-center justify-center border border-dashed border-slate-300 rounded-xl p-6 text-center bg-slate-50/50">
          <Info className="w-5 h-5 text-slate-400 mb-2" />
          <p className="text-xs text-slate-700 font-semibold">
            Longitudinal model-estimate trend requires multiple scans.
          </p>
          <p className="text-[11px] text-slate-500 mt-1 max-w-sm">
            {filteredScores.length === 1
              ? `Single score recorded (${filteredScores[0].date}: ${filteredScores[0].score_pct}).`
              : 'No model scores available for the current filter.'}
          </p>
        </div>
      );
    }

    const minVal = 0;
    const maxVal = 100;
    const width = 500;
    const height = 180;
    const padX = 45;
    const padY = 20;

    const points = filteredScores.map((item, idx) => {
      const val = item.score || 50;
      const x = padX + (idx / (filteredScores.length - 1)) * (width - 2 * padX);
      const normalizedY = (val - minVal) / (maxVal - minVal);
      const y = height - padY - normalizedY * (height - 2 * padY);
      return { x, y, ...item, val };
    });

    const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

    return (
      <div className="space-y-2">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-52 overflow-visible select-none">
          {/* Decision threshold line at 50% */}
          <line
            x1={padX}
            y1={height - padY - ((50 - minVal) / (maxVal - minVal)) * (height - 2 * padY)}
            x2={width - padX}
            y2={height - padY - ((50 - minVal) / (maxVal - minVal)) * (height - 2 * padY)}
            stroke="#94a3b8"
            strokeDasharray="3 3"
          />
          <text x={padX - 8} y={height - padY - ((50 - minVal) / (maxVal - minVal)) * (height - 2 * padY) + 3} fill="#64748b" fontSize="9" textAnchor="end">
            50%
          </text>
          <text x={padX - 8} y={height - padY - ((100 - minVal) / (maxVal - minVal)) * (height - 2 * padY) + 3} fill="#64748b" fontSize="9" textAnchor="end">
            100%
          </text>

          <path d={pathD} fill="none" stroke="#6366f1" strokeWidth="2.5" strokeLinecap="round" />

          {points.map((p, idx) => (
            <g key={idx}>
              <circle cx={p.x} cy={p.y} r="4.5" fill="#ffffff" stroke="#6366f1" strokeWidth="2.5" />
              <text x={p.x} y={p.y - 8} fill="#0f172a" fontSize="10" fontWeight="bold" textAnchor="middle">
                {p.val.toFixed(1)}%
              </text>
              <text x={p.x} y={height - 2} fill="#64748b" fontSize="9" textAnchor="middle">
                {p.date.split('-').slice(1).join('/')}
              </text>
            </g>
          ))}
        </svg>
      </div>
    );
  };

  // Helper: SVG Line Chart for IOP
  const renderIopChart = () => {
    if (filteredIop.length < 2) {
      return (
        <div className="h-52 flex flex-col items-center justify-center border border-dashed border-slate-300 rounded-xl p-6 text-center bg-slate-50/50">
          <Info className="w-5 h-5 text-slate-400 mb-2" />
          <p className="text-xs text-slate-700 font-semibold">
            No longitudinal IOP data available.
          </p>
          <p className="text-[11px] text-slate-500 mt-1 max-w-sm">
            {filteredIop.length === 1
              ? `Single IOP measurement recorded (${filteredIop[0].date}: ${filteredIop[0].iop_mmhg} mmHg).`
              : 'Minimum 2 measurements required to plot longitudinal IOP history.'}
          </p>
        </div>
      );
    }

    const minVal = 10;
    const maxVal = 32;
    const width = 500;
    const height = 180;
    const padX = 45;
    const padY = 20;

    const points = filteredIop.map((item, idx) => {
      const x = padX + (idx / (filteredIop.length - 1)) * (width - 2 * padX);
      const normalizedY = (item.iop_mmhg - minVal) / (maxVal - minVal);
      const y = height - padY - normalizedY * (height - 2 * padY);
      return { x, y, ...item };
    });

    const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

    return (
      <div className="space-y-2">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-52 overflow-visible select-none">
          <rect
            x={padX}
            y={height - padY - ((21 - minVal) / (maxVal - minVal)) * (height - 2 * padY)}
            width={width - 2 * padX}
            height={((21 - 12) / (maxVal - minVal)) * (height - 2 * padY)}
            fill="#2563eb"
            fillOpacity="0.06"
          />
          <line
            x1={padX}
            y1={height - padY - ((21 - minVal) / (maxVal - minVal)) * (height - 2 * padY)}
            x2={width - padX}
            y2={height - padY - ((21 - minVal) / (maxVal - minVal)) * (height - 2 * padY)}
            stroke="#e11d48"
            strokeDasharray="3 3"
            strokeOpacity="0.5"
          />
          <text x={padX - 8} y={height - padY - ((21 - minVal) / (maxVal - minVal)) * (height - 2 * padY) + 3} fill="#e11d48" fontSize="9" textAnchor="end">
            21
          </text>
          <text x={padX - 8} y={height - padY - ((14 - minVal) / (maxVal - minVal)) * (height - 2 * padY) + 3} fill="#64748b" fontSize="9" textAnchor="end">
            14
          </text>

          <path d={pathD} fill="none" stroke="#2563eb" strokeWidth="2.5" strokeLinecap="round" />

          {points.map((p, idx) => (
            <g key={idx}>
              <circle cx={p.x} cy={p.y} r="4.5" fill="#ffffff" stroke="#2563eb" strokeWidth="2.5" />
              <text x={p.x} y={p.y - 8} fill="#0f172a" fontSize="10" fontWeight="bold" textAnchor="middle">
                {p.iop_mmhg}
              </text>
              <text x={p.x} y={height - 2} fill="#64748b" fontSize="9" textAnchor="middle">
                {p.date.split('-').slice(1).join('/')}
              </text>
            </g>
          ))}
        </svg>
      </div>
    );
  };

  // Helper: SVG Line Chart for Visual Field MD
  const renderVfChart = () => {
    if (filteredVf.length < 2) {
      return (
        <div className="h-52 flex flex-col items-center justify-center border border-dashed border-slate-300 rounded-xl p-6 text-center bg-slate-50/50">
          <Info className="w-5 h-5 text-slate-400 mb-2" />
          <p className="text-xs text-slate-700 font-semibold">
            Visual-field data not available.
          </p>
          <p className="text-[11px] text-slate-500 mt-1 max-w-sm">
            {filteredVf.length === 1
              ? `Single perimetric exam (${filteredVf[0].date}: ${filteredVf[0].md_db} dB). Minimum 2 exams required for slope.`
              : 'No standard automated perimetry records available.'}
          </p>
        </div>
      );
    }

    const minVal = -20;
    const maxVal = 2;
    const width = 500;
    const height = 180;
    const padX = 45;
    const padY = 20;

    const points = filteredVf.map((item, idx) => {
      const x = padX + (idx / (filteredVf.length - 1)) * (width - 2 * padX);
      const normalizedY = (item.md_db - minVal) / (maxVal - minVal);
      const y = height - padY - normalizedY * (height - 2 * padY);
      return { x, y, ...item };
    });

    const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

    return (
      <div className="space-y-2">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-52 overflow-visible select-none">
          <line
            x1={padX}
            y1={height - padY - ((0 - minVal) / (maxVal - minVal)) * (height - 2 * padY)}
            x2={width - padX}
            y2={height - padY - ((0 - minVal) / (maxVal - minVal)) * (height - 2 * padY)}
            stroke="#10b981"
            strokeDasharray="3 3"
            strokeOpacity="0.7"
          />
          <text x={padX - 8} y={height - padY - ((0 - minVal) / (maxVal - minVal)) * (height - 2 * padY) + 3} fill="#10b981" fontSize="9" textAnchor="end">
            0dB
          </text>
          <text x={padX - 8} y={height - padY - ((-6 - minVal) / (maxVal - minVal)) * (height - 2 * padY) + 3} fill="#f59e0b" fontSize="9" textAnchor="end">
            -6dB
          </text>

          <path d={pathD} fill="none" stroke="#d97706" strokeWidth="2.5" strokeLinecap="round" />

          {points.map((p, idx) => (
            <g key={idx}>
              <circle cx={p.x} cy={p.y} r="4.5" fill="#ffffff" stroke="#d97706" strokeWidth="2.5" />
              <text x={p.x} y={p.y - 8} fill="#0f172a" fontSize="10" fontWeight="bold" textAnchor="middle">
                {p.md_db}
              </text>
              <text x={p.x} y={height - 2} fill="#64748b" fontSize="9" textAnchor="middle">
                {p.date.split('-').slice(1).join('/')}
              </text>
            </g>
          ))}
        </svg>
      </div>
    );
  };

  // Pairwise Scan Comparison selection
  const sortedScansDesc = [...scans].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  const currScan = sortedScansDesc[currScanIdx] || sortedScansDesc[0];
  const prevScan = sortedScansDesc[prevScanIdx] || (sortedScansDesc.length > 1 ? sortedScansDesc[1] : null);

  const rnfltDiff =
    currScan?.mean_rnflt_um && prevScan?.mean_rnflt_um
      ? (currScan.mean_rnflt_um - prevScan.mean_rnflt_um).toFixed(1)
      : null;
  const scoreDiff =
    currScan?.score && prevScan?.score
      ? (currScan.score - prevScan.score).toFixed(1)
      : null;

  return (
    <div className="space-y-6">
      {/* 1. Header Banner & Quick Filters */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center space-x-2">
              <TrendingDown className="w-5 h-5 text-teal-700" />
              <h2 className="text-base font-bold text-slate-900 tracking-tight">
                Progression Map &bull; Longitudinal Monitoring
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Patient: <strong className="text-slate-800">{patientName}</strong> ({patientId}) &bull; Primary Eye: <strong className="font-mono text-teal-800">{eye}</strong>
            </p>
          </div>

          {/* Eye selector */}
          <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl text-xs">
            {(['ALL', 'OD', 'OS'] as const).map((e) => (
              <button
                key={e}
                onClick={() => setSelectedEye(e)}
                className={`px-3 py-1 rounded-lg font-mono font-medium transition cursor-pointer ${
                  selectedEye === e
                    ? 'bg-white text-slate-900 font-bold shadow-xs'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                {e === 'ALL' ? 'Both Eyes' : e}
              </button>
            ))}
          </div>
        </div>

        {/* Quick Date Filters */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs">
          <div className="flex items-center space-x-1.5 text-slate-500 font-medium">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <span>Time Range:</span>
          </div>
          <div className="flex items-center space-x-1">
            {[
              { id: '7D', label: 'Last 7 days' },
              { id: '30D', label: 'Last 30 days' },
              { id: '3M', label: 'Last 3 months' },
              { id: '6M', label: 'Last 6 months' },
              { id: '12M', label: 'Last 12 months' },
              { id: 'ALL', label: 'All History' },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setDateFilter(f.id as any)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition cursor-pointer ${
                  dateFilter === f.id
                    ? 'bg-teal-50 text-teal-800 border border-teal-200'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 2. Top LONGITUDINAL SUMMARY Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
          LONGITUDINAL SUMMARY
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-6 gap-3 text-xs">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
            <span className="text-[10px] text-slate-500 uppercase font-semibold">Scans</span>
            <div className="text-base font-bold text-slate-900 font-mono mt-0.5">{totalScansCount}</div>
          </div>
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 sm:col-span-2">
            <span className="text-[10px] text-slate-500 uppercase font-semibold">Date Range</span>
            <div className="text-xs font-semibold text-slate-800 font-mono mt-0.5 truncate">{dateRangeDisplay}</div>
          </div>
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
            <span className="text-[10px] text-slate-500 uppercase font-semibold">RNFLT Change</span>
            <div className="text-base font-bold text-teal-800 font-mono mt-0.5">{rnfltChangeDisplay}</div>
          </div>
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
            <span className="text-[10px] text-slate-500 uppercase font-semibold">AI Estimate Trend</span>
            <div className="text-base font-bold text-indigo-800 font-mono mt-0.5">{aiScoreChangeDisplay}</div>
          </div>
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
            <span className="text-[10px] text-slate-500 uppercase font-semibold">IOP / VF Trend</span>
            <div className="text-xs font-bold text-slate-800 font-mono mt-0.5 truncate">{iopChangeDisplay} / {vfChangeDisplay}</div>
          </div>
        </div>
      </div>

      {/* 3. Primary Charts Grid: RNFLT Trend & AI Score Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* RNFLT Trend */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div>
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                RNFLT Trend (µm) vs Date
              </h3>
              <p className="text-[10px] text-slate-500">Observed structural trend across calibrated thickness maps</p>
            </div>
            <span className="text-[11px] text-teal-700 font-semibold font-mono">
              Target: ≥80 µm
            </span>
          </div>
          {renderRnfltChart()}
        </div>

        {/* AI Model Score Trend */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div>
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                AI Model Score vs Date
              </h3>
              <p className="text-[10px] text-slate-500">Longitudinal model-estimate trend (ResNet-18 output)</p>
            </div>
            <span className="text-[11px] text-indigo-700 font-semibold font-mono">
              Boundary: 50%
            </span>
          </div>
          {renderScoreChart()}
        </div>
      </div>

      {/* 4. Secondary Charts Grid: IOP & Visual Field */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* IOP History */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              IOP History (mmHg) vs Date
            </h3>
            <span className="text-[11px] text-blue-700 font-semibold font-mono">
              Target: ≤18 mmHg
            </span>
          </div>
          {renderIopChart()}
        </div>

        {/* Visual Field MD */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Visual Field MD (dB) vs Date
            </h3>
            <span className="text-[11px] text-amber-800 font-semibold font-mono">
              Target: &gt;-6 dB
            </span>
          </div>
          {renderVfChart()}
        </div>
      </div>

      {/* 5. SCAN-TO-SCAN COMPARISON */}
      {sortedScansDesc.length >= 2 && (
        <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <ArrowRightLeft className="w-4 h-4 text-teal-700" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Scan-to-Scan Comparison
              </h3>
            </div>
            <span className="text-xs text-slate-500">Pairwise structural delta</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            {/* Previous scan selector */}
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <span className="text-[10px] font-bold text-slate-500 uppercase">Previous Scan</span>
              <select
                value={prevScanIdx}
                onChange={(e) => setPrevScanIdx(Number(e.target.value))}
                className="w-full bg-white border border-slate-200 rounded-lg p-1.5 text-xs text-slate-800"
              >
                {sortedScansDesc.map((s, idx) => (
                  <option key={s.id} value={idx} disabled={idx === currScanIdx}>
                    {s.date} — {s.eye} ({s.mean_rnflt_um ? `${s.mean_rnflt_um} µm` : 'Raw'})
                  </option>
                ))}
              </select>
              <div className="pt-2 text-[11px] text-slate-700 space-y-1">
                <div>RNFLT: <strong className="font-mono">{prevScan?.mean_rnflt_um ? `${prevScan.mean_rnflt_um} µm` : '—'}</strong></div>
                <div>AI Score: <strong className="font-mono">{prevScan?.score ? `${prevScan.score}%` : '—'}</strong></div>
              </div>
            </div>

            {/* Current scan selector */}
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
              <span className="text-[10px] font-bold text-slate-500 uppercase">Current Scan</span>
              <select
                value={currScanIdx}
                onChange={(e) => setCurrScanIdx(Number(e.target.value))}
                className="w-full bg-white border border-slate-200 rounded-lg p-1.5 text-xs text-slate-800"
              >
                {sortedScansDesc.map((s, idx) => (
                  <option key={s.id} value={idx} disabled={idx === prevScanIdx}>
                    {s.date} — {s.eye} ({s.mean_rnflt_um ? `${s.mean_rnflt_um} µm` : 'Raw'})
                  </option>
                ))}
              </select>
              <div className="pt-2 text-[11px] text-slate-700 space-y-1">
                <div>RNFLT: <strong className="font-mono">{currScan?.mean_rnflt_um ? `${currScan.mean_rnflt_um} µm` : '—'}</strong></div>
                <div>AI Score: <strong className="font-mono">{currScan?.score ? `${currScan.score}%` : '—'}</strong></div>
              </div>
            </div>

            {/* Observed Difference */}
            <div className="p-4 bg-teal-50/60 rounded-xl border border-teal-200 space-y-2 flex flex-col justify-between">
              <div>
                <span className="text-[10px] font-bold text-teal-800 uppercase">Observed Change</span>
                <div className="text-xl font-bold font-mono text-teal-950 mt-1">
                  {rnfltDiff !== null ? `${Number(rnfltDiff) > 0 ? '+' : ''}${rnfltDiff} µm` : 'N/A'}
                </div>
                <div className="text-[11px] text-teal-800 font-mono mt-0.5">
                  AI Score Delta: {scoreDiff !== null ? `${Number(scoreDiff) > 0 ? '+' : ''}${scoreDiff}%` : 'N/A'}
                </div>
              </div>
              <p className="text-[10px] text-teal-700 italic">
                Observed change between two visits reflects localized difference. Do not infer disease progression from a single pairwise delta without clinical correlation.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 6a. EARLY RISK ALERTS */}
      {progressionData?.risk_alerts && progressionData.risk_alerts.length > 0 && (
        <div className="bg-white border border-amber-200 rounded-2xl p-5 shadow-sm space-y-3">
          <h3 className="text-xs font-bold text-amber-900 uppercase tracking-wider flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4" /> Early Risk Alerts
            <span className="ml-2 text-[10px] font-normal normal-case text-slate-500">Research alerts — clinical correlation required</span>
          </h3>
          <div className="space-y-2">
            {progressionData.risk_alerts.map((a: any, i: number) => (
              <div key={i} className={`p-3 rounded-xl border text-xs ${a.level === 'critical' ? 'bg-rose-50 border-rose-200 text-rose-900' : 'bg-amber-50 border-amber-200 text-amber-900'}`}>
                <div className="font-bold">{a.level === 'critical' ? '● Critical' : '▲ Warning'}: {a.title}</div>
                <div className="text-[11px] mt-0.5 leading-relaxed opacity-90">{a.detail}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 6b. INTEGRATED PROGRESSION HEATMAP (observation matrix, not a diagnosis) */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Integrated Progression Map
            </h3>
            <p className="text-[10px] text-slate-500">
              Compact observation matrix across measurement types and examination dates. Colors show observed values, not a diagnosis.
            </p>
          </div>
          <span className="text-[11px] text-slate-500 font-mono">
            Legend: teal = normal range · amber = borderline · rose = abnormal/flagged · slate = no data
          </span>
        </div>
        {(() => {
          const dates = Array.from(
            new Set([
              ...filteredRnflt.map((r) => r.date),
              ...filteredIop.map((i) => i.date),
              ...filteredVf.map((v) => v.date),
            ])
          ).sort((a, b) => new Date(a).getTime() - new Date(b).getTime());
          const rnfltByDate = new Map(filteredRnflt.map((r) => [r.date, r.mean_rnflt_um]));
          const iopByDate = new Map(filteredIop.map((i) => [i.date, i.iop_mmhg]));
          const vfByDate = new Map(filteredVf.map((v) => [v.date, v.md_db]));
          const scoreByDate = new Map(filteredScores.map((s) => [s.date, s.score]));
          const cell = (val: number | undefined | null, kind: 'rnflt' | 'iop' | 'vf' | 'score') => {
            if (val === undefined || val === null) {
              return { label: '—', cls: 'bg-slate-100 text-slate-400 border-slate-200' };
            }
            if (kind === 'rnflt') {
              const cls = val >= 80 ? 'bg-teal-50 text-teal-800 border-teal-200' : val >= 65 ? 'bg-amber-50 text-amber-800 border-amber-200' : 'bg-rose-50 text-rose-800 border-rose-200';
              return { label: `${val} µm`, cls };
            }
            if (kind === 'iop') {
              const cls = val <= 18 ? 'bg-teal-50 text-teal-800 border-teal-200' : val <= 21 ? 'bg-amber-50 text-amber-800 border-amber-200' : 'bg-rose-50 text-rose-800 border-rose-200';
              return { label: `${val}`, cls };
            }
            if (kind === 'vf') {
              const cls = val >= -2 ? 'bg-teal-50 text-teal-800 border-teal-200' : val >= -6 ? 'bg-amber-50 text-amber-800 border-amber-200' : 'bg-rose-50 text-rose-800 border-rose-200';
              return { label: `${val} dB`, cls };
            }
            const cls = val < 50 ? 'bg-teal-50 text-teal-800 border-teal-200' : val < 75 ? 'bg-amber-50 text-amber-800 border-amber-200' : 'bg-rose-50 text-rose-800 border-rose-200';
            return { label: `${val}%`, cls };
          };
          const rows: Array<{ label: string; kind: 'rnflt' | 'iop' | 'vf' | 'score'; byDate: Map<string, any> }> = [
            { label: 'RNFLT (µm)', kind: 'rnflt', byDate: rnfltByDate },
            { label: 'IOP (mmHg)', kind: 'iop', byDate: iopByDate },
            { label: 'Visual Field MD (dB)', kind: 'vf', byDate: vfByDate },
            { label: 'AI Score (%)', kind: 'score', byDate: scoreByDate },
          ];
          if (dates.length === 0) {
            return (
              <div className="p-6 text-center text-xs text-slate-500 border border-dashed border-slate-300 rounded-xl bg-slate-50/50">
                No longitudinal measurements available for the selected patient/eye/date range.
              </div>
            );
          }
          return (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs min-w-[520px]">
                <thead>
                  <tr className="text-slate-500 uppercase text-[10px] tracking-wider font-semibold border-b border-slate-200">
                    <th className="pb-2 pr-3">Measure</th>
                    {dates.map((d) => (
                      <th key={d} className="pb-2 px-2 font-mono font-medium text-slate-700">{d}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {rows.map((row) => (
                    <tr key={row.label}>
                      <td className="py-2 pr-3 font-semibold text-slate-800 whitespace-nowrap">{row.label}</td>
                      {dates.map((d) => {
                        const c = cell(row.byDate.get(d), row.kind);
                        return (
                          <td key={d} className="py-1.5 px-2">
                            <span className={`inline-block min-w-[86px] text-center px-2 py-1 rounded-lg border font-mono text-[11px] ${c.cls}`}>
                              {c.label}
                            </span>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="text-[10px] text-slate-500 mt-2 italic">
                Observation tool only. Cell colors reflect recorded value ranges; they do not establish a diagnosis. Clinical correlation required.
              </p>
            </div>
          );
        })()}
      </div>

      {/* 7. LONGITUDINAL SUMMARY (observed facts only) */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm space-y-3">
        <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider pb-2 border-b border-slate-100">
          Longitudinal Summary — Observed Pattern
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-[10px] text-slate-500 uppercase font-semibold">Structural (RNFLT)</span>
            <p className="text-slate-800 mt-1 leading-relaxed">
              {filteredRnflt.length >= 2
                ? `RNFLT measurements ${filteredRnflt[filteredRnflt.length - 1].mean_rnflt_um < filteredRnflt[0].mean_rnflt_um ? 'decreased' : 'changed'} between the available examinations (${filteredRnflt[0].date}: ${filteredRnflt[0].mean_rnflt_um} µm → ${filteredRnflt[filteredRnflt.length - 1].date}: ${filteredRnflt[filteredRnflt.length - 1].mean_rnflt_um} µm; observed change ${rnfltChangeDisplay}).`
                : 'Additional longitudinal scans are required to describe an RNFLT trend.'}
            </p>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-[10px] text-slate-500 uppercase font-semibold">Pressure (IOP)</span>
            <p className="text-slate-800 mt-1 leading-relaxed">
              {filteredIop.length >= 2
                ? `IOP measurements ranged from ${Math.min(...filteredIop.map((i) => i.iop_mmhg))}–${Math.max(...filteredIop.map((i) => i.iop_mmhg))} mmHg across ${filteredIop.length} examinations (observed change ${iopChangeDisplay}).`
                : filteredIop.length === 1
                ? `Single IOP measurement recorded (${filteredIop[0].date}: ${filteredIop[0].iop_mmhg} mmHg). Additional measurements required for a trend.`
                : 'IOP history unavailable for the selected range.'}
            </p>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-[10px] text-slate-500 uppercase font-semibold">Functional (Visual Field MD)</span>
            <p className="text-slate-800 mt-1 leading-relaxed">
              {filteredVf.length >= 2
                ? `Visual Field MD measurements changed from ${filteredVf[0].md_db} dB (${filteredVf[0].date}) to ${filteredVf[filteredVf.length - 1].md_db} dB (${filteredVf[filteredVf.length - 1].date}; observed change ${vfChangeDisplay}).`
                : filteredVf.length === 1
                ? `Single visual-field measurement (${filteredVf[0].date}: ${filteredVf[0].md_db} dB). Additional visual-field measurements required.`
                : 'Visual-field history unavailable for the selected range.'}
            </p>
          </div>
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80">
            <span className="text-[10px] text-slate-500 uppercase font-semibold">AI Model Estimate</span>
            <p className="text-slate-800 mt-1 leading-relaxed">
              {filteredScores.length >= 2 && filteredScores[0].score !== undefined
                ? `Model-estimated scores moved from ${filteredScores[0].score_pct} to ${filteredScores[filteredScores.length - 1].score_pct} (observed longitudinal model-estimate trend ${aiScoreChangeDisplay}). Research model estimate — not a clinical diagnosis.`
                : 'No longitudinal model-estimate trend available for the selected range.'}
            </p>
          </div>
        </div>
        <p className="text-[11px] text-slate-600 italic border-t border-slate-100 pt-3">
          Observed longitudinal pattern — factual summary of recorded measurements only. Clinical correlation required. GlaucoMap does not replace ophthalmological diagnosis or treatment decisions.
        </p>
      </div>

      {/* 8. 24-Month Trajectory (research estimate) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
        <div className="p-4 bg-white border border-slate-200 rounded-2xl space-y-2">
          <div className="font-bold text-slate-800 flex items-center justify-between">
            <span className="flex items-center gap-1.5"><Layers className="w-4 h-4 text-slate-500" /> 24-Month Progression Forecast</span>
            <span className={`text-[10px] px-2 py-0.5 rounded-full border ${progressionData?.forecast?.available ? 'bg-teal-50 text-teal-800 border-teal-200' : 'bg-slate-50 text-slate-600 border-slate-200'}`}>{progressionData?.forecast?.available ? 'Research estimate' : 'Unavailable'}</span>
          </div>
          {progressionData?.forecast?.available && progressionData.forecast.trajectory?.length ? (
            <div className="space-y-2">
              <div className="overflow-x-auto">
                <table className="w-full text-[11px] border border-slate-200 rounded-xl overflow-hidden">
                  <thead className="bg-slate-50 text-slate-600"><tr><th className="p-1.5 text-left">Horizon</th><th className="p-1.5">RNFLT est.</th><th className="p-1.5">95% band</th></tr></thead>
                  <tbody>{progressionData.forecast.trajectory.map((t: any) => (<tr key={t.horizon_months} className="border-t border-slate-100"><td className="p-1.5 font-mono">{t.horizon_months} mo</td><td className="p-1.5 font-mono text-center">{t.estimated_rnflt_um} µm</td><td className="p-1.5 font-mono text-center text-slate-600">{t.lower_bound_um} – {t.upper_bound_um}</td></tr>))}</tbody>
                </table>
              </div>
              <p className="text-[10px] text-slate-500 italic">{progressionData.forecast.message} — {progressionData.forecast.model_name}</p>
            </div>
          ) : (
            <p className="text-[11px] text-slate-600 leading-relaxed">{progressionData?.forecast?.message || '24-month forecast unavailable. Additional longitudinal data and a validated progression model are required.'}</p>
          )}
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-2xl space-y-2">
          <div className="font-bold text-slate-800 flex items-center justify-between">
            <span className="flex items-center gap-1.5"><ShieldAlert className="w-4 h-4 text-slate-500" /> Glaucoma Stage Assessment</span>
            <span className={`text-[10px] px-2 py-0.5 rounded-full border ${progressionData?.stage?.available ? 'bg-teal-50 text-teal-800 border-teal-200' : 'bg-slate-50 text-slate-600 border-slate-200'}`}>{progressionData?.stage?.available ? (progressionData.stage.stage_label || 'Estimate') : 'Unavailable'}</span>
          </div>
          {progressionData?.stage?.available ? (
            <div className="space-y-1">
              <div className="text-sm font-bold text-slate-900">{progressionData.stage.stage_label} <span className="text-xs font-normal text-slate-500">({progressionData.stage.staging_system})</span></div>
              <p className="text-[11px] text-slate-600 leading-relaxed">{progressionData.stage.message} {progressionData.stage.confidence != null ? `Confidence ~${(progressionData.stage.confidence * 100).toFixed(0)}%.` : ''}</p>
            </div>
          ) : (
            <p className="text-[11px] text-slate-600 leading-relaxed">{progressionData?.stage?.message || 'Stage assessment unavailable. The current structural model provides binary classification only. Clinical correlation required.'}</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default LongitudinalCharts;
