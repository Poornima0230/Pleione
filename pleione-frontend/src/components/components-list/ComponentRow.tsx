"use client";

import Link from "next/link";

import type { ComponentRow as ComponentRowType } from "./types";

import { decisionClass, formatNumber, riskClass } from "./utils";

type Props = {
  component: ComponentRowType;
};

function moduleAClass(status: string) {
  switch (status?.toUpperCase()) {
    case "ANOMALOUS":
      return "text-red-600 dark:text-red-400";
    case "WATCH":
      return "text-amber-600 dark:text-amber-400";
    default:
      return "text-slate-500 dark:text-slate-400";
  }
}

function moduleAIndicator(status: string) {
  switch (status?.toUpperCase()) {
    case "ANOMALOUS":
      return "bg-red-500";
    case "WATCH":
      return "bg-amber-500";
    default:
      return "bg-slate-300 dark:bg-slate-600";
  }
}

function futureRiskClass(risk: string) {
  switch (risk?.toUpperCase()) {
    case "CRITICAL":
    case "HIGH":
      return riskClass(risk);
    case "MEDIUM":
      return "text-amber-600 dark:text-amber-400";
    case "LOW":
      return "text-emerald-600 dark:text-emerald-400";
    default:
      return "text-slate-500 dark:text-slate-400";
  }
}

export default function ComponentRow({ component }: Props) {
  const moduleAStatus = component.module_a_status?.toUpperCase() || "NORMAL";

  const futureRisk = component.future_risk?.toUpperCase() || "LOW";

  const currentDecision = component.final_decision || "PASS";

  const probability = component.failure_probability ?? null;

  return (
    <div className="grid grid-cols-[1.45fr_0.75fr_0.95fr_1fr_1.05fr_1.05fr_0.9fr_80px] items-center gap-3 px-5 py-4 transition hover:bg-slate-50 dark:hover:bg-white/[0.025]">
      {/* Component */}
      <div className="min-w-0">
        <Link
          href={`/components/${encodeURIComponent(component.component_id)}`}
          className="group inline-flex items-center gap-2"
        >
          <span
            className={`h-1.5 w-1.5 rounded-full transition group-hover:bg-emerald-500 ${moduleAIndicator(
              moduleAStatus,
            )}`}
          />

          <span className="truncate text-sm font-medium text-slate-900 group-hover:text-emerald-600 dark:text-slate-100 dark:group-hover:text-emerald-400">
            {component.component_id}
          </span>
        </Link>
      </div>

      {/* Lot */}
      <div className="text-sm text-slate-500 dark:text-slate-400">
        {component.lot_id}
      </div>

      {/* Type */}
      <div className="truncate text-sm text-slate-500 dark:text-slate-400">
        {component.component_type}
      </div>

      {/* 0H IDDQ */}
      <div>
        <span className="font-mono text-sm text-slate-800 dark:text-slate-200">
          {formatNumber(component.iddq_0h_uA)}
        </span>

        <span className="ml-1 text-[11px] text-slate-400">µA</span>
      </div>

      {/* Module A */}
      <div>
        <div
          className={`inline-flex items-center gap-1.5 text-sm font-medium ${moduleAClass(
            moduleAStatus,
          )}`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full ${moduleAIndicator(
              moduleAStatus,
            )}`}
          />

          {moduleAStatus}
        </div>

        <div className="mt-0.5 text-[10px] uppercase tracking-wider text-slate-400">
          {component.peer_source || "UNKNOWN"}
        </div>
      </div>

      {/* Future Risk */}
      <div>
        <div className={`text-sm font-medium ${futureRiskClass(futureRisk)}`}>
          {futureRisk}
        </div>

        <div className="mt-0.5 text-[10px] text-slate-400">
          {probability !== null
            ? `${formatNumber(probability * 100, 1)}% probability`
            : "Probability unavailable"}
        </div>
      </div>

      {/* Decision */}
      <div>
        <span
          className={`inline-flex rounded-md border px-2 py-1 text-[10px] font-semibold tracking-[0.08em] ${decisionClass(
            currentDecision,
          )}`}
        >
          {currentDecision}
        </span>
      </div>

      {/* Inspect */}
      <div className="flex justify-end">
        <Link
          href={`/components/${encodeURIComponent(component.component_id)}`}
          className="inline-flex h-8 items-center justify-center rounded-md border border-slate-200 px-2.5 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 dark:border-white/[0.08] dark:text-slate-400 dark:hover:border-white/15 dark:hover:bg-white/[0.04] dark:hover:text-white"
        >
          Inspect
        </Link>
      </div>
    </div>
  );
}
