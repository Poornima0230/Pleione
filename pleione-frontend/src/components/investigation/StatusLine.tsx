import type { ReactNode } from "react";

type StatusLineProps = {
  label: string;
  value: ReactNode;
};

export default function StatusLine({ label, value }: StatusLineProps) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-slate-200 py-2.5 last:border-b-0 dark:border-slate-800/80">
      <span className="text-xs text-slate-500 dark:text-slate-400">
        {label}
      </span>

      <span className="text-right text-xs font-medium text-slate-800 dark:text-slate-200">
        {value}
      </span>
    </div>
  );
}
