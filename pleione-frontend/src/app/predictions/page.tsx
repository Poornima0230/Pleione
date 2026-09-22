"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import ForecastTrajectory from "@/components/predictions/ForecastTrajectory";

const API_URL = "http://127.0.0.1:8000";

type Prediction = {
  component_id: string;
  lot_id?: string;
  component_type?: string;

  iddq_0h_uA?: number;
  iddq_24h_uA?: number;
  early_iddq_change_uA?: number;
  drift_0_24_uA_per_h?: number;

  anomaly_score?: number;
  current_anomaly_level?: string;

  predicted_168h_uA?: number;
  prediction_lower_uA?: number;
  prediction_upper_uA?: number;

  absolute_limit_uA?: number;

  predicted_limit_margin_uA?: number;
  upper_limit_margin_uA?: number;

  predicted_limit_utilization_percent?: number;
  upper_limit_utilization_percent?: number;

  prediction_interval_width_uA?: number;

  predicted_drift_rate?: number;
  safety_slope?: number;
  drift_slope_excess?: number;

  future_drift_risk?: string;
  risk_score?: number;
  final_risk_level?: string;
  final_decision?: string;

  primary_risk_driver?: string;
  evidence_summary?: string;

  screening_category?: string;
  screening_recommendation?: string;
  detailed_explanation?: string;
};

type ApiResponse = {
  data?: Prediction[];
  predictions?: Prediction[];
  total?: number;
  page?: number;
  limit?: number;
};

function numberValue(value?: number) {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return 0;
  }

  return Number(value);
}

function formatNumber(value?: number, digits = 2) {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "—";
  }

  return value.toFixed(digits);
}

function riskRank(value?: string) {
  const risk = String(value || "").toUpperCase();

  if (risk.includes("CRITICAL")) return 4;
  if (risk.includes("HIGH")) return 3;
  if (risk.includes("MEDIUM")) return 2;
  if (risk.includes("WATCH")) return 1;

  return 0;
}

function riskLabel(value?: string) {
  if (!value) return "NORMAL";

  return value.replaceAll("_", " ").toUpperCase();
}

function riskClass(value?: string) {
  const risk = String(value || "").toUpperCase();

  if (risk.includes("CRITICAL")) {
    return "border-red-500/30 bg-red-500/10 text-red-300";
  }

  if (risk.includes("HIGH")) {
    return "border-orange-400/30 bg-orange-400/10 text-orange-300";
  }

  if (risk.includes("MEDIUM") || risk.includes("WATCH")) {
    return "border-amber-400/30 bg-amber-400/10 text-amber-300";
  }

  return "border-emerald-400/20 bg-emerald-400/10 text-emerald-300";
}

function decisionClass(value?: string) {
  const decision = String(value || "").toUpperCase();

  if (decision.includes("REJECT") || decision.includes("CRITICAL")) {
    return "text-red-300";
  }

  if (
    decision.includes("REVIEW") ||
    decision.includes("HOLD") ||
    decision.includes("MONITOR")
  ) {
    return "text-amber-300";
  }

  return "text-emerald-300";
}

function utilizationWidth(value?: number) {
  const numeric = numberValue(value);

  return Math.min(100, Math.max(0, numeric));
}

