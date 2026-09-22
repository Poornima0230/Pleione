"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { getReportSummary } from "@/lib/api";

type ScreeningSummary = {
  components?: number;
  lots?: number;
  pass_count?: number;
  review_count?: number;
  reject_count?: number;
  pass_rate?: number;
  review_rate?: number;
  reject_rate?: number;
};

type ReliabilitySummary = {
  active_anomalies?: number;
  anomaly_rate?: number;
  latent_risk?: number;
  critical?: number;
  high?: number;
  medium?: number;
  average_risk?: number;
};

type ForecastSummary = {
  predicted_over_limit?: number;
  upper_interval_over_limit?: number;
  assessment?: string;
};

type LotFinding = {
  lot_id?: string;
  components?: number;
  anomaly_count?: number;
  anomaly_rate?: number;
  latent_risk_count?: number;
  critical_count?: number;
  high_count?: number;
  average_risk?: number;
  finding?: string;
};

type PriorityComponent = {
  component_id?: string;
  lot_id?: string;
  severity?: string;
  current_anomaly_level?: string;
  latent_risk?: boolean | string;
  screening_status?: string;
  risk_score?: number;
  final_risk_level?: string;
  final_decision?: string;
  predicted_168h_uA?: number;
  absolute_limit_uA?: number;
  predicted_limit_utilization_percent?: number;
  upper_limit_utilization_percent?: number;
  future_drift_risk?: string;
  primary_risk_driver?: string;
  evidence_summary?: string;
  explanation?: string;
};

type Report = {
  report_id?: string;
  run_id?: string;
  problem_statement?: string;
  title?: string;
  status?: string;
  duration?: string;
  generated_from?: {
    dataset?: string;
    anomaly_results?: string;
    prediction_results?: string;
    explanation_results?: string;
  };
  screening_summary?: ScreeningSummary;
  reliability_summary?: ReliabilitySummary;
  forecast_summary?: ForecastSummary;
  overall_assessment?: string;
  recommended_action?: string;
  measurement_points?: string[];
  detection_engine?: string;
  prediction_engine?: string;
  lot_findings?: LotFinding[];
  priority_components?: PriorityComponent[];
};

