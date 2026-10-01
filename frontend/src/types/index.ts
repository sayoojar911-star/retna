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
  input_status?: string;
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

export interface ModelResult {
  status: 'TRAINED' | 'UNAVAILABLE' | 'ERROR';
  model_name: string;
  checkpoint_file: string;
  raw_logit?: number;
  model_estimated_classification_score?: number;
  model_estimated_classification_score_pct?: string;
  normal_score?: number;
  predicted_class?: number;
  predicted_category?: string;
  is_glaucoma_risk?: boolean;
  confidence_display?: string;
  wording_disclaimer?: string;
  error?: string;
}

export interface ExplainabilityData {
  available: boolean;
  target_conv_layer?: string;
  gradient_l1_norm?: number;
  gradients_verified_real?: boolean;
  original_rnflt_image?: string;
  gradcam_heatmap_image?: string;
  gradcam_overlay_image?: string;
  explanation_text?: string;
  error?: string;
}

export interface SafetyInfo {
  explanation_disclaimer: string;
  clinical_prototype_notice: string;
  research_only?: boolean;
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

export interface RawOctStudyInfo {
  filename: string;
  file_format: string;
  dimensions: number[];
  color_mode: string;
  technical_validation: string;
  input_integrity: string;
  preview_image?: string;
}

export interface RawOctAiAnalysis {
  status: string;
  analysis_available: boolean;
  reason: string;
  message: string;
}

export interface OCTAnalysisResponse {
  is_valid: boolean;
  status: 'PASS' | 'FAIL';
  quality_status: string;
  input_type?: 'rnflt_numeric' | 'raw_oct';
  input_type_display?: string;
  message: string;
  filename?: string;
  issues?: string[];
  patient_context?: PatientContext;
  validation_checks: ValidationCheck[];
  raw_oct_study?: RawOctStudyInfo;
  ai_analysis?: RawOctAiAnalysis;
  rnflt_analysis?: RNFLTAnalysis;
  model_result?: ModelResult;
  explainability?: ExplainabilityData;
  safety?: SafetyInfo;
  research_ground_truth?: {
    glaucoma_label: number | null;
    progression_label: number | null;
    note: string;
  };
  model_status?: ModelStatusInfo;
  staging?: GlaucomaStagingInfo;
  safety_layer?: SafetyLayerAudit;
}

export interface DemoCase {
  id: string;
  name: string;
  description: string;
  expected_quality: 'VALID' | 'INVALID';
  input_type?: 'rnflt_numeric' | 'raw_oct';
  input_type_display?: string;
  glaucoma_ground_truth: string;
  progression_ground_truth: string;
  age: number;
  eye: string;
  source_dataset?: string;
}

export interface PipelineStep {
  step: string;
  description: string;
  status: 'ready' | 'trained' | 'ready_pending_training' | 'pending_checkpoint' | 'pending_longitudinal_dataset';
}

export interface ModelMetricsSummary {
  test_metrics?: {
    accuracy: number;
    precision: number;
    recall: number;
    specificity: number;
    f1: number;
    roc_auc: number;
    pr_auc: number;
    loss: number;
    confusion_matrix: number[][];
    tp: number;
    tn: number;
    fp: number;
    fn: number;
    total_samples: number;
  };
  validation_metrics_at_best_epoch?: {
    accuracy: number;
    loss: number;
    roc_auc: number;
    f1: number;
  };
  best_epoch?: number;
  checkpoint_file?: string;
}

export interface BackendModelStatus {
  status: string;
  display_status: string;
  model_name?: string;
  checkpoint_file?: string;
  metrics?: ModelMetricsSummary | null;
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
    filename?: string;
    message: string;
  };
}

export interface FundusModelResult {
  status: string;
  model_name: string;
  checkpoint_file: string;
  raw_logit: number;
  glaucoma_probability: number;
  glaucoma_probability_pct: string;
  fundus_ai_score_pct: string;
  predicted_class: number;
  predicted_category: string;
  validation_experiment_auc: number;
  validation_auc_note: string;
  wording_disclaimer: string;
}

export interface FundusExplainability {
  available: boolean;
  target_layer?: string;
  gradient_l1_norm?: number;
  gradients_verified_real?: boolean;
  original_image?: string;
  gradcam_heatmap?: string;
  gradcam_overlay?: string;
  explanation_text?: string;
  error?: string;
}

