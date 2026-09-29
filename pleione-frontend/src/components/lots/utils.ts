import type { Lot } from "./types";

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`;
}

export function formatScore(value: number): string {
  return value.toFixed(2);
}

export function getTotalComponents(lots: Lot[]): number {
  return lots.reduce(
    (total, lot) => total + Number(lot.component_count || 0),
    0,
  );
}

export function getTotalAnomalies(lots: Lot[]): number {
  return lots.reduce((total, lot) => total + Number(lot.anomaly_count || 0), 0);
}

export function getOverallAnomalyRate(lots: Lot[]): number {
  const components = getTotalComponents(lots);
  const anomalies = getTotalAnomalies(lots);

  if (components === 0) return 0;

  return (anomalies / components) * 100;
}
