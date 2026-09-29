"use client";

import { AnomalyRecord } from "./types";
import AnomalyRow from "./AnomalyRow";

type Props = {
  anomalies: AnomalyRecord[];
  loading: boolean;
};

export default function AnomaliesTable({ anomalies, loading }: Props) {
  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-800">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
            Detected anomalies
          </h2>

          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Components showing unusual measurement or behavioral patterns.
          </p>
        </div>
      </div>

      <div className="w-full overflow-hidden">
        <table className="w-full table-fixed text-left">
          <colgroup>
            <col className="w-[22%]" />
            <col className="w-[11%]" />
            <col className="w-[13%]" />
            <col className="w-[14%]" />
            <col className="w-[15%]" />
            <col className="w-[12%]" />
            <col className="w-[13%]" />
          </colgroup>

          <thead>
            <tr className="border-b border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-950/60">
              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Component
              </th>

              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Lot
              </th>

              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Iddq 0h
              </th>

              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Statistical
              </th>

              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Isolation Forest
              </th>

              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Combined
              </th>

              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                Action
              </th>
            </tr>
          </thead>

          <tbody>
            {loading ? (
              Array.from({ length: 6 }).map((_, index) => (
                <tr
                  key={index}
                  className="border-b border-slate-100 dark:border-slate-800"
                >
                  {Array.from({
                    length: 7,
                  }).map((__, cellIndex) => (
                    <td key={cellIndex} className="px-4 py-5">
                      <div className="h-4 w-full max-w-[100px] animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
                    </td>
                  ))}
                </tr>
              ))
            ) : anomalies.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-5 py-12 text-center">
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    No anomalies found
                  </p>

                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    Try changing or clearing the filters.
                  </p>
                </td>
              </tr>
            ) : (
              anomalies.map((anomaly) => (
                <AnomalyRow key={anomaly.component_id} anomaly={anomaly} />
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
