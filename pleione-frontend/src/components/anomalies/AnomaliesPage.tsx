"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Search,
  ShieldAlert,
  Eye,
  Activity,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const PAGE_SIZE = 25;

type AnomalyRecord = {
  component_id: string;
  lot_id: string;
  component_type: string;

  temperature_C: number | null;
  voltage_V: number | null;

  iddq_0h_uA: number | null;
  leakage_0h_uA: number | null;

  module_a_score: number | null;
  module_a_status: string;
  peer_source: string;
};

type AnomalyResponse = {
  page: number;
  limit: number;
  pages: number;
  total: number;
  data: AnomalyRecord[];
};

type Summary = {
  total_components: number;
  anomalous: number;
  watch: number;
  normal: number;
  attention: number;
  anomaly_rate: number;
  attention_rate: number;
};

type FilterResponse = {
  lots: string[];
  component_types: string[];
  statuses: string[];
};

function formatNumber(value: number | null | undefined, digits = 2) {
  if (
    value === null ||
    value === undefined ||
    !Number.isFinite(Number(value))
  ) {
    return "—";
  }

  return Number(value).toFixed(digits);
}

function statusTone(status: string) {
  switch (status.toUpperCase()) {
    case "ANOMALOUS":
      return "text-red-300";

    case "WATCH":
      return "text-amber-300";

    case "NORMAL":
      return "text-emerald-300";

    default:
      return "text-slate-400";
  }
}

function statusDot(status: string) {
  switch (status.toUpperCase()) {
    case "ANOMALOUS":
      return "bg-red-400";

    case "WATCH":
      return "bg-amber-400";

    case "NORMAL":
      return "bg-emerald-400";

    default:
      return "bg-slate-500";
  }
}

function scoreTone(score: number | null) {
  const value = Number(score);

  if (!Number.isFinite(value)) {
    return "text-slate-400";
  }

  if (value >= 5) {
    return "text-red-300";
  }

  if (value >= 3) {
    return "text-amber-300";
  }

  return "text-slate-200";
}

