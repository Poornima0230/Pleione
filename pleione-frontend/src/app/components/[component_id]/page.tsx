"use client";

import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

/* =========================================================
   API
========================================================= */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

/* =========================================================
   TYPES
========================================================= */

type MeasurementPoint = {
  time: number;
  value: number;
};

type ComponentData = {
  component_id: string;
  lot_id: string;
  component_type: string;

  temperature_C: number;
  voltage_V: number;

  iddq_0h_uA: number;
  iddq_24h_uA: number;
  iddq_96h_uA: number;
  iddq_168h_uA: number;

  leakage_0h_uA?: number;
  leakage_24h_uA?: number;
  leakage_96h_uA?: number;
  leakage_168h_uA?: number;

  absolute_limit_uA?: number;

  anomaly_flag?: number | boolean;
  combined_anomaly_score?: number;

  risk_score_100?: number;
  risk_level?: string;

  limit_violation?: number | boolean;
  limit_excess_uA?: number;

  screening_decision?: string;
  explanation?: string;
};

type ComponentDetails = {
  component: ComponentData;

  trajectory?: {
    iddq?: MeasurementPoint[];
    leakage?: MeasurementPoint[];
  };

  anomaly_evidence?: {
    max_robust_z?: number;
    statistical_evidence_count?: number;
    statistical_score?: number;
    temporal_anomaly_score?: number;
    temporal_anomaly_flag?: number | boolean;
    isolation_forest_score?: number;
    isolation_forest_flag?: number | boolean;
    combined_anomaly_score?: number;
    anomaly_flag?: number | boolean;
  };

  risk?: {
    risk_score_100?: number;
    risk_level?: string;
    limit_violation?: number | boolean;
    limit_excess_uA?: number;
    screening_decision?: string;
  };

  explanation?: string;
};

type PredictionData = {
  predicted_168h_uA?: number;
  prediction_lower_uA?: number;
  prediction_upper_uA?: number;

  predicted_drift_uA?: number;
  predicted_drift_rate?: number;
  predicted_relative_drift?: number;

  safety_slope?: number;
  drift_slope_excess?: number;

  early_drift_flag?: boolean | number;
  predicted_limit_exceeded?: boolean | number;
  uncertainty_adjusted_failure?: boolean | number;

  limit_margin_uA?: number;
  upper_bound_limit_margin_uA?: number;

  future_drift_risk?: string;
  module_b_status?: string;
  module_b_explanation?: string;
};

type ExplanationData = {
  component?: {
    component_id?: string;
    component_type?: string;
    lot_id?: string;
  };

  parameter_analysis?: {
    parameter?: string;
    latest_observed_value?: number;
    latest_observed_time_hours?: number;
  };

  specification?: {
    status?: string;
    applicable_limit?: number;
    limit_violation?: boolean;
    limit_excess?: number;
  };

  anomaly?: {
    status?: string;
    reason?: string;
    combined_anomaly_score?: number;
    statistical_score?: number;
    temporal_anomaly_score?: number;
    isolation_forest_score?: number;
    statistical_evidence_count?: number;
  };

  drift?: {
    status?: string;
    reason?: string;
    predicted_drift?: number;
    predicted_drift_rate?: number;
    predicted_relative_drift?: number;
    safety_slope?: number;
    drift_slope_excess?: number;
    early_drift_flag?: boolean;
    future_drift_risk?: string;
  };

  prediction?: {
    available?: boolean;
    prediction_column?: string;
    prediction_horizon_hours?: number;
    predicted_value?: number;
    prediction_lower?: number;
    prediction_upper?: number;
    predicted_limit_exceeded?: boolean;
    uncertainty_adjusted_failure?: boolean;
  };

  risk?: {
    risk_score?: number;
    risk_factors?: {
      anomaly_factor?: number;
      drift_factor?: number;
      future_factor?: number;
      specification_factor?: number;
    };
    strongest_factor?: string;
  };

  qa_decision?: {
    classification?: string;
    reason?: string;
  };

  shap?: {
    available?: boolean;
    features?: string[];
  };

  summary?: string;
};

type ExplanationResponse = {
  explanation?: ExplanationData;
};

/* =========================================================
   HELPERS
========================================================= */

function n(value: unknown, fallback = 0): number {
  const valueAsNumber = Number(value);

  return Number.isFinite(valueAsNumber) ? valueAsNumber : fallback;
}

function isTrue(value: unknown): boolean {
  return value === true || value === 1 || value === "1" || value === "true";
}

function fmt(value: unknown, digits = 2): string {
  const valueAsNumber = Number(value);

  if (!Number.isFinite(valueAsNumber)) {
    return "—";
  }

  return valueAsNumber.toFixed(digits);
}

function pct(value: unknown): string {
  const valueAsNumber = Number(value);

  if (!Number.isFinite(valueAsNumber)) {
    return "—";
  }

  return `${Math.round(valueAsNumber * 100)}%`;
}

