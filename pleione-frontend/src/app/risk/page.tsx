"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { getRiskAssessment } from "@/lib/api";

type RiskRecord = {
  component_id?: string;
  lot_id?: string;
  component_type?: string;

  temperature_C?: number;
  voltage_V?: number;

  iddq_0h_uA?: number;
  iddq_24h_uA?: number;
  absolute_limit_uA?: number;

  drift_0_24_uA_per_h?: number;

  zscore_0h?: number;
  robust_zscore_0h?: number;

  zscore_24h?: number;
  robust_zscore_24h?: number;

  z_anomaly_0h?: boolean;
  robust_z_anomaly_0h?: boolean;
  iqr_anomaly_0h?: boolean;

  z_anomaly_24h?: boolean;
  robust_z_anomaly_24h?: boolean;
  iqr_anomaly_24h?: boolean;

  predicted_168h_uA?: number;
  prediction_lower_uA?: number;
  prediction_upper_uA?: number;

  predicted_drift_uA?: number;
  predicted_drift_rate?: number;

  safety_slope?: number;
  drift_slope_excess?: number;

  early_drift_flag?: boolean;
  predicted_limit_exceeded?: boolean;
  uncertainty_adjusted_failure?: boolean;

  limit_margin_uA?: number;
  upper_bound_limit_margin_uA?: number;

  future_drift_risk?: string;
  module_b_status?: string;
  module_b_explanation?: string;

  anomaly_evidence_count?: number;
  anomaly_score?: number;
  current_anomaly_level?: string;

  early_drift_direction?: string;

  future_drift_abnormal?: boolean;
  future_failure_predicted?: boolean;

  current_anomaly_contribution?: number;
  future_drift_contribution?: number;
  future_failure_contribution?: number;

  risk_score?: number;

  drift_severity?: string;
  final_risk_level?: string;
  final_decision?: string;

  risk_explanation?: string;

  risk_priority?: number;
};

type RiskFilter = "ALL" | "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";

function numberValue(value?: number) {
  if (value === undefined || value === null || !Number.isFinite(value)) {
    return 0;
  }

  return value;
}

function formatNumber(value?: number, digits = 1) {
  if (value === undefined || value === null || !Number.isFinite(value)) {
    return "—";
  }

  return value.toFixed(digits);
}

function formatPercent(value?: number) {
  if (value === undefined || value === null || !Number.isFinite(value)) {
    return "—";
  }

  return `${value.toFixed(0)}%`;
}

function boolValue(value?: boolean) {
  return value === true;
}

function riskRank(level?: string) {
  const normalized = String(level ?? "").toUpperCase();

  if (normalized === "CRITICAL") {
    return 4;
  }

  if (normalized === "HIGH") {
    return 3;
  }

  if (normalized === "MEDIUM") {
    return 2;
  }

  if (normalized === "LOW") {
    return 1;
  }

  return 0;
}

function riskClass(level?: string) {
  const normalized = String(level ?? "").toUpperCase();

  if (normalized === "CRITICAL") {
    return "border-red-300/30 bg-red-500/10 text-red-200";
  }

  if (normalized === "HIGH") {
    return "border-orange-300/30 bg-orange-500/10 text-orange-200";
  }

  if (normalized === "MEDIUM") {
    return "border-amber-300/30 bg-amber-500/10 text-amber-200";
  }

  return "border-emerald-300/20 bg-emerald-500/10 text-emerald-200";
}

function decisionClass(decision?: string) {
  const value = String(decision ?? "").toUpperCase();

  if (value.includes("IMMEDIATE") || value.includes("REJECT")) {
    return "text-red-300";
  }

  if (value.includes("REVIEW") || value.includes("HOLD")) {
    return "text-amber-300";
  }

  return "text-emerald-300";
}

function displayRisk(level?: string) {
  if (!level) {
    return "UNKNOWN";
  }

  return String(level).replaceAll("_", " ").toUpperCase();
}

