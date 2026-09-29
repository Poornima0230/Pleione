import type { ForecastRow } from "./types";
import ForecastRowComponent from "./ForecastRow";

interface ForecastTableProps {
  rows: ForecastRow[];
}

export default function ForecastTable({ rows }: ForecastTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between gap-4 border-b border-slate-200 px-5 py-4 dark:border-slate-800">
        <div>
          <h2 className="text-base font-semibold text-slate-900 dark:text-white">
            Forecast assessments
          </h2>

          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Prospective 168h Iddq predictions and future drift assessment.
          </p>
        </div>

        <span className="hidden rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 sm:inline-flex dark:bg-slate-800 dark:text-slate-300">
          {rows.length} results
        </span>
      </div>

      <div className="w-full overflow-hidden">
        <table className="w-full table-fixed">
          {/* <th/> */}
          <thead>
            <tr className="bg-slate-50 dark:bg-slate-950">
              <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Component
              </th>

              <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Lot
              </th>

              <th className="px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Current Iddq
              </th>

              <th className="px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Predicted 168h
              </th>

              <th className="px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Predicted drift
              </th>

              <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Future risk
              </th>

              <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Forecast status
              </th>

              <th className="px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Action
              </th>

              <th />
            </tr>
          </thead>

          <tbody>
            {rows.map((row) => (
              <ForecastRowComponent key={row.component_id} row={row} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
