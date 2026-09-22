import Link from "next/link";

interface AttentionSummaryProps {
  totalAnomalies: number;
  highRiskComponents: number;
  critical: number;
  high: number;
}

export default function AttentionSummary({
  totalAnomalies,
  highRiskComponents,
  critical,
  high,
}: AttentionSummaryProps) {
  const attentionRequired = critical + high;

  return (
    <section className="mt-8">
      <div className="mb-5 flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">
            QA attention
          </p>

          <h2 className="mt-1 text-lg font-semibold tracking-tight text-slate-950 dark:text-white">
            Investigation signals
          </h2>

          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Components and signals that may require engineering review.
          </p>
        </div>

        <Link
          href="/anomalies"
          className="text-sm font-medium text-slate-700 transition-colors hover:text-slate-950 dark:text-slate-300 dark:hover:text-white"
        >
          View anomalies →
        </Link>
      </div>

      <div className="grid gap-8 border-y border-slate-200 py-6 dark:border-slate-800 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Anomaly signals
          </p>

          <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
            {totalAnomalies}
          </p>

          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Detected by Module A
          </p>
        </div>

        <div>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            High-risk components
          </p>

          <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
            {highRiskComponents}
          </p>

          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Risk assessment
          </p>
        </div>

        <div>
          <p className="text-xs text-slate-500 dark:text-slate-400">Critical</p>

          <p className="mt-2 text-2xl font-semibold tracking-tight text-red-700 dark:text-red-400">
            {critical}
          </p>

          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Highest severity
          </p>
        </div>

        <div>
          <p className="text-xs text-slate-500 dark:text-slate-400">High</p>

          <p className="mt-2 text-2xl font-semibold tracking-tight text-orange-700 dark:text-orange-400">
            {high}
          </p>

          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Requires attention
          </p>
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between border-b border-slate-200 pb-5 dark:border-slate-800">
        <div>
          <p className="text-sm font-medium text-slate-900 dark:text-white">
            {attentionRequired} components with high-severity signals
          </p>

          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Open the anomaly queue to investigate individual components.
          </p>
        </div>

        <Link
          href="/anomalies"
          className="hidden rounded-md border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-50 sm:inline-flex dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-900"
        >
          Open queue
        </Link>
      </div>
    </section>
  );
}
