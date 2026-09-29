import type { ReactNode } from "react";

import type { Tone } from "./types";

type BadgeProps = {
  children: ReactNode;
  tone?: Tone;
};

export default function Badge({ children, tone = "neutral" }: BadgeProps) {
  const styles: Record<Tone, string> = {
    green:
      "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",

    amber:
      "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400",

    red: "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400",

    neutral:
      "border-slate-200 bg-slate-100 text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.1em] ${styles[tone]}`}
    >
      {children}
    </span>
  );
}
