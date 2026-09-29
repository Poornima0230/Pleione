"use client";

function clampProbability(value: unknown) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return 0;
  }

  return Math.min(1, Math.max(0, number));
}

function clampScore(value: unknown) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return 0;
  }

  return Math.max(0, number);
}

function statusTone(status: string) {
  switch (status) {
    case "NORMAL":
    case "LOW":
    case "VERY_LOW":
    case "PASS":
      return "text-emerald-300";

    case "WATCH":
    case "MEDIUM":
    case "REVIEW":
      return "text-amber-300";

    case "ANOMALOUS":
    case "HIGH":
    case "CRITICAL":
    case "REJECT":
      return "text-red-300";

    default:
      return "text-slate-400";
  }
}

type Props = {
  component: any;
  moduleA: any;
  prediction: any;
  risk: any;
  investigation: any;
};

export default function DecisionEvidence({
  component,
  moduleA,
  prediction,
  risk,
  investigation,
}: Props) {
  const anomalyStatus =
    moduleA?.module_a_status || moduleA?.status || "UNKNOWN";

  const anomalyScore = clampScore(moduleA?.module_a_score ?? moduleA?.score);

  const futureRisk =
    risk?.failure_risk ||
    prediction?.failure_risk ||
    component?.future_risk ||
    "UNKNOWN";

  const probability = clampProbability(
    prediction?.failure_probability ?? risk?.failure_probability,
  );

  const decision =
    investigation?.final_decision || component?.final_decision || "UNKNOWN";

  const predicted = Math.max(0, Number(prediction?.predicted_168h_uA) || 0);

  const limit = Math.max(
    0,
    Number(prediction?.absolute_limit_uA ?? component?.absolute_limit_uA) || 0,
  );

  const upper = Math.max(0, Number(prediction?.prediction_upper_uA) || 0);

  const evidenceLevel =
    investigation?.evidence_level || component?.evidence_level || "UNKNOWN";

  const evidenceScore = Math.max(
    0,
    Number(investigation?.evidence_score ?? component?.evidence_score) || 0,
  );

  const pointWithinLimit = predicted <= limit;

  const uncertaintyWithinLimit = upper <= limit;

  return (
    <section>
      <div>
        <h2 className="text-base font-semibold text-white">
          Screening Evidence
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          The signals that support the screening decision.
        </p>
      </div>

      <div className="mt-5 divide-y divide-slate-800/70 border-y border-slate-800/70">
        <EvidenceRow
          label="Anomaly Detection"
          value={anomalyStatus}
          detail={`Peer score ${anomalyScore.toFixed(2)}`}
          tone={statusTone(anomalyStatus)}
        />

        <EvidenceRow
          label="Future Prediction"
          value={futureRisk}
          detail={`${(probability * 100).toFixed(1)}% failure probability`}
          tone={statusTone(futureRisk)}
        />

        <EvidenceRow
          label="Point Forecast"
          value={pointWithinLimit ? "Within limit" : "Above limit"}
          detail={`${predicted.toFixed(2)} / ${limit.toFixed(2)} µA`}
          tone={pointWithinLimit ? "text-emerald-300" : "text-red-300"}
        />

        <EvidenceRow
          label="Prediction Uncertainty"
          value={uncertaintyWithinLimit ? "Within limit" : "Crosses limit"}
          detail={`${upper.toFixed(2)} / ${limit.toFixed(2)} µA`}
          tone={uncertaintyWithinLimit ? "text-emerald-300" : "text-amber-300"}
        />

        <EvidenceRow
          label="Evidence Strength"
          value={evidenceLevel}
          detail={`Evidence score ${evidenceScore.toFixed(0)}`}
          tone={statusTone(evidenceLevel)}
        />

        <EvidenceRow
          label="Screening Decision"
          value={decision}
          detail="Final system disposition"
          tone={statusTone(decision)}
        />
      </div>
    </section>
  );
}

function EvidenceRow({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  tone: string;
}) {
  return (
    <div className="flex flex-col gap-2 py-4 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm text-slate-400">{label}</p>

      <div className="flex items-center gap-3 sm:justify-end">
        <span className={`text-sm font-semibold ${tone}`}>{value}</span>

        <span className="font-mono tabular-nums text-xs text-slate-600">
          {detail}
        </span>
      </div>
    </div>
  );
}
