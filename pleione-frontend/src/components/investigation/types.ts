export type Tone = "green" | "amber" | "red" | "neutral";

export type ComponentData = {
  component_id: string;
  lot_id: string;
  component_type: string;
  temperature_C: number;
  voltage_V: number;

  iddq_0h_uA: number;
  iddq_24h_uA?: number | null;

  leakage_0h_uA?: number | null;
  leakage_24h_uA?: number | null;

  delta_0_24?: number | null;

  absolute_limit_uA?: number | null;
};

export type ModuleAEvidence = {
  module_a_score: number | null;
  module_a_status: string;
  peer_source: string;

  module_a_watch_or_higher?: boolean;
  module_a_anomalous?: boolean;
};

export type ModuleBPrediction = {
  lot_id?: string;
  component_type?: string;
  temperature_C?: number;
  voltage_V?: number;

  iddq_0h_uA?: number | null;
  iddq_24h_uA?: number | null;

  leakage_0h_uA?: number | null;
  leakage_24h_uA?: number | null;

  delta_0_24?: number | null;

  predicted_168h_uA: number | null;
  prediction_lower_uA: number | null;
  prediction_upper_uA: number | null;
  prediction_interval_width_uA: number | null;

  failure_probability: number | null;
  predicted_future_violation: boolean;
  failure_risk: string;

  absolute_limit_uA: number | null;
};

export type ModuleCDecision = {
  final_decision: string;
  future_risk: string;
  evidence_level: string;
  evidence_score: number;
};

export type EvidenceFlags = {
  point_prediction_exceeds_limit?: boolean;
  uncertainty_crosses_limit?: boolean;

  classifier_high_risk?: boolean;
  classifier_medium_or_higher?: boolean;

  module_a_watch_or_higher?: boolean;
  module_a_anomalous?: boolean;
};

export type InvestigationExplanation = {
  decision_reason?: string;
  investigation_summary?: string;
  recommended_action?: string;
};

export type RiskData = {
  decision: ModuleCDecision;

  module_a_evidence: {
    module_a_score: number | null;
    module_a_status: string;
    peer_source: string;

    module_a_watch_or_higher?: boolean;
    module_a_anomalous?: boolean;
  };

  module_b_evidence: {
    predicted_168h_uA: number | null;
    prediction_lower_uA: number | null;
    prediction_upper_uA: number | null;
    prediction_interval_width_uA: number | null;

    failure_probability: number | null;
    predicted_future_violation: boolean;
    failure_risk: string;

    absolute_limit_uA: number | null;
  };

  evidence_flags: EvidenceFlags;

  explanation: InvestigationExplanation;
};

export type ComponentAnalysisResponse = {
  component: ComponentData;

  module_a: ModuleAEvidence;

  prediction: ModuleBPrediction;

  risk: RiskData;

  investigation: {
    component_id: string;
    lot_id: string;
    component_type: string;
    temperature_C: number;
    voltage_V: number;
  };
};
