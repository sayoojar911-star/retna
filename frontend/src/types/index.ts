export interface ValidationCheck {
  name: string;
  status: 'PASS' | 'FAIL' | 'PENDING';
  detail: string;
}

export interface PatientContext {
  patient_id: string;
  age: number | null;
  eye: string;
  iop_mmhg: number | null;
  family_history: string;
}

export interface RNFLTAnalysis {
  mean_thickness_um: number;
  phys_mean_thickness_um: number;
  min_thickness_um: number;
  max_thickness_um: number;
  median_thickness_um: number;
  optic_canal_ratio_pct: number;
  heatmap_image: string;
  dimensions: number[];
}

export interface ModelStatusInfo {
  prediction: string;
  gradcam: string;
  progression_forecast: string;
  checkpoint_status: string;
}

export interface SafetyLayerAudit {
  input_quality_validation: string;
  missing_data_handling: string;
  unsupported_input_handling: string;
  target_leakage_exclusion: string;
  model_uncertainty: string;
  atypical_pattern_review: string;
  longitudinal_consistency: string;
}

export interface OCTAnalysisResponse {
  is_valid: boolean;
  status: 'PASS' | 'FAIL';
  quality_status: string;
  message: string;
  filename?: string;
  issues?: string[];
  patient_context?: PatientContext;
  validation_checks: ValidationCheck[];
  rnflt_analysis?: RNFLTAnalysis;
  research_ground_truth?: {
    glaucoma_label: number | null;
    progression_label: number | null;
    note: string;
  };
  model_status?: ModelStatusInfo;
  safety_layer?: SafetyLayerAudit;
}

export interface DemoCase {
  id: string;
  name: string;
  description: string;
  expected_quality: 'VALID' | 'INVALID';
  glaucoma_ground_truth: string;
  progression_ground_truth: string;
  age: number;
  eye: string;
}

export interface PipelineStep {
  step: string;
  description: string;
  status: 'ready' | 'trained' | 'ready_pending_training' | 'pending_checkpoint' | 'pending_longitudinal_dataset';
}

export interface BackendModelStatus {
  status: string;
  display_status: string;
  pipeline: PipelineStep[];
  hardware: {
    gpu_detected: boolean;
    gpu_name: string;
    active_runtime_device: string;
    training_infrastructure_ready: boolean;
  };
  checkpoint: {
    exists: boolean;
    path: string;
    message: string;
  };
}
