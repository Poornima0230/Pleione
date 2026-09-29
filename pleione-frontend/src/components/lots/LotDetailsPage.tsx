"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Lot = {
  lot_id: string;
  component_count: number;

  anomaly_count: number;
  anomalous_count: number;
  watch_count: number;

  pass_count: number;
  review_count: number;
  reject_count: number;

  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;

  average_iddq_0h_uA: number | null;
  average_predicted_168h_uA: number | null;
  maximum_predicted_168h_uA: number | null;
  predicted_limit_exceedance_count: number;
};

function formatNumber(value: number | null, digits = 2) {
  if (value === null || value === undefined) return "—";

  return value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function percentage(value: number, total: number) {
  if (!total) return "0.0%";
  return `${((value / total) * 100).toFixed(1)}%`;
}

export default function LotDetailsPage() {
  const params = useParams();

  const rawLotId = params?.lot_id;

  const lotId = Array.isArray(rawLotId) ? rawLotId[0] : rawLotId;

  const [lot, setLot] = useState<Lot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!lotId) return;

    const controller = new AbortController();

    async function loadLot() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          `${API_BASE}/api/lots/${encodeURIComponent(lotId)}`,
          {
            signal: controller.signal,
            cache: "no-store",
          },
        );

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error(`Lot ${lotId} was not found.`);
          }

          throw new Error(`Failed to load lot (${response.status})`);
        }

        const result: Lot = await response.json();

        setLot(result);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load lot information.",
        );
      } finally {
        setLoading(false);
      }
    }

    loadLot();

    return () => controller.abort();
  }, [lotId]);

  if (loading) {
    return (
      <main className="min-h-screen bg-white px-6 py-8 dark:bg-[#020618]">
        <div className="mx-auto max-w-[1400px]">
          <div className="h-5 w-24 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />

          <div className="mt-4 h-9 w-52 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />

          <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-3">
            {[1, 2, 3].map((item) => (
              <div
                key={item}
                className="h-32 animate-pulse rounded-xl border border-slate-200 bg-slate-100 dark:border-slate-800 dark:bg-slate-900"
              />
            ))}
          </div>

          <div className="mt-8 h-72 animate-pulse rounded-xl border border-slate-200 bg-slate-100 dark:border-slate-800 dark:bg-slate-900" />
        </div>
      </main>
    );
  }

  if (error || !lot) {
    return (
      <main className="min-h-screen bg-white px-6 py-8 text-slate-900 dark:bg-[#020618] dark:text-slate-100">
        <div className="mx-auto max-w-[1400px]">
          <Link
            href="/lots"
            className="inline-flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
          >
            <span>←</span>
            Back to lots
          </Link>

          <div className="mt-8 rounded-xl border border-red-200 bg-red-50 p-6 dark:border-red-900/50 dark:bg-red-950/20">
            <h1 className="text-lg font-semibold text-red-700 dark:text-red-400">
              Unable to load lot
            </h1>

            <p className="mt-2 text-sm text-red-600 dark:text-red-400/80">
              {error || "Lot information is unavailable."}
            </p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-white px-5 py-7 text-slate-900 dark:bg-[#020618] dark:text-slate-100 sm:px-7 lg:px-8">
      <div className="mx-auto max-w-[1400px]">
        {/* Back */}
        <Link
          href="/lots"
          className="inline-flex items-center gap-2 text-sm text-slate-500 transition hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200"
        >
          <span>←</span>
          Back to lots
        </Link>

        {/* Header */}
        <header className="mt-6 flex flex-col justify-between gap-5 md:flex-row md:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Lot investigation
            </p>

            <h1 className="mt-1 text-3xl font-semibold tracking-tight">
              {lot.lot_id}
            </h1>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
              Screening and predictive-risk profile for components processed
              within this lot.
            </p>
          </div>

          <Link
            href={`/components?lot_id=${encodeURIComponent(lot.lot_id)}`}
            className="inline-flex w-fit items-center gap-2 rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            View components
            <span>→</span>
          </Link>
        </header>

        {/* Key metrics */}
        <section className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Metric
            label="Components"
            value={lot.component_count.toLocaleString()}
            description="Components in this lot"
          />

          <Metric
            label="Anomaly signals"
            value={lot.anomaly_count.toLocaleString()}
            description={`${percentage(
              lot.anomaly_count,
              lot.component_count,
            )} of lot population`}
          />

          <Metric
            label="Review"
            value={lot.review_count.toLocaleString()}
            description="Requires engineering assessment"
          />

          <Metric
            label="Reject"
            value={lot.reject_count.toLocaleString()}
            description="Predicted specification failure"
          />
        </section>

        {/* Screening + risk */}
        <section className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Screening */}
          <section className="rounded-xl border border-slate-200 dark:border-slate-800">
            <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
              <h2 className="font-semibold">Screening outcome</h2>

              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                Final decisions produced by the screening pipeline.
              </p>
            </div>

            <div className="p-5">
              <DecisionRow
                label="PASS"
                value={lot.pass_count}
                total={lot.component_count}
                type="pass"
              />

              <DecisionRow
                label="REVIEW"
                value={lot.review_count}
                total={lot.component_count}
                type="review"
              />

              <DecisionRow
                label="REJECT"
                value={lot.reject_count}
                total={lot.component_count}
                type="reject"
              />
            </div>
          </section>

          {/* Module A */}
          <section className="rounded-xl border border-slate-200 dark:border-slate-800">
            <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
              <h2 className="font-semibold">Anomaly evidence</h2>

              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                0H peer-based anomaly signals detected in this lot.
              </p>
            </div>

            <div className="p-5">
              <DecisionRow
                label="NORMAL"
                value={
                  lot.component_count - lot.watch_count - lot.anomalous_count
                }
                total={lot.component_count}
                type="normal"
              />

              <DecisionRow
                label="WATCH"
                value={lot.watch_count}
                total={lot.component_count}
                type="watch"
              />

              <DecisionRow
                label="ANOMALOUS"
                value={lot.anomalous_count}
                total={lot.component_count}
                type="anomalous"
              />
            </div>
          </section>
        </section>

        {/* Future risk */}
        <section className="mt-6 rounded-xl border border-slate-200 dark:border-slate-800">
          <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <h2 className="font-semibold">Predicted 168H risk</h2>

            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Distribution of predicted future-risk classifications.
            </p>
          </div>

          <div className="grid grid-cols-2 divide-x divide-slate-200 dark:divide-slate-800 md:grid-cols-4">
            <RiskStat
              label="Low"
              value={lot.low_count}
              total={lot.component_count}
            />

            <RiskStat
              label="Medium"
              value={lot.medium_count}
              total={lot.component_count}
            />

            <RiskStat
              label="High"
              value={lot.high_count}
              total={lot.component_count}
            />

            <RiskStat
              label="Critical"
              value={lot.critical_count}
              total={lot.component_count}
            />
          </div>
        </section>

        {/* Measurements */}
        <section className="mt-6 rounded-xl border border-slate-200 dark:border-slate-800">
          <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
            <h2 className="font-semibold">Electrical profile</h2>

            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Aggregate IDDQ measurements and predicted future values.
            </p>
          </div>

          <div className="grid grid-cols-1 divide-y divide-slate-200 dark:divide-slate-800 sm:grid-cols-2 sm:divide-x sm:divide-y-0 lg:grid-cols-4">
            <Measurement
              label="Average 0H IDDQ"
              value={formatNumber(lot.average_iddq_0h_uA)}
              unit="µA"
            />

            <Measurement
              label="Average predicted 168H"
              value={formatNumber(lot.average_predicted_168h_uA)}
              unit="µA"
            />

            <Measurement
              label="Maximum predicted 168H"
              value={formatNumber(lot.maximum_predicted_168h_uA)}
              unit="µA"
            />

            <Measurement
              label="Predicted limit exceedances"
              value={lot.predicted_limit_exceedance_count.toLocaleString()}
              unit="components"
            />
          </div>
        </section>

        {/* Action */}
        <section className="mt-8 flex flex-col justify-between gap-4 rounded-xl border border-slate-200 px-5 py-5 dark:border-slate-800 sm:flex-row sm:items-center">
          <div>
            <h2 className="font-semibold">Investigate components</h2>

            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Open the component population for {lot.lot_id} and investigate
              individual screening evidence.
            </p>
          </div>

          <Link
            href={`/components?lot_id=${encodeURIComponent(lot.lot_id)}`}
            className="inline-flex w-fit items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-slate-700 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
          >
            Open components
            <span>→</span>
          </Link>
        </section>
      </div>
    </main>
  );
}

