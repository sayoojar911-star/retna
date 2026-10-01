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
      id: 'harvard_gd_test_0419',
      patientId: 'GM-DEMO-01',
      name: 'Aarav Menon',
      age: 58,
      sex: 'Male',
      eye: 'OD',
      datasetLabel: 'Harvard-GD Held-Out Test Glaucoma (test_0419)',
      datasetSource: 'Real Harvard-GD Benchmark Dataset',
      groundTruth: 'Confirmed Glaucoma Pattern',
      scanType: 'RNFLT Numerical Map (.npz, 225×225)',
      iopStatus: '4 Longitudinal Readings (24.0 → 18.0 mmHg)',
      rnfltStatus: 'Documented Thinning (72.4 → 66.2 µm)',
      analysisStatus: 'Analyzed with Real CNN & Grad-CAM',
      description:
        'Real held-out test specimen from the Harvard-GD dataset. Features pronounced inferior and superior axonal bundle thinning. Evaluated by trained CNN with verified gradients.',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80',
    },
    {
      id: 'harvard_gd_test_0170',
      patientId: 'GM-DEMO-02',
      name: 'Dr. Sarah Jenkins',
      age: 52,
      sex: 'Female',
      eye: 'OS',
      datasetLabel: 'Harvard-GD Normal Control (test_0170)',
      datasetSource: 'Real Harvard-GD Benchmark Dataset',
      groundTruth: 'Normal Control / Suspect',
      scanType: 'RNFLT Numerical Map (.npz, 225×225)',
      iopStatus: '3 Physiological Readings (15.0 mmHg)',
      rnfltStatus: 'Robust Normal Thickness (99.2 → 98.5 µm)',
      analysisStatus: 'Analyzed with Real CNN & Grad-CAM',
      description:
        'Real healthy control sample from Harvard-GD held-out test split. Demonstrates intact physiological neuroretinal rim contour and low AI model-estimated score.',
      avatar: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80',
    },
    {
      id: 'demo_raw_oct_bscan',
      patientId: 'GM-DEMO-03',
      name: 'David Chen',
      age: 64,
      sex: 'Male',
      eye: 'OD',
      datasetLabel: 'Digital Retinal B-Scan OCT (.png)',
      datasetSource: 'Clinical OCT Export Fixture',
      groundTruth: 'Raw Optical Image (Unsegmented)',
      scanType: 'Raw OCT Cross-Section (512×400 PNG)',
      iopStatus: 'No Tonometry Recorded',
      rnfltStatus: 'RNFLT Extraction Required',
      analysisStatus: 'Validated — Blocked from RNFLT CNN',
      description:
        'Valid raw cross-sectional intensity image. Demonstrates the strict clinical QA gate: safely verified as non-empty, but blocked from direct RNFLT CNN until automated segmentation is run.',
      avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80',
    },
    {
      id: 'fundus_demo_glaucoma',
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
      id: 'demo_normal_0002',
      patientId: 'GM-DEMO-05',
      name: 'Priya Nair',
      age: 47,
      sex: 'Female',
      eye: 'OS',
      datasetLabel: 'Baseline Screening Visit Only',
      datasetSource: 'Harvard-GDP Clinical Cohort',
      groundTruth: 'Normal / Suspect (Class 0)',
      scanType: 'RNFLT Numerical Map (.npz, 225×225)',
      iopStatus: 'Single Baseline (17.0 mmHg)',
      rnfltStatus: 'Single Measurement (76.5 µm)',
      analysisStatus: 'Analyzed with Real CNN',
      description:
        'Baseline cross-sectional examination with single time point. Demonstrates system safety behavior: flags insufficient longitudinal history before computing progression rate trends.',
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
        <p className="text-xs text-slate-600 max-w-3xl leading-relaxed">
          Pre-configured clinical cases backed by real Harvard-GD benchmark datasets, cross-sectional OCT fixtures, and trained ResNet-18 models. Click any case to explore its complete longitudinal timeline or launch AI structural inference.
        </p>
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
                onClick={() => onSelectDemoCase(c.id)}
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