export interface FundusAnalysisResponse {
  is_valid: boolean;
  status: 'PASS' | 'FAIL';
  quality_status: string;
  filename?: string;
  message: string;
  issues?: string[];
  patient_context?: {
    patient_id: string;
    eye: string;
  };
  image_info?: {
    original_dimensions?: number[];
    processed_dimensions?: number[];
    color_mode?: string;
    technical_validation?: string;
    integrity?: string;
  };
  model_result?: FundusModelResult;
  explainability?: FundusExplainability;
  cd_ratio?: {
    status: string;
    value: number | null;
    message: string;
    note?: string;
  };
  combined_score?: {
    status: string;
    value: number | null;
    message: string;
    experimental_combined_auc?: number;
    note?: string;
  };
  validation_checks?: ValidationCheck[];
  safety?: SafetyInfo;
}

export interface FundusDemoCase {
  id: string;
  name: string;
  description: string;
  expected_quality: 'VALID' | 'INVALID';
  input_type: string;
  input_type_display: string;
  glaucoma_ground_truth: string;
  eye: string;
  source_dataset: string;
}

export interface FundusModelStatus {
  status: string;
  model_name: string;
  checkpoint_file: string;
  checkpoint_path: string;
  checkpoint_exists: boolean;
  architecture: string;
  input_resolution: string;
  normalization: string;
  validation_metrics: {
    fundus_image_auc: number;
    cup_size_auc: number;
    experimental_combined_auc: number;
    note: string;
  };
  cd_ratio: {
    available: boolean;
    status: string;
  };
  combined_score: {
    available: boolean;
    status: string;
  };
}

export interface ClinicalPatient {
  id: string;
  name: string;
  age: number;
  dob?: string;
  sex: string;
  eye_laterality: string;
  family_history: string;
  clinical_notes: string;
  last_scan_date: string;
  latest_rnflt_um: number | null;
  status: string;
  is_demo: boolean;
  demo_type?: string;
  photo_avatar?: string;
}

export interface IOPRecord {
  id: string;
  patient_id: string;
  date: string;
  eye: string;
  iop_mmhg: number;
  method: string;
  notes?: string;
}

export interface LongitudinalRNFLT {
  patient_id: string;
  date: string;
  eye: string;
  mean_rnflt_um: number;
}

export interface ClinicalReport {
  id: string;
  patient_id: string;
  patient_name?: string;
  report_date: string;
  upload_date: string;
  report_type: string;
  eye: string;
  file_name: string;
  notes?: string;
}

export interface ClinicalScan {
  id: string;
  patient_id: string;
  patient_name?: string;
  date: string;
  eye: string;
  scan_type: string;
  status: string;
  rnflt_available: boolean;
  mean_rnflt_um?: number | null;
  demo_case_id?: string;
  notes?: string;
}

export interface VisualFieldRecord {
  id: string;
  patient_id: string;
  date: string;
  eye: string;
  md_db: number;
  psd_db?: number | null;
  vfi_pct?: number | null;
  reliability: string;
  notes?: string;
  file_name?: string;
}

export interface ProgressionRateInfo {
  observations_count: number;
  data_sufficient: boolean;
  estimated_slope_um_per_year?: number | null;
  estimated_slope_db_per_year?: number | null;
  message: string;
}

export interface PatientProgressionResponse {
  patient_id: string;
  rnflt_progression: ProgressionRateInfo;
  visual_field_progression: ProgressionRateInfo;
  clinical_notice: string;
}

export interface ForecastResponse {
  patient_id: string;
  available: boolean;
  status: string;
  message: string;
  horizons: number[];
  trajectory: Array<{
    horizon_months: number;
    estimated_rnflt_um: number | null;
    lower_bound_um: number | null;
    upper_bound_um: number | null;
  }>;
  clinical_notice: string;
}

export interface ClinicalComparisonResponse {
  patient_id: string;
  comparison_available: boolean;
  latest_scan?: ClinicalScan;
  previous_scan?: ClinicalScan;
  rnflt_difference_um?: number | null;
  message?: string;
  clinical_notice?: string;
}

export interface GlaucomaStagingInfo {
  available: boolean;
  status: string;
  message: string;
  stage_label?: string | null;
  staging_system?: string;
  requires_clinical_correlation?: boolean;
}

export interface ClinicalTimelineEvent {
  date: string;
  type: string;
  title: string;
  description: string;
  rnflt_um?: number | null;
  iop_mmhg?: number | null;
  vf_md_db?: number | null;
}

export interface PatientProfileResponse {
  patient: ClinicalPatient;
  scans: ClinicalScan[];
  iop_records: IOPRecord[];
  visual_field_records: VisualFieldRecord[];
  longitudinal_rnflt: LongitudinalRNFLT[];
  reports: ClinicalReport[];
  timeline: ClinicalTimelineEvent[];
}

