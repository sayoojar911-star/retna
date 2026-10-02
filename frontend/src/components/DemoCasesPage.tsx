import React from 'react';
import { BookOpen, Activity, ArrowUpRight } from 'lucide-react';
import { ClinicalPatient } from '../types';

interface DemoCasesPageProps {
  patients?: ClinicalPatient[];
  onSelectPatient: (patientId: string) => void;
  onSelectDemoCase: (demoId: string) => void;
}

export const DemoCasesPage: React.FC<DemoCasesPageProps> = ({
  onSelectPatient,
  onSelectDemoCase,
}) => {
  const demoCases = [
    {
      id: 'demo_paired_harvard_0419',
      category: 'RNFLT CLASSIFIER DEMO' as const,
      demoCaseId: 'harvard_gd_test_0419',
      pairedOctImage: '/api/demo-samples/demo_raw_oct_bscan.png',
      patientId: 'GM-DEMO-01',
      name: 'Aarav Menon — RNFLT Classifier Demo',
      age: 68,
      sex: 'Male',
      eye: 'OD',
      datasetLabel: 'Harvard-GD RNFLT 0419',
      datasetSource: 'DEMO RNFLT — Quantitative RNFLT map (225×225, µm). RNFLT structural classifier input.',
      groundTruth: 'Confirmed Glaucoma Pattern (from RNFLT map, not raw OCT)',
      scanType: 'DEMO RNFLT — Quantitative RNFLT Map (.npz 225×225)',
      iopStatus: '4 Longitudinal Readings (22.0 → 18.0 mmHg)',
      rnfltStatus: 'Documented Thinning (72.4 → 66.2 µm)',
      analysisStatus: 'Harvard-GD RNFLT Classifier + Grad-CAM',
      description:
        'DEMO RNFLT — Quantitative RNFLT map (not raw OCT). Passed through Harvard-GD preprocessing -> AdaptedResNet18 -> p_glaucoma. OCT pixels are NOT resized into RNFLT.',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
    },
    {
      id: 'demo_paired_harvard_0170',
      category: 'RNFLT CLASSIFIER DEMO' as const,
      demoCaseId: 'harvard_gd_test_0170',
      pairedOctImage: '/api/demo-samples/demo_raw_oct_bscan.png',
      patientId: 'GM-DEMO-02',
      name: 'Dr. Sarah Jenkins — RNFLT Classifier Demo',
      age: 52,
      sex: 'Female',
      eye: 'OS',
      datasetLabel: 'Harvard-GD RNFLT 0170',
      datasetSource: 'DEMO RNFLT — Quantitative RNFLT map, Harvard-GD held-out test split.',
      groundTruth: 'Non-Glaucomatous / Suspect (from RNFLT map)',
      scanType: 'DEMO RNFLT — Quantitative RNFLT Map (.npz 225×225)',
      iopStatus: 'Stable Readings',
      rnfltStatus: 'Robust Normal Thickness (99.2 → 98.5 µm)',
      analysisStatus: 'Harvard-GD RNFLT Classifier + Grad-CAM',
      description:
        'DEMO RNFLT — Quantitative RNFLT map inference via exact training preprocessing. Not raw OCT.',
      avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80',
    },
    {
      id: 'demo_raw_oct_bscan',
      category: 'RAW OCT IMPORT / PIPELINE DEMO' as const,
      patientId: 'GM-DEMO-03',
      name: 'David Chen — RAW OCT (RNFLT extraction unavailable)',
      age: 64,
      sex: 'Male',
      eye: 'OD',
      datasetLabel: 'Raw OCT B-Scan (512×400 PNG)',
      datasetSource: 'RAW OCT — B-scan cross-section. RNFLT extraction unavailable in current build.',
      groundTruth: 'RAW OCT — analysis blocked · no RNFLT map',
      scanType: 'RAW OCT — B-Scan Cross-Section (512×400 PNG)',
      iopStatus: 'No Tonometry Recorded',
      rnfltStatus: 'RNFLT Extraction Unavailable',
      analysisStatus: 'RAW OCT — Blocked from RNFLT CNN (correct gate)',
      description:
        'RAW OCT — Study imported successfully; OCT quality completed. RNFLT extraction unavailable. Structural AI classification was not performed.',
      avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80',
    },
    {
      id: 'fundus_demo_glaucoma',
      category: 'FUNDUS DEMO' as const,
      patientId: 'GM-DEMO-04',
      name: 'Elena Rostova',
      age: 61,
      sex: 'Female',
      eye: 'OD',
      datasetLabel: 'Color Fundus Retinography Case',
      datasetSource: 'Harvard-GF Fundus Benchmark',
      groundTruth: 'Glaucoma Cup-to-Disc Thinning',
      scanType: 'Fundus Photography (512×512 RGB)',
      iopStatus: 'Single Baseline Reading',
      rnfltStatus: 'N/A (Fundus Photographic Modality)',
      analysisStatus: 'Analyzed with ResNet-18 Fundus CNN',
      description:
        'High-resolution retinal photograph showcasing increased vertical cup-to-disc ratio and neuroretinal rim notching. Evaluated via the separate fundus classifier pathway.',
      avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&auto=format&fit=crop&q=80',
    },
    {
      id: 'demo_paired_harvard_0002',
      category: 'RNFLT CLASSIFIER DEMO' as const,
      demoCaseId: 'demo_normal_0002',
      pairedOctImage: '/api/demo-samples/demo_raw_oct_bscan.png',
      patientId: 'GM-DEMO-05',
      name: 'Priya Nair — RNFLT Classifier Demo',
      age: 47,
      sex: 'Female',
      eye: 'OS',
      datasetLabel: 'Harvard-GD RNFLT 0002',
      datasetSource: 'DEMO RNFLT — Quantitative RNFLT map (single visit).',
      groundTruth: 'Normal / Suspect (Class 0)',
      scanType: 'DEMO RNFLT — Quantitative RNFLT Map (.npz)',
      iopStatus: 'Single Baseline (17.0 mmHg)',
      rnfltStatus: 'Single Measurement (76.5 µm)',
      analysisStatus: 'Harvard-GD RNFLT Classifier',
      description:
        'DEMO RNFLT — Single-visit RNFLT map. RNFLT structural classifier only.',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
    },
    {
      id: 'demo_normal_0002',
      category: 'RNFLT CLASSIFIER DEMO' as const,
      patientId: 'GM-DEMO-05',
      name: 'Priya Nair (Direct RNFLT)',
      age: 47,
      sex: 'Female',
      eye: 'OS',
      datasetLabel: 'Harvard-GD RNFLT Direct',
      datasetSource: 'DEMO RNFLT — Quantitative RNFLT map (225×225), direct path.',
      groundTruth: 'Normal / Suspect (Class 0)',
      scanType: 'DEMO RNFLT — Quantitative RNFLT Map (.npz, 225×225)',
      iopStatus: 'Single Baseline (17.0 mmHg)',
      rnfltStatus: 'Single Measurement (76.5 µm)',
      analysisStatus: 'Harvard-GD RNFLT Classifier',
      description:
        'DEMO RNFLT — Direct RNFLT path (same map as above).',
      avatar: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-2">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
            <BookOpen className="w-4 h-4" />
          </div>
          <h2 className="text-base font-bold text-slate-900 tracking-tight">
            Research Demo Case Library
          </h2>
          <span className="text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300">
            RESEARCH DEMO — NOT A REAL PATIENT
          </span>
        </div>
          <div className="flex flex-wrap gap-2 text-[10px] leading-relaxed">
            <span className="px-2 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-800">RNFLT CLASSIFIER DEMO — Quantitative RNFLT map → Harvard-GD classifier</span>
            <span className="px-2 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-800">RAW OCT IMPORT / PIPELINE DEMO — RNFLT extraction unavailable</span>
          </div>
      </div>

      {/* Demo Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {demoCases.map((c) => (
          <div
            key={c.id}
            className="bg-white border border-slate-200 hover:border-teal-300 rounded-2xl p-5 shadow-sm hover:shadow-md transition-all space-y-4 flex flex-col justify-between"
          >
            <div className="space-y-3">
              {/* Header: Photo (rounded-square) + Demographics + Demo Badge */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center space-x-3.5">
                  <img
                    src={c.avatar}
                    alt={c.name}
                    className="w-14 h-14 rounded-2xl object-cover border border-slate-200 shadow-xs flex-shrink-0"
                  />
                  <div>
                    <div className="flex items-center space-x-2">
                      <h3 className="text-sm font-bold text-slate-900">{c.name}</h3>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                        {c.patientId}
                      </span>
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      {c.age} y/o &bull; {c.sex} &bull; Eye: <strong className="font-mono text-teal-800">{c.eye}</strong>
                    </div>
                  </div>
                </div>

                <span className="text-[9px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
                  Demo
                </span>
              </div>

              <div className={`text-[9px] font-bold tracking-wider px-2 py-1 rounded-full w-fit border ${ (c as unknown as {category?:string}).category === 'RAW OCT IMPORT / PIPELINE DEMO' ? 'bg-amber-100 text-amber-800 border-amber-200' : (c as unknown as {category?:string}).category === 'FUNDUS DEMO' ? 'bg-sky-100 text-sky-800 border-sky-200' : 'bg-teal-100 text-teal-800 border-teal-200'}`}>{(c as unknown as {category?:string}).category || 'RNFLT CLASSIFIER DEMO'}</div>
              {/* Research Source & Label */}
              <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/80 text-xs space-y-1">
                <div className="text-[11px] font-semibold text-slate-800">
                  {c.datasetLabel}
                </div>
                <div className="text-[10px] text-slate-500">
                  Source: {c.datasetSource}
                </div>
              </div>

              {/* Description */}
              <p className="text-xs text-slate-600 leading-relaxed">
                {c.description}
              </p>

              {/* Metadata Badges */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block">Modality</span>
                  <span className="font-mono text-[11px] text-slate-800 font-semibold">{c.scanType.split(' ')[0]}</span>
                </div>
                <div className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                  <span className="text-[10px] text-slate-400 block">Status</span>
                  <span className="font-semibold text-teal-800 text-[11px]">{c.analysisStatus.split(' ')[0]}</span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
              <button
                onClick={() => onSelectPatient(c.patientId)}
                className="px-3.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-semibold transition flex items-center space-x-1 cursor-pointer"
              >
                <span>Open Patient Timeline</span>
                <ArrowUpRight className="w-3.5 h-3.5 text-slate-500" />
              </button>

              <button
                onClick={() => onSelectDemoCase((c as any).demoCaseId || c.id)}
                className="px-3.5 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold transition flex items-center space-x-1.5 shadow-sm cursor-pointer"
              >
                <Activity className="w-3.5 h-3.5" />
                <span>Run AI Analysis</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DemoCasesPage;
