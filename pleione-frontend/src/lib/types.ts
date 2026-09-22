// ============================================================
// Pleione Frontend Data Types
// Version 2
// ============================================================

// ------------------------------------------------------------
// Common
// ------------------------------------------------------------

export type ParameterName = "iddq" | "leakage" | string;

export type ComponentType = "TypeA" | "TypeB" | "TypeC" | string;

export type StatusLevel =
  | "normal"
  | "low"
  | "medium"
  | "high"
  | "critical"
  | "unknown";

// ------------------------------------------------------------
// Component
// ------------------------------------------------------------

export interface Component {
  component_id: string;
  lot_id: string;
  component_type: ComponentType;

  temperature_C: number;
  voltage_V: number;

  iddq_0h_uA: number;
  iddq_24h_uA: number;
  iddq_96h_uA: number;
  iddq_168h_uA: number;

  leakage_0h_uA: number;
  leakage_24h_uA: number;
  leakage_96h_uA: number;
  leakage_168h_uA: number;

  ground_truth?: string;
  absolute_limit_uA?: number;

  // Module A
  combined_anomaly?: boolean | string | number;
  latent_risk_flag?: boolean | string | number;
  anomaly_severity?: string;
  screening_status?: string;
  risk_score?: number;
  anomaly_score?: number;
}

// ------------------------------------------------------------
// Measurement
// ------------------------------------------------------------

export interface Measurement {
  component_id: string;
  component_type?: ComponentType;

  parameter: ParameterName;

  time: number;
  value: number;

  lower_limit?: number | null;
  upper_limit?: number | null;
}

// ------------------------------------------------------------
// Parameter Trajectory
// ------------------------------------------------------------

export interface ParameterTrajectory {
  parameter: ParameterName;

  measurements: Measurement[];

  lower_limit?: number | null;
  upper_limit?: number | null;
}

// ------------------------------------------------------------
// Lot
// ------------------------------------------------------------

export interface Lot {
  lot_id: string;

  component_count?: number;
  component_types?: string[];
  parameters?: ParameterName[];

  temperature_min_C?: number;
  temperature_max_C?: number;

  voltage_min_V?: number;
  voltage_max_V?: number;

  risk_score?: number;
  risk_level?: string;

  // Module A
  anomaly_count?: number;
  latent_risk_count?: number;
  critical_count?: number;
  average_risk?: number;
  anomaly_rate?: number;
}

// ------------------------------------------------------------
// Lots API Response
// ------------------------------------------------------------

export interface LotsResponse {
  total_lots?: number;
  total?: number;

  data?: Lot[];
  items?: Lot[];
}

// ------------------------------------------------------------
// Dataset Summary
// ------------------------------------------------------------

export interface DatasetSummary {
  total_components?: number;
  total_lots?: number;

  parameters?: ParameterName[];
  timepoints?: number[];

  prediction_horizon?: number;

  total_measurements?: number;
  latest_batch?: string;
}

// ------------------------------------------------------------
// Pagination
// ------------------------------------------------------------

export interface Pagination {
  page?: number;
  limit?: number;
  total?: number;
  total_pages?: number;
}

// ------------------------------------------------------------
// Components API Response
// ------------------------------------------------------------

export interface ComponentsResponse {
  items?: Component[];
  data?: Component[];

  pagination?: Pagination;

  total?: number;
  page?: number;
  limit?: number;
}

// ------------------------------------------------------------
// Component Detail
// ------------------------------------------------------------

export interface ComponentDetail extends Component {
  trajectories?: ParameterTrajectory[];
  measurements?: Measurement[];
}

export interface ComponentResponse {
  component?: ComponentDetail;
  data?: ComponentDetail;
}

// ------------------------------------------------------------
// Anomaly
// ------------------------------------------------------------

export interface Anomaly {
  component_id: string;

  lot_id?: string;
  component_type?: ComponentType;

  parameter?: ParameterName;

  time?: number;
  value?: number;

  anomaly_score?: number;

  severity?: string;
  anomaly_type?: string;

  explanation?: string;
  evidence?: string[];

  upper_limit?: number | null;
  lower_limit?: number | null;

  // Module A
  combined_anomaly?: boolean | string | number;
  latent_risk_flag?: boolean | string | number;
  anomaly_severity?: string;
  screening_status?: string;
  risk_score?: number;
}

// ------------------------------------------------------------
// Anomalies API Response
// ------------------------------------------------------------

export interface AnomaliesResponse {
  items?: Anomaly[];
  data?: Anomaly[];

  pagination?: Pagination;

  total?: number;
  page?: number;
  limit?: number;

  lot_id?: string | null;
}

// ------------------------------------------------------------
// Prediction
// ------------------------------------------------------------