function titleCase(value?: string): string {
  if (!value) return "—";

  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function riskColor(level?: string): string {
  const value = String(level || "").toUpperCase();

  if (value === "CRITICAL") {
    return "text-red-600 dark:text-red-400";
  }

  if (value === "HIGH") {
    return "text-orange-600 dark:text-orange-400";
  }

  if (value === "MEDIUM") {
    return "text-amber-600 dark:text-amber-400";
  }

  return "text-emerald-600 dark:text-emerald-400";
}

function decisionColor(decision?: string): string {
  const value = String(decision || "").toUpperCase();

  if (value === "REJECT") {
    return "text-red-600 dark:text-red-400";
  }

  if (value === "REVIEW") {
    return "text-amber-600 dark:text-amber-400";
  }

  return "text-emerald-600 dark:text-emerald-400";
}

function statusTone(status?: string): "green" | "amber" | "red" | "neutral" {
  const value = String(status || "").toUpperCase();

  if (
    value.includes("ANOMALOUS") ||
    value.includes("HIGH") ||
    value.includes("FAIL")
  ) {
    return "red";
  }

  if (
    value.includes("REVIEW") ||
    value.includes("DRIFT") ||
    value.includes("MONITOR")
  ) {
    return "amber";
  }

  if (
    value.includes("NORMAL") ||
    value.includes("PASS") ||
    value.includes("WITHIN")
  ) {
    return "green";
  }

  return "neutral";
}

/* =========================================================
   UI PRIMITIVES
========================================================= */

function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "green" | "amber" | "red" | "neutral";
}) {
  const classes = {
    green:
      "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-400",

    amber:
      "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-400",

    red: "border-red-200 bg-red-50 text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-400",

    neutral:
      "border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300",
  };

  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.08em] ${classes[tone]}`}
    >
      {children}
    </span>
  );
}

function Eyebrow({ children }: { children: ReactNode }) {
  return (
    <div className="mb-1 text-[10px] font-medium uppercase tracking-[0.14em] text-slate-400 dark:text-slate-500">
      {children}
    </div>
  );
}

function Metric({
  label,
  value,
  unit,
  tone = "normal",
  small = false,
}: {
  label: string;
  value: ReactNode;
  unit?: string;
  tone?: "normal" | "good" | "warn" | "danger";
  small?: boolean;
}) {
  const colors = {
    normal: "text-slate-900 dark:text-white",
    good: "text-emerald-600 dark:text-emerald-400",
    warn: "text-amber-600 dark:text-amber-400",
    danger: "text-red-600 dark:text-red-400",
  };

  return (
    <div className="min-w-0">
      <div className="mb-1 text-[10px] font-medium uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
        {label}
      </div>

      <div
        className={[
          "font-sans font-semibold tabular-nums tracking-tight",
          small ? "text-[13px]" : "text-[18px]",
          colors[tone],
        ].join(" ")}
      >
        {value}

        {unit && (
          <span className="ml-1 text-[10px] font-medium tracking-normal text-slate-400 dark:text-slate-500">
            {unit}
          </span>
        )}
      </div>
    </div>
  );
}

function CompactRow({
  label,
  value,
  valueClass = "",
}: {
  label: string;
  value: ReactNode;
  valueClass?: string;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-slate-100 py-2 last:border-b-0 dark:border-slate-800">
      <span className="text-[11px] text-slate-500 dark:text-slate-400">
        {label}
      </span>

      <span
        className={`text-right font-sans text-[11px] font-semibold tabular-nums text-slate-800 dark:text-slate-200 ${valueClass}`}
      >
        {value}
      </span>
    </div>
  );
}

/* =========================================================
   TRAJECTORY GRAPH
========================================================= */

function TrajectoryChart({
  points,
  prediction,
  limit,
}: {
  points: MeasurementPoint[];
  prediction?: PredictionData | null;
  limit: number;
}) {
  const width = 980;
  const height = 360;

  const left = 64;
  const right = 40;
  const top = 34;
  const bottom = 54;

  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;

  const predicted = n(prediction?.predicted_168h_uA, NaN);

  const lower = n(prediction?.prediction_lower_uA, NaN);

  const upper = n(prediction?.prediction_upper_uA, NaN);

  const values = [
    ...points.map((point) => point.value),
    limit,
    Number.isFinite(predicted) ? predicted : null,
    Number.isFinite(lower) ? lower : null,
    Number.isFinite(upper) ? upper : null,
  ].filter(
    (value): value is number => value !== null && Number.isFinite(value),
  );

  const highest = Math.max(...values, 1);

  const yMax = Math.max(10, Math.ceil((highest * 1.12) / 10) * 10);

  const yMin = 0;

  const x = (time: number) => left + (time / 168) * plotWidth;

  const y = (value: number) =>
    top + plotHeight - ((value - yMin) / (yMax - yMin)) * plotHeight;

  /*
    A smooth cubic curve is used only to visually connect
    the observed measurement points.
  */
  function smoothPath(source: MeasurementPoint[]) {
    if (source.length === 0) return "";

    if (source.length === 1) {
      return `M ${x(source[0].time)} ${y(source[0].value)}`;
    }

    let path = `M ${x(source[0].time)} ${y(source[0].value)}`;

    for (let i = 0; i < source.length - 1; i++) {
      const current = source[i];
      const next = source[i + 1];

      const previous = source[Math.max(0, i - 1)];

      const after = source[Math.min(source.length - 1, i + 2)];

      const control1X = x(current.time) + (x(next.time) - x(previous.time)) / 6;

      const control1Y =
        y(current.value) + (y(next.value) - y(previous.value)) / 6;

      const control2X = x(next.time) - (x(after.time) - x(current.time)) / 6;

      const control2Y = y(next.value) - (y(after.value) - y(current.value)) / 6;

      path +=
        ` C ${control1X} ${control1Y}, ` +
        `${control2X} ${control2Y}, ` +
        `${x(next.time)} ${y(next.value)}`;
    }

    return path;
  }

  const observedPath = smoothPath(points);

  const gridValues = Array.from(
    { length: 6 },
    (_, index) => (yMax / 5) * index,
  );

  const xTicks = [0, 24, 96, 168];

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/40">
      {/*
   
       Graph header */}
      <div className="flex flex-col gap-3 border-b border-slate-200 px-5 py-4 sm:flex-row sm:items-center sm:justify-between dark:border-slate-800">
        <div>
          <div className="text-[14px] font-semibold tracking-tight text-slate-900 dark:text-white">
            IDDQ burn-in trajectory
          </div>

          <div className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
            Measured behavior against specification and projected behavior
          </div>
        </div>

        <div className="flex items-center gap-4 text-[10px] font-medium text-slate-500 dark:text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            Measured
          </span>

          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-violet-500" />
            Predicted
          </span>

          <span className="flex items-center gap-1.5">
            <span className="h-[2px] w-4 bg-red-400" />
            Absolute limit
          </span>

          <span className="hidden items-center gap-1.5 sm:flex">
            <span className="h-3 w-2 rounded bg-violet-200 dark:bg-violet-400/20" />
            Prediction range
          </span>
        </div>
      </div>

      {/* Graph */}
      <div className="px-2 pb-2 pt-1 sm:px-4">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="h-[330px] w-full"
          role="img"
          aria-label="IDDQ trajectory chart"
        >
          {/* Horizontal grid */}
          {gridValues.map((value) => {
            const cy = y(value);

            return (
              <g key={`grid-${value}`}>
                <line
                  x1={left}
                  x2={width - right}
                  y1={cy}
                  y2={cy}
                  stroke="currentColor"
                  className="text-slate-100 dark:text-white/[0.055]"
                />

                <text
                  x={left - 12}
                  y={cy + 4}
                  textAnchor="end"
                  fontSize="10"
                  className="fill-slate-400 dark:fill-slate-500"
                  fontFamily="Inter, ui-sans-serif, system-ui, sans-serif"
                >
                  {value.toFixed(0)}
                </text>
              </g>
            );
          })}

          {/* Vertical time guides */}
          {xTicks.map((time) => (
            <g key={`time-${time}`}>
              <line
                x1={x(time)}
                x2={x(time)}
                y1={top}
                y2={height - bottom}
                stroke="currentColor"
                className="text-slate-100 dark:text-white/[0.045]"
              />

              <text
                x={x(time)}
                y={height - 25}
                textAnchor="middle"
                fontSize="10"
                className="fill-slate-400 dark:fill-slate-500"
              >
                {time}h
              </text>
            </g>
          ))}

          {/* Axis title */}
          <text
            x={left}
            y={17}
            fontSize="10"
            fontWeight="600"
            className="fill-slate-400 dark:fill-slate-500"
          >
            IDDQ · µA
          </text>

          {/* Limit */}
          <line
            x1={left}
            x2={width - right}
            y1={y(limit)}
            y2={y(limit)}
            stroke="currentColor"
            className="text-red-400"
            strokeWidth="1.5"
            strokeDasharray="7 6"
          />

          <rect
            x={width - right - 96}
            y={y(limit) - 21}
            width="96"
            height="19"
            rx="4"
            fill="currentColor"
            className="text-white dark:text-slate-900"
          />

          <text
            x={width - right - 8}
            y={y(limit) - 8}
            textAnchor="end"
            fontSize="9"
            fontWeight="700"
            className="fill-red-500 dark:fill-red-400"
          >
            LIMIT {limit.toFixed(0)} µA
          </text>

          {/* Prediction interval */}
          {Number.isFinite(lower) && Number.isFinite(upper) && (
            <>
              <rect
                x={x(168) - 7}
                y={y(upper)}
                width="14"
                height={Math.max(4, y(lower) - y(upper))}
                rx="7"
                fill="currentColor"
                className="text-violet-400/15 dark:text-violet-400/20"
              />

              <line
                x1={x(168)}
                x2={x(168)}
                y1={y(upper)}
                y2={y(lower)}
                stroke="currentColor"
                className="text-violet-400"
                strokeWidth="2"
                opacity="0.5"
              />

              <text
                x={x(168) - 14}
                y={y(upper) - 8}
                textAnchor="end"
                fontSize="9"
                fontWeight="600"
                className="fill-violet-500 dark:fill-violet-300"
              >
                {upper.toFixed(2)}
              </text>

              <text
                x={x(168) - 14}
                y={y(lower) + 13}
                textAnchor="end"
                fontSize="9"
                fontWeight="600"
                className="fill-violet-500 dark:fill-violet-300"
              >
                {lower.toFixed(2)}
              </text>
            </>
          )}

          {/* Observed curve */}
          {points.length > 1 && (
            <>
              {/* subtle glow */}
              <path
                d={observedPath}
                fill="none"
                stroke="currentColor"
                className="text-emerald-400/15"
                strokeWidth="8"
                strokeLinecap="round"
              />

              <path
                d={observedPath}
                fill="none"
                stroke="currentColor"
                className="text-emerald-500"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </>
          )}

          {/* Actual measurement points */}
          {points.map((point, index) => {
            const pointX = x(point.time);
            const pointY = y(point.value);

            const labelAbove = index % 2 === 0;

            const boxY = labelAbove ? pointY - 42 : pointY + 17;

            return (
              <g key={`measurement-${point.time}`}>
                {/* pointer */}
                <line
                  x1={pointX}
                  x2={pointX}
                  y1={labelAbove ? boxY + 22 : boxY}
                  y2={labelAbove ? pointY - 6 : pointY + 6}
                  stroke="currentColor"
                  className="text-emerald-400/70"
                  strokeWidth="1"
                />

                {/* label */}
                <rect
                  x={pointX - 37}
                  y={boxY}
                  width="74"
                  height="23"
                  rx="5"
                  fill="currentColor"
                  className="text-white dark:text-slate-800"
                  stroke="currentColor"
                  strokeWidth="1"
                  opacity="0.98"
                />

                <text
                  x={pointX}
                  y={boxY + 15}
                  textAnchor="middle"
                  fontSize="10"
                  fontWeight="700"
                  className="fill-slate-700 dark:fill-slate-200"
                >
                  {point.value.toFixed(2)} µA
                </text>

                {/* point ring */}
                <circle
                  cx={pointX}
                  cy={pointY}
                  r="7"
                  fill="currentColor"
                  className="text-white dark:text-slate-900"
                />

                <circle
                  cx={pointX}
                  cy={pointY}
                  r="5"
                  fill="currentColor"
                  className="text-emerald-500"
                />

                <circle
                  cx={pointX}
                  cy={pointY}
                  r="8"
                  fill="none"
                  stroke="currentColor"
                  className="text-emerald-400/30"
                />
              </g>
            );
          })}

          {/* Predicted 168H point */}
          {Number.isFinite(predicted) && (
            <g>
              <line
                x1={x(168)}
                x2={x(168)}
                y1={y(predicted)}
                y2={height - bottom}
                stroke="currentColor"
                className="text-violet-400"
                strokeWidth="1"
                strokeDasharray="4 5"
                opacity="0.45"
              />

              <circle
                cx={x(168)}
                cy={y(predicted)}
                r="11"
                fill="none"
                stroke="currentColor"
                className="text-violet-400/35"
                strokeWidth="2"
              />

              <circle
                cx={x(168)}
                cy={y(predicted)}
                r="7"
                fill="currentColor"
                className="text-violet-500"
              />

              <rect
                x={x(168) - 43}
                y={y(predicted) - 39}
                width="86"
                height="22"
                rx="5"
                fill="currentColor"
                className="text-violet-500"
              />

              <text
                x={x(168)}
                y={y(predicted) - 24}
                textAnchor="middle"
                fill="white"
                fontSize="9"
                fontWeight="700"
              >
                PRED {predicted.toFixed(2)} µA
              </text>
            </g>
          )}

          <text
            x={width - right}
            y={height - 7}
            textAnchor="end"
            fontSize="9"
            className="fill-slate-400 dark:fill-slate-500"
          >
            Burn-in time
          </text>
        </svg>
      </div>
    </div>
  );
}

/* =========================================================
   COMPONENT PROFILE
========================================================= */

function ComponentProfile({
  component,
  limit,
}: {
  component: ComponentData;
  limit: number;
}) {
  const measured168 = n(component.iddq_168h_uA);

  return (
    <section className="mb-5 border-y border-slate-200 dark:border-slate-800">
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8">
        <div className="border-r border-slate-200 py-3 pr-4 dark:border-slate-800">
          <Metric label="Lot" value={component.lot_id} small />
        </div>

        <div className="border-r border-slate-200 px-4 py-3 dark:border-slate-800">
          <Metric
            label="Component type"
            value={component.component_type}
            small
          />
        </div>

        <div className="border-r border-slate-200 px-4 py-3 dark:border-slate-800">
          <Metric
            label="Temperature"
            value={fmt(component.temperature_C)}
            unit="°C"
          />
        </div>

        <div className="border-r border-slate-200 px-4 py-3 dark:border-slate-800">
          <Metric label="Voltage" value={fmt(component.voltage_V)} unit="V" />
        </div>

        <div className="border-r border-slate-200 px-4 py-3 dark:border-slate-800">
          <Metric
            label="168H actual"
            value={fmt(measured168)}
            unit="µA"
            tone={measured168 > limit ? "danger" : "normal"}
          />
        </div>

        <div className="border-r border-slate-200 px-4 py-3 dark:border-slate-800">
          <Metric label="Absolute limit" value={fmt(limit)} unit="µA" />
        </div>

        <div className="border-r border-slate-200 px-4 py-3 dark:border-slate-800">
          <Metric
            label="Screening"
            value={component.screening_decision || "—"}
            small
            tone={
              String(component.screening_decision).toUpperCase() === "REVIEW"
                ? "warn"
                : String(component.screening_decision).toUpperCase() ===
                    "REJECT"
                  ? "danger"
                  : "good"
            }
          />
        </div>

        <div className="py-3 pl-4">
          <Metric
            label="Risk level"
            value={component.risk_level || "—"}
            small
            tone={
              String(component.risk_level).toUpperCase() === "HIGH" ||
              String(component.risk_level).toUpperCase() === "CRITICAL"
                ? "danger"
                : String(component.risk_level).toUpperCase() === "MEDIUM"
                  ? "warn"
                  : "good"
            }
          />
        </div>
      </div>
    </section>
  );
}

/* =========================================================
   ASSESSMENT
========================================================= */

function AssessmentStrip({
  anomalyDetected,
  anomalyScore,
  futureRisk,
  predicted168,
  upperPrediction,
  decision,
  riskLevel,
}: {
  anomalyDetected: boolean;
  anomalyScore: number;
  futureRisk: string;
  predicted168: number;
  upperPrediction: number;
  decision: string;
  riskLevel: string;
}) {
  return (
    <section className="mb-5 grid gap-4 lg:grid-cols-3">
      {/* CURRENT */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900/40">
        <div className="flex items-start justify-between gap-3">
          <div>
            <Eyebrow>Current state</Eyebrow>

            <h2 className="text-[14px] font-semibold tracking-tight text-slate-900 dark:text-white">
              {anomalyDetected ? "Anomaly detected" : "No anomaly detected"}
            </h2>
          </div>

          <Badge tone={anomalyDetected ? "amber" : "green"}>
            {anomalyDetected ? "Attention" : "Normal"}
          </Badge>
        </div>

        <div className="mt-5 flex items-end justify-between gap-4">
          <div>
            <div
              className={`font-sans text-[26px] font-semibold tracking-tight tabular-nums ${
                anomalyDetected
                  ? "text-amber-600 dark:text-amber-400"
                  : "text-emerald-600 dark:text-emerald-400"
              }`}
            >
              {fmt(anomalyScore, 3)}
            </div>

            <div className="mt-1 text-[10px] uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
              Combined anomaly score
            </div>
          </div>

          <div className="text-right text-[10px] leading-4 text-slate-400 dark:text-slate-500">
            Statistical
            <br />
            Temporal
            <br />
            Isolation Forest
          </div>
        </div>
      </div>

      {/* FUTURE */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900/40">
        <div className="flex items-start justify-between gap-3">
          <div>
            <Eyebrow>Future state</Eyebrow>

            <h2 className="text-[14px] font-semibold tracking-tight text-slate-900 dark:text-white">
              168H projection
            </h2>
          </div>

          <Badge
            tone={
              futureRisk.toUpperCase() === "HIGH"
                ? "red"
                : futureRisk.toUpperCase() === "MEDIUM"
                  ? "amber"
                  : "green"
            }
          >
            Future {futureRisk}
          </Badge>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-5">
          <Metric
            label="Predicted endpoint"
            value={fmt(predicted168)}
            unit="µA"
          />

          <Metric
            label="Prediction upper bound"
            value={fmt(upperPrediction)}
            unit="µA"
            tone={upperPrediction > 50 ? "danger" : "normal"}
          />
        </div>
      </div>

      {/* DECISION */}
      <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900/40">
        <div className="flex items-start justify-between gap-3">
          <div>
            <Eyebrow>Screening · Decision</Eyebrow>

            <h2 className="text-[14px] font-semibold tracking-tight text-slate-900 dark:text-white">
              Current screening
            </h2>
          </div>

          <Badge
            tone={
              decision.toUpperCase() === "REJECT"
                ? "red"
                : decision.toUpperCase() === "REVIEW"
                  ? "amber"
                  : "green"
            }
          >
            {decision}
          </Badge>
        </div>

        <div className="mt-5 flex items-end justify-between gap-4">
          <div>
            <div
              className={`font-sans text-[25px] font-semibold tracking-tight tabular-nums ${decisionColor(
                decision,
              )}`}
            >
              {decision}
            </div>

            <div className="mt-1 text-[10px] uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
              Operational screening decision
            </div>
          </div>

          <div className="text-right">
            <div
              className={`text-[13px] font-semibold ${riskColor(riskLevel)}`}
            >
              {riskLevel}
            </div>

            <div className="mt-1 text-[10px] text-slate-400 dark:text-slate-500">
              Risk level
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* =========================================================
   RISK FACTORS
========================================================= */

function RiskFactors({
  factors,
  strongest,
}: {
  factors: {
    anomaly: number;
    drift: number;
    future: number;
    specification: number;
  };
  strongest: string;
}) {
  const rows = [
    {
      key: "anomaly_factor",
      label: "Anomaly evidence",
      value: factors.anomaly,
      explanation: "Evidence of abnormal current behavior",
    },
    {
      key: "drift_factor",
      label: "Drift evidence",
      value: factors.drift,
      explanation: "Evidence of abnormal change over time",
    },
    {
      key: "future_factor",
      label: "Future behavior",
      value: factors.future,
      explanation: "Evidence from predicted future behavior",
    },
    {
      key: "specification_factor",
      label: "Specification",
      value: factors.specification,
      explanation: "Contribution from limit violation",
    },
  ];

  return (
    <div className="space-y-3.5">
      {rows.map((row) => {
        const isStrongest =
          strongest.toLowerCase() === row.key.replace("_factor", "");

        return (
          <div key={row.key}>
            <div className="mb-1.5 flex items-end justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-semibold text-slate-700 dark:text-slate-200">
                    {row.label}
                  </span>

                  {isStrongest && (
                    <span className="rounded-md bg-violet-50 px-1.5 py-0.5 text-[8px] font-semibold uppercase tracking-[0.08em] text-violet-600 dark:bg-violet-950/30 dark:text-violet-400">
                      Strongest
                    </span>
                  )}
                </div>

                <div className="mt-0.5 text-[10px] text-slate-400 dark:text-slate-500">
                  {row.explanation}
                </div>
              </div>

              <span className="shrink-0 font-sans text-[11px] font-semibold tabular-nums text-slate-800 dark:text-slate-200">
                {pct(row.value)}
              </span>
            </div>

            <div className="h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
              <div
                className={`h-full rounded-full ${
                  isStrongest
                    ? "bg-violet-500"
                    : "bg-slate-500 dark:bg-slate-400"
                }`}
                style={{
                  width: `${Math.min(100, Math.max(0, row.value * 100))}%`,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* =========================================================
   PAGE
========================================================= */

export default function ComponentInvestigationPage() {
  const params = useParams<{ component_id: string }>();

  const componentId = Array.isArray(params?.component_id)
    ? params.component_id[0]
    : params?.component_id;

  const [details, setDetails] = useState<ComponentDetails | null>(null);

  const [prediction, setPrediction] = useState<PredictionData | null>(null);

  const [explanation, setExplanation] = useState<ExplanationData | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  useEffect(() => {
    if (!componentId) return;

    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");

      try {
        const [componentResponse, predictionResponse, explanationResponse] =
          await Promise.all([
            fetch(
              `${API_BASE}/api/components/${encodeURIComponent(componentId)}`,
              {
                cache: "no-store",
              },
            ),

            fetch(
              `${API_BASE}/api/predictions/${encodeURIComponent(componentId)}`,
              {
                cache: "no-store",
              },
            ),

            fetch(
              `${API_BASE}/api/explanations/${encodeURIComponent(componentId)}`,
              {
                cache: "no-store",
              },
            ),
          ]);

        if (!componentResponse.ok) {
          throw new Error(
            `Component request failed: ${componentResponse.status}`,
          );
        }

        const componentJson = await componentResponse.json();

        let predictionJson: {
          prediction?: PredictionData;
        } = {};

        let explanationJson: ExplanationResponse = {};

        if (predictionResponse.ok) {
          predictionJson = await predictionResponse.json();
        }

        if (explanationResponse.ok) {
          explanationJson = await explanationResponse.json();
        }

        if (cancelled) return;

        setDetails(componentJson);

        setPrediction(predictionJson.prediction ?? null);

        setExplanation(explanationJson.explanation ?? null);
      } catch (err) {
        if (cancelled) return;

        setError(
          err instanceof Error ? err.message : "Unable to load component.",
        );
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [componentId]);

  /* =======================================================
     DATA PREPARATION
  ======================================================= */

  const component = details?.component;

  /*
    IMPORTANT:
    The graph prefers the backend trajectory.

    If trajectory is missing/incomplete, we use the four
    actual component measurements directly from the backend.

    This is display preparation only. No ML/anomaly/risk
    calculation is being performed here.
  */
  const trajectory = useMemo(() => {
    if (!component) {
      return [];
    }

    const backendTrajectory = details?.trajectory?.iddq ?? [];

    const expectedTimes = [0, 24, 96, 168];

    const fromBackend = expectedTimes.map((time) => {
      const existing = backendTrajectory.find(
        (point) => Number(point.time) === time,
      );

      if (existing) {
        return {
          time,
          value: n(existing.value),
        };
      }

      const fieldMap: Record<number, keyof ComponentData> = {
        0: "iddq_0h_uA",
        24: "iddq_24h_uA",
        96: "iddq_96h_uA",
        168: "iddq_168h_uA",
      };

      return {
        time,
        value: n(component[fieldMap[time]]),
      };
    });

    return fromBackend;
  }, [details, component]);

  if (!component) {
    if (loading) {
      return (
        <main className="min-h-full bg-slate-50 dark:bg-[#080b10]">
          <div className="mx-auto max-w-[1500px] px-5 py-6 lg:px-6">
            <div className="h-4 w-32 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />

            <div className="mt-5 h-9 w-72 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />

            <div className="mt-6 h-[400px] animate-pulse rounded-xl bg-slate-200 dark:bg-slate-900" />
          </div>
        </main>
      );
    }

    return (
      <main
        className="min-h-full bg-slate-50
     dark:bg-[#020618]
      "
      >
        {/* dark:bg-[#080b10] */}
        <div className="mx-auto max-w-[1500px] px-5 py-6 lg:px-6">
          <Link
            href="/components"
            className="text-[11px] text-slate-500 hover:text-slate-900 dark:hover:text-white"
          >
            ← Back to components
          </Link>

          <div className="mt-6 rounded-xl border border-red-200 bg-white p-5 dark:border-red-900 dark:bg-slate-900/40">
            <div className="text-sm font-semibold text-red-600 dark:text-red-400">
              Component could not be loaded
            </div>

            <div className="mt-2 text-[11px] text-slate-500 dark:text-slate-400">
              {error || "No component data returned."}
            </div>

            <div className="mt-3 text-[10px] text-slate-400 dark:text-slate-500">
              API: {API_BASE}
            </div>
          </div>
        </div>
      </main>
    );
  }

  const limit = n(component.absolute_limit_uA, 50);

  /* =======================================================
     CURRENT STATE
  ======================================================= */

  const anomalyDetected = isTrue(
    details?.anomaly_evidence?.anomaly_flag ?? component.anomaly_flag,
  );

  const anomalyScore = n(
    explanation?.anomaly?.combined_anomaly_score ??
      details?.anomaly_evidence?.combined_anomaly_score ??
      component.combined_anomaly_score,
  );

  /* =======================================================
     FUTURE STATE
  ======================================================= */

  const predicted168 = n(
    prediction?.predicted_168h_uA ?? explanation?.prediction?.predicted_value,
    NaN,
  );

  const predictionLower = n(
    prediction?.prediction_lower_uA ??
      explanation?.prediction?.prediction_lower,
    NaN,
  );

  const predictionUpper = n(
    prediction?.prediction_upper_uA ??
      explanation?.prediction?.prediction_upper,
    NaN,
  );

  const futureRisk =
    prediction?.future_drift_risk ??
    explanation?.drift?.future_drift_risk ??
    "—";

  const earlyDrift = isTrue(
    prediction?.early_drift_flag ?? explanation?.drift?.early_drift_flag,
  );

  const uncertaintyFailure = isTrue(
    prediction?.uncertainty_adjusted_failure ??
      explanation?.prediction?.uncertainty_adjusted_failure,
  );

  /* =======================================================
     RISK
  ======================================================= */

  const riskScore = n(
    explanation?.risk?.risk_score ??
      details?.risk?.risk_score_100 ??
      component.risk_score_100,
  );

  const riskLevel = details?.risk?.risk_level ?? component.risk_level ?? "—";

  const factors = {
    anomaly: n(explanation?.risk?.risk_factors?.anomaly_factor),

    drift: n(explanation?.risk?.risk_factors?.drift_factor),

    future: n(explanation?.risk?.risk_factors?.future_factor),

    specification: n(explanation?.risk?.risk_factors?.specification_factor),
  };

  const strongestFactor = explanation?.risk?.strongest_factor ?? "";

  /* =======================================================
     SCREENING
  ======================================================= */

  const decision =
    details?.risk?.screening_decision ?? component.screening_decision ?? "—";

  const qaClassification = explanation?.qa_decision?.classification ?? "—";

  const actual168 = n(component.iddq_168h_uA);

  const limitViolation = isTrue(
    details?.risk?.limit_violation ?? component.limit_violation,
  );

  /* =======================================================
     EXPLANATION
  ======================================================= */

  const anomalyReason =
    explanation?.anomaly?.reason ??
    component.explanation ??
    "No additional anomaly explanation available.";

  const driftReason =
    explanation?.drift?.reason ??
    prediction?.module_b_explanation ??
    "No additional drift explanation available.";

  const qaReason =
    explanation?.qa_decision?.reason ??
    explanation?.summary ??
    "No additional QA interpretation available.";

  return (
    <main className="min-h-full bg-slate-50 text-slate-900 dark:bg-[#020618] dark:text-white">
      <div className="mx-auto w-full max-w-[1500px] px-5 pb-10 pt-5 lg:px-6">
        {/* =================================================
            TOP
        ================================================= */}

        <div className="mb-6 flex items-end justify-between gap-6">
          <div>
            <div className="mb-2 flex items-center gap-2 text-[11px]">
              <Link
                href="/components"
                className="text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
              >
                Components
              </Link>

              <span className="text-slate-300 dark:text-slate-700">/</span>

              <span className="font-mono text-slate-400 dark:text-slate-500">
                {component.component_id}
              </span>
            </div>

            <div className="mb-2 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />

              <Eyebrow>Component investigation</Eyebrow>
            </div>

            <div className="flex flex-wrap items-baseline gap-3">
              <h1 className="font-sans text-[24px] font-semibold tracking-tight text-slate-950 dark:text-white">
                {component.component_id}
              </h1>

              <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">
                {component.component_type}
              </span>

              <span className="text-[11px] text-slate-300 dark:text-slate-700">
                ·
              </span>

              <span className="text-[11px] text-slate-500 dark:text-slate-400">
                Lot {component.lot_id}
              </span>
            </div>

            <div className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
              Burn-in screening · 168H horizon
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-2">
            <Badge
              tone={
                decision.toUpperCase() === "REJECT"
                  ? "red"
                  : decision.toUpperCase() === "REVIEW"
                    ? "amber"
                    : "green"
              }
            >
              {decision}
            </Badge>

            <Badge
              tone={
                futureRisk.toUpperCase() === "HIGH"
                  ? "red"
                  : futureRisk.toUpperCase() === "MEDIUM"
                    ? "amber"
                    : "green"
              }
            >
              Future {futureRisk}
            </Badge>
          </div>
        </div>

        {/* =================================================
            PROFILE
        ================================================= */}

        <ComponentProfile component={component} limit={limit} />

        {/* =================================================
            TRAJECTORY
        ================================================= */}

        <section className="mb-5">
          <TrajectoryChart
            points={trajectory}
            prediction={prediction}
            limit={limit}
          />
        </section>

        {/* =================================================
            THREE PRIMARY ANSWERS
        ================================================= */}

        <AssessmentStrip
          anomalyDetected={anomalyDetected}
          anomalyScore={anomalyScore}
          futureRisk={String(futureRisk)}
          predicted168={predicted168}
          upperPrediction={predictionUpper}
          decision={decision}
          riskLevel={riskLevel}
        />

        {/* =================================================
            EVIDENCE AREA
        ================================================= */}

        <section className="mb-5 grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
          {/* -----------------------------------------------
              LEFT — RISK
          ----------------------------------------------- */}

          <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/40">
            <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
              <div className="flex items-end justify-between gap-4">
                <div>
                  <Eyebrow>Risk assessment</Eyebrow>

                  <h2 className="text-[14px] font-semibold tracking-tight text-slate-900 dark:text-white">
                    Risk assessment
                  </h2>

                  <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                    How the evidence contributes to the overall risk.
                  </p>
                </div>

                <div className="text-right">
                  <div className="font-sans text-[24px] font-semibold tracking-tight tabular-nums text-slate-950 dark:text-white">
                    {fmt(riskScore, 1)}
                    <span className="ml-1 text-[10px] font-medium text-slate-400 dark:text-slate-500">
                      /100
                    </span>
                  </div>

                  <div
                    className={`text-[10px] font-semibold uppercase tracking-[0.1em] ${riskColor(
                      riskLevel,
                    )}`}
                  >
                    {riskLevel}
                  </div>
                </div>
              </div>
            </div>

            <div className="p-5">
              <div className="mb-5 flex items-center justify-between gap-4 rounded-lg border border-slate-200 bg-slate-50 px-3.5 py-3 dark:border-slate-800 dark:bg-slate-900">
                <div>
                  <div className="text-[10px] uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
                    Strongest factor
                  </div>

                  <div className="mt-1 text-[11px] font-semibold text-slate-800 dark:text-slate-200">
                    {titleCase(strongestFactor)}
                  </div>
                </div>

                <div className="text-right text-[10px] leading-4 text-slate-400 dark:text-slate-500">
                  Factor level
                  <br />
                  not probability
                </div>
              </div>

              <RiskFactors factors={factors} strongest={strongestFactor} />
            </div>
          </div>

          {/* -----------------------------------------------
              RIGHT — DETECTOR EVIDENCE
          ----------------------------------------------- */}

          <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/40">
            <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
              <Eyebrow>Signal evidence</Eyebrow>

              <h2 className="text-[14px] font-semibold tracking-tight text-slate-900 dark:text-white">
                Signal evidence
              </h2>

              <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                Detector and future-behavior signals behind the assessment.
              </p>
            </div>

            <div className="grid gap-6 p-5 sm:grid-cols-2">
              <div>
                <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
                  Current behavior
                </div>

                <CompactRow
                  label="Statistical score"
                  value={fmt(
                    explanation?.anomaly?.statistical_score ??
                      details?.anomaly_evidence?.statistical_score,
                    3,
                  )}
                />

                <CompactRow
                  label="Temporal score"
                  value={fmt(
                    explanation?.anomaly?.temporal_anomaly_score ??
                      details?.anomaly_evidence?.temporal_anomaly_score,
                    3,
                  )}
                />

                <CompactRow
                  label="Isolation Forest"
                  value={fmt(
                    explanation?.anomaly?.isolation_forest_score ??
                      details?.anomaly_evidence?.isolation_forest_score,
                    3,
                  )}
                />

                <CompactRow
                  label="Evidence signals"
                  value={`${fmt(
                    explanation?.anomaly?.statistical_evidence_count ??
                      details?.anomaly_evidence?.statistical_evidence_count,
                    0,
                  )}`}
                />

                <CompactRow
                  label="Max robust z"
                  value={fmt(details?.anomaly_evidence?.max_robust_z, 2)}
                />
              </div>

              <div>
                <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
                  Future behavior
                </div>

                <CompactRow
                  label="Predicted drift"
                  value={`${fmt(
                    prediction?.predicted_drift_uA ??
                      explanation?.drift?.predicted_drift,
                  )} µA`}
                />

                <CompactRow
                  label="Drift rate"
                  value={`${fmt(
                    prediction?.predicted_drift_rate ??
                      explanation?.drift?.predicted_drift_rate,
                    4,
                  )} µA/h`}
                />

                <CompactRow
                  label="Relative drift"
                  value={fmt(
                    prediction?.predicted_relative_drift ??
                      explanation?.drift?.predicted_relative_drift,
                    4,
                  )}
                />

                <CompactRow
                  label="Safety slope excess"
                  value={fmt(
                    prediction?.drift_slope_excess ??
                      explanation?.drift?.drift_slope_excess,
                    4,
                  )}
                />

                <CompactRow
                  label="Uncertainty-adjusted failure"
                  value={uncertaintyFailure ? "Yes" : "No"}
                  valueClass={
                    uncertaintyFailure
                      ? "text-red-600 dark:text-red-400"
                      : "text-emerald-600 dark:text-emerald-400"
                  }
                />
              </div>
            </div>
          </div>
        </section>

        {/* =================================================
            INVESTIGATION EXPLANATION
        ================================================= */}

        <section className="mb-5 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/40">
          <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
              <div>
                <Eyebrow>Investigation explanation</Eyebrow>

                <h2 className="text-[14px] font-semibold tracking-tight text-slate-900 dark:text-white">
                  Investigation explanation
                </h2>

                <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                  Human-readable reasoning assembled from the anomaly, drift and
                  risk outputs.
                </p>
              </div>

              <Badge
                tone={
                  qaClassification.toUpperCase() === "MONITOR"
                    ? "amber"
                    : "neutral"
                }
              >
                QA · {qaClassification}
              </Badge>
            </div>
          </div>

          <div className="grid md:grid-cols-3">
            <div className="border-b border-slate-100 p-5 md:border-b-0 md:border-r dark:border-slate-800">
              <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
                What is happening now?
              </div>

              <div
                className={`mb-2 text-[12px] font-semibold ${
                  anomalyDetected
                    ? "text-amber-600 dark:text-amber-400"
                    : "text-emerald-600 dark:text-emerald-400"
                }`}
              >
                {anomalyDetected ? "Anomaly detected" : "No anomaly detected"}
              </div>

              <p className="text-[11px] leading-5 text-slate-500 dark:text-slate-400">
                {anomalyReason}
              </p>
            </div>

            <div className="border-b border-slate-100 p-5 md:border-b-0 md:border-r dark:border-slate-800">
              <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
                What may happen next?
              </div>

              <div className="mb-2 text-[12px] font-semibold text-slate-800 dark:text-slate-200">
                {titleCase(
                  explanation?.drift?.status ?? "Projection available",
                )}
              </div>

              <p className="text-[11px] leading-5 text-slate-500 dark:text-slate-400">
                {driftReason}
              </p>
            </div>

            <div className="p-5">
              <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
                Why this screening state?
              </div>

              <div className="mb-2 text-[12px] font-semibold text-slate-800 dark:text-slate-200">
                {qaClassification}
              </div>

              <p className="text-[11px] leading-5 text-slate-500 dark:text-slate-400">
                {qaReason}
              </p>
            </div>
          </div>
        </section>

        {/* =================================================
            MEASUREMENTS
        ================================================= */}

        <section className="grid gap-4 lg:grid-cols-[1.35fr_0.65fr]">
          {/* Measurements */}
          <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/40">
            <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
              <Eyebrow>Observed data</Eyebrow>

              <h2 className="text-[14px] font-semibold tracking-tight text-slate-900 dark:text-white">
                Burn-in measurements
              </h2>

              <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                Actual IDDQ values recorded during screening.
              </p>
            </div>

            <div className="grid grid-cols-4">
              {trajectory.map((point, index) => (
                <div
                  key={point.time}
                  className={`px-5 py-4 ${
                    index < trajectory.length - 1
                      ? "border-r border-slate-100 dark:border-slate-800"
                      : ""
                  }`}
                >
                  <div className="mb-2 flex items-center gap-2">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />

                    <span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
                      {point.time}H
                    </span>
                  </div>

                  <div className="font-sans text-[20px] font-semibold tracking-tight tabular-nums text-slate-900 dark:text-white">
                    {fmt(point.value)}
                  </div>

                  <div className="mt-1 text-[10px] text-slate-400 dark:text-slate-500">
                    µA
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Projection */}
          <div className="rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/40">
            <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
              <Eyebrow>Future projection</Eyebrow>

              <h2 className="text-[14px] font-semibold tracking-tight text-slate-900 dark:text-white">
                168H projection
              </h2>

              <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                Predicted endpoint and uncertainty range.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-x-6 gap-y-5 p-5">
              <Metric label="Predicted" value={fmt(predicted168)} unit="µA" />

              <Metric label="Actual" value={fmt(actual168)} unit="µA" />

              <Metric
                label="Lower bound"
                value={fmt(predictionLower)}
                unit="µA"
              />

              <Metric
                label="Upper bound"
                value={fmt(predictionUpper)}
                unit="µA"
                tone={predictionUpper > limit ? "danger" : "normal"}
              />

              <Metric
                label="Early drift"
                value={earlyDrift ? "Detected" : "Not detected"}
                tone={earlyDrift ? "warn" : "good"}
                small
              />

              <Metric
                label="Future risk"
                value={String(futureRisk).toUpperCase()}
                tone={
                  String(futureRisk).toUpperCase() === "HIGH"
                    ? "danger"
                    : "warn"
                }
                small
              />
            </div>
          </div>
        </section>

        {/* =================================================
            FOOTER
        ================================================= */}

        <footer className="mt-6 flex items-center justify-between border-t border-slate-200 pt-4 text-[10px] text-slate-400 dark:border-slate-800 dark:text-slate-500">
          <span>Pleione · Reliability Intelligence</span>

          <span>{component.component_id} · 168H</span>
        </footer>
      </div>
    </main>
  );
}
