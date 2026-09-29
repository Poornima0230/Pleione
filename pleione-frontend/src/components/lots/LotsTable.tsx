import type { Lot } from "./types";
import LotRow from "./LotRow";

interface LotsTableProps {
  lots: Lot[];
}

export default function LotsTable({ lots }: LotsTableProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between gap-4 border-b border-slate-200 px-5 py-4 dark:border-slate-800">
        <div>
          <h2 className="text-base font-semibold text-slate-900 dark:text-white">
            Lots
          </h2>

          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Compare anomaly activity and risk across screening lots.
          </p>
        </div>

        <span className="hidden rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600 sm:inline-flex dark:bg-slate-800 dark:text-slate-300">
          {lots.length} lots
        </span>
      </div>

      <div className="w-full overflow-hidden">
        <table className="w-full table-fixed">
          <colgroup>
            <col className="w-[15%]" />
            <col className="w-[11%]" />
            <col className="w-[11%]" />
            <col className="w-[12%]" />
            <col className="w-[12%]" />
            <col className="w-[11%]" />
            <col className="w-[18%]" />
            <col className="w-[10%]" />
          </colgroup>

          <thead>
            <tr className="bg-slate-50 dark:bg-slate-950/40">
              <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Lot
              </th>

              <th className="px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Components
              </th>

              <th className="px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Anomalies
              </th>

              <th className="px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Anomaly rate
              </th>

              <th className="px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Avg anomaly
              </th>

              <th className="px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Avg risk
              </th>

              <th className="px-3 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Risk distribution
              </th>

              <th className="px-3 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Action
              </th>
            </tr>
          </thead>

          <tbody>
            {lots.map((lot) => (
              <LotRow key={lot.lot_id} lot={lot} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
