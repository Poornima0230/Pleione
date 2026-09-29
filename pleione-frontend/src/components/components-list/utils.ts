import type { ScreeningDecision } from "./types";

export const PAGE_SIZE = 25;

export function formatNumber(value: number | undefined | null, digits = 2) {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "—";
  }

  return value.toFixed(digits);
}

export function isAnomaly(value: number | boolean) {
  return value === true || value === 1;
}

/**
 * Convert backend screening decisions into
 * the three decisions shown in the UI.
 *
 * Backend:
 * NORMAL              -> PASS
 * MONITOR             -> REVIEW
 * ENHANCED_MONITORING -> REVIEW
 * PRIORITY_SCREENING  -> REVIEW
 * IMMEDIATE_REVIEW    -> REJECT
 * REJECT              -> REJECT
 * FAIL                -> REJECT
 */
export function normalizeDecision(value?: string | null): ScreeningDecision {
  const decision = String(value ?? "")
    .trim()
    .toUpperCase();

  if (
    decision === "REJECT" ||
    decision === "FAIL" ||
    decision === "IMMEDIATE_REVIEW"
  ) {
    return "REJECT";
  }

  if (
    decision === "REVIEW" ||
    decision === "MONITOR" ||
    decision === "ENHANCED_MONITORING" ||
    decision === "PRIORITY_SCREENING"
  ) {
    return "REVIEW";
  }

  return "PASS";
}

export function decisionClass(decision: ScreeningDecision) {
  switch (decision) {
    case "REJECT":
      return "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400";

    case "REVIEW":
      return "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400";

    case "PASS":
      return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400";

    default:
      return "border-slate-300 bg-slate-100 text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300";
  }
}

export function riskClass(level?: string | null) {
  switch ((level || "").toUpperCase()) {
    case "CRITICAL":
      return "text-red-600 dark:text-red-400";

    case "HIGH":
      return "text-orange-600 dark:text-orange-400";

    case "MEDIUM":
      return "text-amber-600 dark:text-amber-400";

    case "LOW":
      return "text-emerald-600 dark:text-emerald-400";

    default:
      return "text-slate-600 dark:text-slate-300";
  }
}

export function getPageNumbers(page: number, totalPages: number) {
  const pages: number[] = [];

  const start = Math.max(1, page - 2);
  const end = Math.min(totalPages, page + 2);

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  return pages;
}
