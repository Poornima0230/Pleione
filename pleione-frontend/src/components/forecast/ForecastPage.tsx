"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type ForecastRecord = {
  component_id: string;
  lot_id: string;
  component_type: string;

  temperature_C: number | null;
  voltage_V: number | null;

  iddq_0h_uA: number | null;
  iddq_24h_uA: number | null;

  leakage_0h_uA: number | null;
  leakage_24h_uA: number | null;

  delta_0_24: number | null;

  predicted_168h_uA: number | null;
  prediction_lower_uA: number | null;
  prediction_upper_uA: number | null;

  failure_probability: number | null;
  failure_risk: string;

  absolute_limit_uA: number | null;
};

type ForecastSummary = {
  very_low: number;
  low: number;
  medium: number;
  high: number;
  critical: number;
};

type ForecastResponse = {
  page: number;
  limit: number;
  pages: number;
  total: number;
  summary: ForecastSummary;
  forecasts: ForecastRecord[];
};

// ============================================================
// Helpers
// ============================================================

function formatNumber(value: number | null | undefined, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }

  return value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function formatProbability(value: number | null | undefined) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "—";
  }

  return `${(value * 100).toFixed(1)}%`;
}

function normalizeRisk(value: string | null | undefined) {
  return String(value || "")
    .trim()
    .toUpperCase()
    .replace(/[\s-]+/g, "_");
}

function riskLabel(value: string) {
  const normalized = normalizeRisk(value);

  switch (normalized) {
    case "VERY_LOW":
      return "VERY LOW";

    case "LOW":
      return "LOW";

    case "MEDIUM":
      return "MEDIUM";

    case "HIGH":
      return "HIGH";

    case "CRITICAL":
      return "CRITICAL";

    default:
      return value || "UNKNOWN";
  }
}

function riskBadgeClass(value: string) {
  const normalized = normalizeRisk(value);

  switch (normalized) {
    case "VERY_LOW":
      return "border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300";

    case "LOW":
      return "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/20 dark:text-emerald-400";

    case "MEDIUM":
      return "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-400";

    case "HIGH":
      return "border-orange-200 bg-orange-50 text-orange-700 dark:border-orange-900/50 dark:bg-orange-950/20 dark:text-orange-400";

    case "CRITICAL":
      return "border-red-200 bg-red-50 text-red-700 dark:border-red-900/50 dark:bg-red-950/20 dark:text-red-400";

    default:
      return "border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300";
  }
}

// ============================================================
// Main page
// ============================================================

