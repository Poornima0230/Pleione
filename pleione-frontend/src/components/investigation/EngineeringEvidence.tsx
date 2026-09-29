"use client";

function clampNonNegative(value: unknown) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return 0;
  }

  return Math.max(0, number);
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

type Props = {
  component: any;
  prediction: any;
  risk: any;
  investigation: any;
};

export default function EngineeringEvidence({
  component,
  prediction,
  investigation,
}: Props) {
  const decision =
    investigation?.final_decision || component?.final_decision || "UNKNOWN";

  const reason =
    investigation?.decision_reason ||
    component?.decision_reason ||
    "No decision explanation is available.";

  const summary =
    investigation?.investigation_summary ||
    component?.investigation_summary ||
    "No investigation summary is available.";

  const action =
    investigation?.recommended_action ||
    component?.recommended_action ||
    "No recommended action is available.";

  const limit = clampNonNegative(
    prediction?.absolute_limit_uA ?? component?.absolute_limit_uA,
  );

  return (
    <section>
      <div>
        <h2 className="text-base font-semibold text-white">
          Engineering Assessment
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Interpreted screening evidence and recommended follow-up.
        </p>
      </div>

      <div className="mt-5 border-y border-slate-800/70">
        <div className="grid gap-8 py-7 lg:grid-cols-[180px_1fr]">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-600">
              Assessment
            </p>

            <p
              className={`mt-2 text-2xl font-semibold ${decisionTone(
                decision,
              )}`}
            >
              {decision}
            </p>
          </div>

          <div className="space-y-6">
            <AssessmentBlock title="Decision rationale" text={reason} />

            <AssessmentBlock title="Investigation summary" text={summary} />

            <AssessmentBlock title="Recommended action" text={action} />
          </div>
        </div>

        <div className="border-t border-slate-800/70 py-4">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
            <span className="text-slate-500">Specification limit</span>

            <span className="font-mono tabular-nums font-semibold text-slate-300">
              {limit.toFixed(2)} µA
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}

function AssessmentBlock({ title, text }: { title: string; text: string }) {
  return (
    <div>
      <p className="text-sm font-medium text-slate-300">{title}</p>

      <p className="mt-2 max-w-4xl text-sm leading-6 text-slate-500">{text}</p>
    </div>
  );
}
