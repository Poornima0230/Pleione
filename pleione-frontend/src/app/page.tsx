"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  ShieldAlert,
  XCircle,
} from "lucide-react";

import { getComponents, getDashboardSummary } from "@/lib/api";
import type { Component, DashboardSummary } from "@/lib/api";
import Link from "next/link";

function formatNumber(value: number | undefined | null) {
  if (value === undefined || value === null) return "—";
  return new Intl.NumberFormat("en-IN").format(value);
}

function formatRisk(value: number | undefined | null) {
  if (value === undefined || value === null) return "—";
  return Number(value).toFixed(1);
}

function decisionTone(decision?: string) {
  const value = decision?.toUpperCase();

  if (value === "REJECT") {
    return {
      text: "text-red-600 dark:text-red-400",
      bg: "bg-red-50 dark:bg-red-950/30",
      border: "border-red-200 dark:border-red-900",
      icon: XCircle,
    };
  }

  if (value === "REVIEW") {
    return {
      text: "text-amber-600 dark:text-amber-400",
      bg: "bg-amber-50 dark:bg-amber-950/30",
      border: "border-amber-200 dark:border-amber-900",
      icon: CircleAlert,
    };
  }

  return {
    text: "text-emerald-600 dark:text-emerald-400",
    bg: "bg-emerald-50 dark:bg-emerald-950/30",
    border: "border-emerald-200 dark:border-emerald-900",
    icon: CheckCircle2,
  };
}

function riskTone(risk?: number | null) {
  const value = Number(risk ?? 0);

  if (value >= 80) {
    return "text-red-600 dark:text-red-400";
  }

  if (value >= 50) {
    return "text-amber-600 dark:text-amber-400";
  }

  return "text-emerald-600 dark:text-emerald-400";
}

function LoadingState() {
  return (
    <div className="flex min-h-[520px] items-center justify-center">
      <div className="text-center">
        <div className="mx-auto mb-3 h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-slate-800 dark:bg-[#020618] dark:border-t-slate-200" />
        <p className="text-sm text-slate-500 dark:text-slate-400">
          Loading screening data...
        </p>
      </div>
    </div>
  );
}

function Metric({
  label,
  value,
  sub,
}: {
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div className="min-w-0">
      <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
        {label}
      </p>

      <p className="mt-1 text-[24px] font-semibold tracking-tight text-slate-950 dark:text-white">
        {value}
      </p>

      {sub && (
        <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
          {sub}
        </p>
      )}
    </div>
  );
}

