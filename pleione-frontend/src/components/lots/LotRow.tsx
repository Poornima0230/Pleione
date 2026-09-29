"use client";

import Link from "next/link";
import type { Lot } from "./types";
import { formatNumber, formatPercent, formatScore } from "./utils";

interface LotRowProps {
  lot: Lot;
}

function RiskDistribution({
  distribution,
}: {
  distribution: Lot["risk_distribution"];
}) {
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
      <span className="text-xs text-red-600 dark:text-red-400">
        Critical {distribution.CRITICAL.toLocaleString()}
      </span>

      <span className="text-xs text-orange-600 dark:text-orange-400">
        High {distribution.HIGH.toLocaleString()}
      </span>

      <span className="text-xs text-amber-600 dark:text-amber-400">
        Medium {distribution.MEDIUM.toLocaleString()}
      </span>

      <span className="text-xs text-emerald-600 dark:text-emerald-400">
        Low {distribution.LOW.toLocaleString()}
      </span>
    </div>
  );
}

export default function LotRow({ lot }: LotRowProps) {
  return (
    <tr className="border-t border-slate-100 transition-colors hover:bg-slate-50 dark:border-slate-800/80 dark:hover:bg-slate-800/40">
      <td className="px-4 py-4">
        <div>
          <p className="font-medium text-slate-900 dark:text-white">
            {lot.lot_id}
          </p>

          <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
            Screening lot
          </p>
        </div>
      </td>

      <td className="px-3 py-4 text-right">
        <span className="text-sm font-medium text-slate-800 dark:text-slate-200">
          {formatNumber(lot.component_count)}
        </span>
      </td>

      <td className="px-3 py-4 text-right">
        <span className="text-sm font-medium text-slate-800 dark:text-slate-200">
          {formatNumber(lot.anomaly_count)}
        </span>
      </td>

      <td className="px-3 py-4 text-right">
        <span className="text-sm font-medium text-slate-800 dark:text-slate-200">
          {formatPercent(lot.anomaly_rate)}
        </span>
      </td>

      <td className="px-3 py-4 text-right">
        <span className="text-sm text-slate-700 dark:text-slate-300">
          {formatScore(lot.average_anomaly_score)}
        </span>
      </td>

      <td className="px-3 py-4 text-right">
        <span className="font-medium text-slate-900 dark:text-white">
          {formatScore(lot.average_risk_score)}
        </span>
      </td>

      <td className="px-3 py-4">
        <RiskDistribution distribution={lot.risk_distribution} />
      </td>

      <td className="px-3 py-4 text-right">
        <Link
          href={`/components?lot_id=${encodeURIComponent(lot.lot_id)}`}
          className="inline-flex items-center justify-center rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          View
        </Link>
      </td>
    </tr>
  );
}
