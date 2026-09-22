"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  Search,
  ShieldAlert,
  SlidersHorizontal,
  XCircle,
} from "lucide-react";

import PageHeader from "@/components/layout/PageHeader";
import { getAnomalies } from "@/lib/api";

type AnomalyRecord = {
  component_id: string;
  lot_id: string;
  component_type: string;

  temperature_C?: number;
  voltage_V?: number;

  iddq_0h_uA?: number;
  iddq_24h_uA?: number;
  iddq_96h_uA?: number;
  iddq_168h_uA?: number;

  leakage_0h_uA?: number;
  leakage_24h_uA?: number;
  leakage_96h_uA?: number;
  leakage_168h_uA?: number;

  combined_anomaly_score?: number;
  anomaly_flag?: number | boolean;

  risk_score?: number;
  risk_score_100?: number;
  risk_level?: string;

  limit_violation?: number | boolean;
  limit_excess_uA?: number;

  screening_decision?: string;

  statistical_evidence_count?: number;
  max_robust_z?: number;
  max_temporal_robust_z?: number;
  temporal_anomaly_score?: number;
  statistical_score?: number;
  isolation_forest_score?: number;

  explanation?: string;
};

type AnomalyResponse = {
  total: number;
  page: number;
  limit: number;
  pages?: number;
  data: AnomalyRecord[];
};

const PAGE_SIZE = 25;

function formatNumber(value: number | undefined, digits = 2) {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "—";
  }

  return value.toFixed(digits);
}

function normalizeRisk(level?: string) {
  return String(level ?? "").toUpperCase();
}

function decisionClasses(decision?: string) {
  switch (normalizeRisk(decision)) {
    case "REJECT":
      return "border-red-200 bg-red-50 text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300";

    case "REVIEW":
      return "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300";

    case "PASS":
      return "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-300";

    default:
      return "border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300";
  }
}

function riskClasses(level?: string) {
  switch (normalizeRisk(level)) {
    case "CRITICAL":
      return "text-red-600 dark:text-red-400";

    case "HIGH":
      return "text-orange-600 dark:text-orange-400";

    case "MEDIUM":
      return "text-amber-600 dark:text-amber-400";

    case "LOW":
      return "text-slate-600 dark:text-slate-300";

    default:
      return "text-slate-600 dark:text-slate-300";
  }
}