function explanationItems(item: RiskRecord) {
  const items: {
    label: string;
    value: string;
    active: boolean;
    tone: string;
  }[] = [];

  items.push({
    label: "CURRENT ANOMALY",
    value: item.current_anomaly_level
      ? displayRisk(item.current_anomaly_level)
      : "NOT DETECTED",
    active:
      Boolean(item.current_anomaly_level) &&
      String(item.current_anomaly_level).toUpperCase() !== "NORMAL",
    tone: "amber",
  });

  items.push({
    label: "EARLY DRIFT",
    value: boolValue(item.early_drift_flag)
      ? item.early_drift_direction
        ? displayRisk(item.early_drift_direction)
        : "DETECTED"
      : "NOT DETECTED",
    active: boolValue(item.early_drift_flag),
    tone: "orange",
  });

  items.push({
    label: "FUTURE DRIFT",
    value: item.future_drift_risk
      ? displayRisk(item.future_drift_risk)
      : "NORMAL",
    active: boolValue(item.future_drift_abnormal),
    tone: "orange",
  });

  items.push({
    label: "FUTURE FAILURE",
    value: boolValue(item.future_failure_predicted)
      ? "PREDICTED"
      : "NOT PREDICTED",
    active: boolValue(item.future_failure_predicted),
    tone: "red",
  });

  items.push({
    label: "LIMIT PROJECTION",
    value: boolValue(item.predicted_limit_exceeded)
      ? "EXCEEDS LIMIT"
      : "WITHIN LIMIT",
    active: boolValue(item.predicted_limit_exceeded),
    tone: "red",
  });

  return items;
}

