"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { getDashboardSummary } from "@/lib/api";

type PriorityComponent = {
  component_id: string;
  lot_id: string | null;
  component_type: string | null;
  module_a_score: number;
  module_a_status: string;
  failure_probability: number;
  failure_risk: string;
  final_decision: string;
  future_risk: string;
};

type HighestAnomaly = {
  component_id: string;
  lot_id: string | null;
  component_type: string | null;
  module_a_score: number;
  module_a_status: string;
  final_decision: string;
};

type DashboardSummary = {
  total_components: number;
  total_lots: number;

  active_signals: number;
  total_anomalies: number;
  anomaly_rate: number;

  normal: number;
  watch: number;
  anomalous: number;

  high_risk_components: number;

  critical: number;
  high: number;
  medium: number;
  low: number;

  passed: number;
  review: number;
  reject: number;

  risk_distribution: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };

  screening_distribution: {
    pass: number;
    review: number;
    reject: number;
  };

  anomaly_distribution: {
    normal: number;
    watch: number;
    anomalous: number;
  };

  risk_components: number;
  risk_coverage: number;

  priority_components: PriorityComponent[];
  highest_anomalies: HighestAnomaly[];
};

/* ============================================================
   HELPERS
============================================================ */

function formatNumber(value: number | null | undefined) {
  return new Intl.NumberFormat("en-IN").format(Number(value ?? 0));
}

function formatPercent(value: number | null | undefined, digits = 1) {
  return `${(Number(value ?? 0) * 100).toFixed(digits)}%`;
}

function formatScore(value: number | null | undefined) {
  return Number(value ?? 0).toFixed(3);
}

function decisionClasses(decision: string) {
  switch (decision?.toUpperCase()) {
    case "REJECT":
      return {
        text: "text-red-400",
        bg: "bg-red-500/10",
        border: "border-red-500/20",
      };

    case "REVIEW":
      return {
        text: "text-amber-400",
        bg: "bg-amber-500/10",
        border: "border-amber-500/20",
      };

    default:
      return {
        text: "text-emerald-400",
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/20",
      };
  }
}

function futureRiskClasses(risk: string) {
  switch (risk?.toUpperCase()) {
    case "CRITICAL":
      return {
        text: "text-red-400",
        bg: "bg-red-500/10",
        border: "border-red-500/20",
      };

    case "HIGH":
      return {
        text: "text-orange-400",
        bg: "bg-orange-500/10",
        border: "border-orange-500/20",
      };

    case "MEDIUM":
      return {
        text: "text-amber-400",
        bg: "bg-amber-500/10",
        border: "border-amber-500/20",
      };

    default:
      return {
        text: "text-emerald-400",
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/20",
      };
  }
}

function anomalyClasses(status: string) {
  switch (status?.toUpperCase()) {
    case "ANOMALOUS":
      return {
        text: "text-red-400",
        bg: "bg-red-500/10",
        border: "border-red-500/20",
      };

    case "WATCH":
      return {
        text: "text-amber-400",
        bg: "bg-amber-500/10",
        border: "border-amber-500/20",
      };

    default:
      return {
        text: "text-slate-400",
        bg: "bg-slate-500/10",
        border: "border-slate-500/20",
      };
  }
}

/* ============================================================
   SMALL UI COMPONENTS
============================================================ */

function SectionTitle({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex items-end justify-between gap-6">
      <div>
        {eyebrow && (
          <div className="mb-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
            {eyebrow}
          </div>
        )}

        <h2 className="text-lg font-semibold tracking-tight text-slate-100">
          {title}
        </h2>

        {description && (
          <p className="mt-1 text-sm text-slate-500">{description}</p>
        )}
      </div>

      {action}
    </div>
  );
}

