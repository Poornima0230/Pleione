"use client";

type Props = {
  onClear: () => void;
};

export default function AnomaliesEmptyState({ onClear }: Props) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-6 py-16 text-center dark:border-slate-800 dark:bg-slate-900">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400">
        ✓
      </div>

      <h2 className="mt-4 text-base font-semibold text-slate-900 dark:text-white">
        No anomaly records
      </h2>

      <p className="mx-auto mt-1 max-w-md text-sm text-slate-500 dark:text-slate-400">
        No detected anomalies match the current filters.
      </p>

      <button
        type="button"
        onClick={onClear}
        className="mt-5 rounded-lg border border-slate-200 px-4 py-2 text-xs font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
      >
        Clear filters
      </button>
    </div>
  );
}
