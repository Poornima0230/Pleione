import type { ReactNode } from "react";

type ReasonProps = {
  number: string;
  title: ReactNode;
  detail: ReactNode;
};

export default function Reason({ number, title, detail }: ReasonProps) {
  return (
    <div className="grid grid-cols-[26px_1fr] gap-3">
      <div className="pt-0.5 text-[9px] font-semibold tracking-[0.12em] text-slate-400 dark:text-slate-600">
        {number}
      </div>

      <div className="min-w-0">
        <div className="text-[13px] font-semibold leading-5 text-slate-800 dark:text-slate-200">
          {title}
        </div>

        <div className="mt-1.5 text-[11px] leading-[1.55] text-slate-500 dark:text-slate-400">
          {detail}
        </div>
      </div>
    </div>
  );
}
