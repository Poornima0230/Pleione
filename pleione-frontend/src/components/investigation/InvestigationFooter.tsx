"use client";

import Link from "next/link";

function toneForStatus(status: string) {
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
      return "text-slate-500";
  }
}

type Props = {
  component: any;
  moduleA: any;
  prediction: any;
  risk: any;
};

export default function InvestigationFooter({
  component,
  moduleA,
  prediction,
  risk,
}: Props) {
  const anomalyStatus =
    moduleA?.module_a_status || moduleA?.status || "UNKNOWN";

  const futureRisk =
    risk?.failure_risk ||
    prediction?.failure_risk ||
    component?.future_risk ||
    "UNKNOWN";

  const decision = component?.final_decision || "UNKNOWN";

  return (
    <footer className="border-t border-slate-800/80 pt-7 pb-4">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
            Screening provenance
          </p>

          <p className="mt-2 max-w-2xl text-xs leading-5 text-slate-600">
            Screening decisions use 0H and 24H measurements. The 168H value
            shown here is a model prediction, while later measurements remain
            outside the deployment-time decision input.
          </p>
        </div>

        <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs">
          <Status label="Anomaly Detection" value={anomalyStatus} />

          <Status label="Future Prediction" value={futureRisk} />

          <Status label="Screening Decision" value={decision} />
        </div>
      </div>

      <div className="mt-7 flex flex-wrap gap-3">
        <Link
          href="/components"
          className="rounded-lg border border-slate-800 px-4 py-2 text-sm font-medium text-slate-300 transition hover:border-slate-700 hover:bg-slate-900/70 hover:text-white"
        >
          ← Back to Components
        </Link>

        <Link
          href={`/anomalies?component_id=${encodeURIComponent(
            component?.component_id || "",
          )}`}
          className="rounded-lg border border-slate-800 px-4 py-2 text-sm font-medium text-slate-300 transition hover:border-slate-700 hover:bg-slate-900/70 hover:text-white"
        >
          View anomaly evidence
        </Link>
      </div>
    </footer>
  );
}

function Status({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-slate-600">{label}</span>

      <span className={`font-semibold ${toneForStatus(value)}`}>{value}</span>
    </div>
  );
}
