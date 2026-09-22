import type { ReactNode } from "react";

interface MetricProps {
  label: string;
  value: string | number;
  detail?: string;
  icon?: ReactNode;
  accent?: "default" | "blue" | "amber" | "red" | "green";
}

const accentStyles = {
  default: {
    value: "text-slate-950 dark:text-white",
    icon: "text-slate-500 dark:text-slate-400",
  },
  blue: {
    value: "text-blue-700 dark:text-blue-400",
    icon: "text-blue-600 dark:text-blue-400",
  },
  amber: {
    value: "text-amber-700 dark:text-amber-400",
    icon: "text-amber-600 dark:text-amber-400",
  },
  red: {
    value: "text-red-700 dark:text-red-400",
    icon: "text-red-600 dark:text-red-400",
  },
  green: {
    value: "text-emerald-700 dark:text-emerald-400",
    icon: "text-emerald-600 dark:text-emerald-400",
  },
};

export default function Metric({
  label,
  value,
  detail,
  icon,
  accent = "default",
}: MetricProps) {
  const styles = accentStyles[accent];

  return (
    <div className="group border-l border-slate-200 pl-5 dark:border-slate-800">
      <div className="flex items-center gap-2">
        {icon && <span className={styles.icon}>{icon}</span>}

        <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">
          {label}
        </p>
      </div>

      <p
        className={`mt-2 text-2xl font-semibold tracking-tight ${styles.value}`}
      >
        {value}
      </p>

      {detail && (
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          {detail}
        </p>
      )}
    </div>
  );
}