export interface Prediction {
  component_id: string;

  lot_id?: string;
  component_type?: ComponentType;

  parameter?: ParameterName;

  predicted_168h_uA?: number;

  prediction_lower_uA?: number;
  prediction_upper_uA?: number;

  predicted_drift_uA?: number;
  predicted_drift_rate?: number;

  safety_slope?: number;

  predicted_limit_exceeded?: boolean | string;

  future_drift_risk?: string;

  early_drift_flag?: boolean | string;
  early_drift_direction?: string;
}

// ------------------------------------------------------------
// Predictions API Response
// ------------------------------------------------------------

export interface PredictionsResponse {
  items?: Prediction[];
  data?: Prediction[];

  pagination?: Pagination;

  total?: number;
  page?: number;
  limit?: number;
}

// ------------------------------------------------------------
// Risk
// ------------------------------------------------------------

export interface RiskAssessment {
  component_id: string;

  lot_id?: string;
  component_type?: ComponentType;

  risk_score?: number;

  final_risk_level?: string;
  final_decision?: string;

  risk_priority?: number;

  current_anomaly_level?: string;
  anomaly_score?: number;
  anomaly_evidence_count?: number;

  early_drift_flag?: boolean | string;
  early_drift_direction?: string;

  future_drift_risk?: string;
  future_drift_abnormal?: boolean | string;

  future_failure_predicted?: boolean | string;

  predicted_limit_exceeded?: boolean | string;

  predicted_168h_uA?: number;
  absolute_limit_uA?: number;

  current_anomaly_contribution?: number;
  future_drift_contribution?: number;
  future_failure_contribution?: number;

  risk_explanation?: string;
}

// ------------------------------------------------------------
// Risk API Response
// ------------------------------------------------------------

export interface RiskResponse {
  items?: RiskAssessment[];
  data?: RiskAssessment[];

  pagination?: Pagination;

  total?: number;
  page?: number;
  limit?: number;
}

// ------------------------------------------------------------
// Screening Run
// ------------------------------------------------------------

export interface ScreeningRun {
  run_id: string;

  name?: string;
  status?: string;

  started_at?: string;
  completed_at?: string;

  total_components?: number;
  analyzed_components?: number;
  priority_components?: number;

  pass_count?: number;
  review_count?: number;
  reject_count?: number;
}

// ------------------------------------------------------------
// Screening Runs API Response
// ------------------------------------------------------------

export interface ScreeningRunsResponse {
  items?: ScreeningRun[];
  data?: ScreeningRun[];

  total?: number;
}

// ------------------------------------------------------------
// Validation / Module F
// ------------------------------------------------------------

export interface ValidationMetrics {
  prediction_mae?: number;
  prediction_rmse?: number;
  prediction_r2?: number;

  failure_accuracy?: number;
  failure_precision?: number;
  failure_recall?: number;
  failure_f1?: number;

  risk_accuracy?: number;
  risk_precision?: number;
  risk_recall?: number;
  risk_f1?: number;

  latent_defects?: number;
  latent_defects_detected?: number;
  latent_defect_detection_rate?: number;

  absolute_failures?: number;
  absolute_failures_detected?: number;
  absolute_failure_detection_rate?: number;

  total_components?: number;
  priority_screening_components?: number;

  priority_screening_load_percent?: number;
  screening_reduction_percent?: number;
}

// ------------------------------------------------------------
// Report
// ------------------------------------------------------------

export interface Report {
  report_id: string;

  name?: string;
  description?: string;

  created_at?: string;

  type?: string;
  status?: string;
}

// ------------------------------------------------------------
// Configuration
// ------------------------------------------------------------

export interface ParameterLimit {
  min: number;
  max: number;
}

export interface PleioneConfig {
  parameters: ParameterName[];

  timepoints: number[];

  prediction_horizon: number;

  limits?: Record<string, ParameterLimit>;

  missing_value_strategy?: string;
}

// ------------------------------------------------------------
// UI Helpers
// ------------------------------------------------------------

export interface SelectOption {
  label: string;
  value: string;
}

// ------------------------------------------------------------
// Dashboard Summary
// ------------------------------------------------------------

export interface DashboardSummary {
  // Backend Module A summary
  total_components?: number;
  total_lots?: number;

  active_signals?: number;
  latent_risks?: number;

  critical?: number;
  high?: number;

  review?: number;
  reject?: number;
  passed?: number;

  // Future dashboard fields
  total_anomalies?: number;
  high_risk_components?: number;
  priority_components?: number;

  screening_reduction_percent?: number;

  parameters?: ParameterName[];
  timepoints?: number[];

  dataset?: DatasetSummary;
}
