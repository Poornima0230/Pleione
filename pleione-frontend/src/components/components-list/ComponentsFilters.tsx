"use client";

import type { ComponentsFiltersProps } from "./types";

export default function ComponentsFilters({
  componentId,
  lotId,
  componentType,
  decision,
  lots,
  componentTypes,
  onComponentIdChange,
  onLotChange,
  onComponentTypeChange,
  onDecisionChange,
  onClear,
  hasFilters,
}: ComponentsFiltersProps) {
  return (
    <section className="mb-5 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-col gap-3 p-4 xl:flex-row xl:items-center">
        {/* Component search */}
        <div className="relative min-w-0 flex-1 xl:max-w-[310px]">
          <svg
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-4-4" />
          </svg>

          <input
            value={componentId}
            onChange={(event) => onComponentIdChange(event.target.value)}
            placeholder="Search component ID"
            className="h-10 w-full rounded-lg border border-slate-200 bg-slate-50 pl-9 pr-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-slate-400 dark:border-white/[0.08] dark:bg-white/[0.025] dark:placeholder:text-slate-500 dark:focus:border-white/20"
          />
        </div>

        {/* Lot */}
        <select
          value={lotId}
          onChange={(event) => onLotChange(event.target.value)}
          className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-[#020618] dark:text-slate-200"
        >
          <option
            value=""
            className="bg-white text-slate-700 dark:bg-[#020618] dark:text-slate-200"
          >
            All lots
          </option>

          {lots.map((lot) => (
            <option
              key={lot}
              value={lot}
              className="bg-white text-slate-700 dark:bg-[#020618] dark:text-slate-200"
            >
              {lot}
            </option>
          ))}
        </select>

        {/* Component Type */}
        <select
          value={componentType}
          onChange={(event) => onComponentTypeChange(event.target.value)}
          className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-[#020618] dark:text-slate-200"
        >
          <option
            value=""
            className="bg-white text-slate-700 dark:bg-[#020618] dark:text-slate-200"
          >
            All types
          </option>

          {componentTypes.map((type) => (
            <option
              key={type}
              value={type}
              className="bg-white text-slate-700 dark:bg-[#020618] dark:text-slate-200"
            >
              {type}
            </option>
          ))}
        </select>

        {/* Decision */}
        <select
          value={decision}
          onChange={(event) => onDecisionChange(event.target.value)}
          className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-[#020618] dark:text-slate-200"
        >
          <option
            value=""
            className="bg-white text-slate-700 dark:bg-[#020618] dark:text-slate-200"
          >
            All decisions
          </option>

          <option
            value="PASS"
            className="bg-white text-slate-700 dark:bg-[#020618] dark:text-slate-200"
          >
            PASS
          </option>

          <option
            value="REVIEW"
            className="bg-white text-slate-700 dark:bg-[#020618] dark:text-slate-200"
          >
            REVIEW
          </option>

          <option
            value="REJECT"
            className="bg-white text-slate-700 dark:bg-[#020618] dark:text-slate-200"
          >
            REJECT
          </option>
        </select>

        {hasFilters ? (
          <button
            onClick={onClear}
            className="h-10 rounded-lg px-3 text-sm text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/[0.05] dark:hover:text-white"
          >
            Clear filters
          </button>
        ) : null}
      </div>
    </section>
  );
}
