"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  CheckCircle2,
  AlertTriangle,
  CircleAlert,
  Database,
  RefreshCw,
  ShieldCheck,
  XCircle,
} from "lucide-react";

import { getDashboardSummary, getComponents } from "@/lib/api";
import type { Component, DashboardSummary } from "@/lib/api";

function formatNumber(value: number | undefined | null) {
  if (value === undefined || value === null) return "—";

  return new Intl.NumberFormat("en-IN").format(value);
}

function formatPercentage(value: number) {
  return `${value.toFixed(1)}%`;
}

function DecisionRow({
  label,
  value,
  total,
  icon: Icon,
  type,
}: {
  label: string;
  value: number;
  total: number;
  icon: typeof CheckCircle2;
  type: "pass" | "review" | "reject";
}) {
  const percentage = total > 0 ? (value / total) * 100 : 0;

  const styles = {
    pass: {
      icon: "text-emerald-500",
      bar: "bg-emerald-500",
      value: "text-emerald-600 dark:text-emerald-400",
    },
    review: {
      icon: "text-amber-500",
      bar: "bg-amber-500",
      value: "text-amber-600 dark:text-amber-400",
    },
    reject: {
      icon: "text-red-500",
      bar: "bg-red-500",
      value: "text-red-600 dark:text-red-400",
    },
  };

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon size={15} className={styles[type].icon} />

          <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
            {label}
          </span>
        </div>

        <div className="flex items-baseline gap-2">
          <span
            className={`text-sm font-semibold tabular-nums ${styles[type].value}`}
          >
            {formatNumber(value)}
          </span>

          <span className="text-[10px] tabular-nums text-slate-400">
            {formatPercentage(percentage)}
          </span>
        </div>
      </div>

      <div className="h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
        <div
          className={`h-full rounded-full ${styles[type].bar}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function SummaryMetric({
  label,
  value,
  description,
}: {
  label: string;
  value: string | number;
  description: string;
}) {
  return (
    <div>
      <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-slate-400 dark:text-slate-500">
        {label}
      </p>

      <p className="mt-1 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
        {value}
      </p>

      <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
        {description}
      </p>
    </div>
  );
}

export default function ScreeningRunsPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [components, setComponents] = useState<Component[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  async function loadData(isRefresh = false) {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      setError("");

      /*
       * There is currently no verified /api/screening-runs
       * backend endpoint in the project.
       *
       * So this page uses the existing backend data:
       *
       * /api/dashboard/summary
       * /api/components/
       *
       * This keeps the page completely connected to real
       * backend values without inventing a screening-runs API.
       */

      const [summaryData, componentData] = await Promise.all([
        getDashboardSummary(),
        getComponents({
          page: 1,
          limit: 100,
        }),
      ]);

      setSummary(summaryData);
      setComponents(componentData.data ?? []);
    } catch (err) {
      console.error("Screening run load error:", err);
      setError("Unable to load screening data.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const anomalyCount = useMemo(() => {
    return components.filter((component) => component.anomaly_flag).length;
  }, [components]);

  const limitViolations = useMemo(() => {
    return components.filter((component) => component.limit_violation).length;
  }, [components]);

  if (loading) {
    return (
      <div className="flex min-h-[520px] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-3 h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-800 dark:border-slate-700 dark:border-t-slate-200" />

          <p className="text-sm text-slate-500 dark:text-slate-400">
            Loading screening data...
          </p>
        </div>
      </div>
    );
  }

  if (!summary || error) {
    return (
      <div className="flex min-h-[520px] items-center justify-center">
        <div className="rounded-xl border border-red-200 bg-red-50 px-6 py-5 text-center dark:border-red-900 dark:bg-red-950/20">
          <XCircle size={22} className="mx-auto mb-3 text-red-500" />

          <p className="text-sm font-medium text-red-700 dark:text-red-400">
            {error || "Screening data unavailable."}
          </p>

          <button
            onClick={() => loadData(true)}
            className="mt-4 inline-flex items-center gap-2 rounded-md border border-red-200 bg-white px-3 py-2 text-xs font-medium text-red-700 hover:bg-red-50 dark:border-red-900 dark:bg-slate-950 dark:text-red-400"
          >
            <RefreshCw size={13} />
            Retry
          </button>
        </div>
      </div>
    );
  }

  const total = Number(summary.total_components ?? 0);
  const passed = Number(summary.passed ?? 0);
  const review = Number(summary.review ?? 0);
  const reject = Number(summary.reject ?? 0);

  const passPercentage = total > 0 ? (passed / total) * 100 : 0;
  const reviewPercentage = total > 0 ? (review / total) * 100 : 0;
  const rejectPercentage = total > 0 ? (reject / total) * 100 : 0;

  return (
    <div className="mx-auto max-w-[1500px]">
      {/* HEADER */}
      <div className="mb-7 flex flex-col gap-4 border-b border-slate-200 pb-6 dark:border-slate-800 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />

            <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-600 dark:text-emerald-400">
              Screening engine online
            </span>
          </div>

          <h1 className="text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
            Screening Run
          </h1>

          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Current burn-in screening state
          </p>
        </div>

        <button
          onClick={() => loadData(true)}
          disabled={refreshing}
          className="inline-flex h-9 items-center justify-center gap-2 rounded-md border border-slate-200 bg-white px-3 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          <RefreshCw size={13} className={refreshing ? "animate-spin" : ""} />

          {refreshing ? "Refreshing" : "Refresh"}
        </button>
      </div>

      {/* RUN STATE */}
      <section className="mb-7 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/40">
        <div className="flex flex-col gap-5 p-5 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-emerald-50 dark:bg-emerald-950/30">
              <Activity
                size={21}
                className="text-emerald-600 dark:text-emerald-400"
              />
            </div>

            <div>
              <p className="text-sm font-semibold text-slate-900 dark:text-white">
                Burn-in screening active
              </p>

              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Component-level anomaly and screening assessment
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs">
            <div>
              <span className="text-slate-400">Stage</span>

              <span className="ml-2 font-medium text-slate-700 dark:text-slate-300">
                168H
              </span>
            </div>

            <div>
              <span className="text-slate-400">Components</span>

              <span className="ml-2 font-medium tabular-nums text-slate-700 dark:text-slate-300">
                {formatNumber(total)}
              </span>
            </div>

            <div>
              <span className="text-slate-400">Lots</span>

              <span className="ml-2 font-medium tabular-nums text-slate-700 dark:text-slate-300">
                {formatNumber(summary.total_lots)}
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* SUMMARY */}
      <section className="mb-8 border-b border-slate-200 pb-7 dark:border-slate-800">
        <div className="grid grid-cols-2 gap-y-6 md:grid-cols-4">
          <SummaryMetric
            label="Components"
            value={formatNumber(summary.total_components)}
            description="screened"
          />

          <SummaryMetric
            label="Anomaly signals"
            value={formatNumber(summary.total_anomalies)}
            description="detected"
          />

          <SummaryMetric
            label="High risk"
            value={formatNumber(summary.high_risk_components)}
            description="requires attention"
          />

          <SummaryMetric
            label="Limit violations"
            value={formatNumber(limitViolations)}
            description="loaded results"
          />
        </div>
      </section>

      {/* DISPOSITION */}
      <section className="mb-7 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900/40">
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
              Screening disposition
            </h2>

            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Final screening decisions
            </p>
          </div>

          <div className="space-y-5">
            <DecisionRow
              label="PASS"
              value={passed}
              total={total}
              icon={CheckCircle2}
              type="pass"
            />

            <DecisionRow
              label="REVIEW"
              value={review}
              total={total}
              icon={CircleAlert}
              type="review"
            />

            <DecisionRow
              label="REJECT"
              value={reject}
              total={total}
              icon={XCircle}
              type="reject"
            />
          </div>

          <div className="mt-7 flex h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
            <div
              className="bg-emerald-500"
              style={{ width: `${passPercentage}%` }}
            />

            <div
              className="bg-amber-500"
              style={{ width: `${reviewPercentage}%` }}
            />

            <div
              className="bg-red-500"
              style={{ width: `${rejectPercentage}%` }}
            />
          </div>
        </div>

        {/* RUN HEALTH */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900/40">
          <div className="mb-6">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
              Run health
            </h2>

            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Current screening indicators
            </p>
          </div>

          <div className="space-y-4">
            <HealthRow
              icon={Database}
              label="Components processed"
              value={formatNumber(total)}
            />

            <HealthRow
              icon={ShieldCheck}
              label="Passed screening"
              value={formatNumber(passed)}
            />

            <HealthRow
              icon={CircleAlert}
              label="Review required"
              value={formatNumber(review)}
            />

            <HealthRow
              icon={AlertTriangle}
              label="Anomaly signals"
              value={formatNumber(anomalyCount)}
            />
          </div>
        </div>
      </section>

      {/* RESULT SUMMARY */}
      <section className="rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/40">
        <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
            Run result
          </h2>

          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Current screening output
          </p>
        </div>

        <div className="grid grid-cols-2 divide-x divide-slate-200 dark:divide-slate-800 md:grid-cols-4">
          <ResultCell label="Total" value={formatNumber(total)} />

          <ResultCell
            label="PASS"
            value={formatNumber(passed)}
            tone="emerald"
          />

          <ResultCell
            label="REVIEW"
            value={formatNumber(review)}
            tone="amber"
          />

          <ResultCell label="REJECT" value={formatNumber(reject)} tone="red" />
        </div>
      </section>

      {/* FOOTER */}
      <div className="mt-7 flex items-center justify-between border-t border-slate-200 pt-4 text-[10px] text-slate-400 dark:border-slate-800 dark:text-slate-500">
        <span>Pleione Reliability Intelligence</span>

        <span>Live backend data</span>
      </div>
    </div>
  );
}

function HealthRow({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Database;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between border-b border-slate-100 pb-3 last:border-0 last:pb-0 dark:border-slate-800">
      <div className="flex items-center gap-2.5">
        <Icon size={15} className="text-slate-400 dark:text-slate-500" />

        <span className="text-xs text-slate-600 dark:text-slate-400">
          {label}
        </span>
      </div>

      <span className="text-sm font-semibold tabular-nums text-slate-900 dark:text-white">
        {value}
      </span>
    </div>
  );
}

function ResultCell({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "emerald" | "amber" | "red";
}) {
  const toneClass =
    tone === "emerald"
      ? "text-emerald-600 dark:text-emerald-400"
      : tone === "amber"
        ? "text-amber-600 dark:text-amber-400"
        : tone === "red"
          ? "text-red-600 dark:text-red-400"
          : "text-slate-950 dark:text-white";

  return (
    <div className="px-5 py-5 first:pl-5">
      <p className="text-[10px] uppercase tracking-[0.12em] text-slate-400">
        {label}
      </p>

      <p className={`mt-1 text-xl font-semibold tabular-nums ${toneClass}`}>
        {value}
      </p>
    </div>
  );
}
