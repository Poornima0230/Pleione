"use client";

import type { ComponentRow } from "./types";
import ComponentRowItem from "./ComponentRow";

type Props = {
  components: ComponentRow[];
  loading: boolean;
};

function LoadingRows() {
  return (
    <div className="divide-y divide-slate-200 dark:divide-white/[0.06]">
      {Array.from({ length: 8 }).map((_, index) => (
        <div
          key={index}
          className="grid grid-cols-[1.45fr_0.75fr_0.95fr_1fr_1.05fr_1.05fr_0.9fr_80px] gap-3 px-5 py-4"
        >
          {Array.from({ length: 8 }).map((__, cell) => (
            <div
              key={cell}
              className="h-4 animate-pulse rounded bg-slate-200 dark:bg-white/[0.06]"
            />
          ))}
        </div>
      ))}
    </div>
  );
}

export default function ComponentsTable({ components, loading }: Props) {
  return (
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="w-full overflow-x-auto">
        <div className="min-w-[1080px]">
          {/* Header */}
          <div className="grid grid-cols-[1.45fr_0.75fr_0.95fr_1fr_1.05fr_1.05fr_0.9fr_80px] gap-3 border-b border-slate-200 bg-slate-50/70 px-5 py-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-400 dark:border-white/[0.06] dark:bg-white/[0.015]">
            <div>Component</div>
            <div>Lot</div>
            <div>Type</div>
            <div>0H IDDQ</div>
            <div>Module A</div>
            <div>Future Risk</div>
            <div>Decision</div>
            <div />
          </div>

          {/* Loading */}
          {loading ? (
            <LoadingRows />
          ) : components.length === 0 ? (
            <div className="flex min-h-[280px] items-center justify-center px-5">
              <div className="text-center">
                <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 dark:border-white/10">
                  <svg
                    className="h-5 w-5 text-slate-400"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.6"
                  >
                    <circle cx="11" cy="11" r="7" />
                    <path d="m20 20-4-4" />
                  </svg>
                </div>

                <p className="text-sm font-medium">No components found</p>

                <p className="mt-1 text-xs text-slate-400">
                  Try changing or clearing your filters.
                </p>
              </div>
            </div>
          ) : (
            <div className="divide-y divide-slate-200 dark:divide-white/[0.06]">
              {components.map((component) => (
                <ComponentRowItem
                  key={component.component_id}
                  component={component}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
