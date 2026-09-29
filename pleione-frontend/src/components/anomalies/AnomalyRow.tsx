"use client";

import Link from "next/link";

import { AnomalyRecord } from "./types";
import { formatNumber, getAnomalyScoreTone } from "./utils";

type Props = {
  anomaly: AnomalyRecord;
};

export default function AnomalyRow({ anomaly }: Props) {
  return (
    <tr className="border-b border-slate-100 last:border-0 dark:border-slate-800">
      {/* Component */}
      <td className="px-4 py-4">
        <div className="min-w-0">
          <Link
            href={`/components/${encodeURIComponent(anomaly.component_id)}`}
            className="font-medium text-slate-900 transition hover:text-slate-600 dark:text-white dark:hover:text-slate-300"
          >
            {anomaly.component_id}
          </Link>

          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            {anomaly.component_type || "Unknown type"}
          </p>
        </div>
      </td>

      {/* Lot */}
      <td className="px-4 py-4">
        <span className="text-sm text-slate-700 dark:text-slate-300">
          {anomaly.lot_id || "—"}
        </span>
      </td>

      {/* Iddq */}
      <td className="px-4 py-4">
        <span className="text-sm text-slate-700 dark:text-slate-300">
          {formatNumber(anomaly.iddq_0h_uA, 2)} µA
        </span>
      </td>

      {/* Statistical */}
      <td className="px-4 py-4">
        <span
          className={`text-sm font-medium ${getAnomalyScoreTone(
            anomaly.statistical_score,
          )}`}
        >
          {formatNumber(anomaly.statistical_score, 3)}
        </span>
      </td>

      {/* Isolation Forest */}
      <td className="px-4 py-4">
        <span
          className={`text-sm font-medium ${getAnomalyScoreTone(
            anomaly.isolation_forest_score,
          )}`}
        >
          {formatNumber(anomaly.isolation_forest_score, 3)}
        </span>
      </td>

      {/* Combined */}
      <td className="px-4 py-4">
        <span
          className={`text-sm font-semibold ${getAnomalyScoreTone(
            anomaly.combined_anomaly_score,
          )}`}
        >
          {formatNumber(anomaly.combined_anomaly_score, 3)}
        </span>
      </td>

      {/* Action */}
      <td className="px-4 py-4 text-right">
        <Link
          href={`/components/${encodeURIComponent(anomaly.component_id)}`}
          className="inline-flex h-8 items-center rounded-lg border border-slate-200 px-3 text-xs font-medium text-slate-700 transition hover:bg-slate-50 hover:text-slate-900 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
        >
          Investigate
        </Link>
      </td>
    </tr>
  );
}