function Metric({
  label,
  value,
  description,
  accent = "neutral",
}: {
  label: string;
  value: string | number;
  description: string;
  accent?: "neutral" | "red" | "amber" | "green";
}) {
  const accentClass = {
    neutral: "text-slate-100",
    red: "text-red-400",
    amber: "text-amber-400",
    green: "text-emerald-400",
  }[accent];

  return (
    <div className="min-w-0 border-r border-slate-800/80 px-6 first:pl-0 last:border-r-0 last:pr-0">
      <div className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">
        {label}
      </div>

      <div
        className={`mt-2 text-2xl font-semibold tracking-tight ${accentClass}`}
      >
        {value}
      </div>

      <div className="mt-1 text-xs text-slate-500">{description}</div>
    </div>
  );
}

function DistributionBar({
  label,
  value,
  total,
  valueLabel,
  className = "bg-slate-500",
}: {
  label: string;
  value: number;
  total: number;
  valueLabel?: string;
  className?: string;
}) {
  const percentage = total > 0 ? Math.min((value / total) * 100, 100) : 0;

  return (
    <div>
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="text-slate-400">{label}</span>

        <span className="font-medium text-slate-200">
          {valueLabel ?? formatNumber(value)}
        </span>
      </div>

      <div className="h-1.5 overflow-hidden rounded-full bg-slate-800">
        <div
          className={`h-full rounded-full ${className}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

/* ============================================================
   PRIORITY ROW
============================================================ */

function PriorityRow({ item }: { item: PriorityComponent }) {
  const decision = decisionClasses(item.final_decision);
  const futureRisk = futureRiskClasses(item.future_risk);
  const anomaly = anomalyClasses(item.module_a_status);

  return (
    <Link
      href={`/components/${encodeURIComponent(item.component_id)}`}
      className="group block border-b border-slate-800/70 py-4 last:border-b-0"
    >
      <div className="grid grid-cols-[minmax(180px,1.5fr)_90px_130px_130px_110px_80px] items-center gap-4">
        {/* Component */}
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-100 transition group-hover:text-white">
              {item.component_id}
            </span>

            <span
              className={`rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${decision.text} ${decision.bg} ${decision.border}`}
            >
              {item.final_decision}
            </span>
          </div>

          <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
            <span>{item.component_type || "Unknown type"}</span>

            <span className="text-slate-700">•</span>

            <span>{item.lot_id || "—"}</span>
          </div>
        </div>

        {/* Module A */}
        <div>
          <div
            className={`inline-flex rounded-md border px-2 py-1 text-[10px] font-semibold uppercase tracking-wide ${anomaly.text} ${anomaly.bg} ${anomaly.border}`}
          >
            {item.module_a_status}
          </div>

          <div className="mt-1 text-[11px] text-slate-600">
            A: {formatScore(item.module_a_score)}
          </div>
        </div>

        {/* Future probability */}
        <div>
          <div className="text-sm font-semibold text-slate-100">
            {formatPercent(item.failure_probability, 2)}
          </div>

          <div className="mt-1 text-[11px] text-slate-500">
            future failure probability
          </div>
        </div>

        {/* Future risk */}
        <div>
          <span
            className={`inline-flex rounded-md border px-2 py-1 text-[10px] font-semibold uppercase tracking-wide ${futureRisk.text} ${futureRisk.bg} ${futureRisk.border}`}
          >
            {item.future_risk}
          </span>
        </div>

        {/* Failure risk */}
        <div>
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Risk
          </div>

          <div className={`mt-1 text-xs font-semibold ${futureRisk.text}`}>
            {item.failure_risk}
          </div>
        </div>

        {/* Inspect */}
        <div className="text-right">
          <span className="text-xs font-medium text-slate-500 transition group-hover:text-slate-200">
            Inspect →
          </span>
        </div>
      </div>
    </Link>
  );
}

/* ============================================================
   MAIN COMPONENT
============================================================ */

export default function CommandCenter() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      try {
        setLoading(true);
        setError(null);

        const response = await getDashboardSummary();

        if (cancelled) return;

        /*
         * getDashboardSummary may return either:
         *   response
         * or:
         *   response.data
         *
         * Supporting both keeps this page compatible with
         * the current API helper.
         */
        const data = response as unknown as DashboardSummary;

        setSummary(data);
      } catch (err) {
        if (cancelled) return;

        console.error("Failed to load Command Center:", err);

        setError(
          err instanceof Error ? err.message : "Unable to load dashboard data.",
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      cancelled = true;
    };
  }, []);

  const priorityComponents = useMemo(() => {
    return summary?.priority_components ?? [];
  }, [summary]);

  const highestAnomalies = useMemo(() => {
    return summary?.highest_anomalies ?? [];
  }, [summary]);

  if (loading) {
    return (
      <main className="min-h-screen bg-white px-6 py-8 text-slate-900 dark:bg-[#020618] dark:text-slate-100">
        <div className="mx-auto max-w-[1500px]">
          <div className="flex min-h-[60vh] items-center justify-center">
            <div className="text-center">
              <div className="mx-auto h-7 w-7 animate-spin rounded-full border-2 border-slate-700 border-t-slate-200" />

              <p className="mt-4 text-sm text-slate-500">
                Loading screening data...
              </p>
            </div>
          </div>
        </div>
      </main>
    );
  }

  if (error || !summary) {
    return (
      <main className="min-h-screen bg-white px-6 py-8 text-slate-900 dark:bg-[#020618] dark:text-slate-100">
        <div className="mx-auto max-w-[1500px]">
          <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-6">
            <div className="text-sm font-semibold text-red-400">
              Command Center unavailable
            </div>

            <p className="mt-2 text-sm text-slate-500">
              {error || "No dashboard summary was returned by the API."}
            </p>

            <p className="mt-3 text-xs text-slate-600">
              Verify that the FastAPI server is running and that
              /api/dashboard/summary is available.
            </p>
          </div>
        </div>
      </main>
    );
  }

  const total = summary.total_components || 0;

  const activeSignalRate =
    total > 0 ? (summary.active_signals / total) * 100 : 0;

  return (
    <main className="min-h-screen bg-white px-4 py-6 text-slate-900 sm:px-6 lg:px-8 dark:bg-[#020618] dark:text-slate-100">
      <div className="mx-auto max-w-[1500px]">
        {/* ==================================================
            HEADER
        ================================================== */}

        <header className="border-b border-slate-200 pb-6 dark:border-slate-800/80">
          <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
            <div>
              <div className="mb-2 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />

                <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-400">
                  Screening engine online
                </span>

                <span className="text-slate-700">/</span>

                <span className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-500">
                  FastAPI connected
                </span>
              </div>

              <h1 className="text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
                Command Center
              </h1>

              <p className="mt-1 text-sm text-slate-500">
                Component screening and quality status
              </p>
            </div>

            <div className="text-left lg:text-right">
              <div className="text-xs uppercase tracking-[0.14em] text-slate-500">
                Screening dataset
              </div>

              <div className="mt-1 text-sm font-medium text-slate-300">
                {formatNumber(total)} components ·{" "}
                {formatNumber(summary.total_lots)} lots
              </div>
            </div>
          </div>
        </header>

        {/* ==================================================
            TOP METRICS
        ================================================== */}

        <section className="border-b border-slate-200 py-7 dark:border-slate-800/80">
          <div className="grid grid-cols-1 gap-y-6 sm:grid-cols-2 lg:grid-cols-4 lg:gap-y-0">
            <Metric
              label="Total components"
              value={formatNumber(summary.total_components)}
              description="Components in current screening data"
            />

            <Metric
              label="Total lots"
              value={formatNumber(summary.total_lots)}
              description="Lots represented in the dataset"
            />

            <Metric
              label="Active signals"
              value={formatNumber(summary.active_signals)}
              description={`${activeSignalRate.toFixed(1)}% with WATCH or ANOMALOUS evidence`}
              accent={summary.active_signals > 0 ? "amber" : "green"}
            />

            <Metric
              label="Requires attention"
              value={formatNumber(summary.review + summary.reject)}
              description={`${formatNumber(summary.reject)} reject · ${formatNumber(summary.review)} review`}
              accent={
                summary.reject > 0
                  ? "red"
                  : summary.review > 0
                    ? "amber"
                    : "green"
              }
            />
          </div>
        </section>

        {/* ==================================================
            SCREENING STATUS
        ================================================== */}

        <section className="border-b border-slate-200 py-8 dark:border-slate-800/80">
          <SectionTitle
            eyebrow="Module C"
            title="Screening disposition"
            description="Final decision after current anomaly evidence, future prediction, and specification assessment."
          />

          <div className="mt-7 grid grid-cols-1 gap-8 md:grid-cols-3">
            {/* PASS */}
            <div>
              <div className="flex items-end justify-between">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-400">
                    Pass
                  </div>

                  <div className="mt-2 text-3xl font-semibold tracking-tight text-slate-100">
                    {formatNumber(summary.passed)}
                  </div>
                </div>

                <div className="text-xs text-slate-500">
                  {total > 0
                    ? ((summary.passed / total) * 100).toFixed(1)
                    : "0.0"}
                  %
                </div>
              </div>

              <div className="mt-4 h-1.5 rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-emerald-500"
                  style={{
                    width: `${total ? (summary.passed / total) * 100 : 0}%`,
                  }}
                />
              </div>

              <p className="mt-2 text-xs text-slate-600">
                No current evidence requiring escalation.
              </p>
            </div>

            {/* REVIEW */}
            <div>
              <div className="flex items-end justify-between">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.14em] text-amber-400">
                    Review
                  </div>

                  <div className="mt-2 text-3xl font-semibold tracking-tight text-slate-100">
                    {formatNumber(summary.review)}
                  </div>
                </div>

                <div className="text-xs text-slate-500">
                  {total > 0
                    ? ((summary.review / total) * 100).toFixed(1)
                    : "0.0"}
                  %
                </div>
              </div>

              <div className="mt-4 h-1.5 rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-amber-500"
                  style={{
                    width: `${total ? (summary.review / total) * 100 : 0}%`,
                  }}
                />
              </div>

              <p className="mt-2 text-xs text-slate-600">
                Evidence requires engineering review.
              </p>
            </div>

            {/* REJECT */}
            <div>
              <div className="flex items-end justify-between">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-[0.14em] text-red-400">
                    Reject
                  </div>

                  <div className="mt-2 text-3xl font-semibold tracking-tight text-slate-100">
                    {formatNumber(summary.reject)}
                  </div>
                </div>

                <div className="text-xs text-slate-500">
                  {total > 0
                    ? ((summary.reject / total) * 100).toFixed(1)
                    : "0.0"}
                  %
                </div>
              </div>

              <div className="mt-4 h-1.5 rounded-full bg-slate-800">
                <div
                  className="h-full rounded-full bg-red-500"
                  style={{
                    width: `${total ? (summary.reject / total) * 100 : 0}%`,
                  }}
                />
              </div>

              <p className="mt-2 text-xs text-slate-600">
                Predicted or assessed evidence crosses the screening decision
                threshold.
              </p>
            </div>
          </div>
        </section>

        {/* ==================================================
            TWO-COLUMN ANALYSIS
        ================================================== */}

        <section className="grid grid-cols-1 gap-10 border-b border-slate-200 py-8 lg:grid-cols-2 dark:border-slate-800/80">
          {/* FUTURE RISK */}

          <div>
            <SectionTitle
              eyebrow="Module B"
              title="Future risk"
              description="Predicted 168h failure risk from the 0h + 24h screening window."
            />

            <div className="mt-7 space-y-5">
              <DistributionBar
                label="Critical"
                value={summary.critical}
                total={total}
                className="bg-red-500"
              />

              <DistributionBar
                label="High"
                value={summary.high}
                total={total}
                className="bg-orange-500"
              />

              <DistributionBar
                label="Medium"
                value={summary.medium}
                total={total}
                className="bg-amber-500"
              />

              <DistributionBar
                label="Low"
                value={summary.low}
                total={total}
                className="bg-emerald-500"
              />
            </div>
          </div>

          {/* MODULE A */}

          <div>
            <SectionTitle
              eyebrow="Module A"
              title="Anomaly evidence"
              description="Current abnormality detection using the 0h peer-aware screening signal."
            />

            <div className="mt-7 space-y-5">
              <DistributionBar
                label="Anomalous"
                value={summary.anomalous}
                total={total}
                className="bg-red-500"
              />

              <DistributionBar
                label="Watch"
                value={summary.watch}
                total={total}
                className="bg-amber-500"
              />

              <DistributionBar
                label="Normal"
                value={summary.normal}
                total={total}
                className="bg-slate-500"
              />
            </div>

            <div className="mt-6 flex items-center justify-between border-t border-slate-800/70 pt-4">
              <span className="text-xs text-slate-500">
                Active anomaly signals
              </span>

              <span className="text-sm font-semibold text-slate-200">
                {formatNumber(summary.active_signals)}
              </span>
            </div>
          </div>
        </section>

        {/* ==================================================
            PRIORITY QUEUE
        ================================================== */}

        <section className="border-b border-slate-200 py-8 dark:border-slate-800/80">
          <SectionTitle
            eyebrow="Investigation queue"
            title="Needs attention"
            description="Components requiring review based on Module A, Module B, or Module C evidence."
            action={
              <Link
                href="/anomalies"
                className="text-xs font-medium text-slate-500 transition hover:text-slate-200"
              >
                View all →
              </Link>
            }
          />

          <div className="mt-6 overflow-x-auto">
            <div className="min-w-[900px]">
              {/* Header */}
              <div className="grid grid-cols-[minmax(180px,1.5fr)_90px_130px_130px_110px_80px] gap-4 border-b border-slate-800 pb-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-600">
                <div>Component</div>
                <div>Module A</div>
                <div>Future probability</div>
                <div>Future risk</div>
                <div>Risk class</div>
                <div />
              </div>

              {priorityComponents.length > 0 ? (
                priorityComponents.map((item) => (
                  <PriorityRow key={item.component_id} item={item} />
                ))
              ) : (
                <div className="py-12 text-center">
                  <div className="text-sm font-medium text-emerald-400">
                    No components require attention
                  </div>

                  <p className="mt-1 text-xs text-slate-600">
                    Current Module A, Module B, and Module C results contain no
                    priority items.
                  </p>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* ==================================================
            HIGHEST ANOMALY SIGNALS
        ================================================== */}

        <section className="border-b border-slate-200 py-8 dark:border-slate-800/80">
          <SectionTitle
            eyebrow="Module A evidence"
            title="Highest anomaly signals"
            description="Strongest current anomaly evidence identified by the peer-aware detector."
            action={
              <Link
                href="/components"
                className="text-xs font-medium text-slate-500 transition hover:text-slate-200"
              >
                View components →
              </Link>
            }
          />

          <div className="mt-6">
            {highestAnomalies.length > 0 ? (
              <div className="grid grid-cols-1 divide-y divide-slate-800/70 md:grid-cols-2 md:divide-x md:divide-y-0">
                {highestAnomalies.map((item) => {
                  const anomaly = anomalyClasses(item.module_a_status);

                  const decision = decisionClasses(item.final_decision);

                  return (
                    <Link
                      key={item.component_id}
                      href={`/components/${encodeURIComponent(
                        item.component_id,
                      )}`}
                      className="group border-b border-slate-800/70 py-4 first:pt-0 md:px-6 md:first:pl-0 md:nth-last-2:border-b-0 md:last:border-b-0 md:last:pr-0"
                    >
                      <div className="flex items-center justify-between gap-5">
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-slate-100 group-hover:text-white">
                              {item.component_id}
                            </span>

                            <span
                              className={`rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${anomaly.text} ${anomaly.bg} ${anomaly.border}`}
                            >
                              {item.module_a_status}
                            </span>
                          </div>

                          <div className="mt-1 text-xs text-slate-500">
                            {item.component_type || "Unknown type"}{" "}
                            <span className="text-slate-700">•</span>{" "}
                            {item.lot_id || "—"}
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="text-sm font-semibold text-slate-200">
                            {formatScore(item.module_a_score)}
                          </div>

                          <div
                            className={`mt-1 text-[10px] font-semibold uppercase tracking-wide ${decision.text}`}
                          >
                            {item.final_decision}
                          </div>
                        </div>
                      </div>
                    </Link>
                  );
                })}
              </div>
            ) : (
              <div className="py-8 text-sm text-slate-500">
                No WATCH or ANOMALOUS Module A signals found.
              </div>
            )}
          </div>
        </section>

        {/* ==================================================
            QUICK ACCESS
        ================================================== */}

        <section className="py-8">
          <SectionTitle
            eyebrow="Navigation"
            title="Screening workspace"
            description="Move from dashboard evidence into detailed investigation."
          />

          <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-3">
            <Link
              href="/components"
              className="group border border-slate-800/80 bg-slate-950/30 p-5 transition hover:border-slate-700 hover:bg-slate-900/40"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-200">
                  Components
                </span>

                <span className="text-slate-600 transition group-hover:text-slate-300">
                  →
                </span>
              </div>

              <p className="mt-2 text-xs leading-5 text-slate-500">
                Browse all screened components and open component
                investigations.
              </p>

              <div className="mt-5 text-lg font-semibold text-slate-200">
                {formatNumber(summary.total_components)}
              </div>

              <div className="mt-1 text-[11px] uppercase tracking-wide text-slate-600">
                screened components
              </div>
            </Link>

            <Link
              href="/anomalies"
              className="group border border-slate-800/80 bg-slate-950/30 p-5 transition hover:border-slate-700 hover:bg-slate-900/40"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-200">
                  Anomalies
                </span>

                <span className="text-slate-600 transition group-hover:text-slate-300">
                  →
                </span>
              </div>

              <p className="mt-2 text-xs leading-5 text-slate-500">
                Review WATCH and ANOMALOUS current-screening evidence.
              </p>

              <div className="mt-5 text-lg font-semibold text-slate-200">
                {formatNumber(summary.active_signals)}
              </div>

              <div className="mt-1 text-[11px] uppercase tracking-wide text-slate-600">
                active signals
              </div>
            </Link>

            <Link
              href="/lots"
              className="group border border-slate-800/80 bg-slate-950/30 p-5 transition hover:border-slate-700 hover:bg-slate-900/40"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-200">
                  Lots
                </span>

                <span className="text-slate-600 transition group-hover:text-slate-300">
                  →
                </span>
              </div>

              <p className="mt-2 text-xs leading-5 text-slate-500">
                View component distribution and screening status by lot.
              </p>

              <div className="mt-5 text-lg font-semibold text-slate-200">
                {formatNumber(summary.total_lots)}
              </div>

              <div className="mt-1 text-[11px] uppercase tracking-wide text-slate-600">
                represented lots
              </div>
            </Link>
          </div>
        </section>

        {/* ==================================================
            FOOTER NOTE
        ================================================== */}

        <footer className="border-t border-slate-800/70 py-5">
          <div className="flex flex-col justify-between gap-2 text-[11px] text-slate-600 sm:flex-row">
            <span>Component screening dashboard</span>

            <span>Module A · Module B · Module C</span>
          </div>
        </footer>
      </div>
    </main>
  );
}