export default function PredictionsPage() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [search, setSearch] = useState("");

  const [riskFilter, setRiskFilter] = useState("ALL");

  const [lotFilter, setLotFilter] = useState("ALL");

  const [sortBy, setSortBy] = useState("risk");

  const [selected, setSelected] = useState<Prediction | null>(null);

  useEffect(() => {
    async function loadPredictions() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          `${API_URL}/api/predictions/?page=1&limit=500`,
          {
            cache: "no-store",
          },
        );

        if (!response.ok) {
          throw new Error("Prediction API request failed");
        }

        const json: ApiResponse = await response.json();

        const rows = json.data || json.predictions || [];

        setPredictions(rows);
      } catch (err) {
        console.error(err);

        setError("Unable to load Module B prediction data.");
      } finally {
        setLoading(false);
      }
    }

    loadPredictions();
  }, []);

  const lots = useMemo(() => {
    return Array.from(
      new Set(predictions.map((item) => item.lot_id).filter(Boolean)),
    ).sort();
  }, [predictions]);

  const filteredPredictions = useMemo(() => {
    const query = search.trim().toLowerCase();

    const rows = predictions.filter((item) => {
      const matchesSearch =
        !query ||
        String(item.component_id || "")
          .toLowerCase()
          .includes(query) ||
        String(item.lot_id || "")
          .toLowerCase()
          .includes(query) ||
        String(item.primary_risk_driver || "")
          .toLowerCase()
          .includes(query);

      const matchesRisk =
        riskFilter === "ALL" ||
        String(item.final_risk_level || "").toUpperCase() === riskFilter;

      const matchesLot = lotFilter === "ALL" || item.lot_id === lotFilter;

      return matchesSearch && matchesRisk && matchesLot;
    });

    return [...rows].sort((a, b) => {
      if (sortBy === "predicted") {
        return (
          numberValue(b.predicted_limit_utilization_percent) -
          numberValue(a.predicted_limit_utilization_percent)
        );
      }

      if (sortBy === "margin") {
        return (
          numberValue(a.predicted_limit_margin_uA) -
          numberValue(b.predicted_limit_margin_uA)
        );
      }

      return (
        riskRank(b.final_risk_level) - riskRank(a.final_risk_level) ||
        numberValue(b.risk_score) - numberValue(a.risk_score)
      );
    });
  }, [predictions, search, riskFilter, lotFilter, sortBy]);

  const statistics = useMemo(() => {
    const total = predictions.length;

    const critical = predictions.filter(
      (item) =>
        String(item.final_risk_level || "").toUpperCase() === "CRITICAL",
    ).length;

    const high = predictions.filter(
      (item) => String(item.final_risk_level || "").toUpperCase() === "HIGH",
    ).length;

    const medium = predictions.filter(
      (item) => String(item.final_risk_level || "").toUpperCase() === "MEDIUM",
    ).length;

    const watch = predictions.filter(
      (item) => String(item.final_risk_level || "").toUpperCase() === "WATCH",
    ).length;

    const overLimit = predictions.filter(
      (item) => numberValue(item.predicted_limit_utilization_percent) >= 100,
    ).length;

    const averageRisk =
      total === 0
        ? 0
        : predictions.reduce(
            (sum, item) => sum + numberValue(item.risk_score),
            0,
          ) / total;

    const averageUtilization =
      total === 0
        ? 0
        : predictions.reduce(
            (sum, item) =>
              sum + numberValue(item.predicted_limit_utilization_percent),
            0,
          ) / total;

    return {
      total,
      critical,
      high,
      medium,
      watch,
      overLimit,
      averageRisk,
      averageUtilization,
    };
  }, [predictions]);

  const riskDistribution = useMemo(() => {
    return [
      {
        label: "CRITICAL",
        count: statistics.critical,
      },
      {
        label: "HIGH",
        count: statistics.high,
      },
      {
        label: "MEDIUM",
        count: statistics.medium,
      },
      {
        label: "WATCH",
        count: statistics.watch,
      },
    ];
  }, [statistics]);

  const driverDistribution = useMemo(() => {
    const counts: Record<string, number> = {};

    predictions.forEach((item) => {
      const driver = item.primary_risk_driver || "Unclassified";

      counts[driver] = (counts[driver] || 0) + 1;
    });

    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6);
  }, [predictions]);

  return (
    <div className="min-h-screen bg-[#f4f4f1] text-[#111]">
      <div className="mx-auto max-w-[1600px] px-8 py-8">
        {/* HEADER */}

        <div className="mb-8 flex items-end justify-between border-b border-black/10 pb-6">
          <div>
            <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-black/40">
              Module B · Predictive Reliability
            </div>

            <h1 className="text-3xl font-semibold tracking-tight">
              Failure Forecast
            </h1>

            <p className="mt-2 max-w-2xl text-sm text-black/50">
              Forecasting future Iddq behavior from early burn-in measurements
              and drift characteristics.
            </p>
          </div>

          <div className="text-right">
            <div className="text-[10px] uppercase tracking-[0.2em] text-black/35">
              Prediction Horizon
            </div>

            <div className="mt-1 text-lg font-medium">168H</div>
          </div>
        </div>

        {/* ERROR */}

        {error && (
          <div className="mb-6 border border-red-500/20 bg-red-500/5 px-5 py-4 text-sm text-red-700">
            <div className="font-medium">Forecast service unavailable</div>

            <div className="mt-1 text-red-700/70">{error}</div>

            <div className="mt-3 font-mono text-xs">
              Expected: /api/predictions/
            </div>
          </div>
        )}

        {/* KPI STRIP */}

        <section className="mb-8 grid grid-cols-2 border-y border-black/10 lg:grid-cols-6">
          <Metric
            label="Components Forecast"
            value={loading ? "—" : statistics.total}
          />

          <Metric
            label="Critical"
            value={loading ? "—" : statistics.critical}
            warning
          />

          <Metric
            label="High Risk"
            value={loading ? "—" : statistics.high}
            warning
          />

          <Metric
            label="Predicted Over Limit"
            value={loading ? "—" : statistics.overLimit}
            warning
          />

          <Metric
            label="Average Risk"
            value={loading ? "—" : formatNumber(statistics.averageRisk, 1)}
          />

          <Metric
            label="Avg Limit Util."
            value={
              loading
                ? "—"
                : `${formatNumber(statistics.averageUtilization, 1)}%`
            }
          />
        </section>

        {/* FORECAST MODEL VIEW */}

        <section className="mb-8 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <div className="border border-black/10 bg-white/40 p-6">
            <div className="mb-6 flex items-start justify-between">
              <div>
                <div className="text-[10px] uppercase tracking-[0.2em] text-black/35">
                  Forecast Logic
                </div>

                <h2 className="mt-1 text-lg font-medium">
                  Early Signal → Future State
                </h2>
              </div>

              <div className="font-mono text-[10px] uppercase text-black/35">
                Module B
              </div>
            </div>

            <div className="grid grid-cols-4 gap-2">
              <ForecastStep number="01" title="OBSERVE" text="0H / 24H" />

              <ForecastStep number="02" title="MEASURE" text="Early change" />

              <ForecastStep number="03" title="PROJECT" text="168H Iddq" />

              <ForecastStep
                number="04"
                title="ASSESS"
                text="Future risk"
                last
              />
            </div>

            <div className="mt-6 border-t border-black/10 pt-5 text-xs leading-5 text-black/50">
              The forecast does not replace the screening limit. It provides an
              early indication of whether the component is moving toward an
              unsafe future state.
            </div>
          </div>

          {/* RISK DISTRIBUTION */}

          <div className="border border-black/10 bg-[#111313] p-6 text-white">
            <div className="text-[10px] uppercase tracking-[0.2em] text-white/35">
              Forecast Population
            </div>

            <h2 className="mt-1 text-lg font-medium">Risk Distribution</h2>

            <div className="mt-6 space-y-4">
              {riskDistribution.map((item) => {
                const percentage =
                  statistics.total === 0
                    ? 0
                    : (item.count / statistics.total) * 100;

                return (
                  <div key={item.label}>
                    <div className="mb-2 flex justify-between text-xs">
                      <span className="text-white/60">{item.label}</span>

                      <span className="font-mono text-white/80">
                        {item.count}
                      </span>
                    </div>

                    <div className="h-1 bg-white/10">
                      <div
                        className="h-full bg-amber-400 transition-all"
                        style={{
                          width: `${percentage}%`,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* FILTER BAR */}

        <section className="mb-6 border-y border-black/10 py-4">
          <div className="flex flex-col gap-3 lg:flex-row">
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search component, lot or risk driver..."
              className="h-10 flex-1 border border-black/10 bg-white/50 px-3 text-sm outline-none placeholder:text-black/30 focus:border-black/30"
            />

            <select
              value={riskFilter}
              onChange={(event) => setRiskFilter(event.target.value)}
              className="h-10 border border-black/10 bg-white/50 px-3 text-sm outline-none"
            >
              <option value="ALL">All risk levels</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="WATCH">Watch</option>
            </select>

            <select
              value={lotFilter}
              onChange={(event) => setLotFilter(event.target.value)}
              className="h-10 border border-black/10 bg-white/50 px-3 text-sm outline-none"
            >
              <option value="ALL">All lots</option>

              {lots.map((lot) => (
                <option key={lot} value={lot}>
                  {lot}
                </option>
              ))}
            </select>

            <select
              value={sortBy}
              onChange={(event) => setSortBy(event.target.value)}
              className="h-10 border border-black/10 bg-white/50 px-3 text-sm outline-none"
            >
              <option value="risk">Sort: Risk</option>

              <option value="predicted">Sort: Limit utilization</option>

              <option value="margin">Sort: Lowest margin</option>
            </select>
          </div>
        </section>

        {/* MAIN FORECAST TABLE */}

        <section className="border border-black/10 bg-white/30">
          <div className="flex items-center justify-between border-b border-black/10 px-5 py-4">
            <div>
              <div className="text-[10px] uppercase tracking-[0.2em] text-black/35">
                Component Forecast Register
              </div>

              <div className="mt-1 text-sm font-medium">
                {filteredPredictions.length} components
              </div>
            </div>

            <div className="font-mono text-[10px] text-black/35">
              PREDICTIVE SCREENING
            </div>
          </div>

          {loading ? (
            <div className="px-6 py-16 text-center text-sm text-black/40">
              Loading Module B predictions...
            </div>
          ) : filteredPredictions.length === 0 ? (
            <div className="px-6 py-16 text-center text-sm text-black/40">
              No prediction records match the current filters.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[1200px] border-collapse text-sm">
                <thead>
                  <tr className="border-b border-black/10 text-left text-[10px] uppercase tracking-[0.15em] text-black/35">
                    <th className="px-5 py-4">Component</th>

                    <th className="px-4 py-4">Lot</th>

                    <th className="px-4 py-4">Current</th>

                    <th className="px-4 py-4">Predicted 168H</th>

                    <th className="px-4 py-4">Forecast Range</th>

                    <th className="px-4 py-4">Limit Util.</th>

                    <th className="px-4 py-4">Future Risk</th>

                    <th className="px-4 py-4">Driver</th>

                    <th className="px-4 py-4">Decision</th>

                    <th className="px-5 py-4" />
                  </tr>
                </thead>

                <tbody>
                  {filteredPredictions.map((item) => {
                    const utilization = numberValue(
                      item.predicted_limit_utilization_percent,
                    );

                    return (
                      <tr
                        key={item.component_id}
                        className="border-b border-black/5 transition hover:bg-black/[0.025]"
                      >
                        <td className="px-5 py-4">
                          <Link
                            href={`/components/${item.component_id}`}
                            className="font-mono text-xs font-medium hover:underline"
                          >
                            {item.component_id}
                          </Link>

                          <div className="mt-1 text-[10px] uppercase tracking-wider text-black/35">
                            {item.component_type || "Component"}
                          </div>
                        </td>

                        <td className="px-4 py-4 font-mono text-xs text-black/60">
                          {item.lot_id || "—"}
                        </td>

                        <td className="px-4 py-4">
                          <div className="font-mono text-xs">
                            {formatNumber(item.iddq_24h_uA)} µA
                          </div>

                          <div className="mt-1 text-[10px] text-black/35">
                            24H
                          </div>
                        </td>

                        <td className="px-4 py-4">
                          <div className="font-mono text-xs font-medium">
                            {formatNumber(item.predicted_168h_uA)} µA
                          </div>

                          <div className="mt-1 text-[10px] text-black/35">
                            predicted
                          </div>
                        </td>

                        <td className="px-4 py-4">
                          <div className="font-mono text-[11px] text-black/60">
                            {formatNumber(item.prediction_lower_uA)}
                            {" — "}
                            {formatNumber(item.prediction_upper_uA)}
                            {" µA"}
                          </div>

                          <div className="mt-1 text-[10px] text-black/35">
                            {item.prediction_interval_width_uA !== undefined
                              ? `± ${formatNumber(
                                  item.prediction_interval_width_uA / 2,
                                )}`
                              : "prediction interval"}
                          </div>
                        </td>

                        <td className="px-4 py-4">
                          <div className="w-32">
                            <div className="mb-1 flex justify-between text-[10px]">
                              <span className="font-mono">
                                {formatNumber(utilization, 1)}%
                              </span>

                              <span className="text-black/30">100</span>
                            </div>

                            <div className="h-1.5 bg-black/10">
                              <div
                                className={`h-full ${
                                  utilization >= 100
                                    ? "bg-red-500"
                                    : utilization >= 80
                                      ? "bg-amber-400"
                                      : "bg-emerald-500"
                                }`}
                                style={{
                                  width: `${utilizationWidth(utilization)}%`,
                                }}
                              />
                            </div>
                          </div>
                        </td>

                        <td className="px-4 py-4">
                          <span
                            className={`inline-flex border px-2 py-1 text-[10px] uppercase tracking-wider ${riskClass(
                              item.final_risk_level,
                            )}`}
                          >
                            {riskLabel(item.final_risk_level)}
                          </span>

                          <div className="mt-2 font-mono text-[10px] text-black/40">
                            score {formatNumber(item.risk_score, 2)}
                          </div>
                        </td>

                        <td className="max-w-[190px] px-4 py-4">
                          <div className="truncate text-xs text-black/70">
                            {item.primary_risk_driver || "—"}
                          </div>
                        </td>

                        <td className="px-4 py-4">
                          <span
                            className={`text-xs font-medium ${decisionClass(
                              item.final_decision,
                            )}`}
                          >
                            {item.final_decision || "—"}
                          </span>
                        </td>

                        <td className="px-5 py-4 text-right">
                          <button
                            onClick={() => setSelected(item)}
                            className="border border-black/10 px-3 py-2 text-[10px] uppercase tracking-wider text-black/50 transition hover:border-black/30 hover:text-black"
                          >
                            Inspect
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* LOWER ANALYTICS */}

        <section className="mt-8 grid gap-6 lg:grid-cols-2">
          <div className="border border-black/10 bg-white/30 p-6">
            <div className="text-[10px] uppercase tracking-[0.2em] text-black/35">
              Primary Risk Drivers
            </div>

            <h2 className="mt-1 text-lg font-medium">
              Why components are forecast risky
            </h2>

            <div className="mt-6 space-y-4">
              {driverDistribution.length === 0 ? (
                <div className="text-sm text-black/40">
                  No driver data available.
                </div>
              ) : (
                driverDistribution.map(([driver, count]) => {
                  const width =
                    statistics.total === 0
                      ? 0
                      : (count / statistics.total) * 100;

                  return (
                    <div key={driver}>
                      <div className="mb-2 flex justify-between gap-4">
                        <span className="truncate text-xs text-black/60">
                          {driver}
                        </span>

                        <span className="font-mono text-xs text-black/40">
                          {count}
                        </span>
                      </div>

                      <div className="h-1 bg-black/10">
                        <div
                          className="h-full bg-black"
                          style={{
                            width: `${width}%`,
                          }}
                        />
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          <div className="border border-black/10 bg-white/30 p-6">
            <div className="text-[10px] uppercase tracking-[0.2em] text-black/35">
              Engineering Interpretation
            </div>

            <h2 className="mt-1 text-lg font-medium">
              How to read the forecast
            </h2>

            <div className="mt-6 space-y-5">
              <Interpretation
                number="01"
                title="Predicted value"
                text="Estimated Iddq at the 168-hour endpoint based on the early burn-in trajectory."
              />

              <Interpretation
                number="02"
                title="Prediction interval"
                text="Represents the uncertainty around the projected endpoint rather than a guaranteed future measurement."
              />

              <Interpretation
                number="03"
                title="Limit utilization"
                text="Shows how much of the absolute screening limit the predicted endpoint consumes."
              />

              <Interpretation
                number="04"
                title="Future risk"
                text="Combines the projected behavior with drift and safety indicators to prioritize engineering review."
              />
            </div>
          </div>
        </section>

        {/* FOOTER */}

        <div className="mt-10 flex items-center justify-between border-t border-black/10 pt-5 text-[10px] uppercase tracking-[0.2em] text-black/30">
          <span>Pleione Reliability Intelligence</span>

          <span>Observe → Detect → Predict → Decide</span>
        </div>
      </div>

      {/* INSPECTION DRAWER */}

      {selected && (
        <div className="fixed inset-0 z-[100]">
          <button
            aria-label="Close inspection"
            onClick={() => setSelected(null)}
            className="absolute inset-0 bg-black/40"
          />

          <aside className="absolute right-0 top-0 h-full w-full max-w-xl overflow-y-auto bg-[#111313] p-7 text-white shadow-2xl">
            <div className="flex items-start justify-between border-b border-white/10 pb-5">
              <div>
                <div className="text-[10px] uppercase tracking-[0.2em] text-white/35">
                  Forecast Investigation
                </div>

                <h2 className="mt-2 font-mono text-xl">
                  {selected.component_id}
                </h2>

                <div className="mt-1 text-xs text-white/40">
                  Lot {selected.lot_id || "—"}
                </div>
              </div>

              <button
                onClick={() => setSelected(null)}
                className="text-xs text-white/40 hover:text-white"
              >
                CLOSE ×
              </button>
            </div>

            <div className="mt-7">
              <div className="flex items-end justify-between">
                <div>
                  <div className="text-[10px] uppercase tracking-[0.2em] text-white/35">
                    Future Risk
                  </div>

                  <div className="mt-2 text-3xl font-semibold">
                    {riskLabel(selected.final_risk_level)}
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-[10px] uppercase tracking-wider text-white/35">
                    Risk Score
                  </div>

                  <div className="mt-1 font-mono text-xl">
                    {formatNumber(selected.risk_score, 2)}
                  </div>
                </div>
              </div>

              <div className="mt-6 grid grid-cols-2 border-y border-white/10">
                <DarkMetric
                  label="24H Iddq"
                  value={`${formatNumber(selected.iddq_24h_uA)} µA`}
                />

                <DarkMetric
                  label="Predicted 168H"
                  value={`${formatNumber(selected.predicted_168h_uA)} µA`}
                />

                <DarkMetric
                  label="Absolute Limit"
                  value={`${formatNumber(selected.absolute_limit_uA)} µA`}
                />

                <DarkMetric
                  label="Limit Utilization"
                  value={`${formatNumber(
                    selected.predicted_limit_utilization_percent,
                    1,
                  )}%`}
                />
              </div>

              {/* FORECAST TRAJECTORY */}

              <div className="mt-7 border-t border-white/10 pt-6">
                <ForecastTrajectory
                  iddq0={selected.iddq_0h_uA}
                  iddq24={selected.iddq_24h_uA}
                  predicted168={selected.predicted_168h_uA}
                  lower168={selected.prediction_lower_uA}
                  upper168={selected.prediction_upper_uA}
                  absoluteLimit={selected.absolute_limit_uA}
                />
              </div>

              {/* RANGE */}

              <div className="mt-7">
                <div className="mb-3 flex justify-between text-[10px] uppercase tracking-wider text-white/35">
                  <span>Prediction Range</span>

                  <span>µA</span>
                </div>

                <div className="relative h-8 border border-white/10">
                  <div className="absolute left-0 right-0 top-1/2 h-px bg-white/10" />

                  <div className="absolute left-[15%] right-[15%] top-1/2 h-1 -translate-y-1/2 bg-amber-400/50" />

                  <div className="absolute left-1/2 top-1/2 h-4 w-px -translate-y-1/2 bg-amber-400" />
                </div>

                <div className="mt-2 flex justify-between font-mono text-[10px] text-white/40">
                  <span>{formatNumber(selected.prediction_lower_uA)}</span>

                  <span>{formatNumber(selected.predicted_168h_uA)}</span>

                  <span>{formatNumber(selected.prediction_upper_uA)}</span>
                </div>
              </div>

              {/* DRIFT */}

              <div className="mt-7 border-t border-white/10 pt-6">
                <div className="text-[10px] uppercase tracking-[0.2em] text-white/35">
                  Drift Assessment
                </div>

                <div className="mt-4 grid grid-cols-2 gap-px border border-white/10 bg-white/10">
                  <DarkMetric
                    label="Predicted Drift"
                    value={formatNumber(selected.predicted_drift_rate)}
                  />

                  <DarkMetric
                    label="Safety Slope"
                    value={formatNumber(selected.safety_slope)}
                  />

                  <DarkMetric
                    label="Slope Excess"
                    value={formatNumber(selected.drift_slope_excess)}
                  />

                  <DarkMetric
                    label="Early Change"
                    value={`${formatNumber(selected.early_iddq_change_uA)} µA`}
                  />
                </div>
              </div>

              {/* DRIVER */}

              <div className="mt-7 border-t border-white/10 pt-6">
                <div className="text-[10px] uppercase tracking-[0.2em] text-white/35">
                  Primary Risk Driver
                </div>

                <div className="mt-2 text-sm text-white/80">
                  {selected.primary_risk_driver || "No driver recorded"}
                </div>
              </div>

              {/* EVIDENCE */}

              <div className="mt-7 border-t border-white/10 pt-6">
                <div className="text-[10px] uppercase tracking-[0.2em] text-white/35">
                  Evidence
                </div>

                <p className="mt-3 text-sm leading-6 text-white/55">
                  {selected.evidence_summary ||
                    "No evidence summary available."}
                </p>
              </div>

              {/* EXPLANATION */}

              <div className="mt-7 border-t border-white/10 pt-6">
                <div className="text-[10px] uppercase tracking-[0.2em] text-white/35">
                  Model Explanation
                </div>

                <p className="mt-3 text-sm leading-6 text-white/55">
                  {selected.detailed_explanation ||
                    "No detailed explanation available."}
                </p>
              </div>

              {/* DECISION */}

              <div className="mt-7 border-t border-white/10 pt-6">
                <div className="text-[10px] uppercase tracking-[0.2em] text-white/35">
                  Recommended Action
                </div>

                <div className="mt-3 flex items-center justify-between">
                  <span className="text-sm text-white/60">
                    {selected.final_decision ||
                      selected.screening_recommendation ||
                      "No decision"}
                  </span>

                  <Link
                    href={`/components/${selected.component_id}`}
                    className="border border-white/15 px-4 py-2 text-[10px] uppercase tracking-wider text-white/60 hover:border-white/30 hover:text-white"
                  >
                    Open Investigation
                  </Link>
                </div>
              </div>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}

/* ============================================================
   SMALL COMPONENTS
   ============================================================ */

function Metric({
  label,
  value,
  warning = false,
}: {
  label: string;
  value: string | number;
  warning?: boolean;
}) {
  return (
    <div className="border-r border-black/10 px-5 py-5 last:border-r-0">
      <div className="text-[10px] uppercase tracking-[0.16em] text-black/35">
        {label}
      </div>

      <div
        className={`mt-2 font-mono text-xl ${
          warning ? "text-amber-700" : "text-black"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function ForecastStep({
  number,
  title,
  text,
  last = false,
}: {
  number: string;
  title: string;
  text: string;
  last?: boolean;
}) {
  return (
    <div
      className={`relative border border-black/10 bg-[#f4f4f1] p-4 ${
        !last
          ? "after:absolute after:-right-2 after:top-1/2 after:z-10 after:h-px after:w-4 after:bg-black/20"
          : ""
      }`}
    >
      <div className="font-mono text-[10px] text-black/30">{number}</div>

      <div className="mt-4 text-[10px] font-medium tracking-[0.16em]">
        {title}
      </div>

      <div className="mt-2 text-xs text-black/45">{text}</div>
    </div>
  );
}

function Interpretation({
  number,
  title,
  text,
}: {
  number: string;
  title: string;
  text: string;
}) {
  return (
    <div className="flex gap-4">
      <div className="font-mono text-[10px] text-black/25">{number}</div>

      <div>
        <div className="text-xs font-medium">{title}</div>

        <p className="mt-1 text-xs leading-5 text-black/45">{text}</p>
      </div>
    </div>
  );
}

function DarkMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-r border-b border-white/10 bg-white/[0.02] px-4 py-4 last:border-r-0">
      <div className="text-[9px] uppercase tracking-[0.15em] text-white/30">
        {label}
      </div>

      <div className="mt-2 font-mono text-sm text-white/80">{value}</div>
    </div>
  );
}
