import { pct } from "./utils";

type RiskFactorProps = {
  label: string;
  value: number;
  strongest?: boolean;
};

export default function RiskFactor({
  label,
  value,
  strongest = false,
}: RiskFactorProps) {
  const safeValue = Number.isFinite(value)
    ? Math.max(0, Math.min(1, value))
    : 0;

  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between gap-3">
        <span
          className={`text-xs ${
            strongest
              ? "font-medium text-violet-600 dark:text-violet-300"
              : "text-slate-500 dark:text-slate-400"
          }`}
        >
          {label}
        </span>

        <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
          {pct(value)}
        </span>
      </div>

      <div className="h-1.5 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
        <div
          className={`h-full rounded-full ${
            strongest ? "bg-violet-500" : "bg-slate-400 dark:bg-slate-500"
          }`}
          style={{
            width: `${safeValue * 100}%`,
          }}
        />
      </div>
    </div>
  );
}
