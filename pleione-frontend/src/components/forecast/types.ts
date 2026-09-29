export interface ForecastRow {
  component_id: string;
  lot_id: string;
  component_type: string;

  temperature: number | null;
  voltage: number | null;

  iddq_0h_uA: number | null;
  iddq_24h_uA: number | null;

  predicted_168h_uA: number | null;
  prediction_lower_uA: number | null;
  prediction_upper_uA: number | null;

  predicted_drift_uA: number | null;
  predicted_drift_rate: number | null;
  predicted_relative_drift: number | null;

  safety_slope: number | null;
  drift_slope_excess: number | null;

  early_drift_flag: boolean | number | string | null;
  predicted_limit_exceeded: boolean | number | string | null;
  uncertainty_adjusted_failure: boolean | number | string | null;

  absolute_limit_uA: number | null;
  limit_margin_uA: number | null;
  upper_bound_limit_margin_uA: number | null;

  future_drift_risk: string | null;
  module_b_status: string | null;
  module_b_explanation: string | null;
}

export interface ForecastResponse {
  total: number;
  page: number;
  limit: number;
  pages: number;
  data: ForecastRow[];
}

export interface ForecastSummary {
  total_components: number;
  model_name: string | null;
  stage: number | null;
  cumulative_components: number | null;
  average_predicted_168h_uA: number | null;
  average_predicted_drift_uA: number | null;
  predicted_limit_exceeded: number;
  uncertainty_adjusted_failure: number;
  future_drift_risk: Record<string, number>;
  module_b_status: Record<string, number>;
}