export default function AnomaliesPage() {
  const [response, setResponse] = useState<AnomalyResponse | null>(null);

  const [summary, setSummary] = useState<Summary | null>(null);

  const [filters, setFilters] = useState<FilterResponse | null>(null);

  const [page, setPage] = useState(1);

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("ALL");
  const [lot, setLot] = useState("ALL");
  const [componentType, setComponentType] = useState("ALL");

  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(true);

  const [error, setError] = useState("");

  // ==========================================================
  // LOAD SUMMARY + FILTER OPTIONS
  // ==========================================================

  useEffect(() => {
    const controller = new AbortController();

    async function loadOverview() {
      try {
        setSummaryLoading(true);

        const [summaryResponse, filtersResponse] = await Promise.all([
          fetch(`${API_BASE}/api/anomalies/summary`, {
            signal: controller.signal,
          }),
          fetch(`${API_BASE}/api/anomalies/filters`, {
            signal: controller.signal,
          }),
        ]);

        if (!summaryResponse.ok) {
          throw new Error("Unable to load anomaly summary.");
        }

        if (!filtersResponse.ok) {
          throw new Error("Unable to load anomaly filters.");
        }

        const summaryData = (await summaryResponse.json()) as Summary;

        const filterData = (await filtersResponse.json()) as FilterResponse;

        if (!controller.signal.aborted) {
          setSummary(summaryData);
          setFilters(filterData);
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }

        console.error(err);
      } finally {
        if (!controller.signal.aborted) {
          setSummaryLoading(false);
        }
      }
    }

    loadOverview();

    return () => {
      controller.abort();
    };
  }, []);

  // ==========================================================
  // LOAD TABLE
  // ==========================================================

  useEffect(() => {
    const controller = new AbortController();

    async function loadAnomalies() {
      try {
        setLoading(true);
        setError("");

        const params = new URLSearchParams();

        params.set("page", String(page));

        params.set("limit", String(PAGE_SIZE));

        if (search.trim()) {
          params.set("search", search.trim());
        }

        if (status !== "ALL") {
          params.set("status", status);
        }

        if (lot !== "ALL") {
          params.set("lot_id", lot);
        }

        if (componentType !== "ALL") {
          params.set("component_type", componentType);
        }

        const response = await fetch(
          `${API_BASE}/api/anomalies/?${params.toString()}`,
          {
            signal: controller.signal,
          },
        );

        if (!response.ok) {
          let message = "Unable to load anomaly results.";

          try {
            const body = await response.json();

            if (body?.detail) {
              message =
                typeof body.detail === "string"
                  ? body.detail
                  : JSON.stringify(body.detail);
            }
          } catch {
            // Ignore invalid JSON.
          }

          throw new Error(message);
        }

        const result = (await response.json()) as AnomalyResponse;

        if (!controller.signal.aborted) {
          setResponse(result);
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }

        if (!controller.signal.aborted) {
          console.error(err);

          setError(
            err instanceof Error
              ? err.message
              : "Unable to load anomaly results.",
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadAnomalies();

    return () => {
      controller.abort();
    };
  }, [page, search, status, lot, componentType]);

  // ==========================================================
  // LOCAL SORT
  // ==========================================================

  const anomalies = useMemo(() => {
    return [...(response?.data ?? [])].sort(
      (a, b) => (b.module_a_score ?? 0) - (a.module_a_score ?? 0),
    );
  }, [response]);

  const total = response?.total ?? 0;

  const pages = response?.pages ?? Math.max(1, Math.ceil(total / PAGE_SIZE));

  const start = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;

  const end = total === 0 ? 0 : Math.min(page * PAGE_SIZE, total);

  // ==========================================================
  // FILTER RESET
  // ==========================================================

  function clearFilters() {
    setSearch("");
    setStatus("ALL");
    setLot("ALL");
    setComponentType("ALL");
    setPage(1);
  }

  const hasFilters =
    search.trim() !== "" ||
    status !== "ALL" ||
    lot !== "ALL" ||
    componentType !== "ALL";

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <main className="min-h-screen bg-[#020618] text-slate-100">
      <div className="mx-auto w-full max-w-[1500px] px-5 py-8 sm:px-6 lg:px-8">
        {/* ================================================== */}
        {/* HEADER */}
        {/* ================================================== */}

        <header>
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-400">
                Reliability Monitoring
              </p>

              <h1 className="mt-2 text-2xl font-semibold tracking-tight text-white">
                Anomaly Detection
              </h1>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
                Review components that show abnormal behavior at 0H screening
                compared with comparable components under similar operating
                conditions.
              </p>
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-500">
              <Activity className="h-4 w-4" />
              <span>Module A · 0H evidence</span>
            </div>
          </div>
        </header>

        {/* ================================================== */}
        {/* SUMMARY */}
        {/* ================================================== */}

        <section className="mt-8 grid grid-cols-1 gap-px overflow-hidden border border-slate-800 bg-slate-800 sm:grid-cols-2 xl:grid-cols-4">
          <SummaryMetric
            label="Components screened"
            value={
              summaryLoading
                ? "—"
                : (summary?.total_components.toLocaleString() ?? "0")
            }
            description="Current Module A population"
            icon={<Activity className="h-4 w-4" />}
          />

          <SummaryMetric
            label="Anomalous"
            value={
              summaryLoading
                ? "—"
                : (summary?.anomalous.toLocaleString() ?? "0")
            }
            description={
              summary
                ? `${summary.anomaly_rate.toFixed(2)}% of components`
                : "Strong deviation"
            }
            icon={<ShieldAlert className="h-4 w-4" />}
            tone="red"
          />

          <SummaryMetric
            label="Watch"
            value={
              summaryLoading ? "—" : (summary?.watch.toLocaleString() ?? "0")
            }
            description="Requires attention"
            icon={<Eye className="h-4 w-4" />}
            tone="amber"
          />

          <SummaryMetric
            label="Normal"
            value={
              summaryLoading ? "—" : (summary?.normal.toLocaleString() ?? "0")
            }
            description="Within peer behavior"
            icon={<Activity className="h-4 w-4" />}
            tone="green"
          />
        </section>

        {/* ================================================== */}
        {/* INFORMATION LINE */}
        {/* ================================================== */}

        <div className="mt-6 flex items-start gap-3 border-y border-slate-800/80 py-4">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />

          <p className="text-xs leading-5 text-slate-500">
            An anomaly indicates deviation from comparable components at 0H. It
            is screening evidence, not an automatic failure decision. Final
            disposition is determined separately by the screening risk engine.
          </p>
        </div>

        {/* ================================================== */}
        {/* FILTERS */}
        {/* ================================================== */}

        <section className="mt-6 border-b border-slate-800 pb-5">
          <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex flex-1 flex-col gap-3 md:flex-row">
              {/* SEARCH */}

              <div className="relative min-w-0 flex-1 md:max-w-md">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-600" />

                <input
                  value={search}
                  onChange={(event) => {
                    setSearch(event.target.value);
                    setPage(1);
                  }}
                  placeholder="Search component, lot or type..."
                  className="h-10 w-full border border-slate-800 bg-[#020618] pl-9 pr-3 text-sm text-slate-200 outline-none transition placeholder:text-slate-600 focus:border-slate-600"
                />
              </div>

              {/* STATUS */}

              <select
                value={status}
                onChange={(event) => {
                  setStatus(event.target.value);
                  setPage(1);
                }}
                className="h-10 border border-slate-800 bg-[#020618] px-3 text-sm text-slate-300 outline-none focus:border-slate-600"
              >
                <option value="ALL">All statuses</option>

                <option value="ANOMALOUS">Anomalous</option>

                <option value="WATCH">Watch</option>

                <option value="NORMAL">Normal</option>
              </select>

              {/* LOT */}

              <select
                value={lot}
                onChange={(event) => {
                  setLot(event.target.value);
                  setPage(1);
                }}
                className="h-10 border border-slate-800 bg-[#020618] px-3 text-sm text-slate-300 outline-none focus:border-slate-600"
              >
                <option value="ALL">All lots</option>

                {(filters?.lots ?? []).map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>

              {/* TYPE */}

              <select
                value={componentType}
                onChange={(event) => {
                  setComponentType(event.target.value);
                  setPage(1);
                }}
                className="h-10 border border-slate-800 bg-[#020618] px-3 text-sm text-slate-300 outline-none focus:border-slate-600"
              >
                <option value="ALL">All component types</option>

                {(filters?.component_types ?? []).map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>

              {hasFilters && (
                <button
                  type="button"
                  onClick={clearFilters}
                  className="h-10 px-3 text-sm text-slate-500 transition hover:text-white"
                >
                  Clear
                </button>
              )}
            </div>

            <div className="text-xs text-slate-600">0H peer comparison</div>
          </div>
        </section>

        {/* ================================================== */}
        {/* ERROR */}
        {/* ================================================== */}

        {error && (
          <div className="mt-5 border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {/* ================================================== */}
        {/* TABLE */}
        {/* ================================================== */}

        <section className="mt-6 overflow-hidden border border-slate-800">
          <div className="flex flex-col gap-2 border-b border-slate-800 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-sm font-semibold text-white">
                Anomaly evidence
              </h2>

              <p className="mt-1 text-xs text-slate-600">
                Showing {start.toLocaleString()}–{end.toLocaleString()} of{" "}
                {total.toLocaleString()} matching components
              </p>
            </div>

            <div className="text-xs text-slate-600">
              Page {page} of {pages || 1}
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full min-w-[1050px] text-left">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-900/40 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-600">
                  <th className="px-5 py-3">Component</th>

                  <th className="px-4 py-3">Lot</th>

                  <th className="px-4 py-3">Type</th>

                  <th className="px-4 py-3">0H IDDQ</th>

                  <th className="px-4 py-3">0H Leakage</th>

                  <th className="px-4 py-3">Peer Source</th>

                  <th className="px-4 py-3">Peer Score</th>

                  <th className="px-4 py-3">Status</th>

                  <th className="px-5 py-3 text-right">Inspect</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-800/70">
                {/* LOADING */}

                {loading ? (
                  Array.from({
                    length: 8,
                  }).map((_, index) => (
                    <tr key={index}>
                      <td colSpan={9} className="px-5 py-5">
                        <div className="h-5 w-full animate-pulse bg-slate-900/80" />
                      </td>
                    </tr>
                  ))
                ) : anomalies.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-5 py-16 text-center">
                      <div className="mx-auto max-w-md">
                        <Activity className="mx-auto h-7 w-7 text-slate-700" />

                        <p className="mt-4 text-sm font-medium text-slate-300">
                          No matching anomaly evidence
                        </p>

                        <p className="mt-2 text-xs leading-5 text-slate-600">
                          No components match the current search and screening
                          filters.
                        </p>

                        {hasFilters && (
                          <button
                            type="button"
                            onClick={clearFilters}
                            className="mt-4 text-xs font-medium text-slate-400 underline underline-offset-4 hover:text-white"
                          >
                            Clear filters
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ) : (
                  anomalies.map((item) => (
                    <tr
                      key={item.component_id}
                      className="transition hover:bg-slate-900/40"
                    >
                      {/* COMPONENT */}

                      <td className="px-5 py-4">
                        <div>
                          <p className="text-sm font-semibold text-white">
                            {item.component_id}
                          </p>

                          <p className="mt-1 text-xs text-slate-600">
                            {formatNumber(item.temperature_C, 2)}
                            °C
                            <span className="mx-1.5 text-slate-800">/</span>
                            {formatNumber(item.voltage_V, 2)}V
                          </p>
                        </div>
                      </td>

                      {/* LOT */}

                      <td className="px-4 py-4">
                        <span className="text-sm text-slate-300">
                          {item.lot_id}
                        </span>
                      </td>

                      {/* TYPE */}

                      <td className="px-4 py-4">
                        <span className="text-sm text-slate-500">
                          {item.component_type}
                        </span>
                      </td>

                      {/* IDDQ */}

                      <td className="px-4 py-4">
                        <span className="font-mono text-sm tabular-nums text-slate-200">
                          {formatNumber(item.iddq_0h_uA, 2)}
                          <span className="ml-1 text-[11px] text-slate-600">
                            µA
                          </span>
                        </span>
                      </td>

                      {/* LEAKAGE */}

                      <td className="px-4 py-4">
                        <span className="font-mono text-sm tabular-nums text-slate-300">
                          {formatNumber(item.leakage_0h_uA, 2)}
                          <span className="ml-1 text-[11px] text-slate-600">
                            µA
                          </span>
                        </span>
                      </td>

                      {/* PEER SOURCE */}

                      <td className="px-4 py-4">
                        <span className="text-xs text-slate-500">
                          {item.peer_source || "—"}
                        </span>
                      </td>

                      {/* SCORE */}

                      <td className="px-4 py-4">
                        <span
                          className={`font-mono text-sm font-semibold tabular-nums ${scoreTone(
                            item.module_a_score,
                          )}`}
                        >
                          {formatNumber(item.module_a_score, 2)}
                        </span>
                      </td>

                      {/* STATUS */}

                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2">
                          <span
                            className={`h-1.5 w-1.5 rounded-full ${statusDot(
                              item.module_a_status,
                            )}`}
                          />

                          <span
                            className={`text-xs font-semibold uppercase tracking-[0.08em] ${statusTone(
                              item.module_a_status,
                            )}`}
                          >
                            {item.module_a_status}
                          </span>
                        </div>
                      </td>

                      {/* INSPECT */}

                      <td className="px-5 py-4 text-right">
                        <Link
                          href={`/components/${encodeURIComponent(
                            item.component_id,
                          )}`}
                          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 transition hover:text-white"
                        >
                          Inspect
                          <ArrowRight className="h-3.5 w-3.5" />
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* ================================================= */}
          {/* PAGINATION */}
          {/* ================================================= */}

          <div className="flex items-center justify-between border-t border-slate-800 px-5 py-3">
            <p className="text-xs text-slate-600">
              {total.toLocaleString()} matching components
            </p>

            <div className="flex items-center gap-1">
              <button
                type="button"
                disabled={page <= 1 || loading}
                onClick={() => setPage((value) => Math.max(1, value - 1))}
                className="inline-flex h-8 w-8 items-center justify-center border border-slate-800 text-slate-500 transition hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-30"
                aria-label="Previous page"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>

              <span className="px-3 text-xs tabular-nums text-slate-500">
                {page} / {pages || 1}
              </span>

              <button
                type="button"
                disabled={page >= pages || loading || pages === 0}
                onClick={() => setPage((value) => Math.min(pages, value + 1))}
                className="inline-flex h-8 w-8 items-center justify-center border border-slate-800 text-slate-500 transition hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-30"
                aria-label="Next page"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </section>

        {/* ================================================== */}
        {/* FOOTNOTE */}
        {/* ================================================== */}

        <footer className="mt-5 flex items-start gap-3 text-xs leading-5 text-slate-600">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500/70" />

          <p>
            Module A evaluates 0H behavior against comparable components using
            operating conditions and peer measurements. WATCH and ANOMALOUS
            identify evidence requiring attention; they are not final screening
            dispositions.
          </p>
        </footer>
      </div>
    </main>
  );
}

// ============================================================
// SUMMARY METRIC
// ============================================================

function SummaryMetric({
  label,
  value,
  description,
  icon,
  tone = "default",
}: {
  label: string;
  value: string;
  description: string;
  icon: React.ReactNode;
  tone?: "default" | "red" | "amber" | "green";
}) {
  const iconTone =
    tone === "red"
      ? "text-red-400"
      : tone === "amber"
        ? "text-amber-400"
        : tone === "green"
          ? "text-emerald-400"
          : "text-slate-500";

  return (
    <div className="bg-[#020618] px-5 py-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-600">
            {label}
          </p>

          <p className="mt-2 text-2xl font-semibold tabular-nums text-white">
            {value}
          </p>

          <p className="mt-1 text-xs text-slate-600">{description}</p>
        </div>

        <span className={iconTone}>{icon}</span>
      </div>
    </div>
  );
}
