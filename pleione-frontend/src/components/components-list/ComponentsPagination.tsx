"use client";

type Props = {
  page: number;
  total: number;
  totalPages: number;
  pageNumbers: number[];

  onPrevious: () => void;
  onNext: () => void;
  onPageChange: (page: number) => void;
};

export default function ComponentsPagination({
  page,
  total,
  totalPages,
  pageNumbers,
  onPrevious,
  onNext,
  onPageChange,
}: Props) {
  if (total <= 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-3 border-t border-slate-200 px-5 py-3 sm:flex-row sm:items-center sm:justify-between dark:border-white/[0.06]">
      <div className="text-xs text-slate-400">
        Page {page} of {totalPages}
      </div>

      <div className="flex items-center gap-1">
        <button
          disabled={page === 1}
          onClick={onPrevious}
          className="h-8 rounded-md border border-slate-200 px-2.5 text-xs text-slate-500 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
        >
          Previous
        </button>

        {pageNumbers.map((pageNumber) => (
          <button
            key={pageNumber}
            onClick={() => onPageChange(pageNumber)}
            className={`h-8 min-w-8 rounded-md border px-2 text-xs transition ${
              pageNumber === page
                ? "border-slate-900 bg-slate-900 text-white dark:border-white dark:bg-white dark:text-slate-900"
                : "border-slate-200 text-slate-500 hover:bg-slate-50 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
            }`}
          >
            {pageNumber}
          </button>
        ))}

        <button
          disabled={page === totalPages}
          onClick={onNext}
          className="h-8 rounded-md border border-slate-200 px-2.5 text-xs text-slate-500 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
        >
          Next
        </button>
      </div>
    </div>
  );
}
