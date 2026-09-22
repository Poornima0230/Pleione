"use client";

import StatusBadge from "@/components/ui/StatusBadge";

interface ScreeningStatusProps {
  passed: number;
  review: number;
  reject: number;
  total: number;
}

export default function ScreeningStatus({
  passed,
  review,
  reject,
  total,
}: ScreeningStatusProps) {
  const processed = passed + review + reject;
  const remaining = Math.max(total - processed, 0);

  const passPercentage = total > 0 ? Math.round((passed / total) * 100) : 0;

  const reviewPercentage = total > 0 ? Math.round((review / total) * 100) : 0;

  const rejectPercentage = total > 0 ? Math.round((reject / total) * 100) : 0;

  return (
    <section className="border-y border-slate-200 py-6 dark:border-slate-800">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
              Screening outcome
            </h2>

            {remaining > 0 ? (
              <StatusBadge status="IN PROGRESS" variant="neutral" />
            ) : (
              <StatusBadge status="COMPLETE" variant="pass" />
            )}
          </div>

          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Distribution of components by current screening decision
          </p>
        </div>

        <div className="grid grid-cols-3 gap-8">
          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400">Pass</p>

            <p className="mt-1 text-lg font-semibold text-emerald-700 dark:text-emerald-400">
              {passed}
            </p>

            <p className="text-xs text-slate-400 dark:text-slate-500">
              {passPercentage}%
            </p>
          </div>

          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400">Review</p>

            <p className="mt-1 text-lg font-semibold text-amber-700 dark:text-amber-400">
              {review}
            </p>

            <p className="text-xs text-slate-400 dark:text-slate-500">
              {reviewPercentage}%
            </p>
          </div>

          <div>
            <p className="text-xs text-slate-500 dark:text-slate-400">Reject</p>

            <p className="mt-1 text-lg font-semibold text-red-700 dark:text-red-400">
              {reject}
            </p>

            <p className="text-xs text-slate-400 dark:text-slate-500">
              {rejectPercentage}%
            </p>
          </div>
        </div>
      </div>

      <div className="mt-6 h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
        <div className="flex h-full w-full">
          {passPercentage > 0 && (
            <div
              className="h-full bg-emerald-500"
              style={{ width: `${passPercentage}%` }}
            />
          )}

          {reviewPercentage > 0 && (
            <div
              className="h-full bg-amber-500"
              style={{ width: `${reviewPercentage}%` }}
            />
          )}

          {rejectPercentage > 0 && (
            <div
              className="h-full bg-red-500"
              style={{ width: `${rejectPercentage}%` }}
            />
          )}
        </div>
      </div>
    </section>
  );
}