export default function RiskPage() {
  const [records, setRecords] = useState<RiskRecord[]>([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [filter, setFilter] = useState<RiskFilter>("ALL");

  const [search, setSearch] = useState("");

  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        setError("");

        const response = await getRiskAssessment(1, 5000);

        const data = Array.isArray(response?.data) ? response.data : [];

        if (mounted) {
          setRecords(data);
        }
      } catch (err) {
        if (mounted) {
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load risk assessment",
          );
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      mounted = false;
    };
  }, []);

  const filteredRecords = useMemo(() => {
    const query = search.trim().toLowerCase();

    return records
      .filter((item) => {
        if (
          filter !== "ALL" &&
          String(item.final_risk_level ?? "").toUpperCase() !== filter
        ) {
          return false;
        }

        if (!query) {
          return true;
        }

        return (
          String(item.component_id ?? "")
            .toLowerCase()
            .includes(query) ||
          String(item.lot_id ?? "")
            .toLowerCase()
            .includes(query)
        );
      })
      .sort((a, b) => numberValue(b.risk_score) - numberValue(a.risk_score));
  }, [records, filter, search]);

  const selected = useMemo(() => {
    if (!selectedId) {
      return filteredRecords[0] ?? null;
    }

    return (
      records.find((item) => String(item.component_id) === selectedId) ?? null
    );
  }, [records, filteredRecords, selectedId]);

  const summary = useMemo(() => {
    const count = (level: RiskFilter) => {
      if (level === "ALL") {
        return records.length;
      }

      return records.filter(
        (item) => String(item.final_risk_level ?? "").toUpperCase() === level,
      ).length;
    };

    const earlyDrift = records.filter(
      (item) => item.early_drift_flag === true,
    ).length;

    const futureFailure = records.filter(
      (item) => item.future_failure_predicted === true,
    ).length;

    const limitExceeded = records.filter(
      (item) => item.predicted_limit_exceeded === true,
    ).length;

    const averageRisk = records.length
      ? records.reduce(
          (total, item) => total + numberValue(item.risk_score),
          0,
        ) / records.length
      : 0;

    return {
      total: records.length,

      critical: count("CRITICAL"),

      high: count("HIGH"),

      medium: count("MEDIUM"),

      low: count("LOW"),

      earlyDrift,

      futureFailure,

      limitExceeded,

      averageRisk,
    };
  }, [records]);

  const riskDistribution = useMemo(() => {
    const total = Math.max(summary.total, 1);

    return [
      {
        label: "CRITICAL",
        value: summary.critical,
        percentage: (summary.critical / total) * 100,
      },
      {
        label: "HIGH",
        value: summary.high,
        percentage: (summary.high / total) * 100,
      },
      {
        label: "MEDIUM",
        value: summary.medium,
        percentage: (summary.medium / total) * 100,
      },
      {
        label: "LOW",
        value: summary.low,
        percentage: (summary.low / total) * 100,
      },
    ];
  }, [summary]);

  const contribution = useMemo(() => {
    const current = records.reduce(
      (total, item) => total + numberValue(item.current_anomaly_contribution),
      0,
    );

    const futureDrift = records.reduce(
      (total, item) => total + numberValue(item.future_drift_contribution),
      0,
    );

    const futureFailure = records.reduce(
      (total, item) => total + numberValue(item.future_failure_contribution),
      0,
    );

    return {
      current,
      futureDrift,
      futureFailure,
    };
  }, [records]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#f4f4f1] p-8">
        <div className="flex min-h-[70vh] items-center justify-center">
          <div className="text-center">
            <div className="text-[10px] uppercase tracking-[0.3em] text-black/35">
              Pleione
            </div>

            <div className="mt-3 text-sm text-black/50">
              Loading risk assessment...
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#f4f4f1] p-8">
        <div className="border border-red-300/40 bg-red-50 p-6">
          <div className="text-[10px] uppercase tracking-[0.25em] text-red-500">
            Risk Engine Error
          </div>

          <div className="mt-2 text-sm text-red-800">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f4f4f1] text-[#111]">
      {/* =====================================================
          HEADER
      ====================================================== */}

      <section className="border-b border-black/10 px-8 py-8">
        <div className="flex flex-col justify-between gap-6 xl:flex-row xl:items-end">
          <div>
            <div className="text-[10px] uppercase tracking-[0.3em] text-black/35">
              Pleione / Reliability Intelligence
            </div>

            <h1 className="mt-3 text-3xl font-semibold tracking-tight">
              Risk Assessment
            </h1>

            <p className="mt-2 max-w-2xl text-sm text-black/50">
              Current anomaly evidence combined with early drift, future
              behavior and predicted failure risk.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="border border-black/10 bg-white px-4 py-3">
              <div className="text-[9px] uppercase tracking-[0.2em] text-black/35">
                Components
              </div>

              <div className="mt-1 text-xl font-semibold">
                {summary.total.toLocaleString()}
              </div>
            </div>

            <div className="border border-black/10 bg-white px-4 py-3">
              <div className="text-[9px] uppercase tracking-[0.2em] text-black/35">
                Avg risk
              </div>

              <div className="mt-1 text-xl font-semibold">
                {summary.averageRisk.toFixed(1)}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================
          TOP SIGNALS
      ====================================================== */}

      <section className="grid border-b border-black/10 xl:grid-cols-4">
        <SignalMetric
          label="Critical"
          value={summary.critical}
          detail="Highest intervention priority"
          tone="critical"
        />

        <SignalMetric
          label="High"
          value={summary.high}
          detail="Requires engineering review"
          tone="high"
        />

        <SignalMetric
          label="Early drift"
          value={summary.earlyDrift}
          detail="Abnormal behavior before failure"
          tone="warning"
        />

        <SignalMetric
          label="Predicted failure"
          value={summary.futureFailure}
          detail="Future failure signal detected"
          tone="critical"
        />
      </section>

      {/* =====================================================
          VISUAL ANALYTICS
      ====================================================== */}

      <section className="grid gap-px border-b border-black/10 bg-black/10 lg:grid-cols-2">
        <div className="bg-[#f4f4f1] p-8">
          <SectionLabel>Risk distribution</SectionLabel>

          <div className="mt-6 space-y-5">
            {riskDistribution.map((item) => (
              <RiskDistributionRow
                key={item.label}
                label={item.label}
                value={item.value}
                percentage={item.percentage}
              />
            ))}
          </div>

          <div className="mt-7 border-t border-black/10 pt-4 text-xs text-black/45">
            Distribution is based on
            <span className="font-medium text-black/70">
              {" "}
              final_risk_level
            </span>{" "}
            from the risk fusion output.
          </div>
        </div>

        <div className="bg-[#f4f4f1] p-8">
          <SectionLabel>Risk signal contribution</SectionLabel>

          <p className="mt-2 text-xs text-black/45">
            What is driving the final risk assessment.
          </p>

          <div className="mt-7 space-y-6">
            <ContributionRow
              label="Current anomaly"
              value={contribution.current}
              total={Math.max(
                contribution.current,
                contribution.futureDrift,
                contribution.futureFailure,
                1,
              )}
            />

            <ContributionRow
              label="Future drift"
              value={contribution.futureDrift}
              total={Math.max(
                contribution.current,
                contribution.futureDrift,
                contribution.futureFailure,
                1,
              )}
            />

            <ContributionRow
              label="Future failure"
              value={contribution.futureFailure}
              total={Math.max(
                contribution.current,
                contribution.futureDrift,
                contribution.futureFailure,
                1,
              )}
            />
          </div>
        </div>
      </section>

      {/* =====================================================
          ENGINEERING STATE
      ====================================================== */}

      <section className="border-b border-black/10 px-8 py-8">
        <SectionLabel>Engineering state</SectionLabel>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
          <StateBlock
            label="Predicted limit exceeded"
            value={summary.limitExceeded}
            description="Components whose projected 168H value crosses the absolute limit."
          />

          <StateBlock
            label="Early drift detected"
            value={summary.earlyDrift}
            description="Components showing abnormal progression before final failure."
          />

          <StateBlock
            label="Future failure predicted"
            value={summary.futureFailure}
            description="Components for which the forecast indicates future failure."
          />
        </div>
      </section>

      {/* =====================================================
          PRIORITY REGISTER
      ====================================================== */}

      <section className="px-8 py-8">
        <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
          <div>
            <SectionLabel>Priority register</SectionLabel>

            <p className="mt-2 text-xs text-black/45">
              Highest-risk components requiring engineering attention.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {(["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"] as RiskFilter[]).map(
              (item) => (
                <button
                  key={item}
                  onClick={() => setFilter(item)}
                  className={`border px-3 py-2 text-[10px] uppercase tracking-[0.15em] transition ${
                    filter === item
                      ? "border-black bg-black text-white"
                      : "border-black/10 bg-white text-black/50 hover:border-black/30"
                  }`}
                >
                  {item}
                </button>
              ),
            )}
          </div>
        </div>

        <div className="mt-5">
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search component or lot..."
            className="w-full border border-black/10 bg-white px-4 py-3 text-sm outline-none placeholder:text-black/30 focus:border-black/30"
          />
        </div>

        <div className="mt-5 overflow-hidden border border-black/10 bg-white">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1050px] text-left">
              <thead>
                <tr className="border-b border-black/10 bg-black/[0.025]">
                  <Header>Component</Header>

                  <Header>Lot</Header>

                  <Header>Current</Header>

                  <Header>Future</Header>

                  <Header>Risk</Header>

                  <Header>Score</Header>

                  <Header>Decision</Header>

                  <Header>Action</Header>
                </tr>
              </thead>

              <tbody>
                {filteredRecords.slice(0, 100).map((item) => (
                  <tr
                    key={item.component_id}
                    onClick={() => setSelectedId(String(item.component_id))}
                    className="cursor-pointer border-b border-black/5 transition hover:bg-black/[0.025]"
                  >
                    <td className="px-4 py-4">
                      <div className="font-mono text-sm font-medium">
                        {item.component_id ?? "—"}
                      </div>

                      <div className="mt-1 text-[10px] text-black/35">
                        {item.component_type ?? "—"}
                      </div>
                    </td>

                    <td className="px-4 py-4 font-mono text-xs text-black/55">
                      {item.lot_id ?? "—"}
                    </td>

                    <td className="px-4 py-4">
                      <div className="text-xs font-medium">
                        {displayRisk(item.current_anomaly_level)}
                      </div>

                      <div className="mt-1 text-[10px] text-black/40">
                        evidence {item.anomaly_evidence_count ?? 0}
                      </div>
                    </td>

                    <td className="px-4 py-4">
                      <div className="text-xs font-medium">
                        {displayRisk(item.future_drift_risk)}
                      </div>

                      <div className="mt-1 text-[10px] text-black/40">
                        {boolValue(item.future_failure_predicted)
                          ? "Failure predicted"
                          : "No failure predicted"}
                      </div>
                    </td>

                    <td className="px-4 py-4">
                      <span
                        className={`inline-flex border px-2 py-1 text-[9px] font-medium uppercase tracking-[0.15em] ${riskClass(
                          item.final_risk_level,
                        )}`}
                      >
                        {displayRisk(item.final_risk_level)}
                      </span>
                    </td>

                    <td className="px-4 py-4">
                      <div className="flex items-center gap-3">
                        <div className="h-1.5 w-16 overflow-hidden bg-black/10">
                          <div
                            className="h-full bg-black"
                            style={{
                              width: `${Math.min(
                                100,
                                Math.max(0, numberValue(item.risk_score)),
                              )}%`,
                            }}
                          />
                        </div>

                        <span className="font-mono text-xs">
                          {formatNumber(item.risk_score, 0)}
                        </span>
                      </div>
                    </td>

                    <td
                      className={`px-4 py-4 text-xs font-medium ${decisionClass(
                        item.final_decision,
                      )}`}
                    >
                      {displayRisk(item.final_decision)}
                    </td>

                    <td className="px-4 py-4">
                      <button
                        onClick={(event) => {
                          event.stopPropagation();

                          setSelectedId(String(item.component_id));
                        }}
                        className="border border-black/10 px-3 py-2 text-[9px] uppercase tracking-[0.15em] text-black/55 hover:border-black/30 hover:text-black"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredRecords.length === 0 && (
            <div className="px-6 py-12 text-center text-sm text-black/40">
              No components match the current filter.
            </div>
          )}
        </div>
      </section>

      {/* =====================================================
          COMPONENT INVESTIGATION
      ====================================================== */}

      {selected && (
        <section className="border-t border-black/10 bg-[#101213] px-8 py-10 text-white">
          <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-start">
            <div>
              <div className="text-[9px] uppercase tracking-[0.3em] text-white/35">
                Component investigation
              </div>

              <div className="mt-3 flex flex-wrap items-center gap-3">
                <h2 className="font-mono text-2xl font-medium">
                  {selected.component_id ?? "UNKNOWN"}
                </h2>

                <span
                  className={`border px-2 py-1 text-[9px] uppercase tracking-[0.15em] ${riskClass(
                    selected.final_risk_level,
                  )}`}
                >
                  {displayRisk(selected.final_risk_level)}
                </span>
              </div>

              <div className="mt-2 text-xs text-white/40">
                {selected.lot_id ?? "—"} / {selected.component_type ?? "—"}
              </div>
            </div>

            <div className="text-right">
              <div className="text-[9px] uppercase tracking-[0.2em] text-white/30">
                Final decision
              </div>

              <div
                className={`mt-2 text-sm font-semibold uppercase tracking-[0.1em] ${decisionClass(
                  selected.final_decision,
                )}`}
              >
                {displayRisk(selected.final_decision)}
              </div>
            </div>
          </div>

          {/* STATE FLOW */}

          <div className="mt-10 grid gap-px border border-white/10 bg-white/10 md:grid-cols-4">
            <InvestigationStage
              number="01"
              label="Current"
              value={displayRisk(selected.current_anomaly_level)}
              detail={`${selected.anomaly_evidence_count ?? 0} evidence signals`}
              active={
                String(selected.current_anomaly_level ?? "").toUpperCase() !==
                "NORMAL"
              }
            />

            <InvestigationStage
              number="02"
              label="Early drift"
              value={
                selected.early_drift_flag
                  ? displayRisk(selected.early_drift_direction)
                  : "NONE"
              }
              detail={
                selected.early_drift_flag
                  ? "Abnormal progression"
                  : "No early warning"
              }
              active={selected.early_drift_flag === true}
            />

            <InvestigationStage
              number="03"
              label="Future"
              value={
                selected.future_failure_predicted
                  ? "FAILURE"
                  : displayRisk(selected.future_drift_risk)
              }
              detail={
                selected.predicted_limit_exceeded
                  ? "Projected limit exceeded"
                  : "Forecast within limit"
              }
              active={
                selected.future_failure_predicted === true ||
                selected.future_drift_abnormal === true
              }
            />

            <InvestigationStage
              number="04"
              label="Decision"
              value={displayRisk(selected.final_decision)}
              detail="Risk engine output"
              active={true}
            />
          </div>

          {/* SIGNAL CARDS */}

          <div className="mt-8">
            <div className="text-[9px] uppercase tracking-[0.25em] text-white/30">
              Why this component was flagged
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
              {explanationItems(selected).map((item) => (
                <SignalCard
                  key={item.label}
                  label={item.label}
                  value={item.value}
                  active={item.active}
                  tone={item.tone}
                />
              ))}
            </div>
          </div>

          {/* MEASUREMENTS + FORECAST */}

          <div className="mt-8 grid gap-px border border-white/10 bg-white/10 lg:grid-cols-2">
            <div className="bg-[#101213] p-6">
              <div className="text-[9px] uppercase tracking-[0.2em] text-white/30">
                Measurement state
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3">
                <DarkMetric
                  label="0H Iddq"
                  value={
                    selected.iddq_0h_uA !== undefined
                      ? `${formatNumber(selected.iddq_0h_uA, 2)} μA`
                      : "—"
                  }
                />

                <DarkMetric
                  label="24H Iddq"
                  value={
                    selected.iddq_24h_uA !== undefined
                      ? `${formatNumber(selected.iddq_24h_uA, 2)} μA`
                      : "—"
                  }
                />

                <DarkMetric
                  label="Absolute limit"
                  value={
                    selected.absolute_limit_uA !== undefined
                      ? `${formatNumber(selected.absolute_limit_uA, 2)} μA`
                      : "—"
                  }
                />

                <DarkMetric
                  label="24H drift"
                  value={
                    selected.drift_0_24_uA_per_h !== undefined
                      ? `${formatNumber(selected.drift_0_24_uA_per_h, 3)} μA/h`
                      : "—"
                  }
                />
              </div>
            </div>

            <div className="bg-[#101213] p-6">
              <div className="text-[9px] uppercase tracking-[0.2em] text-white/30">
                168H projection
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3">
                <DarkMetric
                  label="Predicted"
                  value={
                    selected.predicted_168h_uA !== undefined
                      ? `${formatNumber(selected.predicted_168h_uA, 2)} μA`
                      : "—"
                  }
                />

                <DarkMetric
                  label="Upper bound"
                  value={
                    selected.prediction_upper_uA !== undefined
                      ? `${formatNumber(selected.prediction_upper_uA, 2)} μA`
                      : "—"
                  }
                />

                <DarkMetric
                  label="Limit margin"
                  value={
                    selected.limit_margin_uA !== undefined
                      ? `${formatNumber(selected.limit_margin_uA, 2)} μA`
                      : "—"
                  }
                />

                <DarkMetric
                  label="Future drift"
                  value={
                    selected.predicted_drift_rate !== undefined
                      ? `${formatNumber(selected.predicted_drift_rate, 3)} μA/h`
                      : "—"
                  }
                />
              </div>
            </div>
          </div>

          {/* RISK SCORE */}

          <div className="mt-8 border border-white/10 p-6">
            <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
              <div>
                <div className="text-[9px] uppercase tracking-[0.2em] text-white/30">
                  Final risk score
                </div>

                <div className="mt-2 text-4xl font-semibold">
                  {formatNumber(selected.risk_score, 1)}
                </div>
              </div>

              <div className="w-full max-w-md">
                <div className="mb-2 flex justify-between text-[9px] uppercase tracking-[0.15em] text-white/30">
                  <span>Risk intensity</span>

                  <span>0 — 100</span>
                </div>

                <div className="h-2 bg-white/10">
                  <div
                    className="h-full bg-amber-400"
                    style={{
                      width: `${Math.min(
                        100,
                        Math.max(0, numberValue(selected.risk_score)),
                      )}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* EXPLANATION */}

          <div className="mt-8 border border-white/10 p-6">
            <div className="text-[9px] uppercase tracking-[0.2em] text-white/30">
              Decision evidence
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-2">
              {explanationItems(selected)
                .filter((item) => item.active)
                .map((item) => (
                  <div
                    key={`evidence-${item.label}`}
                    className="flex items-center justify-between border border-white/10 px-4 py-3"
                  >
                    <span className="text-[10px] uppercase tracking-[0.15em] text-white/40">
                      {item.label}
                    </span>

                    <span className="text-xs font-medium text-white">
                      {item.value}
                    </span>
                  </div>
                ))}
            </div>
          </div>

          {/* ACTION */}

          <div className="mt-8 flex flex-col justify-between gap-4 border border-amber-300/20 bg-amber-300/[0.04] p-5 md:flex-row md:items-center">
            <div>
              <div className="text-[9px] uppercase tracking-[0.2em] text-amber-300/60">
                Recommended engineering action
              </div>

              <div className="mt-2 text-sm font-medium text-white">
                {selected.final_decision
                  ? displayRisk(selected.final_decision)
                  : "REVIEW COMPONENT"}
              </div>
            </div>

            {selected.component_id && (
              <Link
                href={`/components/${encodeURIComponent(
                  selected.component_id,
                )}`}
                className="border border-white/15 px-4 py-3 text-[10px] uppercase tracking-[0.15em] text-white/70 hover:border-white/30 hover:text-white"
              >
                Open component investigation
              </Link>
            )}
          </div>
        </section>
      )}
    </div>
  );
}

/* =========================================================
   SMALL COMPONENTS
========================================================= */

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-[10px] uppercase tracking-[0.25em] text-black/40">
      {children}
    </div>
  );
}

function SignalMetric({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: number;
  detail: string;
  tone: "critical" | "high" | "warning";
}) {
  const toneClass =
    tone === "critical"
      ? "text-red-600"
      : tone === "high"
        ? "text-orange-600"
        : "text-amber-600";

  return (
    <div className="border-r border-black/10 bg-[#f4f4f1] px-8 py-6 last:border-r-0">
      <div className="text-[9px] uppercase tracking-[0.2em] text-black/35">
        {label}
      </div>

      <div className={`mt-2 text-3xl font-semibold ${toneClass}`}>
        {value.toLocaleString()}
      </div>

      <div className="mt-1 text-xs text-black/40">{detail}</div>
    </div>
  );
}

function RiskDistributionRow({
  label,
  value,
  percentage,
}: {
  label: string;
  value: number;
  percentage: number;
}) {
  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[10px] font-medium uppercase tracking-[0.18em]">
          {label}
        </span>

        <span className="font-mono text-xs text-black/50">
          {value.toLocaleString()}
        </span>
      </div>

      <div className="h-2 bg-black/10">
        <div
          className="h-full bg-black"
          style={{
            width: `${Math.min(100, percentage)}%`,
          }}
        />
      </div>

      <div className="mt-1 text-[9px] text-black/35">
        {percentage.toFixed(1)}% of components
      </div>
    </div>
  );
}

function ContributionRow({
  label,
  value,
  total,
}: {
  label: string;
  value: number;
  total: number;
}) {
  const percentage = total > 0 ? (value / total) * 100 : 0;

  return (
    <div>
      <div className="mb-2 flex justify-between">
        <span className="text-xs text-black/65">{label}</span>

        <span className="font-mono text-xs text-black/50">
          {value.toFixed(0)}
        </span>
      </div>

      <div className="h-3 bg-black/10">
        <div
          className="h-full bg-black"
          style={{
            width: `${Math.min(100, percentage)}%`,
          }}
        />
      </div>
    </div>
  );
}

function StateBlock({
  label,
  value,
  description,
}: {
  label: string;
  value: number;
  description: string;
}) {
  return (
    <div className="border border-black/10 bg-white p-5">
      <div className="text-[9px] uppercase tracking-[0.18em] text-black/35">
        {label}
      </div>

      <div className="mt-2 text-2xl font-semibold">
        {value.toLocaleString()}
      </div>

      <div className="mt-2 text-xs leading-5 text-black/45">{description}</div>
    </div>
  );
}

function Header({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-3 text-[9px] font-medium uppercase tracking-[0.15em] text-black/35">
      {children}
    </th>
  );
}

function InvestigationStage({
  number,
  label,
  value,
  detail,
  active,
}: {
  number: string;
  label: string;
  value: string;
  detail: string;
  active: boolean;
}) {
  return (
    <div className="bg-[#101213] p-5">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[9px] text-white/25">{number}</span>

        <span
          className={`h-2 w-2 rounded-full ${
            active ? "bg-amber-400" : "bg-white/15"
          }`}
        />
      </div>

      <div className="mt-6 text-[9px] uppercase tracking-[0.2em] text-white/30">
        {label}
      </div>

      <div className="mt-2 text-sm font-medium text-white">{value}</div>

      <div className="mt-1 text-[10px] text-white/35">{detail}</div>
    </div>
  );
}

function SignalCard({
  label,
  value,
  active,
  tone,
}: {
  label: string;
  value: string;
  active: boolean;
  tone: string;
}) {
  const activeClass = active
    ? tone === "red"
      ? "border-red-300/30 bg-red-500/[0.08]"
      : tone === "orange"
        ? "border-orange-300/30 bg-orange-500/[0.08]"
        : "border-amber-300/30 bg-amber-500/[0.08]"
    : "border-white/10 bg-transparent";

  return (
    <div className={`border p-4 ${activeClass}`}>
      <div className="text-[8px] uppercase tracking-[0.18em] text-white/30">
        {label}
      </div>

      <div className="mt-3 text-xs font-medium text-white">{value}</div>

      <div className="mt-2 text-[9px] text-white/30">
        {active ? "SIGNAL ACTIVE" : "NO SIGNAL"}
      </div>
    </div>
  );
}

function DarkMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-white/10 p-4">
      <div className="text-[8px] uppercase tracking-[0.18em] text-white/25">
        {label}
      </div>

      <div className="mt-2 font-mono text-sm text-white/85">{value}</div>
    </div>
  );
}