function Metric({
  label,
  value,
  description,
}: {
  label: string;
  value: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-slate-200 px-5 py-5 dark:border-slate-800">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
        {label}
      </p>

      <p className="mt-3 text-2xl font-semibold tracking-tight">{value}</p>

      <p className="mt-1 text-xs text-slate-500 dark:text-slate-500">
        {description}
      </p>
    </div>
  );
}

function DecisionRow({
  label,
  value,
  total,
  type,
}: {
  label: string;
  value: number;
  total: number;
  type: "pass" | "review" | "reject" | "normal" | "watch" | "anomalous";
}) {
  const percentageValue = total ? (value / total) * 100 : 0;

  const textClass =
    type === "pass" || type === "normal"
      ? "text-emerald-600 dark:text-emerald-400"
      : type === "review" || type === "watch"
        ? "text-amber-600 dark:text-amber-400"
        : "text-red-600 dark:text-red-400";

  return (
    <div className="flex items-center justify-between border-b border-slate-100 py-4 last:border-b-0 dark:border-slate-800/70">
      <div>
        <p className={`text-sm font-semibold ${textClass}`}>{label}</p>

        <p className="mt-1 text-xs text-slate-500">
          {percentageValue.toFixed(1)}% of lot
        </p>
      </div>

      <p className="text-lg font-semibold">{value.toLocaleString()}</p>
    </div>
  );
}

function RiskStat({
  label,
  value,
  total,
}: {
  label: string;
  value: number;
  total: number;
}) {
  return (
    <div className="px-5 py-5">
      <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">
        {label}
      </p>

      <p className="mt-2 text-xl font-semibold">{value.toLocaleString()}</p>

      <p className="mt-1 text-xs text-slate-500">{percentage(value, total)}</p>
    </div>
  );
}

function Measurement({
  label,
  value,
  unit,
}: {
  label: string;
  value: string;
  unit: string;
}) {
  return (
    <div className="px-5 py-5">
      <p className="text-xs text-slate-500">{label}</p>

      <div className="mt-2 flex items-baseline gap-1.5">
        <span className="text-xl font-semibold">{value}</span>

        <span className="text-xs text-slate-500">{unit}</span>
      </div>
    </div>
  );
}