export default function ForecastPage() {
  const [data, setData] = useState<ForecastResponse | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [page, setPage] = useState(1);

  const limit = 20;

  const [search, setSearch] = useState("");

  const [lot, setLot] = useState("ALL");

  const [componentType, setComponentType] = useState("ALL");

  const [risk, setRisk] = useState("ALL");

  const [filterOptions, setFilterOptions] = useState<{
    lots: string[];
    componentTypes: string[];
  }>({
    lots: [],
    componentTypes: [],
  });

  // ==========================================================
  // Load current forecast page
  // ==========================================================

  useEffect(() => {
    const controller = new AbortController();

    async function loadForecast() {
      try {
        setLoading(true);
        setError("");

        const params = new URLSearchParams();

        params.set("page", String(page));

        params.set("limit", String(limit));

        if (search.trim()) {
          params.set("search", search.trim());
        }

        if (lot !== "ALL") {
          params.set("lot_id", lot);
        }

        if (componentType !== "ALL") {
          params.set("component_type", componentType);
        }

        if (risk !== "ALL") {
          params.set("risk", risk);
        }

        const response = await fetch(
          `${API_BASE}/api/forecast/?${params.toString()}`,
          {
            signal: controller.signal,
            cache: "no-store",
          },
        );

        if (!response.ok) {
          throw new Error(`Failed to load forecast data (${response.status})`);
        }

        const result: ForecastResponse = await response.json();

        setData(result);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }

        setError(
          err instanceof Error ? err.message : "Unable to load forecast data.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadForecast();

    return () => controller.abort();
  }, [page, search, lot, componentType, risk]);

  // ==========================================================
  // Load filter options only
  //
  // This does NOT calculate summary values.
  // Summary comes from the main API response.
  // ==========================================================

  useEffect(() => {
    const controller = new AbortController();

    async function loadFilterOptions() {
      try {
        const response = await fetch(
          `${API_BASE}/api/forecast/?page=1&limit=200`,
          {
            signal: controller.signal,
            cache: "no-store",
          },
        );

        if (!response.ok) {
          return;
        }

        const result: ForecastResponse = await response.json();

        const lots = Array.from(
          new Set(result.forecasts.map((item) => item.lot_id).filter(Boolean)),
        ).sort();

        const componentTypes = Array.from(
          new Set(
            result.forecasts.map((item) => item.component_type).filter(Boolean),
          ),
        ).sort();

        setFilterOptions({
          lots,
          componentTypes,
        });
      } catch {
        // Filter options are non-critical.
      }
    }

    loadFilterOptions();

    return () => controller.abort();
  }, []);

  // ==========================================================
  // Summary
  // ==========================================================

  const summary = data?.summary ?? {
    very_low: 0,
    low: 0,
    medium: 0,
    high: 0,
    critical: 0,
  };

  const riskTotal = useMemo(() => {
    return (
      summary.very_low +
      summary.low +
      summary.medium +
      summary.high +
      summary.critical
    );
  }, [summary]);

  const resetFilters = () => {
    setSearch("");
    setLot("ALL");
    setComponentType("ALL");
    setRisk("ALL");
    setPage(1);
  };

  const hasFilters =
    search.trim() !== "" ||
    lot !== "ALL" ||
    componentType !== "ALL" ||
    risk !== "ALL";

  // ==========================================================
  // Loading
  // ==========================================================

  if (loading && !data) {
    return <ForecastLoading />;
  }

  // ==========================================================
  // Error
  // ==========================================================

  if (error && !data) {
    return (
      <main className="min-h-screen bg-white px-5 py-8 text-slate-900 dark:bg-[#020618] dark:text-slate-100 sm:px-7 lg:px-8">
        <div className="mx-auto max-w-[1450px]">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            Module B · Predictive screening
          </p>

          <h1 className="mt-2 text-3xl font-semibold">Forecast</h1>

          <div className="mt-8 rounded-xl border border-red-200 bg-red-50 p-5 dark:border-red-900/50 dark:bg-red-950/20">
            <p className="font-medium text-red-700 dark:text-red-400">
              Unable to load forecast data
            </p>

            <p className="mt-1 text-sm text-red-600 dark:text-red-400/80">
              {error}
            </p>

            <button
              onClick={() => window.location.reload()}
              className="mt-4 rounded-lg border border-red-300 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-100 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950/40"
            >
              Retry
            </button>
          </div>
        </div>
      </main>
    );
  }

  if (!data) {
    return null;
  }

  // ==========================================================
  // Page
  // ==========================================================

  return (
    <main className="min-h-screen bg-white px-5 py-7 text-slate-900 dark:bg-[#020618] dark:text-slate-100 sm:px-7 lg:px-8">
      <div className="mx-auto max-w-[1450px]">
        {/* ================================================== */}
        {/* Header */}
        {/* ================================================== */}

        <header className="mb-8">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            Module B · Predictive screening
          </p>

          <div className="mt-2 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                Forecast
              </h1>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
                Predictive assessment of component behavior at 168h using the
                available 0h and 24h screening measurements.
              </p>
            </div>

            <div className="text-sm text-slate-500 dark:text-slate-400">
              <span className="font-semibold text-slate-900 dark:text-slate-100">
                {data.total.toLocaleString()}
              </span>{" "}
              forecasted components
            </div>
          </div>
        </header>

        {/* ================================================== */}
        {/* Forecast path */}
        {/* ================================================== */}

        <section className="mb-8 rounded-2xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/20">
          <div className="flex flex-col md:flex-row">
            <ForecastStep
              number="01"
              label="Screening input"
              value="0h"
              description="Baseline electrical measurement"
            />

            <ForecastConnector />

            <ForecastStep
              number="02"
              label="Screening input"
              value="24h"
              description="Early burn-in measurement"
            />

            <ForecastConnector />

            <ForecastStep
              number="03"
              label="Forecast horizon"
              value="168h"
              description="Predicted electrical behavior"
            />
          </div>
        </section>

        {/* ================================================== */}
        {/* Risk distribution — compact, not dashboard cards */}
        {/* ================================================== */}

        <section className="mb-8">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold">Future risk</h2>

              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Failure probability estimated by Module B.
              </p>
            </div>

            <span className="text-xs text-slate-400">
              {riskTotal.toLocaleString()} classified
            </span>
          </div>

          <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800">
            <div className="grid grid-cols-2 divide-x divide-y divide-slate-200 sm:grid-cols-5 sm:divide-y-0 dark:divide-slate-800">
              <RiskCell
                label="Very low"
                range="< 15%"
                count={summary.very_low}
                total={riskTotal}
              />

              <RiskCell
                label="Low"
                range="15–40%"
                count={summary.low}
                total={riskTotal}
              />

              <RiskCell
                label="Medium"
                range="40–75%"
                count={summary.medium}
                total={riskTotal}
              />

              <RiskCell
                label="High"
                range="≥ 75%"
                count={summary.high}
                total={riskTotal}
              />

              <RiskCell
                label="Critical"
                range="critical"
                count={summary.critical}
                total={riskTotal}
              />
            </div>
          </div>
        </section>

        {/* ================================================== */}
        {/* Filters */}
        {/* ================================================== */}

        <section className="mb-7">
          <div className="mb-3 flex items-end justify-between">
            <div>
              <h2 className="text-base font-semibold">Forecast explorer</h2>

              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Inspect predicted 168h behavior for individual components.
              </p>
            </div>

            {hasFilters && (
              <button
                onClick={resetFilters}
                className="text-xs font-medium text-slate-500 hover:text-slate-900 hover:underline dark:text-slate-400 dark:hover:text-slate-100"
              >
                Reset
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
            <div className="xl:col-span-1">
              <label className="mb-1.5 block text-xs font-medium text-slate-500">
                Search component
              </label>

              <input
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
                placeholder="C00001"
                className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm outline-none placeholder:text-slate-400 focus:border-slate-400 dark:border-slate-700 dark:bg-[#020618] dark:text-slate-100"
              />
            </div>

            <FilterSelect
              label="Lot"
              value={lot}
              options={filterOptions.lots}
              allLabel="All lots"
              onChange={(value) => {
                setLot(value);
                setPage(1);
              }}
            />

            <FilterSelect
              label="Component type"
              value={componentType}
              options={filterOptions.componentTypes}
              allLabel="All types"
              onChange={(value) => {
                setComponentType(value);
                setPage(1);
              }}
            />

            <FilterSelect
              label="Future risk"
              value={risk}
              options={["VERY_LOW", "LOW", "MEDIUM", "HIGH", "CRITICAL"]}
              allLabel="All risk levels"
              onChange={(value) => {
                setRisk(value);
                setPage(1);
              }}
            />
          </div>
        </section>

        {/* ================================================== */}
        {/* Table */}
        {/* ================================================== */}

        <section>
          <div className="mb-3 flex items-end justify-between">
            <div>
              <h2 className="text-base font-semibold">
                168h forecast assessment
              </h2>

              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Predicted behavior and uncertainty from the 0h and 24h
                observations.
              </p>
            </div>

            <span className="text-xs text-slate-500 dark:text-slate-400">
              Page {data.page} of {data.pages}
            </span>
          </div>

          <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[1200px] border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 bg-slate-50 text-left dark:border-slate-800 dark:bg-slate-900/50">
                    <th className="px-5 py-3.5 text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500">
                      Component
                    </th>

                    <th className="px-5 py-3.5 text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500">
                      Lot
                    </th>

                    <th className="px-5 py-3.5 text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500">
                      0h → 24h IDDQ
                    </th>

                    <th className="px-5 py-3.5 text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500">
                      Δ IDDQ
                    </th>

                    <th className="px-5 py-3.5 text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500">
                      168h prediction
                    </th>

                    <th className="px-5 py-3.5 text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500">
                      Prediction interval
                    </th>

                    <th className="px-5 py-3.5 text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500">
                      Failure probability
                    </th>

                    <th className="px-5 py-3.5 text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500">
                      Risk
                    </th>

                    <th className="px-5 py-3.5 text-right text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-500">
                      Inspect
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {data.forecasts.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="px-6 py-16 text-center">
                        <p className="text-sm font-medium">
                          No forecast records found
                        </p>

                        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                          Try changing the selected filters.
                        </p>
                      </td>
                    </tr>
                  ) : (
                    data.forecasts.map((item) => (
                      <ForecastRow key={item.component_id} item={item} />
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}

            <div className="flex items-center justify-between border-t border-slate-200 px-5 py-4 dark:border-slate-800">
              <span className="text-xs text-slate-500 dark:text-slate-400">
                Page {data.page} of {data.pages}
              </span>

              <div className="flex gap-2">
                <button
                  disabled={data.page <= 1}
                  onClick={() => setPage((current) => Math.max(1, current - 1))}
                  className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-700 dark:hover:bg-slate-900"
                >
                  Previous
                </button>

                <button
                  disabled={data.page >= data.pages}
                  onClick={() =>
                    setPage((current) => Math.min(data.pages, current + 1))
                  }
                  className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-700 dark:hover:bg-slate-900"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* ================================================== */}
        {/* Method note */}
        {/* ================================================== */}

        <section className="mt-7 border-t border-slate-200 pt-5 dark:border-slate-800">
          <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">
            Forecast interpretation
          </p>

          <p className="mt-2 max-w-4xl text-xs leading-6 text-slate-500 dark:text-slate-400">
            Module B uses the available 0h and 24h measurements to estimate
            component behavior at 168h. The prediction interval represents
            uncertainty around the forecast, while failure probability estimates
            the likelihood of exceeding the specified electrical limit. Final
            screening decisions are determined separately by Module C.
          </p>
        </section>
      </div>
    </main>
  );
}

// ============================================================
// Forecast row
// ============================================================

function ForecastRow({ item }: { item: ForecastRecord }) {
  const probability = item.failure_probability ?? 0;

  return (
    <tr className="transition hover:bg-slate-50 dark:hover:bg-slate-900/40">
      {/* Component */}

      <td className="px-5 py-5">
        <Link
          href={`/components/${encodeURIComponent(item.component_id)}`}
          className="font-semibold text-slate-900 hover:underline dark:text-slate-100"
        >
          {item.component_id}
        </Link>

        <p className="mt-1 text-[11px] text-slate-400">{item.component_type}</p>
      </td>

      {/* Lot */}

      <td className="px-5 py-5 text-sm text-slate-600 dark:text-slate-300">
        {item.lot_id}
      </td>

      {/* 0h → 24h */}

      <td className="px-5 py-5">
        <div className="whitespace-nowrap text-sm font-medium">
          {formatNumber(item.iddq_0h_uA)}

          <span className="mx-1.5 text-slate-400">→</span>

          {formatNumber(item.iddq_24h_uA)}

          <span className="ml-1 text-[11px] font-normal text-slate-400">
            µA
          </span>
        </div>
      </td>

      {/* Delta */}

      <td className="px-5 py-5">
        <span className="whitespace-nowrap text-sm font-medium">
          {item.delta_0_24 !== null && item.delta_0_24 > 0 ? "+" : ""}

          {formatNumber(item.delta_0_24)}

          <span className="ml-1 text-[11px] font-normal text-slate-400">
            µA
          </span>
        </span>
      </td>

      {/* Prediction */}

      <td className="px-5 py-5">
        <p className="whitespace-nowrap text-sm font-semibold">
          {formatNumber(item.predicted_168h_uA)}

          <span className="ml-1 text-[11px] font-normal text-slate-400">
            µA
          </span>
        </p>

        {item.absolute_limit_uA !== null && (
          <p className="mt-1 text-[11px] text-slate-400">
            limit {formatNumber(item.absolute_limit_uA)} µA
          </p>
        )}
      </td>

      {/* Prediction interval */}

      <td className="px-5 py-5">
        <span className="whitespace-nowrap text-sm text-slate-600 dark:text-slate-300">
          {formatNumber(item.prediction_lower_uA)}

          <span className="mx-1 text-slate-400">–</span>

          {formatNumber(item.prediction_upper_uA)}

          <span className="ml-1 text-[11px] text-slate-400">µA</span>
        </span>
      </td>

      {/* Probability */}

      <td className="px-5 py-5">
        <div className="w-[130px]">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold">
              {formatProbability(item.failure_probability)}
            </span>
          </div>

          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
            <div
              className="h-full rounded-full bg-slate-500"
              style={{
                width: `${Math.min(100, Math.max(0, probability * 100))}%`,
              }}
            />
          </div>
        </div>
      </td>

      {/* Risk */}

      <td className="px-5 py-5">
        <span
          className={`inline-flex rounded-md border px-2.5 py-1.5 text-[10px] font-semibold tracking-wide ${riskBadgeClass(
            item.failure_risk,
          )}`}
        >
          {riskLabel(item.failure_risk)}
        </span>
      </td>

      {/* Inspect */}

      <td className="px-5 py-5 text-right">
        <Link
          href={`/components/${encodeURIComponent(item.component_id)}`}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          Inspect
          <svg
            width="13"
            height="13"
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
  );
}

// ============================================================
// Forecast step
// ============================================================

function ForecastStep({
  number,
  label,
  value,
  description,
}: {
  number: string;
  label: string;
  value: string;
  description: string;
}) {
  return (
    <div className="flex-1 px-5 py-5">
      <div className="flex items-start gap-4">
        <span className="pt-0.5 text-[10px] font-semibold tracking-[0.15em] text-slate-400">
          {number}
        </span>

        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500">
            {label}
          </p>

          <p className="mt-1 text-xl font-semibold tracking-tight">{value}</p>

          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            {description}
          </p>
        </div>
      </div>
    </div>
  );
}

function ForecastConnector() {
  return (
    <div className="hidden items-center md:flex">
      <div className="h-px w-10 bg-slate-300 dark:bg-slate-700" />
      <span className="px-1 text-xs text-slate-400">→</span>
    </div>
  );
}

// ============================================================
// Risk cell
// ============================================================

function RiskCell({
  label,
  range,
  count,
  total,
}: {
  label: string;
  range: string;
  count: number;
  total: number;
}) {
  const percentage = total > 0 ? (count / total) * 100 : 0;

  return (
    <div className="px-5 py-4">
      <div className="flex items-baseline justify-between gap-3">
        <div>
          <p className="text-xs font-semibold">{label}</p>

          <p className="mt-1 text-[10px] text-slate-400">{range}</p>
        </div>

        <p className="text-lg font-semibold">{count.toLocaleString()}</p>
      </div>

      <div className="mt-3 h-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
        <div
          className="h-full rounded-full bg-slate-400 dark:bg-slate-500"
          style={{
            width: `${Math.min(100, percentage)}%`,
          }}
        />
      </div>

      <p className="mt-1.5 text-[10px] text-slate-400">
        {percentage.toFixed(1)}%
      </p>
    </div>
  );
}

// ============================================================
// Filter
// ============================================================

function FilterSelect({
  label,
  value,
  options,
  allLabel,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  allLabel: string;
  onChange: (value: string) => void;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-slate-500">
        {label}
      </label>

      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-lg border border-slate-200 bg-white px-3.5 py-2.5 text-sm outline-none focus:border-slate-400 dark:border-slate-700 dark:bg-[#020618] dark:text-slate-100"
      >
        <option value="ALL">{allLabel}</option>

        {options.map((option) => (
          <option key={option} value={option}>
            {label === "Future risk" ? riskLabel(option) : option}
          </option>
        ))}
      </select>
    </div>
  );
}

// ============================================================
// Loading
// ============================================================

function ForecastLoading() {
  return (
    <main className="min-h-screen bg-white px-5 py-7 dark:bg-[#020618] sm:px-7 lg:px-8">
      <div className="mx-auto max-w-[1450px]">
        <div className="h-3 w-52 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />

        <div className="mt-3 h-10 w-48 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />

        <div className="mt-3 h-4 w-[550px] max-w-full animate-pulse rounded bg-slate-200 dark:bg-slate-800" />

        <div className="mt-8 h-32 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-900" />

        <div className="mt-7 h-28 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-900" />

        <div className="mt-7 h-16 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-900" />

        <div className="mt-7 h-[500px] animate-pulse rounded-xl bg-slate-100 dark:bg-slate-900" />
      </div>
    </main>
  );
}
