"use client";

import Link from "next/link";

function safeText(value: unknown, fallback = "—") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }

  return String(value);
}

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
      return "border-emerald-400/20 bg-emerald-400/10 text-emerald-300";
    case "REVIEW":
      return "border-amber-400/20 bg-amber-400/10 text-amber-300";
    case "REJECT":
      return "border-red-400/20 bg-red-400/10 text-red-300";
    default:
      return "border-slate-700 bg-slate-800/50 text-slate-300";
  }
}

type Props = {
  component: any;
  investigation: any;
  risk: any;
};

export default function InvestigationHeader({
  component,
  investigation,
}: Props) {
  const decision =
    investigation?.final_decision ||
    investigation?.decision ||
    component?.final_decision ||
    "UNKNOWN";

  const temperature = component?.temperature_C;
  const voltage = component?.voltage_V;

  return (
    <header>
      <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <Link href="/components" className="transition hover:text-slate-200">
          Components
        </Link>

        <span>/</span>

        <span>Investigation</span>
      </div>

      <div className="mt-5 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Component Investigation
          </p>

          <div className="mt-2 flex flex-wrap items-center gap-3">
            <h1 className="font-mono text-3xl font-semibold tracking-tight text-white">
              {safeText(component?.component_id)}
            </h1>

            <span
              className={`rounded-full border px-3 py-1 text-xs font-semibold ${decisionTone(
                decision,
              )}`}
            >
              {decision}
            </span>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-400">
            <span>{safeText(component?.component_type)}</span>

            <span className="text-slate-700">•</span>

            <span>
              Lot{" "}
              <span className="font-mono tabular-nums text-slate-300">
                {safeText(component?.lot_id)}
              </span>
            </span>

            <span className="text-slate-700">•</span>

            <span>
              {temperature !== null && temperature !== undefined
                ? `${Number(temperature).toFixed(2)}°C`
                : "—"}
            </span>

            <span className="text-slate-700">•</span>

            <span>
              {voltage !== null && voltage !== undefined
                ? `${Number(voltage).toFixed(2)}V`
                : "—"}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          Detect → Assess → Investigate
        </div>
      </div>
    </header>
  );
}
