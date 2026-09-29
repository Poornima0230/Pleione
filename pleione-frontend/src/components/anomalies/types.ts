export type AnomalyRecord = {
  component_id: string;
  lot_id: string;
  component_type: string;

  temperature_C: number | null;
  voltage_V: number | null;
  iddq_0h_uA: number | null;

  statistical_score: number | null;
  isolation_forest_score: number | null;
  combined_anomaly_score: number | null;

  anomaly_flag: number | boolean;
};

export type AnomalySummary = {
  total_components: number;
  total_anomalies: number;
  anomaly_rate: number;
};

export type AnomaliesResponse = {
  page: number;
  limit: number;
  pages: number;
  total: number;
  anomalies: AnomalyRecord[];
};
