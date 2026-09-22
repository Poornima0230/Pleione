const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function apiFetch<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const errorData = await response.json();
      if (errorData?.detail) {
        message = errorData.detail;
      }
    } catch {
      // Keep default message.
    }

    throw new Error(message);
  }

  return response.json();
}

/* =========================================================
   DASHBOARD
========================================================= */

export interface DashboardSummary {
  total_components: number;
  total_lots: number;
  active_signals: number;
  total_anomalies: number;
  latent_risks: number;
  high_risk_components: number;
  critical: number;
  high: number;
  passed: number;
  review: number;
  reject: number;
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  return apiFetch<DashboardSummary>("/api/dashboard/summary");
}

/* =========================================================
   COMPONENTS
========================================================= */

export interface Component {
  component_id: string;
  lot_id: string;
  component_type: string;

  temperature_C?: number;
  voltage_V?: number;

  iddq_0h_uA?: number;
  iddq_24h_uA?: number;
  iddq_96h_uA?: number;
  iddq_168h_uA?: number;

  leakage_0h_uA?: number;
  leakage_24h_uA?: number;
  leakage_96h_uA?: number;
  leakage_168h_uA?: number;

  anomaly_flag?: number | boolean;
  combined_anomaly_score?: number;

  risk_score?: number;
  risk_score_100?: number;
  risk_level?: string;

  limit_violation?: number | boolean;
  limit_excess_uA?: number;

  screening_decision?: string;
  explanation?: string;
}

export interface TrajectoryPoint {
  time: string;
  value: number;
}

export interface AnomalyEvidence {
  max_robust_z: number;
  statistical_evidence_count: number;

  statistical_score: number;

  temporal_anomaly_score: number;
  temporal_anomaly_flag: number | boolean;

  isolation_forest_score: number;
  isolation_forest_flag: number | boolean;

  combined_anomaly_score: number;
  anomaly_flag: number | boolean;
}

export interface RiskAssessment {
  risk_score_100: number;
  risk_level: string;

  limit_violation: number | boolean;
  limit_excess_uA: number;

  screening_decision: string;
}

export interface ComponentResponse {
  component: Component;

  trajectory: {
    iddq: TrajectoryPoint[];
    leakage: TrajectoryPoint[];
  };

  anomaly_evidence: AnomalyEvidence;

  risk: RiskAssessment;

  explanation: string;
}

export interface ComponentsResponse {
  total: number;
  page: number;
  limit: number;

  filter_options?: {
    lots: string[];
    component_types: string[];
    screening_decisions: string[];
  };

  data: Component[];
}

export interface ComponentParams {
  page?: number;
  limit?: number;

  component_id?: string;
  lot_id?: string;
  component_type?: string;
  screening_decision?: string;
}

export async function getComponents(
  params: ComponentParams = {},
): Promise<ComponentsResponse> {
  const searchParams = new URLSearchParams();

  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("limit", String(params.limit ?? 25));

  if (params.component_id) {
    searchParams.set("component_id", params.component_id);
  }

  if (params.lot_id) {
    searchParams.set("lot_id", params.lot_id);
  }

  if (params.component_type) {
    searchParams.set("component_type", params.component_type);
  }

  if (params.screening_decision) {
    searchParams.set("screening_decision", params.screening_decision);
  }

  return apiFetch<ComponentsResponse>(
    `/api/components/?${searchParams.toString()}`,
  );
}

export async function getComponent(
  componentId: string,
): Promise<ComponentResponse> {
  return apiFetch<ComponentResponse>(
    `/api/components/${encodeURIComponent(componentId)}`,
  );
}

/* =========================================================
   ANOMALIES
========================================================= */

export interface AnomalyRecord {
  component_id: string;
  lot_id: string;
  component_type: string;

  temperature_C?: number;
  voltage_V?: number;

  iddq_0h_uA?: number;
  iddq_24h_uA?: number;
  iddq_96h_uA?: number;
  iddq_168h_uA?: number;

  leakage_0h_uA?: number;
  leakage_24h_uA?: number;
  leakage_96h_uA?: number;
  leakage_168h_uA?: number;

  combined_anomaly_score?: number;

  anomaly_flag?: number | boolean;

  risk_score?: number;
  risk_score_100?: number;
  risk_level?: string;

  limit_violation?: number | boolean;
  limit_excess_uA?: number;

  screening_decision?: string;

  statistical_evidence_count?: number;
  max_robust_z?: number;
  max_temporal_robust_z?: number;

  temporal_anomaly_score?: number;
  statistical_score?: number;
  isolation_forest_score?: number;

  explanation?: string;
}

export interface AnomalyResponse {
  total: number;
  page: number;
  limit: number;
  pages: number;
  lot_id: string | null;
  data: AnomalyRecord[];
}

export interface AnomalyParams {
  page?: number;
  limit?: number;
  lot_id?: string;
}

export async function getAnomalies(
  params: AnomalyParams = {},
): Promise<AnomalyResponse> {
  const searchParams = new URLSearchParams();

  searchParams.set("page", String(params.page ?? 1));
  searchParams.set("limit", String(params.limit ?? 25));

  if (params.lot_id) {
    searchParams.set("lot_id", params.lot_id);
  }

  return apiFetch<AnomalyResponse>(
    `/api/anomalies/?${searchParams.toString()}`,
  );
}

/* =========================================================
   LOTS
========================================================= */

export interface Lot {
  lot_id: string;

  component_count: number;
  anomaly_count: number;
  latent_risk_count: number;
  critical_count: number;

  average_risk: number;
  anomaly_rate: number;
}

interface LotsResponse {
  total_lots: number;
  data: Lot[];
}

export async function getLots(): Promise<Lot[]> {
  const response = await apiFetch<LotsResponse>("/api/lots/");
  return response.data;
}

/* =========================================================
   MODULE B — DRIFT PREDICTION
========================================================= */

export interface ComponentPrediction {
  component_id: string;
  lot_id: string;
  component_type: string;

  temperature: number;
  voltage: number;

  iddq_0h_uA: number;
  iddq_24h_uA: number;
  iddq_96h_uA: number;
  iddq_168h_uA: number;

  leakage_0h_uA: number;
  leakage_24h_uA: number;
  leakage_96h_uA: number;
  leakage_168h_uA: number;

  ground_truth: string;
  absolute_limit_uA: number;

  actual_abnormal: boolean;

  predicted_168h_uA: number;
  prediction_lower_uA: number;
  prediction_upper_uA: number;

  prediction_error_uA: number;
  absolute_prediction_error_uA: number;

  predicted_drift_uA: number;
  predicted_drift_rate: number;
  predicted_relative_drift: number;

  actual_drift_uA: number;
  actual_drift_rate: number;

  safety_slope: number;
  drift_slope_excess: number;

  early_drift_flag: boolean;
  predicted_limit_exceeded: boolean;
  uncertainty_adjusted_failure: boolean;

  limit_margin_uA: number;
  upper_bound_limit_margin_uA: number;

  future_drift_risk: string;
  module_b_status: string;
  module_b_explanation: string;
}

export interface ComponentPredictionResponse {
  prediction: ComponentPrediction;
}

export async function getComponentPrediction(
  componentId: string,
): Promise<ComponentPredictionResponse> {
  return apiFetch<ComponentPredictionResponse>(
    `/api/predictions/${encodeURIComponent(componentId)}`,
  );
}
