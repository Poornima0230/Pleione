export interface RiskDistribution {
  CRITICAL: number;
  HIGH: number;
  MEDIUM: number;
  LOW: number;
}

export interface Lot {
  lot_id: string;
  component_count: number;
  anomaly_count: number;
  anomaly_rate: number;
  average_anomaly_score: number;
  average_risk_score: number;
  risk_distribution: RiskDistribution;
}

export interface LotsResponse {
  total_lots: number;
  lots: Lot[];
}
