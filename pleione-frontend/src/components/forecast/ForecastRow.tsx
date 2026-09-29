"use client";

import Link from "next/link";

import type { ForecastRow as ForecastRowType } from "./types";
import {
  formatCurrent,
  formatDecimal,
  formatDrift,
  riskClass,
  statusClass,
} from "./utils";

interface ForecastRowProps {
  row: ForecastRowType;
}

export default function ForecastRow({ row }: ForecastRowProps) {
  return (
    <tr className="border-t border-slate-100 transition-colors hover:bg-slate-50 dark:border-slate-800/80 dark:hover:bg-slate-800/40">
      <td className="px-4 py-4">
        <div>
          <p className="font-medium text-slate-900 dark:text-white">
            {row.component_id}
          </p>

          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            {row.component_type || "Component"}
          </p>
        </div>
      </td>

      <td className="px-3 py-4">
        <span className="text-sm text-slate-700 dark:text-slate-300">
          {row.lot_id}
        </span>
      </td>

      <td className="px-3 py-4 text-right">
        <span className="text-sm font-medium text-slate-900 dark:text-white">
          {formatCurrent(row.iddq_0h_uA)}
        </span>
      </td>

      <td className="px-3 py-4 text-right">
        <div>
          <p className="text-sm font-medium text-slate-900 dark:text-white">
            {formatCurrent(row.predicted_168h_uA)}
          </p>

          <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
            range {formatDecimal(row.prediction_lower_uA)}–
            {formatDecimal(row.prediction_upper_uA)} µA
          </p>
        </div>
      </td>

      <td className="px-3 py-4 text-right">
        <span
          className={`text-sm font-medium ${
            Number(row.predicted_drift_uA ?? 0) > 0
              ? "text-amber-600 dark:text-amber-400"
              : "text-slate-700 dark:text-slate-300"
          }`}
        >
          {formatDrift(row.predicted_drift_uA)}
        </span>
      </td>

      <td className="px-3 py-4">
        <span
          className={`text-xs font-semibold ${riskClass(
            row.future_drift_risk,
          )}`}
        >
          {row.future_drift_risk || "—"}
        </span>
      </td>

      <td className="px-3 py-4">
        <span
          className={`text-xs font-medium ${statusClass(row.module_b_status)}`}
        >
          {String(row.module_b_status || "—").replaceAll("_", " ")}
        </span>
      </td>

      <td className="px-3 py-4 text-right">
        <Link
          href={`/components/${encodeURIComponent(row.component_id)}`}
          className="inline-flex items-center justify-center rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          View
        </Link>
      </td>
    </tr>
  );
}
