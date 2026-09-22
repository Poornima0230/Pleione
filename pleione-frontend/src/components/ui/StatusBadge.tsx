import type { ReactNode } from "react";

type StatusVariant =
  | "pass"
  | "review"
  | "reject"
  | "critical"
  | "high"
  | "medium"
  | "normal"
  | "neutral";

interface StatusBadgeProps {
  status: string;
  variant?: StatusVariant;
  icon?: ReactNode;
  className?: string;
}

const variantStyles: Record<StatusVariant, string> = {
  pass: "border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-400",

  review:
    "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-400",

  reject:
    "border-red-200 bg-red-50 text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-400",

  critical:
    "border-red-200 bg-red-50 text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-400",

  high: "border-orange-200 bg-orange-50 text-orange-700 dark:border-orange-900/60 dark:bg-orange-950/40 dark:text-orange-400",

  medium:
    "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-400",

  normal:
    "border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300",

  neutral:
    "border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300",
};

export default function StatusBadge({
  status,
  variant = "neutral",
  icon,
  className = "",
}: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex w-fit items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-medium leading-none ${variantStyles[variant]} ${className}`}
    >
      {icon && (
        <span className="flex h-3.5 w-3.5 items-center justify-center">
          {icon}
        </span>
      )}

      <span>{status}</span>
    </span>
  );
}
