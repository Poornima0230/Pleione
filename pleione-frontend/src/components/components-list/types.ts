export type ScreeningDecision = "PASS" | "REVIEW" | "REJECT";

export type ComponentRow = {
  component_id: string;
  lot_id: string;
  component_type: string;

  temperature_C: number | null;
  voltage_V: number | null;

  iddq_0h_uA: number | null;
  iddq_24h_uA: number | null;

  // Module A
  module_a_score: number | null;
  module_a_status: string;
  peer_source: string;

  // Module B
  failure_probability: number | null;
  failure_risk: string;
  predicted_168h_uA: number | null;
  prediction_upper_uA: number | null;
  absolute_limit_uA: number | null;

  // Module C
  final_decision: ScreeningDecision;
  future_risk: string;
  evidence_level: string;
  evidence_score: number | null;

  // Explanation
  decision_reason: string | null;
  investigation_summary: string | null;
  recommended_action: string | null;
};

export type ComponentsResponse = {
  total: number;
  page: number;
  limit: number;

  filter_options?: {
    lots?: string[];
    component_types?: string[];
    screening_decisions?: string[];
  };

  data: ComponentRow[];
};

export type ComponentsFiltersProps = {
  componentId: string;
  lotId: string;
  componentType: string;
  decision: string;

  lots: string[];
  componentTypes: string[];

  onComponentIdChange: (value: string) => void;
  onLotChange: (value: string) => void;
  onComponentTypeChange: (value: string) => void;
  onDecisionChange: (value: string) => void;

  onClear: () => void;
  hasFilters: boolean;
};