export default function CommandCenter() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [components, setComponents] = useState<Component[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        setError("");

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
        console.error(err);
        setError("Unable to load screening data.");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  const priorityComponents = useMemo(() => {
    return [...components]
      .filter((component) => {
        const decision = component.screening_decision?.toUpperCase();

        return (
          component.anomaly_flag ||
          decision === "REVIEW" ||
          decision === "REJECT" ||
          component.risk_level?.toUpperCase() === "HIGH" ||
          component.risk_level?.toUpperCase() === "CRITICAL"
        );
      })
      .sort(
        (a, b) => Number(b.risk_score_100 ?? 0) - Number(a.risk_score_100 ?? 0),
      )
      .slice(0, 8);
  }, [components]);

  if (loading) {
    return <LoadingState />;
  }

  if (error || !summary) {
    return (
      <div className="flex min-h-[520px] items-center justify-center">
        <div
          className="rounded-lg border border-red-200 bg-red-50 px-6 py-5 text-center dark:border-red-900
         dark:bg-[#020618]"
        >
          <p className="text-sm font-medium text-red-700 dark:text-red-400">
            {error || "Dashboard data unavailable."}
          </p>
        </div>
      </div>
    );
  }

  const total = Number(summary.total_components ?? 0);
  const passed = Number(summary.passed ?? 0);
  const review = Number(summary.review ?? 0);
  const reject = Number(summary.reject ?? 0);

  const passPercent = total ? (passed / total) * 100 : 0;
  const reviewPercent = total ? (review / total) * 100 : 0;
  const rejectPercent = total ? (reject / total) * 100 : 0;

  return (
    <div className="mx-auto max-w-[1500px]">
      {/* TOP STATUS */}
      <section className="mb-7 flex flex-col gap-4 border-b border-slate-200 pb-6 dark:border-slate-800 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span className="text-[11px] font-medium uppercase tracking-[0.16em] text-emerald-600 dark:text-emerald-400">
              Screening engine online
            </span>
          </div>

          <h1 className="text-3xl font-semibold tracking-tight text-slate-950 dark:text-white">
            Command Center
          </h1>

          <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">
            Burn-in screening overview and investigation queue
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
          <span className="rounded-md border border-slate-200 bg-white px-2.5 py-1.5 dark:border-slate-800 dark:bg-slate-900">
            168H screening
          </span>

          <span className="rounded-md border border-slate-200 bg-white px-2.5 py-1.5 dark:border-slate-800 dark:bg-slate-900">
            FastAPI connected
          </span>
        </div>
      </section>

      {/* KEY NUMBERS */}
      <section className="mb-8 border-b border-slate-200 pb-7 dark:border-slate-800">
        <div className="grid grid-cols-2 gap-y-6 md:grid-cols-4">
          <Metric
            label="Components"
            value={formatNumber(summary.total_components)}
            sub="screened"
          />

          <Metric
            label="Lots"
            value={formatNumber(summary.total_lots)}
            sub="in dataset"
          />

          <Metric
            label="Anomalies"
            value={formatNumber(summary.total_anomalies)}
            sub="detected signals"
          />

          <Metric
            label="High risk"
            value={formatNumber(summary.high_risk_components)}
            sub="requires attention"
          />
        </div>
      </section>

      {/* ATTENTION + DISPOSITION */}
      <section className="mb-8 grid gap-6 xl:grid-cols-[1.65fr_1fr]">
        {/* ATTENTION */}
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900/40">
          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <div>
              <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
                Needs attention
              </h2>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                Highest-risk components in the current result set
              </p>
            </div>

            <Link
              href="/components"
              className="flex items-center gap-1 text-xs font-medium text-slate-600 hover:text-slate-950 dark:text-slate-400 dark:hover:text-white"
            >
              View all
              <ArrowRight size={13} />
            </Link>
          </div>

          {priorityComponents.length === 0 ? (
            <div className="flex min-h-[230px] items-center justify-center px-6">
              <div className="text-center">
                <CheckCircle2
                  size={24}
                  className="mx-auto mb-3 text-emerald-500"
                />
                <p className="text-sm font-medium text-slate-800 dark:text-slate-200">
                  No attention items
                </p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                  No flagged components are present in the loaded results.
                </p>
              </div>
            </div>
          ) : (
            <div className="divide-y divide-slate-100 dark:divide-slate-800">
              {priorityComponents.map((component) => {
                const tone = decisionTone(component.screening_decision);
                const Icon = tone.icon;

                return (
                  <a
                    key={component.component_id}
                    href={`/components/${component.component_id}`}
                    className="group flex items-center gap-4 px-5 py-4 transition-colors hover:bg-slate-50 dark:hover:bg-slate-900"
                  >
                    <div
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${tone.bg}`}
                    >
                      <Icon size={16} className={tone.text} />
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="truncate text-sm font-semibold text-slate-900 dark:text-slate-100">
                          {component.component_id}
                        </span>

                        <span className="text-xs text-slate-400">
                          {component.lot_id}
                        </span>
                      </div>

                      <div className="mt-1 flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
                        <span>{component.component_type}</span>

                        {component.limit_violation && (
                          <span className="text-red-500">Limit violation</span>
                        )}
                      </div>
                    </div>

                    <div className="hidden text-right sm:block">
                      <p className="text-[10px] uppercase tracking-wider text-slate-400">
                        Risk
                      </p>
                      <p
                        className={`mt-0.5 text-sm font-semibold tabular-nums ${riskTone(
                          component.risk_score_100,
                        )}`}
                      >
                        {formatRisk(component.risk_score_100)}
                      </p>
                    </div>

                    <span
                      className={`hidden rounded-md border px-2 py-1 text-[10px] font-semibold uppercase tracking-wide sm:block ${tone.bg} ${tone.border} ${tone.text}`}
                    >
                      {component.screening_decision || "—"}
                    </span>

                    <ChevronRight
                      size={16}
                      className="shrink-0 text-slate-300 transition-transform group-hover:translate-x-0.5 dark:text-slate-600"
                    />
                  </a>
                );
              })}
            </div>
          )}
        </div>

        {/* SCREENING DISPOSITION */}
        <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900/40">
          <div className="mb-5">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
              Screening disposition
            </h2>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              Final decisions across screened components
            </p>
          </div>

          <div className="space-y-5">
            <DispositionRow
              label="PASS"
              value={passed}
              percent={passPercent}
              icon={CheckCircle2}
              tone="emerald"
            />

            <DispositionRow
              label="REVIEW"
              value={review}
              percent={reviewPercent}
              icon={CircleAlert}
              tone="amber"
            />

            <DispositionRow
              label="REJECT"
              value={reject}
              percent={rejectPercent}
              icon={XCircle}
              tone="red"
            />
          </div>

          <div className="mt-7 border-t border-slate-200 pt-5 dark:border-slate-800">
            <div className="flex h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
              <div
                className="bg-emerald-500"
                style={{ width: `${passPercent}%` }}
              />
              <div
                className="bg-amber-500"
                style={{ width: `${reviewPercent}%` }}
              />
              <div
                className="bg-red-500"
                style={{ width: `${rejectPercent}%` }}
              />
            </div>

            <div className="mt-2 flex justify-between text-[10px] text-slate-400">
              <span>PASS</span>
              <span>REVIEW</span>
              <span>REJECT</span>
            </div>
          </div>
        </div>
      </section>

      {/* RISK / ANOMALY SNAPSHOT */}
      <section className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900/40">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
                Risk state
              </h2>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                Current risk signals
              </p>
            </div>

            <ShieldAlert
              size={18}
              className="text-slate-400 dark:text-slate-500"
            />
          </div>

          <div className="grid grid-cols-3 divide-x divide-slate-200 dark:divide-slate-800">
            <RiskMetric label="Critical" value={summary.critical} tone="red" />

            <RiskMetric label="High" value={summary.high} tone="amber" />

            <RiskMetric
              label="Anomalies"
              value={summary.total_anomalies}
              tone="slate"
            />
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900/40">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
                Investigation entry points
              </h2>

              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                Move from screening result to component analysis
              </p>
            </div>

            <AlertTriangle
              size={18}
              className="text-slate-400 dark:text-slate-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <QuickLink
              href="/components"
              label="Components"
              value={formatNumber(summary.total_components)}
            />

            <QuickLink
              href="/anomalies"
              label="Anomalies"
              value={formatNumber(summary.total_anomalies)}
            />

            <QuickLink
              href="/lots"
              label="Lots"
              value={formatNumber(summary.total_lots)}
            />

            <QuickLink
              href="/screening-runs"
              label="Screening runs"
              value="Open"
            />
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <div className="mt-8 flex items-center justify-between border-t border-slate-200 pt-4 text-[11px] text-slate-400 dark:border-slate-800 dark:text-slate-500">
        <span>Pleione Reliability Intelligence</span>
        <span>Module A screening results</span>
      </div>
    </div>
  );
}

function DispositionRow({
  label,
  value,
  percent,
  icon: Icon,
  tone,
}: {
  label: string;
  value: number;
  percent: number;
  icon: typeof CheckCircle2;
  tone: "emerald" | "amber" | "red";
}) {
  const tones = {
    emerald: {
      icon: "text-emerald-500",
      bar: "bg-emerald-500",
    },
    amber: {
      icon: "text-amber-500",
      bar: "bg-amber-500",
    },
    red: {
      icon: "text-red-500",
      bar: "bg-red-500",
    },
  };

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon size={15} className={tones[tone].icon} />
          <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
            {label}
          </span>
        </div>

        <div className="flex items-baseline gap-2">
          <span className="text-sm font-semibold tabular-nums text-slate-900 dark:text-white">
            {formatNumber(value)}
          </span>

          <span className="text-[10px] tabular-nums text-slate-400">
            {percent.toFixed(1)}%
          </span>
        </div>
      </div>

      <div className="h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
        <div
          className={`h-full rounded-full ${tones[tone].bar}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </div>
  );
}

function RiskMetric({
  label,
  value,
  tone,
}: {
  label: string;
  value: number | undefined;
  tone: "red" | "amber" | "slate";
}) {
  const toneClass =
    tone === "red"
      ? "text-red-600 dark:text-red-400"
      : tone === "amber"
        ? "text-amber-600 dark:text-amber-400"
        : "text-slate-900 dark:text-white";

  return (
    <div className="px-4 first:pl-0 last:pr-0">
      <p className="text-[10px] uppercase tracking-[0.12em] text-slate-400">
        {label}
      </p>

      <p className={`mt-1 text-xl font-semibold tabular-nums ${toneClass}`}>
        {formatNumber(value)}
      </p>
    </div>
  );
}

function QuickLink({
  href,
  label,
  value,
}: {
  href: string;
  label: string;
  value: string;
}) {
  return (
    <a
      href={href}
      className="group flex items-center justify-between rounded-lg border border-slate-200 px-3.5 py-3 transition-colors hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:hover:border-slate-700 dark:hover:bg-slate-900"
    >
      <div>
        <p className="text-xs font-medium text-slate-700 dark:text-slate-300">
          {label}
        </p>

        <p className="mt-0.5 text-[11px] tabular-nums text-slate-400">
          {value}
        </p>
      </div>

      <ArrowRight
        size={14}
        className="text-slate-300 transition-transform group-hover:translate-x-0.5 dark:text-slate-600"
      />
    </a>
  );
}
