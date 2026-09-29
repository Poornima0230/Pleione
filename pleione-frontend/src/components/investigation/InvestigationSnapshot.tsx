"use client";

function clampNonNegative(value: unknown) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return 0;
  }

  return Math.max(0, number);
}

function clampProbability(value: unknown) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return 0;
  }

  return Math.min(1, Math.max(0, number));
}

function decisionTone(decision: string) {
  switch (decision) {
    case "PASS":
      return "text-emerald-300";
    case "REVIEW":
      return "text-amber-300";
    case "REJECT":
      return "text-red-300";
    default:
      return "text-slate-300";
  }
}

function riskTone(risk: string) {
  switch (risk) {
    case "LOW":
    case "VERY_LOW":
      return "text-emerald-300";
    case "MEDIUM":
      return "text-amber-300";
    case "HIGH":
    case "CRITICAL":
      return "text-red-300";
    default:
      return "text-slate-300";
  }
}

type Props = {
  component: any;
  prediction: any;
  risk: any;
  investigation: any;
};

export default function InvestigationSnapshot({
  component,
  prediction,
  risk,
  investigation,
}: Props) {
  const decision =
    investigation?.final_decision ||
    investigation?.decision ||
    component?.final_decision ||
    "UNKNOWN";

  const futureRisk =
    investigation?.future_risk ||
    risk?.failure_risk ||
    component?.future_risk ||
    "UNKNOWN";

  const limit = clampNonNegative(
    prediction?.absolute_limit_uA ?? component?.absolute_limit_uA,
  );

  const current = clampNonNegative(
    prediction?.iddq_0h_uA ?? component?.iddq_0h_uA,
  );

  const forecast = clampNonNegative(prediction?.predicted_168h_uA);

  const probability = clampProbability(
    prediction?.failure_probability ?? risk?.failure_probability,
  );

  return (
    <section className="border-y border-slate-800/80 py-7">
      <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Screening Result
          </p>

          <div className="mt-2 flex flex-wrap items-baseline gap-x-4 gap-y-1">
            <span
              className={`text-3xl font-semibold tracking-tight ${decisionTone(
                decision,
              )}`}
            >
              {decision}
            </span>

            <span className="text-sm text-slate-400">
              Future risk{" "}
              <span className={`font-semibold ${riskTone(futureRisk)}`}>
                {futureRisk}
              </span>
            </span>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-7 sm:gap-10">
          <Metric label="Current 0H" value={`${current.toFixed(2)} µA`} />

          <Metric label="Predicted 168H" value={`${forecast.toFixed(2)} µA`} />

          <Metric label="Specification" value={`${limit.toFixed(2)} µA`} />
        </div>
      </div>

      {Number.isFinite(probability) && probability > 0 && (
        <div className="mt-6 flex items-center gap-3 border-t border-slate-800/70 pt-5 text-sm">
          <span className="text-slate-500">Future failure probability</span>

          <span className="font-mono tabular-nums font-semibold text-slate-200">
            {(probability * 100).toFixed(1)}%
          </span>

          <span className="text-slate-700">•</span>

          <span className={`font-medium ${riskTone(futureRisk)}`}>
            {futureRisk}
          </span>
        </div>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-[0.15em] text-slate-600">
        {label}
      </p>

      <p className="mt-1 font-mono tabular-nums text-base font-semibold text-slate-200">
        {value}
      </p>
    </div>
  );
}
