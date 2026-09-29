interface LotsEmptyStateProps {
  message?: string;
}

export default function LotsEmptyState({
  message = "No lot records found",
}: LotsEmptyStateProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-6 py-14 text-center dark:border-slate-800 dark:bg-slate-900">
      <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-full bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          className="h-5 w-5"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M4.75 7.25h14.5M6.75 4.75h10.5a1 1 0 011 1v12.5a1 1 0 01-1 1H6.75a1 1 0 01-1-1V5.75a1 1 0 011-1z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M8.5 11h7M8.5 14.5h4"
          />
        </svg>
      </div>

      <h3 className="mt-4 text-sm font-semibold text-slate-900 dark:text-white">
        {message}
      </h3>

      <p className="mx-auto mt-1 max-w-md text-sm text-slate-500 dark:text-slate-400">
        Lot-level screening data will appear here when records are available.
      </p>
    </div>
  );
}
