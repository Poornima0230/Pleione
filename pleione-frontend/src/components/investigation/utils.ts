export type ScreeningDecision = "PASS" | "REVIEW" | "REJECT";

/* ----------------------------- */
/* Number helper                  */
/* ----------------------------- */

export function num(value: unknown): number | null {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const parsed = Number(value);

  return Number.isFinite(parsed) ? parsed : null;
}

/* ----------------------------- */
/* Number formatting              */
/* ----------------------------- */

export function fmt(value: unknown, digits = 2): string {
  const parsed = num(value);

  if (parsed === null) {
    return "—";
  }

  return parsed.toFixed(digits);
}

/* ----------------------------- */
/* Percentage formatting         */
/* ----------------------------- */

export function pct(value: unknown): string {
  const parsed = num(value);

  if (parsed === null) {
    return "0%";
  }

  return `${Math.round(parsed)}%`;
}

/* ----------------------------- */
/* Display-only non-negative     */
/* ----------------------------- */

export function displayNonNegative(value: unknown): number | null {
  const parsed = num(value);

  if (parsed === null) {
    return null;
  }

  return Math.max(0, parsed);
}

/* ----------------------------- */
/* Boolean helper                */
/* ----------------------------- */

export function bool(value: unknown): boolean {
  if (typeof value === "boolean") {
    return value;
  }

  if (typeof value === "number") {
    return value === 1;
  }

  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();

    return (
      normalized === "true" ||
      normalized === "1" ||
      normalized === "yes" ||
      normalized === "detected"
    );
  }

  return false;
}

/* ----------------------------- */
/* Decision normalization        */
/* ----------------------------- */

export function normalizeDecision(decision: unknown): ScreeningDecision {
  const value = String(decision ?? "")
    .trim()
    .toUpperCase();

  /*
   * REJECT
   */
  if (value === "REJECT" || value === "FAIL" || value === "IMMEDIATE_REVIEW") {
    return "REJECT";
  }

  /*
   * REVIEW
   */
  if (
    value === "REVIEW" ||
    value === "MONITOR" ||
    value === "ENHANCED_MONITORING" ||
    value === "PRIORITY_SCREENING"
  ) {
    return "REVIEW";
  }

  /*
   * PASS
   */
  return "PASS";
}

/* ----------------------------- */
/* Decision tone                 */
/* ----------------------------- */

export function toneForDecision(
  decision: ScreeningDecision,
): "green" | "amber" | "red" {
  if (decision === "REJECT") {
    return "red";
  }

  if (decision === "REVIEW") {
    return "amber";
  }

  return "green";
}

/* ----------------------------- */
/* Risk tone                     */
/* ----------------------------- */

export function toneForRisk(
  risk: unknown,
): "green" | "amber" | "red" | "neutral" {
  const value = String(risk ?? "")
    .trim()
    .toUpperCase();

  if (value === "CRITICAL" || value === "HIGH") {
    return "red";
  }

  if (value === "MEDIUM" || value === "MODERATE") {
    return "amber";
  }

  if (value === "LOW" || value === "NORMAL") {
    return "green";
  }

  return "neutral";
}
