"use client";

type Props = {
  page: number;
  pages: number;
  total: number;
  limit: number;
  onPageChange: (page: number) => void;
};

export default function AnomaliesPagination({
  page,
  pages,
  total,
  limit,
  onPageChange,
}: Props) {
  if (total === 0) {
    return null;
  }

  const start = (page - 1) * limit + 1;

  const end = Math.min(page * limit, total);

  return (
    <div className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-xs text-slate-500 dark:text-slate-400">
        Showing{" "}
        <span className="font-medium text-slate-700 dark:text-slate-300">
          {start}
        </span>{" "}
        to{" "}
        <span className="font-medium text-slate-700 dark:text-slate-300">
          {end}
        </span>{" "}
        of{" "}
        <span className="font-medium text-slate-700 dark:text-slate-300">
          {total}
        </span>{" "}
        anomalies
      </p>

      <div className="flex items-center gap-2">
        <button
          type="button"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          className="h-9 rounded-lg border border-slate-200 px-3 text-xs font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          Previous
        </button>

        <div className="flex h-9 min-w-9 items-center justify-center rounded-lg border border-slate-200 px-3 text-xs font-semibold text-slate-900 dark:border-slate-700 dark:text-white">
          {page}
        </div>

        <button
          type="button"
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
          className="h-9 rounded-lg border border-slate-200 px-3 text-xs font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          Next
        </button>
      </div>
    </div>
  );
}
