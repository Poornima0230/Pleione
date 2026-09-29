interface ForecastEmptyStateProps {
  message?: string;
}

export default function ForecastEmptyState({
  message = "No forecast records found",
}: ForecastEmptyStateProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-6 py-14 text-center dark:border-slate-800 dark:bg-slate-900">
      <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.7"
          className="h-5 w-5"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M4 17l5-5 4 4 7-8"
          />
          <path strokeLinecap="round" strokeLinejoin="round" d="M16 8h4v4" />
        </svg>
      </div>

      <h3 className="mt-4 text-sm font-semibold text-slate-900 dark:text-white">
        {message}
      </h3>

      <p className="mx-auto mt-1 max-w-md text-sm text-slate-500 dark:text-slate-400">
        Prospective prediction data will appear here when available.
      </p>
    </div>
  );
}