export default function AnomaliesPage() {
  const [response, setResponse] = useState<AnomalyResponse | null>(null);

  const [page, setPage] = useState(1);

  const [search, setSearch] = useState("");
  const [decision, setDecision] = useState("ALL");
  const [risk, setRisk] = useState("ALL");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadAnomalies() {
      try {
        setLoading(true);
        setError("");

        const result = await getAnomalies({
          page,
          limit: PAGE_SIZE,
        });

        if (!cancelled) {
          setResponse(result as AnomalyResponse);
        }
      } catch (err) {
        if (!cancelled) {
          console.error(err);
          setError(
            "Unable to load anomaly results from the screening backend.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadAnomalies();

    return () => {
      cancelled = true;
    };
  }, [page]);

  const anomalies = response?.data ?? [];

  const filteredAnomalies = useMemo(() => {
    const query = search.trim().toLowerCase();

    return anomalies
      .filter((item) => {
        if (decision !== "ALL") {
          if (normalizeRisk(item.screening_decision) !== decision) {
            return false;
          }
        }

        if (risk !== "ALL") {
          if (normalizeRisk(item.risk_level) !== risk) {
            return false;
          }
        }

        if (!query) return true;

        return [item.component_id, item.lot_id, item.component_type]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(query));
      })
      .sort((a, b) => (b.risk_score_100 ?? 0) - (a.risk_score_100 ?? 0));
  }, [anomalies, search, decision, risk]);

  const total = response?.total ?? 0;

  const pages = response?.pages ?? Math.max(1, Math.ceil(total / PAGE_SIZE));

  const currentStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;

  const currentEnd = total === 0 ? 0 : Math.min(page * PAGE_SIZE, total);

  const pageReviewCount = anomalies.filter(
    (item) => normalizeRisk(item.screening_decision) === "REVIEW",
  ).length;

  const pageRejectCount = anomalies.filter(
    (item) => normalizeRisk(item.screening_decision) === "REJECT",
  ).length;

  const pageHighRiskCount = anomalies.filter((item) =>
    ["HIGH", "CRITICAL"].includes(normalizeRisk(item.risk_level)),
  ).length;

  function clearFilters() {
    setSearch("");
    setDecision("ALL");
    setRisk("ALL");
  }

  const hasFilters =
    search.trim() !== "" || decision !== "ALL" || risk !== "ALL";

  return (
    <div className="mx-auto w-full max-w-[1500px]">
      <PageHeader
        eyebrow="Reliability Monitoring"
        title="Anomalies"
        description="Review components with detected deviation, elevated risk, or screening concerns."
      />

      {/* Overview */}
      <section className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <div className="border border-slate-200 bg-white px-5 py-4 dark:border-slate-800 dark:bg-slate-950">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">
                Anomalies
              </p>

              <p className="mt-2 text-2xl font-semibold tabular-nums text-slate-950 dark:text-white">
                {loading ? "—" : total.toLocaleString()}
              </p>

              <p className="mt-1 text-xs text-slate-500">
                Across the screening dataset
              </p>
            </div>

            <AlertTriangle className="h-5 w-5 text-amber-500" />
          </div>
        </div>

        <div className="border border-slate-200 bg-white px-5 py-4 dark:border-slate-800 dark:bg-slate-950">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">
                High risk
              </p>

              <p className="mt-2 text-2xl font-semibold tabular-nums text-slate-950 dark:text-white">
                {loading ? "—" : pageHighRiskCount}
              </p>

              <p className="mt-1 text-xs text-slate-500">On this result page</p>
            </div>

            <ShieldAlert className="h-5 w-5 text-orange-500" />
          </div>
        </div>

        <div className="border border-slate-200 bg-white px-5 py-4 dark:border-slate-800 dark:bg-slate-950">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">
                Review
              </p>

              <p className="mt-2 text-2xl font-semibold tabular-nums text-slate-950 dark:text-white">
                {loading ? "—" : pageReviewCount}
              </p>

              <p className="mt-1 text-xs text-slate-500">On this result page</p>
            </div>

            <CircleAlert className="h-5 w-5 text-amber-500" />
          </div>
        </div>

        <div className="border border-slate-200 bg-white px-5 py-4 dark:border-slate-800 dark:bg-slate-950">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500">
                Reject
              </p>

              <p className="mt-2 text-2xl font-semibold tabular-nums text-slate-950 dark:text-white">
                {loading ? "—" : pageRejectCount}
              </p>

              <p className="mt-1 text-xs text-slate-500">On this result page</p>
            </div>

            <XCircle className="h-5 w-5 text-red-500" />
          </div>
        </div>
      </section>

      {/* Controls */}
      <section className="mb-5 border-y border-slate-200 py-4 dark:border-slate-800">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div className="flex flex-1 flex-col gap-3 md:flex-row">
            <div className="relative min-w-0 flex-1 md:max-w-md">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />

              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search component, lot or type..."
                className="h-10 w-full border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:focus:border-slate-600"
              />
            </div>

            <select
              value={decision}
              onChange={(event) => setDecision(event.target.value)}
              className="h-10 border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300"
            >
              <option value="ALL">All decisions</option>
              <option value="REVIEW">Review</option>
              <option value="REJECT">Reject</option>
              <option value="PASS">Pass</option>
            </select>

            <select
              value={risk}
              onChange={(event) => setRisk(event.target.value)}
              className="h-10 border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300"
            >
              <option value="ALL">All risk levels</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>

            {hasFilters && (
              <button
                onClick={clearFilters}
                className="h-10 px-3 text-sm font-medium text-slate-500 transition hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
              >
                Clear
              </button>
            )}
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-500">
            <SlidersHorizontal className="h-4 w-4" />
            <span>Backend anomaly results</span>
          </div>
        </div>
      </section>

      {/* Error */}
      {error && (
        <div className="mb-5 border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Table */}
      <section className="overflow-hidden border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
        <div className="flex flex-col gap-2 border-b border-slate-200 px-5 py-4 sm:flex-row sm:items-center sm:justify-between dark:border-slate-800">
          <div>
            <h2 className="text-sm font-semibold text-slate-950 dark:text-white">
              Detected anomalies
            </h2>

            <p className="mt-1 text-xs text-slate-500">
              Showing {currentStart.toLocaleString()}–
              {currentEnd.toLocaleString()} of {total.toLocaleString()} backend
              results
            </p>
          </div>

          <div className="text-xs text-slate-500">
            Page {page} of {pages}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[1050px] text-left">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 text-[11px] font-medium uppercase tracking-[0.12em] text-slate-500 dark:border-slate-800 dark:bg-slate-900/50">
                <th className="px-5 py-3">Component</th>
                <th className="px-4 py-3">Lot</th>
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">168H Iddq</th>
                <th className="px-4 py-3">Evidence</th>
                <th className="px-4 py-3">Risk</th>
                <th className="px-4 py-3">Decision</th>
                <th className="px-5 py-3 text-right">Inspect</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {loading ? (
                Array.from({ length: 8 }).map((_, index) => (
                  <tr key={index}>
                    <td colSpan={8} className="px-5 py-5">
                      <div className="h-5 animate-pulse bg-slate-100 dark:bg-slate-900" />
                    </td>
                  </tr>
                ))
              ) : filteredAnomalies.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-5 py-14 text-center">
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                      No anomalies match the current filters.
                    </p>

                    {hasFilters && (
                      <button
                        onClick={clearFilters}
                        className="mt-2 text-xs font-medium text-slate-500 underline underline-offset-4 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                      >
                        Clear filters
                      </button>
                    )}
                  </td>
                </tr>
              ) : (
                filteredAnomalies.map((item) => {
                  const riskScore = item.risk_score_100 ?? 0;

                  const evidence = item.statistical_evidence_count ?? 0;

                  const temporalScore =
                    item.max_temporal_robust_z ??
                    item.max_temporal_robust_z ??
                    0;

                  return (
                    <tr
                      key={item.component_id}
                      className="transition hover:bg-slate-50 dark:hover:bg-slate-900/50"
                    >
                      <td className="px-5 py-4">
                        <div>
                          <p className="text-sm font-semibold text-slate-900 dark:text-white">
                            {item.component_id}
                          </p>

                          <p className="mt-1 text-xs text-slate-500">
                            {formatNumber(item.temperature_C)}°C
                            <span className="mx-1.5 text-slate-300 dark:text-slate-700">
                              /
                            </span>
                            {formatNumber(item.voltage_V)}V
                          </p>
                        </div>
                      </td>

                      <td className="px-4 py-4">
                        <span className="text-sm text-slate-700 dark:text-slate-300">
                          {item.lot_id}
                        </span>
                      </td>

                      <td className="px-4 py-4">
                        <span className="text-sm text-slate-600 dark:text-slate-400">
                          {item.component_type}
                        </span>
                      </td>

                      <td className="px-4 py-4">
                        <div>
                          <p className="text-sm font-semibold tabular-nums text-slate-900 dark:text-white">
                            {formatNumber(item.iddq_168h_uA)}{" "}
                            <span className="text-xs font-normal text-slate-500">
                              µA
                            </span>
                          </p>

                          {item.limit_violation ? (
                            <p className="mt-1 text-[11px] font-medium text-red-600 dark:text-red-400">
                              Limit exceeded
                            </p>
                          ) : (
                            <p className="mt-1 text-[11px] text-slate-500">
                              Within absolute limit
                            </p>
                          )}
                        </div>
                      </td>

                      <td className="px-4 py-4">
                        <div className="space-y-1">
                          <p className="text-xs font-medium text-slate-700 dark:text-slate-300">
                            {evidence} statistical signal
                            {evidence === 1 ? "" : "s"}
                          </p>

                          <p className="text-[11px] text-slate-500">
                            Temporal z {formatNumber(temporalScore, 2)}
                          </p>
                        </div>
                      </td>

                      <td className="px-4 py-4">
                        <div>
                          <p
                            className={`text-sm font-semibold tabular-nums ${riskClasses(
                              item.risk_level,
                            )}`}
                          >
                            {formatNumber(riskScore, 1)}
                          </p>

                          <p className="mt-1 text-[11px] text-slate-500">
                            {item.risk_level ?? "—"}
                          </p>
                        </div>
                      </td>

                      <td className="px-4 py-4">
                        <span
                          className={`inline-flex border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.08em] ${decisionClasses(
                            item.screening_decision,
                          )}`}
                        >
                          {item.screening_decision ?? "—"}
                        </span>
                      </td>

                      <td className="px-5 py-4 text-right">
                        <Link
                          href={`/components/${encodeURIComponent(
                            item.component_id,
                          )}`}
                          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 transition hover:text-slate-950 dark:text-slate-400 dark:hover:text-white"
                        >
                          Inspect
                          <ArrowRight className="h-3.5 w-3.5" />
                        </Link>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between border-t border-slate-200 px-5 py-3 dark:border-slate-800">
          <p className="text-xs text-slate-500">
            {total.toLocaleString()} anomaly results
          </p>

          <div className="flex items-center gap-1">
            <button
              disabled={page <= 1 || loading}
              onClick={() => setPage((value) => Math.max(1, value - 1))}
              className="inline-flex h-8 w-8 items-center justify-center border border-slate-200 text-slate-500 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-800 dark:hover:bg-slate-900"
              aria-label="Previous page"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>

            <span className="px-3 text-xs tabular-nums text-slate-600 dark:text-slate-400">
              {page} / {pages}
            </span>

            <button
              disabled={page >= pages || loading}
              onClick={() => setPage((value) => Math.min(pages, value + 1))}
              className="inline-flex h-8 w-8 items-center justify-center border border-slate-200 text-slate-500 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-800 dark:hover:bg-slate-900"
              aria-label="Next page"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      </section>

      {/* Explanation */}
      <div className="mt-4 flex items-start gap-3 text-xs leading-5 text-slate-500">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />

        <p>
          Anomaly results are sourced directly from the Module A screening
          output. An anomaly indicates detected deviation; it does not by itself
          mean the component must be rejected. The screening decision remains a
          separate outcome based on the backend screening logic.
        </p>
      </div>
    </div>
  );
}
