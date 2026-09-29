export function formatNumber(
  value: number | null | undefined,
  digits = 2,
): string {
  if (value === null || value === undefined) {
    return "—";
  }

  if (!Number.isFinite(Number(value))) {
    return "—";
  }

  return Number(value).toFixed(digits);
}

export function formatInteger(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "0";
  }

  if (!Number.isFinite(Number(value))) {
    return "0";
  }

  return Math.round(Number(value)).toLocaleString();
}

export function formatPercentage(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "0%";
  }

  if (!Number.isFinite(Number(value))) {
    return "0%";
  }

  return `${Number(value).toFixed(1)}%`;
}

export function getAnomalyScoreTone(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "text-slate-500 dark:text-slate-400";
  }

  const score = Number(value);

  if (score >= 0.8) {
    return "text-red-600 dark:text-red-400";
  }

  if (score >= 0.5) {
    return "text-amber-600 dark:text-amber-400";
  }

  return "text-emerald-600 dark:text-emerald-400";
}
