export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }

  return Number(value).toLocaleString("en-US");
}

export function formatDecimal(
  value: number | null | undefined,
  digits = 2,
): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }

  return Number(value).toFixed(digits);
}

export function formatCurrent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }

  return `${Number(value).toFixed(2)} µA`;
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }

  return `${(Number(value) * 100).toFixed(1)}%`;
}

export function formatDrift(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }

  const number = Number(value);

  return `${number >= 0 ? "+" : ""}${number.toFixed(2)} µA`;
}

export function toBoolean(value: unknown): boolean {
  if (typeof value === "boolean") {
    return value;
  }

  if (typeof value === "number") {
    return value !== 0;
  }

  if (typeof value === "string") {
    return ["true", "1", "yes", "y", "detected"].includes(
      value.trim().toLowerCase(),
    );
  }

  return false;
}

export function riskClass(risk: string | null | undefined): string {
  switch (String(risk ?? "").toUpperCase()) {
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

export function statusClass(status: string | null | undefined): string {
  const value = String(status ?? "").toUpperCase();

  if (value.includes("FAILURE") || value.includes("EXCEEDED")) {
    return "text-red-600 dark:text-red-400";
  }

  if (value.includes("DRIFT") || value.includes("RISK")) {
    return "text-amber-600 dark:text-amber-400";
  }

  return "text-emerald-600 dark:text-emerald-400";
}