export default function ReportsPage() {
  const [report, setReport] = useState<Report | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [selectedComponent, setSelectedComponent] =
    useState<PriorityComponent | null>(null);

  useEffect(() => {
    async function loadReport() {
      try {
        setLoading(true);
        setError("");

        const result = await getReportSummary();

        // setReport(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load report");
      } finally {
        setLoading(false);
      }
    }

    loadReport();
  }, []);

  const screening = report?.screening_summary;

  const reliability = report?.reliability_summary;

  const forecast = report?.forecast_summary;

  const priorityComponents = report?.priority_components ?? [];

  const lotFindings = report?.lot_findings ?? [];

  const visiblePriorityComponents = useMemo(
    () => priorityComponents.slice(0, 8),
    [priorityComponents],
  );

  if (loading) {
    return (
      <main className="min-h-screen bg-[#f4f4f1] px-8 py-8">
        <div className="mx-auto max-w-[1500px]">
          <div className="text-[10px] uppercase tracking-[0.3em] text-black/30">
            Report Center
          </div>

          <div className="mt-3 h-10 w-80 animate-pulse bg-black/10" />

          <div className="mt-8 grid grid-cols-4 gap-px border border-black/10 bg-black/10">
            {[1, 2, 3, 4].map((item) => (
              <div key={item} className="h-32 animate-pulse bg-[#f4f4f1]" />
            ))}
          </div>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-[#f4f4f1] px-8 py-8">
        <div className="mx-auto max-w-[1500px]">
          <div className="border border-red-500/30 bg-red-500/5 p-8">
            <div className="text-[10px] uppercase tracking-[0.25em] text-red-600">
              Report Error
            </div>

            <div className="mt-3 text-sm text-black/70">{error}</div>
          </div>
        </div>
      </main>
    );
  }

  if (!report) {
    return (
      <main className="min-h-screen bg-[#f4f4f1] px-8 py-8">
        <div className="mx-auto max-w-[1500px]">
          <div className="border border-black/10 p-12 text-center">
            <div className="text-sm">No report available.</div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#f4f4f1] text-[#111]">
      <div className="mx-auto max-w-[1500px] px-8 py-8">
        {/* HEADER */}

        <section className="border-b border-black/10 pb-7">
          <div className="flex items-end justify-between">
            <div>
              <div className="text-[10px] uppercase tracking-[0.3em] text-black/40">
                Engineering Report Center
              </div>

              <h1 className="mt-2 text-3xl font-semibold tracking-tight">
                Screening Report
              </h1>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-black/50">
                Consolidated reliability assessment generated from the Pleione
                burn-in screening pipeline.
              </p>
            </div>

            <div className="text-right">
              <div className="text-[10px] uppercase tracking-[0.25em] text-black/35">
                Report ID
              </div>

              <div className="mt-2 font-mono text-sm">{report.report_id}</div>
            </div>
          </div>

          <div className="mt-6 flex items-center gap-8 text-xs">
            <div>
              <span className="text-black/35">RUN</span>

              <span className="ml-2 font-mono">{report.run_id}</span>
            </div>

            <div>
              <span className="text-black/35">PROBLEM</span>

              <span className="ml-2 font-mono">{report.problem_statement}</span>
            </div>

            <div>
              <span className="text-black/35">DURATION</span>

              <span className="ml-2 font-mono">{report.duration}</span>
            </div>

            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />

              <span className="uppercase tracking-[0.15em]">
                {report.status}
              </span>
            </div>
          </div>
        </section>

        {/* EXECUTIVE SUMMARY */}

        <section className="mt-8">
          <SectionLabel>Executive Summary</SectionLabel>

          <div className="mt-3 grid grid-cols-4 gap-px border border-black/10 bg-black/10">
            <MetricCard
              label="Components"
              value={formatNumber(screening?.components)}
            />

            <MetricCard label="Lots" value={formatNumber(screening?.lots)} />

            <MetricCard
              label="Active Anomalies"
              value={formatNumber(reliability?.active_anomalies)}
            />

            <MetricCard
              label="Latent Risk"
              value={formatNumber(reliability?.latent_risk)}
            />
          </div>
        </section>

        {/* SCREENING DISPOSITION */}

        <section className="mt-8">
          <SectionLabel>Screening Disposition</SectionLabel>

          <div className="mt-3 border border-black/10 bg-white/40 p-6">
            <div className="grid grid-cols-3 gap-8">
              <Disposition
                label="PASS"
                value={screening?.pass_count}
                percentage={screening?.pass_rate}
              />

              <Disposition
                label="REVIEW"
                value={screening?.review_count}
                percentage={screening?.review_rate}
              />

              <Disposition
                label="REJECT"
                value={screening?.reject_count}
                percentage={screening?.reject_rate}
              />
            </div>

            <div className="mt-8 h-3 flex overflow-hidden bg-black/10">
              <div
                className="bg-emerald-500/70"
                style={{
                  width: `${screening?.pass_rate ?? 0}%`,
                }}
              />

              <div
                className="bg-amber-500/70"
                style={{
                  width: `${screening?.review_rate ?? 0}%`,
                }}
              />

              <div
                className="bg-red-500/70"
                style={{
                  width: `${screening?.reject_rate ?? 0}%`,
                }}
              />
            </div>
          </div>
        </section>

        {/* ENGINEERING ASSESSMENT */}

        <section className="mt-8 grid grid-cols-2 gap-6">
          <div>
            <SectionLabel>Overall Assessment</SectionLabel>

            <div className="mt-3 border border-black/10 bg-white/40 p-7">
              <div className="text-[10px] uppercase tracking-[0.2em] text-black/35">
                Reliability Finding
              </div>

              <p className="mt-4 text-sm leading-7 text-black/70">
                {report.overall_assessment}
              </p>
            </div>
          </div>

          <div>
            <SectionLabel>Recommended Action</SectionLabel>

            <div className="mt-3 border border-black/10 bg-white/40 p-7">
              <div className="text-[10px] uppercase tracking-[0.2em] text-black/35">
                Engineering Disposition
              </div>

              <p className="mt-4 text-sm leading-7 text-black/70">
                {report.recommended_action}
              </p>
            </div>
          </div>
        </section>

        {/* RELIABILITY PROFILE */}

        <section className="mt-8">
          <SectionLabel>Reliability Profile</SectionLabel>

          <div className="mt-3 grid grid-cols-5 gap-px border border-black/10 bg-black/10">
            <ProfileMetric
              label="Anomaly Rate"
              value={formatPercent(reliability?.anomaly_rate)}
            />

            <ProfileMetric
              label="Critical"
              value={formatNumber(reliability?.critical)}
            />

            <ProfileMetric
              label="High"
              value={formatNumber(reliability?.high)}
            />

            <ProfileMetric
              label="Medium"
              value={formatNumber(reliability?.medium)}
            />

            <ProfileMetric
              label="Average Risk"
              value={formatRisk(reliability?.average_risk)}
            />
          </div>
        </section>

        {/* FORECAST */}

        <section className="mt-8">
          <SectionLabel>168H Forecast Assessment</SectionLabel>

          <div className="mt-3 grid grid-cols-3 gap-px border border-black/10 bg-black/10">
            <ForecastMetric
              label="Predicted Over Limit"
              value={formatNumber(forecast?.predicted_over_limit)}
            />

            <ForecastMetric
              label="Upper Interval Over Limit"
              value={formatNumber(forecast?.upper_interval_over_limit)}
            />

            <div className="bg-[#f4f4f1] p-6">
              <div className="text-[10px] uppercase tracking-[0.2em] text-black/35">
                Forecast Finding
              </div>

              <div className="mt-3 text-sm leading-6 text-black/65">
                {forecast?.assessment}
              </div>
            </div>
          </div>
        </section>

        {/* LOT FINDINGS */}

        <section className="mt-8">
          <SectionLabel>Lot-Level Findings</SectionLabel>

          <div className="mt-3 overflow-hidden border border-black/10 bg-white/30">
            <table className="w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-black/10 text-[10px] uppercase tracking-[0.18em] text-black/35">
                  <th className="px-5 py-4">Lot</th>

                  <th className="px-5 py-4">Components</th>

                  <th className="px-5 py-4">Anomaly Rate</th>

                  <th className="px-5 py-4">Latent Risk</th>

                  <th className="px-5 py-4">Critical</th>

                  <th className="px-5 py-4">Avg Risk</th>

                  <th className="px-5 py-4">Finding</th>
                </tr>
              </thead>

              <tbody>
                {lotFindings.map((lot) => (
                  <tr
                    key={lot.lot_id}
                    className="border-b border-black/5 last:border-0"
                  >
                    <td className="px-5 py-4 font-mono text-xs">
                      {lot.lot_id}
                    </td>

                    <td className="px-5 py-4 font-mono text-xs">
                      {formatNumber(lot.components)}
                    </td>

                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div className="h-1.5 w-20 bg-black/10">
                          <div
                            className="h-full bg-black"
                            style={{
                              width: `${Math.min(
                                Math.max(lot.anomaly_rate ?? 0, 0),
                                100,
                              )}%`,
                            }}
                          />
                        </div>

                        <span className="font-mono text-xs">
                          {formatPercent(lot.anomaly_rate)}
                        </span>
                      </div>
                    </td>

                    <td className="px-5 py-4 font-mono text-xs">
                      {formatNumber(lot.latent_risk_count)}
                    </td>

                    <td className="px-5 py-4 font-mono text-xs">
                      {formatNumber(lot.critical_count)}
                    </td>

                    <td className="px-5 py-4 font-mono text-xs">
                      {formatRisk(lot.average_risk)}
                    </td>

                    <td className="max-w-sm px-5 py-4 text-xs leading-5 text-black/55">
                      {lot.finding}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* PRIORITY REGISTER */}

        <section className="mt-8">
          <div className="flex items-end justify-between">
            <SectionLabel>Priority Components</SectionLabel>

            <div className="text-[10px] uppercase tracking-[0.18em] text-black/30">
              Top {visiblePriorityComponents.length}
            </div>
          </div>

          <div className="mt-3 overflow-hidden border border-black/10 bg-white/30">
            <table className="w-full border-collapse text-left">
              <thead>
                <tr className="border-b border-black/10 text-[10px] uppercase tracking-[0.18em] text-black/35">
                  <th className="px-5 py-4">Component</th>

                  <th className="px-5 py-4">Lot</th>

                  <th className="px-5 py-4">Severity</th>

                  <th className="px-5 py-4">Risk</th>

                  <th className="px-5 py-4">Forecast</th>

                  <th className="px-5 py-4">Driver</th>

                  <th className="px-5 py-4">Decision</th>
                </tr>
              </thead>

              <tbody>
                {visiblePriorityComponents.map((component) => (
                  <tr
                    key={component.component_id}
                    className="border-b border-black/5 transition last:border-0 hover:bg-black/[0.02]"
                  >
                    <td className="px-5 py-4">
                      <Link
                        href={`/components/${component.component_id}`}
                        className="font-mono text-xs font-semibold hover:underline"
                      >
                        {component.component_id}
                      </Link>
                    </td>

                    <td className="px-5 py-4 font-mono text-xs text-black/55">
                      {component.lot_id ?? "—"}
                    </td>

                    <td className="px-5 py-4">
                      <RiskBadge
                        value={component.final_risk_level ?? component.severity}
                      />
                    </td>

                    <td className="px-5 py-4">
                      <RiskScore value={component.risk_score} />
                    </td>

                    <td className="px-5 py-4">
                      <div className="text-xs">
                        {component.predicted_168h_uA !== undefined &&
                        component.predicted_168h_uA !== null
                          ? `${component.predicted_168h_uA.toFixed(2)} µA`
                          : "—"}
                      </div>

                      <div className="mt-1 text-[10px] text-black/35">
                        {component.predicted_limit_utilization_percent !==
                          undefined &&
                        component.predicted_limit_utilization_percent !== null
                          ? `${component.predicted_limit_utilization_percent.toFixed(1)}% limit`
                          : "No forecast"}
                      </div>
                    </td>

                    <td className="max-w-[220px] px-5 py-4 text-xs text-black/55">
                      {component.primary_risk_driver ?? "—"}
                    </td>

                    <td className="px-5 py-4">
                      <button
                        type="button"
                        onClick={() => setSelectedComponent(component)}
                        className="border border-black/15 px-3 py-1.5 text-[10px] uppercase tracking-[0.15em] transition hover:bg-black hover:text-white"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* ENGINE */}

        <section className="mt-8 grid grid-cols-2 gap-6">
          <div>
            <SectionLabel>Detection Architecture</SectionLabel>

            <div className="mt-3 border border-black/10 bg-white/40 p-6">
              <div className="text-sm leading-7 text-black/65">
                {report.detection_engine}
              </div>
            </div>
          </div>

          <div>
            <SectionLabel>Prediction Architecture</SectionLabel>

            <div className="mt-3 border border-black/10 bg-white/40 p-6">
              <div className="text-sm leading-7 text-black/65">
                {report.prediction_engine}
              </div>
            </div>
          </div>
        </section>

        {/* DATA PROVENANCE */}

        <section className="mt-8">
          <SectionLabel>Data Provenance</SectionLabel>

          <div className="mt-3 border border-black/10 bg-white/40 p-6">
            <div className="grid grid-cols-2 gap-x-12 gap-y-5">
              <SourceFile
                label="Screening Dataset"
                value={report.generated_from?.dataset}
              />

              <SourceFile
                label="Anomaly Results"
                value={report.generated_from?.anomaly_results}
              />

              <SourceFile
                label="Prediction Results"
                value={report.generated_from?.prediction_results}
              />

              <SourceFile
                label="Explainability Results"
                value={report.generated_from?.explanation_results}
              />
            </div>
          </div>
        </section>

        {/* MEASUREMENT PIPELINE */}

        <section className="mt-8">
          <SectionLabel>Measurement Timeline</SectionLabel>

          <div className="mt-3 border border-black/10 bg-white/40 p-7">
            <div className="flex items-center">
              {(report.measurement_points ?? ["0H", "24H", "96H", "168H"]).map(
                (point, index, array) => (
                  <div key={point} className="flex flex-1 items-center">
                    <div className="relative">
                      <div
                        className={`flex h-10 w-10 items-center justify-center border text-[10px] font-semibold ${
                          index === array.length - 1
                            ? "border-amber-500 bg-amber-500/10"
                            : "border-black/20 bg-white"
                        }`}
                      >
                        {index + 1}
                      </div>

                      <div className="absolute left-0 top-12 whitespace-nowrap text-[10px] uppercase tracking-[0.15em] text-black/40">
                        {point}
                      </div>
                    </div>

                    {index < array.length - 1 && (
                      <div className="mx-4 h-px flex-1 bg-black/15" />
                    )}
                  </div>
                ),
              )}
            </div>

            <div className="mt-16 grid grid-cols-4 gap-5">
              <PipelineStage
                number="01"
                title="OBSERVE"
                text="Capture screening measurements."
              />

              <PipelineStage
                number="02"
                title="DETECT"
                text="Identify abnormal behavior and drift."
              />

              <PipelineStage
                number="03"
                title="PREDICT"
                text="Estimate future limit proximity."
              />

              <PipelineStage
                number="04"
                title="DECIDE"
                text="Support engineering disposition."
              />
            </div>
          </div>
        </section>

        {/* FOOTER */}

        <footer className="mt-12 border-t border-black/10 py-6">
          <div className="flex items-center justify-between">
            <div className="text-[10px] uppercase tracking-[0.25em] text-black/30">
              Pleione Reliability Intelligence
            </div>

            <div className="font-mono text-[10px] text-black/30">
              ENGINEERING SCREENING REPORT
            </div>
          </div>
        </footer>
      </div>

      {/* INSPECTION DRAWER */}

      {selectedComponent && (
        <div className="fixed inset-0 z-[100]">
          <button
            type="button"
            aria-label="Close inspection"
            onClick={() => setSelectedComponent(null)}
            className="absolute inset-0 bg-black/30"
          />

          <aside className="absolute right-0 top-0 h-full w-[520px] overflow-y-auto border-l border-black/10 bg-[#f4f4f1] shadow-2xl">
            <div className="border-b border-black/10 px-7 py-6">
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-[10px] uppercase tracking-[0.25em] text-black/35">
                    Priority Component
                  </div>

                  <div className="mt-2 font-mono text-lg font-semibold">
                    {selectedComponent.component_id}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setSelectedComponent(null)}
                  className="text-xl text-black/35 hover:text-black"
                >
                  ×
                </button>
              </div>
            </div>

            <div className="space-y-7 px-7 py-7">
              <div className="grid grid-cols-2 gap-px border border-black/10 bg-black/10">
                <DrawerMetric
                  label="Lot"
                  value={selectedComponent.lot_id ?? "—"}
                />

                <DrawerMetric
                  label="Risk Score"
                  value={formatRisk(selectedComponent.risk_score)}
                />

                <DrawerMetric
                  label="Severity"
                  value={
                    selectedComponent.final_risk_level ??
                    selectedComponent.severity ??
                    "—"
                  }
                />

                <DrawerMetric
                  label="Decision"
                  value={
                    selectedComponent.final_decision ??
                    selectedComponent.screening_status ??
                    "—"
                  }
                />
              </div>

              <div>
                <DrawerLabel>Primary Risk Driver</DrawerLabel>

                <div className="mt-3 border border-black/10 bg-white/50 p-5 text-sm leading-6">
                  {selectedComponent.primary_risk_driver ??
                    "No driver available."}
                </div>
              </div>

              <div>
                <DrawerLabel>Forecast</DrawerLabel>

                <div className="mt-3 border border-black/10 bg-white/50 p-5">
                  <div className="grid grid-cols-2 gap-5">
                    <DrawerValue
                      label="Predicted 168H"
                      value={
                        selectedComponent.predicted_168h_uA !== undefined &&
                        selectedComponent.predicted_168h_uA !== null
                          ? `${selectedComponent.predicted_168h_uA.toFixed(2)} µA`
                          : "—"
                      }
                    />

                    <DrawerValue
                      label="Absolute Limit"
                      value={
                        selectedComponent.absolute_limit_uA !== undefined &&
                        selectedComponent.absolute_limit_uA !== null
                          ? `${selectedComponent.absolute_limit_uA.toFixed(2)} µA`
                          : "—"
                      }
                    />

                    <DrawerValue
                      label="Predicted Utilization"
                      value={
                        selectedComponent.predicted_limit_utilization_percent !==
                          undefined &&
                        selectedComponent.predicted_limit_utilization_percent !==
                          null
                          ? `${selectedComponent.predicted_limit_utilization_percent.toFixed(1)}%`
                          : "—"
                      }
                    />

                    <DrawerValue
                      label="Upper Utilization"
                      value={
                        selectedComponent.upper_limit_utilization_percent !==
                          undefined &&
                        selectedComponent.upper_limit_utilization_percent !==
                          null
                          ? `${selectedComponent.upper_limit_utilization_percent.toFixed(1)}%`
                          : "—"
                      }
                    />
                  </div>
                </div>
              </div>

              <div>
                <DrawerLabel>Evidence</DrawerLabel>

                <div className="mt-3 border border-black/10 bg-white/50 p-5 text-sm leading-6 text-black/65">
                  {selectedComponent.evidence_summary ??
                    "No evidence summary available."}
                </div>
              </div>

              <div>
                <DrawerLabel>Explanation</DrawerLabel>

                <div className="mt-3 border border-black/10 bg-white/50 p-5 text-sm leading-6 text-black/65">
                  {selectedComponent.explanation ?? "No explanation available."}
                </div>
              </div>

              <Link
                href={`/components/${selectedComponent.component_id}`}
                className="block border border-black bg-black px-5 py-3 text-center text-xs font-medium uppercase tracking-[0.18em] text-white transition hover:bg-black/80"
              >
                Open Component Investigation
              </Link>
            </div>
          </aside>
        </div>
      )}
    </main>
  );
}

/* -------------------------------------------------- */
/* UI COMPONENTS */
/* -------------------------------------------------- */

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-[10px] font-semibold uppercase tracking-[0.25em] text-black/40">
      {children}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-[#f4f4f1] p-6">
      <div className="text-[10px] uppercase tracking-[0.2em] text-black/35">
        {label}
      </div>

      <div className="mt-3 font-mono text-2xl font-semibold">{value}</div>
    </div>
  );
}

function Disposition({
  label,
  value,
  percentage,
}: {
  label: string;
  value?: number;
  percentage?: number;
}) {
  return (
    <div>
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-[0.2em] text-black/35">
            {label}
          </div>

          <div className="mt-2 font-mono text-3xl font-semibold">
            {formatNumber(value)}
          </div>
        </div>

        <div className="font-mono text-xs text-black/40">
          {formatPercent(percentage)}
        </div>
      </div>
    </div>
  );
}

function ProfileMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-[#f4f4f1] p-5">
      <div className="text-[10px] uppercase tracking-[0.18em] text-black/35">
        {label}
      </div>

      <div className="mt-3 font-mono text-xl font-semibold">{value}</div>
    </div>
  );
}

function ForecastMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-[#f4f4f1] p-6">
      <div className="text-[10px] uppercase tracking-[0.2em] text-black/35">
        {label}
      </div>

      <div className="mt-3 font-mono text-2xl font-semibold">{value}</div>
    </div>
  );
}

function RiskBadge({ value }: { value?: string }) {
  const normalized = String(value ?? "UNKNOWN").toUpperCase();

  let className = "border-black/15 bg-black/5 text-black/60";

  if (normalized.includes("CRITICAL")) {
    className = "border-red-500/30 bg-red-500/10 text-red-700";
  } else if (normalized.includes("HIGH")) {
    className = "border-orange-500/30 bg-orange-500/10 text-orange-700";
  } else if (normalized.includes("MEDIUM")) {
    className = "border-amber-500/30 bg-amber-500/10 text-amber-700";
  }

  return (
    <span
      className={`inline-flex border px-2.5 py-1 text-[9px] font-semibold uppercase tracking-[0.15em] ${className}`}
    >
      {value ?? "UNKNOWN"}
    </span>
  );
}

function RiskScore({ value }: { value?: number }) {
  if (value === undefined || value === null || !Number.isFinite(value)) {
    return <span className="font-mono text-xs text-black/30">—</span>;
  }

  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 bg-black/10">
        <div
          className="h-full bg-black"
          style={{
            width: `${Math.min(Math.max(value, 0), 100)}%`,
          }}
        />
      </div>

      <span className="font-mono text-xs">{value.toFixed(1)}</span>
    </div>
  );
}

function SourceFile({ label, value }: { label: string; value?: string }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.18em] text-black/35">
        {label}
      </div>

      <div className="mt-2 break-all font-mono text-xs text-black/60">
        {value ?? "Not available"}
      </div>
    </div>
  );
}

