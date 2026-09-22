"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  Boxes,
  Search,
  ShieldAlert,
  TriangleAlert,
} from "lucide-react";

import PageHeader from "@/components/layout/PageHeader";
import { getLots, type Lot } from "@/lib/api";

function formatNumber(value: number | undefined | null, digits = 1) {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "—";
  }

  return value.toFixed(digits);
}

function getRiskLevel(score: number) {
  if (score >= 75) return "CRITICAL";
  if (score >= 50) return "HIGH";
  if (score >= 25) return "MEDIUM";
  return "LOW";
}

function getRiskClass(level: string) {
  switch (level) {
    case "CRITICAL":
      return "text-red-600 dark:text-red-400";

    case "HIGH":
      return "text-orange-600 dark:text-orange-400";

    case "MEDIUM":
      return "text-amber-600 dark:text-amber-400";

    default:
      return "text-slate-600 dark:text-slate-300";
  }
}

export default function LotsPage() {
  const [lots, setLots] = useState<Lot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");

  // ==========================================================
  // LOAD LOTS
  // ==========================================================

  useEffect(() => {
    let cancelled = false;

    async function loadLots() {
      try {
        setLoading(true);
        setError("");

        const result = await getLots();

        if (!cancelled) {
          setLots(result);
        }
      } catch (err) {
        console.error("Lots loading error:", err);

        if (!cancelled) {
          setError(
            "Unable to load lot information from the screening backend.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadLots();

    return () => {
      cancelled = true;
    };
  }, []);

  // ==========================================================
  // SEARCH
  // ==========================================================

  const filteredLots = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) {
      return lots;
    }

    return lots.filter((lot) =>
      String(lot.lot_id).toLowerCase().includes(query),
    );
  }, [lots, search]);

  // ==========================================================
  // OVERALL METRICS
  // ==========================================================

  const totalLots = lots.length;

  const totalComponents = lots.reduce(
    (sum, lot) => sum + Number(lot.component_count || 0),
    0,
  );

  const totalAnomalies = lots.reduce(
    (sum, lot) => sum + Number(lot.anomaly_count || 0),
    0,
  );

  const criticalLots = lots.filter(
    (lot) => Number(lot.critical_count || 0) > 0,
  ).length;

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <div className="mx-auto w-full max-w-[1500px]">
      <PageHeader
        eyebrow="Production Groups"
        title="Lots"
        description="Review screening behavior across production lots and identify groups requiring investigation."
      />

      {/* =====================================================
          SUMMARY
      ===================================================== */}

      <section className="mb-7 grid grid-cols-1 gap-px overflow-hidden border border-slate-200 bg-slate-200 dark:border-slate-800 dark:bg-slate-800 sm:grid-cols-2 xl:grid-cols-4">
        {/* Lots */}

        <div className="bg-white px-5 py-5 dark:bg-slate-950">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-500">
                Lots
              </p>

              <p className="mt-2 text-2xl font-semibold tabular-nums text-slate-950 dark:text-white">
                {loading ? "—" : totalLots.toLocaleString()}
              </p>

              <p className="mt-1 text-xs text-slate-500">Production groups</p>
            </div>

            <Boxes className="h-5 w-5 text-slate-400" />
          </div>
        </div>

        {/* Components */}

        <div className="bg-white px-5 py-5 dark:bg-slate-950">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-500">
                Components
              </p>

              <p className="mt-2 text-2xl font-semibold tabular-nums text-slate-950 dark:text-white">
                {loading ? "—" : totalComponents.toLocaleString()}
              </p>

              <p className="mt-1 text-xs text-slate-500">Across all lots</p>
            </div>

            <Boxes className="h-5 w-5 text-slate-400" />
          </div>
        </div>

        {/* Anomalies */}

        <div className="bg-white px-5 py-5 dark:bg-slate-950">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-500">
                Anomalies
              </p>

              <p className="mt-2 text-2xl font-semibold tabular-nums text-slate-950 dark:text-white">
                {loading ? "—" : totalAnomalies.toLocaleString()}
              </p>

              <p className="mt-1 text-xs text-slate-500">
                Detected across lots
              </p>
            </div>

            <TriangleAlert className="h-5 w-5 text-amber-500" />
          </div>
        </div>

        {/* Critical lots */}

        <div className="bg-white px-5 py-5 dark:bg-slate-950">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-slate-500">
                Attention lots
              </p>

              <p className="mt-2 text-2xl font-semibold tabular-nums text-slate-950 dark:text-white">
                {loading ? "—" : criticalLots.toLocaleString()}
              </p>

              <p className="mt-1 text-xs text-slate-500">
                Lots with critical findings
              </p>
            </div>

            <ShieldAlert className="h-5 w-5 text-red-500" />
          </div>
        </div>
      </section>

      {/* =====================================================
          SEARCH BAR
      ===================================================== */}

      <section className="mb-5 flex flex-col gap-3 border-y border-slate-200 py-4 dark:border-slate-800 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full sm:max-w-sm">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />

          <input
            type="text"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search lot ID..."
            className="h-10 w-full border border-slate-200 bg-white pl-9 pr-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 dark:border-slate-800 dark:bg-slate-950 dark:text-white dark:focus:border-slate-600"
          />
        </div>

        <div className="text-xs text-slate-500">
          {filteredLots.length.toLocaleString()} of {totalLots.toLocaleString()}{" "}
          lots
        </div>
      </section>

      {/* =====================================================
          ERROR
      ===================================================== */}

      {error && (
        <div className="mb-5 border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300">
          <div className="flex items-center gap-2">
            <TriangleAlert className="h-4 w-4 shrink-0" />

            <span>{error}</span>
          </div>
        </div>
      )}

      {/* =====================================================
          TABLE
      ===================================================== */}

      <section className="overflow-hidden border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
        {/* Table heading */}

        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-800">
          <div>
            <h2 className="text-sm font-semibold text-slate-950 dark:text-white">
              Lot overview
            </h2>

            <p className="mt-1 text-xs text-slate-500">
              Reliability indicators from the screening results.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[950px] text-left">
            {/* Header */}

            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/50">
                <th className="px-5 py-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                  Lot
                </th>

                <th className="px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                  Components
                </th>

                <th className="px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                  Anomalies
                </th>

                <th className="px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                  Anomaly rate
                </th>

                <th className="px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                  Average risk
                </th>

                <th className="px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                  Critical
                </th>

                <th className="px-5 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                  Inspect
                </th>
              </tr>
            </thead>

            {/* Body */}

            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {/* Loading */}

              {loading &&
                Array.from({ length: 6 }).map((_, index) => (
                  <tr key={index}>
                    <td colSpan={7} className="px-5 py-5">
                      <div className="h-5 animate-pulse bg-slate-100 dark:bg-slate-900" />
                    </td>
                  </tr>
                ))}

              {/* Empty */}

              {!loading && filteredLots.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-5 py-16 text-center">
                    <Boxes className="mx-auto h-6 w-6 text-slate-400" />

                    <p className="mt-3 text-sm font-medium text-slate-700 dark:text-slate-300">
                      No lots found
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      Try a different lot ID.
                    </p>
                  </td>
                </tr>
              )}

              {/* Data */}

              {!loading &&
                filteredLots.map((lot) => {
                  const riskScore = Number(lot.average_risk || 0);

                  const riskLevel = getRiskLevel(riskScore);

                  const anomalyRate = Math.min(
                    100,
                    Math.max(0, Number(lot.anomaly_rate || 0)),
                  );

                  return (
                    <tr
                      key={lot.lot_id}
                      className="transition-colors hover:bg-slate-50 dark:hover:bg-slate-900/50"
                    >
                      {/* Lot */}

                      <td className="px-5 py-4">
                        <div>
                          <p className="text-sm font-semibold text-slate-900 dark:text-white">
                            {lot.lot_id}
                          </p>

                          <p className="mt-1 text-[11px] text-slate-500">
                            Production lot
                          </p>
                        </div>
                      </td>

                      {/* Components */}

                      <td className="px-4 py-4">
                        <span className="text-sm tabular-nums text-slate-700 dark:text-slate-300">
                          {Number(lot.component_count || 0).toLocaleString()}
                        </span>
                      </td>

                      {/* Anomalies */}

                      <td className="px-4 py-4">
                        <span className="text-sm font-medium tabular-nums text-slate-900 dark:text-white">
                          {Number(lot.anomaly_count || 0).toLocaleString()}
                        </span>
                      </td>

                      {/* Anomaly rate */}

                      <td className="px-4 py-4">
                        <div className="flex items-center gap-3">
                          <div className="h-1.5 w-20 overflow-hidden bg-slate-100 dark:bg-slate-800">
                            <div
                              className="h-full bg-slate-500 dark:bg-slate-400"
                              style={{
                                width: `${anomalyRate}%`,
                              }}
                            />
                          </div>

                          <span className="text-sm tabular-nums text-slate-700 dark:text-slate-300">
                            {formatNumber(lot.anomaly_rate, 1)}%
                          </span>
                        </div>
                      </td>

                      {/* Average risk */}

                      <td className="px-4 py-4">
                        <div>
                          <p
                            className={`text-sm font-semibold tabular-nums ${getRiskClass(
                              riskLevel,
                            )}`}
                          >
                            {formatNumber(riskScore, 1)}
                          </p>

                          <p className="mt-1 text-[10px] font-medium uppercase tracking-[0.1em] text-slate-400">
                            {riskLevel}
                          </p>
                        </div>
                      </td>

                      {/* Critical */}

                      <td className="px-4 py-4">
                        <span
                          className={
                            Number(lot.critical_count || 0) > 0
                              ? "text-sm font-semibold tabular-nums text-red-600 dark:text-red-400"
                              : "text-sm tabular-nums text-slate-500"
                          }
                        >
                          {Number(lot.critical_count || 0).toLocaleString()}
                        </span>
                      </td>

                      {/* Inspect */}

                      <td className="px-5 py-4 text-right">
                        <Link
                          href={`/components?lot_id=${encodeURIComponent(
                            lot.lot_id,
                          )}`}
                          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 transition hover:text-slate-950 dark:text-slate-400 dark:hover:text-white"
                        >
                          View components
                          <ArrowRight className="h-3.5 w-3.5" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>

        {/* Footer */}

        <div className="border-t border-slate-200 px-5 py-3 dark:border-slate-800">
          <p className="text-xs text-slate-500">
            Showing {filteredLots.length.toLocaleString()} of{" "}
            {totalLots.toLocaleString()} lots
          </p>
        </div>
      </section>

      {/* =====================================================
          INFORMATION NOTE
      ===================================================== */}

      <div className="mt-4 flex items-start gap-2 text-xs leading-5 text-slate-500">
        <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />

        <p>
          Lot indicators are calculated from the Module A screening results. Use
          component inspection to investigate individual anomalies and screening
          decisions.
        </p>
      </div>
    </div>
  );
}
