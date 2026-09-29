"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Lot = {
  lot_id: string;
  component_count: number;

  anomaly_count: number;
  anomalous_count: number;
  watch_count: number;

  pass_count: number;
  review_count: number;
  reject_count: number;

  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;

  average_iddq_0h_uA: number | null;
  average_predicted_168h_uA: number | null;
  maximum_predicted_168h_uA: number | null;
  predicted_limit_exceedance_count: number;
};

type LotsResponse = {
  total_lots: number;
  total_components: number;
  lots: Lot[];
};

function formatNumber(value: number | null, digits = 2) {
  if (value === null || value === undefined) return "—";

  return value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function percentage(value: number, total: number) {
  if (!total) return "0.0%";
  return `${((value / total) * 100).toFixed(1)}%`;
}

export default function LotsPage() {
  const [data, setData] = useState<LotsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadLots() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(`${API_BASE}/api/lots/`, {
          signal: controller.signal,
          cache: "no-store",
        });

        if (!response.ok) {
          throw new Error(`Failed to load lots (${response.status})`);
        }

        const result: LotsResponse = await response.json();

        setData(result);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load lot information.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadLots();

    return () => controller.abort();
  }, []);

  const totals = useMemo(() => {
    if (!data?.lots) {
      return {
        anomalies: 0,
        pass: 0,
        review: 0,
        reject: 0,
        critical: 0,
        high: 0,
      };
    }

    return data.lots.reduce(
      (acc, lot) => {
        acc.anomalies += lot.anomaly_count;
        acc.pass += lot.pass_count;
        acc.review += lot.review_count;
        acc.reject += lot.reject_count;
        acc.critical += lot.critical_count;
        acc.high += lot.high_count;

        return acc;
      },
      {
        anomalies: 0,
        pass: 0,
        review: 0,
        reject: 0,
        critical: 0,
        high: 0,
      },
    );
  }, [data]);

  if (loading) {
    return (
      <main className="min-h-screen bg-white px-6 py-8 text-slate-900 dark:bg-[#020618] dark:text-slate-100">
        <div className="mx-auto max-w-[1500px]">
          <div className="h-8 w-40 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />

          <div className="mt-3 h-4 w-80 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />

          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[1, 2, 3, 4].map((item) => (
              <div
                key={item}
                className="h-28 animate-pulse rounded-xl border border-slate-200 bg-slate-100 dark:border-slate-800 dark:bg-slate-900"
              />
            ))}
          </div>

          <div className="mt-8 h-96 animate-pulse rounded-xl border border-slate-200 bg-slate-100 dark:border-slate-800 dark:bg-slate-900" />
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-white px-6 py-8 text-slate-900 dark:bg-[#020618] dark:text-slate-100">
        <div className="mx-auto max-w-[1500px]">
          <h1 className="text-2xl font-semibold">Lots</h1>

          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-5 dark:border-red-900/50 dark:bg-red-950/20">
            <p className="font-medium text-red-700 dark:text-red-400">
              Unable to load lot data
            </p>

            <p className="mt-1 text-sm text-red-600 dark:text-red-400/80">
              {error}
            </p>

            <button
              onClick={() => window.location.reload()}
              className="mt-4 rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-700 transition hover:bg-red-100 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950/40"
            >
              Retry
            </button>
          </div>
        </div>
      </main>
    );
  }

  if (!data) return null;

  return (
    <main className="min-h-screen bg-white px-5 py-7 text-slate-900 dark:bg-[#020618] dark:text-slate-100 sm:px-7 lg:px-8">
      <div className="mx-auto max-w-[1500px]">
        {/* Header */}
        <header className="mb-8">
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-500">
                Screening intelligence
              </p>

              <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">
                Lots
              </h1>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
                Lot-level view of component screening, anomaly evidence and
                predicted 168H risk.
              </p>
            </div>

            <div className="text-sm text-slate-500 dark:text-slate-400">
              {data.total_components.toLocaleString()} components across{" "}
              {data.total_lots} lots
            </div>
          </div>
        </header>

        {/* Summary */}
        <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <SummaryCard
            label="Total components"
            value={data.total_components.toLocaleString()}
            description="Across all screening lots"
          />

          <SummaryCard
            label="Anomaly signals"
            value={totals.anomalies.toLocaleString()}
            description={`${percentage(
              totals.anomalies,
              data.total_components,
            )} of components`}
          />

          <SummaryCard
            label="Review"
            value={totals.review.toLocaleString()}
            description="Requires engineering assessment"
          />

          <SummaryCard
            label="Reject"
            value={totals.reject.toLocaleString()}
            description="Predicted specification failure"
          />
        </section>

        {/* Secondary overview */}
        <section className="mt-7 grid grid-cols-1 gap-5 lg:grid-cols-3">
          <OverviewItem
            label="PASS"
            value={totals.pass}
            total={data.total_components}
            description="No final screening escalation"
          />

          <OverviewItem
            label="HIGH / CRITICAL FUTURE RISK"
            value={totals.high + totals.critical}
            total={data.total_components}
            description="Elevated predicted 168H risk"
          />

          <OverviewItem
            label="CRITICAL"
            value={totals.critical}
            total={data.total_components}
            description="Predicted specification exceedance"
          />
        </section>

        {/* Lots table */}
        <section className="mt-8">
          <div className="mb-4">
            <h2 className="text-lg font-semibold">Lot overview</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Compare screening outcomes and future-risk signals across lots.
            </p>
          </div>

          <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[1100px] border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-left dark:border-slate-800 dark:bg-slate-900/60">
                    <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Lot
                    </th>

                    <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Components
                    </th>

                    <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Anomaly signals
                    </th>

                    <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Future risk
                    </th>

                    <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Screening
                    </th>

                    <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Avg 0H IDDQ
                    </th>

                    <th className="px-5 py-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Max predicted 168H
                    </th>

                    <th className="px-5 py-4 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
                      Action
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {data.lots.map((lot) => (
                    <tr
                      key={lot.lot_id}
                      className="transition hover:bg-slate-50 dark:hover:bg-slate-900/40"
                    >
                      {/* Lot */}
                      <td className="px-5 py-5">
                        <Link
                          href={`/lots/${encodeURIComponent(lot.lot_id)}`}
                          className="group inline-flex items-center gap-2"
                        >
                          <span className="font-semibold text-slate-900 group-hover:underline dark:text-slate-100">
                            {lot.lot_id}
                          </span>

                          <svg
                            width="15"
                            height="15"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            className="text-slate-400 transition group-hover:translate-x-0.5"
                          >
                            <path d="M9 18l6-6-6-6" />
                          </svg>
                        </Link>
                      </td>

                      {/* Components */}
                      <td className="px-5 py-5 text-sm font-medium">
                        {lot.component_count.toLocaleString()}
                      </td>

                      {/* Anomalies */}
                      <td className="px-5 py-5">
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-medium">
                            {lot.anomaly_count}
                          </span>

                          <span className="text-xs text-slate-500 dark:text-slate-500">
                            {percentage(lot.anomaly_count, lot.component_count)}
                          </span>
                        </div>

                        <div className="mt-2 flex gap-3 text-[11px] text-slate-500 dark:text-slate-500">
                          <span>Watch {lot.watch_count}</span>

                          <span>Anomalous {lot.anomalous_count}</span>
                        </div>
                      </td>

                      {/* Future risk */}
                      <td className="px-5 py-5">
                        <div className="flex items-center gap-2">
                          {lot.critical_count > 0 && (
                            <RiskBadge
                              label="Critical"
                              count={lot.critical_count}
                              type="critical"
                            />
                          )}

                          {lot.high_count > 0 && (
                            <RiskBadge
                              label="High"
                              count={lot.high_count}
                              type="high"
                            />
                          )}

                          {lot.critical_count === 0 && lot.high_count === 0 && (
                            <span className="text-sm text-slate-500 dark:text-slate-400">
                              No high-risk signals
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Screening */}
                      <td className="px-5 py-5">
                        <div className="flex items-center gap-2 text-xs">
                          <DecisionCount
                            label="P"
                            value={lot.pass_count}
                            type="pass"
                          />

                          <DecisionCount
                            label="R"
                            value={lot.review_count}
                            type="review"
                          />

                          <DecisionCount
                            label="X"
                            value={lot.reject_count}
                            type="reject"
                          />
                        </div>
                      </td>

                      {/* Average IDDQ */}
                      <td className="px-5 py-5 text-sm text-slate-700 dark:text-slate-300">
                        {formatNumber(lot.average_iddq_0h_uA)}{" "}
                        <span className="text-xs text-slate-400">µA</span>
                      </td>

                      {/* Maximum predicted */}
                      <td className="px-5 py-5 text-sm text-slate-700 dark:text-slate-300">
                        {formatNumber(lot.maximum_predicted_168h_uA)}{" "}
                        <span className="text-xs text-slate-400">µA</span>
                      </td>

                      {/* Action */}
                      <td className="px-5 py-5 text-right">
                        <Link
                          href={`/lots/${encodeURIComponent(lot.lot_id)}`}
                          className="inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3.5 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
                        >
                          View lot
                          <svg
                            width="14"
                            height="14"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <path d="M5 12h14" />
                            <path d="M13 6l6 6-6 6" />
                          </svg>
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function SummaryCard({
  label,
  value,
  description,
}: {
  label: string;
  value: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-5 py-5 dark:border-slate-800 dark:bg-slate-900/30">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
        {label}
      </p>

      <p className="mt-3 text-2xl font-semibold tracking-tight">{value}</p>

      <p className="mt-1 text-xs text-slate-500 dark:text-slate-500">
        {description}
      </p>
    </div>
  );
}

function OverviewItem({
  label,
  value,
  total,
  description,
}: {
  label: string;
  value: number;
  total: number;
  description: string;
}) {
  const percentageValue = total ? (value / total) * 100 : 0;

  return (
    <div className="border-l-2 border-slate-200 pl-4 dark:border-slate-800">
      <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">
        {label}
      </p>

      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-xl font-semibold">{value.toLocaleString()}</span>

        <span className="text-xs text-slate-500">
          {percentageValue.toFixed(1)}%
        </span>
      </div>

      <p className="mt-1 text-xs text-slate-500 dark:text-slate-500">
        {description}
      </p>
    </div>
  );
}

function RiskBadge({
  label,
  count,
  type,
}: {
  label: string;
  count: number;
  type: "critical" | "high";
}) {
  const classes =
    type === "critical"
      ? "border-red-200 bg-red-50 text-red-700 dark:border-red-900/50 dark:bg-red-950/20 dark:text-red-400"
      : "border-orange-200 bg-orange-50 text-orange-700 dark:border-orange-900/50 dark:bg-orange-950/20 dark:text-orange-400";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-[11px] font-medium ${classes}`}
    >
      {label}
      <span className="font-semibold">{count}</span>
    </span>
  );
}

function DecisionCount({
  label,
  value,
  type,
}: {
  label: string;
  value: number;
  type: "pass" | "review" | "reject";
}) {
  const classes =
    type === "pass"
      ? "text-emerald-600 dark:text-emerald-400"
      : type === "review"
        ? "text-amber-600 dark:text-amber-400"
        : "text-red-600 dark:text-red-400";

  return (
    <span className={classes}>
      <span className="font-semibold">{label}</span>{" "}
      <span className="text-slate-600 dark:text-slate-400">{value}</span>
    </span>
  );
}
