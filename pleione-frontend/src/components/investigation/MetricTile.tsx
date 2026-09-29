import type { ReactNode } from "react";

type MetricTone = "default" | "green" | "amber" | "red";

type MetricTileProps = {
  label: string;
  value: ReactNode;
  unit?: string;
  sub?: ReactNode;
  tone?: MetricTone;
  unavailable?: boolean;
};

export default function MetricTile({
  label,
  value,
  unit,
  sub,
  tone = "default",
  unavailable = false,
}: MetricTileProps) {
  const valueTone: Record<MetricTone, string> = {
    default: "text-slate-900 dark:text-white",
    green: "text-emerald-600 dark:text-emerald-400",
    amber: "text-amber-600 dark:text-amber-400",
    red: "text-red-600 dark:text-red-400",
  };

  return (
    <div
      className={`min-w-0 rounded-lg border p-4 transition-colors ${
        unavailable
          ? "border-dashed border-slate-200 bg-slate-50/70 dark:border-slate-800 dark:bg-slate-950/30"
          : "border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-950/40"
      }`}
    >
      <div className="text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">
        {label}
      </div>

      <div className="mt-2 flex min-h-[28px] items-baseline gap-1.5">
        <span
          className={`text-lg font-semibold tracking-tight ${
            unavailable ? "text-slate-400 dark:text-slate-500" : valueTone[tone]
          }`}
        >
          {value}
        </span>

        {unit && !unavailable && (
          <span className="text-xs text-slate-500 dark:text-slate-400">
            {unit}
          </span>
        )}
      </div>

      {sub && (
        <div
          className={`mt-1 text-[11px] leading-4 ${
            unavailable
              ? "text-slate-400 dark:text-slate-500"
              : "text-slate-500 dark:text-slate-400"
          }`}
        >
          {sub}
        </div>
      )}
    </div>
  );
}
