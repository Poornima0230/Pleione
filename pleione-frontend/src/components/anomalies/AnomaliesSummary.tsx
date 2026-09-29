"use client";

import { AnomalySummary } from "./types";
import { formatInteger, formatPercentage } from "./utils";

type Props = {
  summary: AnomalySummary | null;
  loading: boolean;
};

export default function AnomaliesSummary({ summary, loading }: Props) {
  const totalAnomalies = summary?.total_anomalies ?? 0;

  const totalComponents = summary?.total_components ?? 0;

  const anomalyRate = summary?.anomaly_rate ?? 0;

  return (
    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
          Detected anomalies
        </p>

        <div className="mt-2">
          {loading ? (
            <div className="h-8 w-24 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
          ) : (
            <p className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
              {formatInteger(totalAnomalies)}
            </p>
          )}
        </div>

        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Components requiring further attention
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
          Anomaly rate
        </p>

        <div className="mt-2">
          {loading ? (
            <div className="h-8 w-24 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
          ) : (
            <p className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
              {formatPercentage(anomalyRate)}
            </p>
          )}
        </div>

        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Share of screened components with detected anomalies
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
        <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
          Components screened
        </p>

        <div className="mt-2">
          {loading ? (
            <div className="h-8 w-24 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
          ) : (
            <p className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
              {formatInteger(totalComponents)}
            </p>
          )}
        </div>

        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Components included in the screening data
        </p>
      </div>
    </section>
  );
}