function PipelineStage({
  number,
  title,
  text,
}: {
  number: string;
  title: string;
  text: string;
}) {
  return (
    <div>
      <div className="font-mono text-[10px] text-black/30">{number}</div>

      <div className="mt-2 text-[10px] font-semibold tracking-[0.2em]">
        {title}
      </div>

      <div className="mt-2 text-xs leading-5 text-black/45">{text}</div>
    </div>
  );
}

function DrawerMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-[#f4f4f1] p-4">
      <div className="text-[9px] uppercase tracking-[0.18em] text-black/35">
        {label}
      </div>

      <div className="mt-2 font-mono text-xs font-semibold">{value}</div>
    </div>
  );
}

function DrawerLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-black/40">
      {children}
    </div>
  );
}

function DrawerValue({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[9px] uppercase tracking-[0.15em] text-black/35">
        {label}
      </div>

      <div className="mt-2 font-mono text-sm font-semibold">{value}</div>
    </div>
  );
}

/* -------------------------------------------------- */
/* FORMATTERS */
/* -------------------------------------------------- */

function formatNumber(value?: number) {
  if (value === undefined || value === null || !Number.isFinite(value)) {
    return "—";
  }

  return new Intl.NumberFormat("en-US").format(value);
}

function formatPercent(value?: number) {
  if (value === undefined || value === null || !Number.isFinite(value)) {
    return "—";
  }

  return `${value.toFixed(1)}%`;
}

function formatRisk(value?: number) {
  if (value === undefined || value === null || !Number.isFinite(value)) {
    return "—";
  }

  return value.toFixed(1);
}
