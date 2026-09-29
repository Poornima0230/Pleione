"use client";

export default function ComponentsEmptyState() {
  return (
    <div className="flex min-h-[280px] items-center justify-center px-5">
      <div className="text-center">
        <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 dark:border-white/10">
          <svg
            className="h-5 w-5 text-slate-400"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-4-4" />
          </svg>
        </div>

        <p className="text-sm font-medium">No components found</p>

        <p className="mt-1 text-xs text-slate-400">
          Try changing or clearing your filters.
        </p>
      </div>
    </div>
  );
}
