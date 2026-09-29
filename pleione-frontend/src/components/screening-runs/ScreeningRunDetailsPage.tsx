"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Activity,
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Clock3,
  FileText,
  RefreshCw,
  ServerCog,
  Terminal,
  XCircle,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type RunStatus = "not_started" | "queued" | "running" | "completed" | "failed";

type ModuleStatus = RunStatus;

type ModuleState = {
  key: string;
  label: string;
  description: string;
  status: ModuleStatus;
  started_at: string | null;
  finished_at: string | null;
  duration_seconds: number | null;
  script: string;
  output: string;
  artifact?: {
    path: string;
    exists: boolean;
    bytes: number | null;
    modified_at: string | null;
    row_count: number | null;
  };
  error: string | null;
};

type RunSummary = {
  component_count?: number | null;

  module_a?: {
    total?: number;
    status_counts?: Record<string, number>;
  };

  module_b?: {
    total?: number;
    risk_counts?: Record<string, number>;
  };

  module_c?: {
    total?: number;
    decision_counts?: Record<string, number>;
    future_risk_counts?: Record<string, number>;
    evidence_counts?: Record<string, number>;
  };
};

type ScreeningRun = {
  run_id: string;
  status: RunStatus;
  scope: string;
  lot_id: string | null;
  notes: string | null;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  total_duration_seconds: number | null;
  component_count: number | null;
  pipeline: Record<string, ModuleState>;
  artifacts: Array<{
    module: string;
    label: string;
    path: string;
    exists: boolean;
    row_count: number | null;
    bytes: number | null;
    modified_at: string | null;
  }>;
  summary: RunSummary;
  error: string | null;
};

type LogResponse = {
  run_id: string;
  module: string;
  exists: boolean;
  content: string;
};

function formatDate(value: string | null) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleString();
}

function formatDuration(seconds: number | null) {
  if (seconds === null || seconds === undefined) {
    return "—";
  }

  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }

  const minutes = Math.floor(seconds / 60);
  const remaining = Math.round(seconds % 60);

  return `${minutes}m ${remaining}s`;
}

function statusLabel(status: RunStatus) {
  switch (status) {
    case "not_started":
      return "Not started";
    case "queued":
      return "Queued";
    case "running":
      return "Running";
    case "completed":
      return "Completed";
    case "failed":
      return "Failed";
    default:
      return status;
  }
}

function statusClass(status: RunStatus) {
  switch (status) {
    case "completed":
      return "border-emerald-500/20 bg-emerald-500/10 text-emerald-400";

    case "running":
      return "border-blue-500/20 bg-blue-500/10 text-blue-400";

    case "queued":
      return "border-amber-500/20 bg-amber-500/10 text-amber-400";

    case "failed":
      return "border-red-500/20 bg-red-500/10 text-red-400";

    default:
      return "border-slate-700 bg-slate-800/50 text-slate-400";
  }
}

function StatusIcon({ status }: { status: RunStatus }) {
  if (status === "completed") {
    return <CheckCircle2 size={16} />;
  }

  if (status === "failed") {
    return <XCircle size={16} />;
  }

  if (status === "running") {
    return <Activity size={16} />;
  }

  if (status === "queued") {
    return <Clock3 size={16} />;
  }

  return <ServerCog size={16} />;
}

function MetricCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-[#071126]">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-xs text-slate-500 dark:text-slate-400">
          {label}
        </span>

        <span className="text-slate-400">{icon}</span>
      </div>

      <p className="text-lg font-semibold">{value}</p>
    </div>
  );
}

function Distribution({
  title,
  data,
}: {
  title: string;
  data: Record<string, number> | undefined;
}) {
  const entries = Object.entries(data || {});

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-[#071126]">
      <h3 className="text-sm font-semibold">{title}</h3>

      {entries.length === 0 ? (
        <p className="mt-4 text-xs text-slate-500">No data available.</p>
      ) : (
        <div className="mt-4 space-y-3">
          {entries.map(([key, value]) => (
            <div key={key} className="flex items-center justify-between">
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {key}
              </span>

              <span className="text-sm font-semibold">
                {value.toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ScreeningRunDetailsPage() {
  const params = useParams();

  const runId = String(params?.runId || "");

  const [run, setRun] = useState<ScreeningRun | null>(null);

  const [logs, setLogs] = useState<Record<string, string>>({});

  const [selectedLog, setSelectedLog] = useState("pipeline");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadRun = useCallback(async () => {
    if (!runId) return;

    try {
      const response = await fetch(
        `${API_BASE}/api/screening-runs/${encodeURIComponent(runId)}`,
        {
          cache: "no-store",
        },
      );

      if (!response.ok) {
        throw new Error("Unable to load screening run.");
      }

      const data: ScreeningRun = await response.json();

      setRun(data);
      setError("");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to load screening run.",
      );
    } finally {
      setLoading(false);
    }
  }, [runId]);

  const loadLog = useCallback(
    async (moduleName: string) => {
      if (!runId) return;

      try {
        const response = await fetch(
          `${API_BASE}/api/screening-runs/${encodeURIComponent(
            runId,
          )}/logs/${moduleName}`,
          {
            cache: "no-store",
          },
        );

        if (!response.ok) return;

        const data: LogResponse = await response.json();

        setLogs((previous) => ({
          ...previous,
          [moduleName]: data.content || "",
        }));
      } catch {
        // Keep previous log content.
      }
    },
    [runId],
  );

  useEffect(() => {
    loadRun();
  }, [loadRun]);

  useEffect(() => {
    if (!run) return;

    if (run.status !== "queued" && run.status !== "running") {
      return;
    }

    const interval = window.setInterval(() => {
      loadRun();
      loadLog(selectedLog);
    }, 2500);

    return () => {
      window.clearInterval(interval);
    };
  }, [run, loadRun, loadLog, selectedLog]);

  useEffect(() => {
    if (run) {
      loadLog(selectedLog);
    }
  }, [run, selectedLog, loadLog]);

  const modules = useMemo(() => {
    if (!run) return [];

    return [
      run.pipeline?.module_a,
      run.pipeline?.module_b,
      run.pipeline?.module_c,
    ].filter(Boolean) as ModuleState[];
  }, [run]);

  if (loading) {
    return (
      <main className="min-h-screen bg-white px-5 py-10 dark:bg-[#020618]">
        <div className="mx-auto max-w-[1500px]">
          <p className="text-sm text-slate-500">Loading screening run...</p>
        </div>
      </main>
    );
  }

  if (error || !run) {
    return (
      <main className="min-h-screen bg-white px-5 py-10 dark:bg-[#020618]">
        <div className="mx-auto max-w-[1500px]">
          <Link
            href="/screening-runs"
            className="mb-6 inline-flex items-center gap-2 text-sm text-blue-500"
          >
            <ArrowLeft size={16} />
            Back to Screening Runs
          </Link>

          <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-400">
            {error || "Screening run not found."}
          </div>
        </div>
      </main>
    );
  }

  const finalDecisionCounts = run.summary?.module_c?.decision_counts || {};

  const riskCounts = run.summary?.module_c?.future_risk_counts || {};

  const anomalyCounts = run.summary?.module_a?.status_counts || {};

  const forecastRiskCounts = run.summary?.module_b?.risk_counts || {};

  return (
    <main className="min-h-screen bg-white px-5 py-8 text-slate-900 dark:bg-[#020618] dark:text-slate-100 md:px-8 lg:px-10">
      <div className="mx-auto max-w-[1500px]">
        {/* TOP */}
        <div className="mb-8">
          <Link
            href="/screening-runs"
            className="mb-5 inline-flex items-center gap-2 text-sm text-slate-500 transition hover:text-blue-500"
          >
            <ArrowLeft size={16} />
            Back to Screening Runs
          </Link>

          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="mb-3 flex items-center gap-3">
                <h1 className="text-3xl font-semibold tracking-tight">
                  Screening Run
                </h1>

                <span
                  className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium ${statusClass(
                    run.status,
                  )}`}
                >
                  <StatusIcon status={run.status} />
                  {statusLabel(run.status)}
                </span>
              </div>

              <p className="font-mono text-xs text-slate-500">{run.run_id}</p>

              {run.notes && (
                <p className="mt-3 max-w-2xl text-sm text-slate-500 dark:text-slate-400">
                  {run.notes}
                </p>
              )}
            </div>

            <button
              onClick={() => {
                loadRun();
                loadLog(selectedLog);
              }}
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-[#071126]"
            >
              <RefreshCw size={16} />
              Refresh
            </button>
          </div>
        </div>

        {/* FAILURE */}
        {run.error && (
          <div className="mb-6 flex items-start gap-3 rounded-2xl border border-red-500/20 bg-red-500/10 p-5 text-sm text-red-400">
            <AlertCircle size={18} className="mt-0.5 shrink-0" />

            <div>
              <p className="font-semibold">Pipeline execution failed</p>

              <p className="mt-1 leading-6">{run.error}</p>
            </div>
          </div>
        )}

        {/* METRICS */}
        <div className="mb-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <MetricCard
            label="Scope"
            value={run.scope}
            icon={<ServerCog size={17} />}
          />

          <MetricCard
            label="Components"
            value={
              run.component_count ? run.component_count.toLocaleString() : "—"
            }
            icon={<Activity size={17} />}
          />

          <MetricCard
            label="Created"
            value={formatDate(run.created_at)}
            icon={<Clock3 size={17} />}
          />

          <MetricCard
            label="Duration"
            value={formatDuration(run.total_duration_seconds)}
            icon={<Clock3 size={17} />}
          />

          <MetricCard
            label="Finished"
            value={formatDate(run.finished_at)}
            icon={<CheckCircle2 size={17} />}
          />
        </div>

        {/* PIPELINE */}
        <section className="mb-8">
          <div className="mb-4">
            <h2 className="text-lg font-semibold">Pipeline execution</h2>

            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Execution trace for Module A, Module B and Module C.
            </p>
          </div>

          <div className="grid gap-4 xl:grid-cols-3">
            {modules.map((module, index) => (
              <div
                key={module.key}
                className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-[#071126]"
              >
                <div className="mb-5 flex items-start justify-between gap-4">
                  <div className="flex gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-500/10 text-xs font-bold text-blue-500">
                      0{index + 1}
                    </div>

                    <div>
                      <h3 className="font-semibold">{module.label}</h3>

                      <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
                        {module.description}
                      </p>
                    </div>
                  </div>

                  <span
                    className={`inline-flex shrink-0 items-center gap-1 rounded-full border px-2.5 py-1 text-[10px] font-medium ${statusClass(
                      module.status,
                    )}`}
                  >
                    <StatusIcon status={module.status} />
                    {statusLabel(module.status)}
                  </span>
                </div>

                <div className="space-y-3 border-t border-slate-200 pt-4 dark:border-slate-800">
                  <div className="flex justify-between gap-4 text-xs">
                    <span className="text-slate-500">Duration</span>

                    <span className="font-medium">
                      {formatDuration(module.duration_seconds)}
                    </span>
                  </div>

                  <div className="flex justify-between gap-4 text-xs">
                    <span className="text-slate-500">Output rows</span>

                    <span className="font-medium">
                      {module.artifact?.row_count !== null &&
                      module.artifact?.row_count !== undefined
                        ? module.artifact.row_count.toLocaleString()
                        : "—"}
                    </span>
                  </div>

                  <div>
                    <p className="mb-1 text-[10px] uppercase tracking-wider text-slate-500">
                      Output
                    </p>

                    <p className="break-all font-mono text-[11px] text-slate-400">
                      {module.output}
                    </p>
                  </div>
                </div>

                {module.error && (
                  <div className="mt-4 rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-xs leading-5 text-red-400">
                    {module.error}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        {/* RESULT SUMMARY */}
        <section className="mb-8">
          <div className="mb-4">
            <h2 className="text-lg font-semibold">Screening result summary</h2>

            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Summary generated from the current pipeline outputs.
            </p>
          </div>

          <div className="grid gap-4 lg:grid-cols-4">
            <Distribution title="Final decisions" data={finalDecisionCounts} />

            <Distribution title="Future risk" data={riskCounts} />

            <Distribution title="Module A status" data={anomalyCounts} />

            <Distribution title="Module B risk" data={forecastRiskCounts} />
          </div>
        </section>

        {/* ARTIFACTS */}
        <section className="mb-8">
          <div className="mb-4">
            <h2 className="text-lg font-semibold">Generated artifacts</h2>

            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Output files produced by this pipeline.
            </p>
          </div>

          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-[#071126]">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[800px] text-left">
                <thead className="border-b border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#02091a]">
                  <tr className="text-[11px] uppercase tracking-wider text-slate-500">
                    <th className="px-5 py-4">Module</th>

                    <th className="px-5 py-4">Artifact</th>

                    <th className="px-5 py-4">Rows</th>

                    <th className="px-5 py-4">Size</th>

                    <th className="px-5 py-4">Modified</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {run.artifacts.map((artifact) => (
                    <tr key={artifact.module}>
                      <td className="px-5 py-4 text-sm font-medium">
                        {artifact.label}
                      </td>

                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          <FileText size={15} className="text-slate-500" />

                          <span className="font-mono text-xs text-slate-500">
                            {artifact.path}
                          </span>
                        </div>
                      </td>

                      <td className="px-5 py-4 text-xs">
                        {artifact.row_count !== null
                          ? artifact.row_count.toLocaleString()
                          : "—"}
                      </td>

                      <td className="px-5 py-4 text-xs text-slate-500">
                        {artifact.bytes !== null
                          ? `${(artifact.bytes / 1024).toFixed(1)} KB`
                          : "—"}
                      </td>

                      <td className="px-5 py-4 text-xs text-slate-500">
                        {formatDate(artifact.modified_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* LOGS */}
        <section>
          <div className="mb-4">
            <h2 className="text-lg font-semibold">Execution logs</h2>

            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Direct stdout and execution information from the pipeline.
            </p>
          </div>

          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-[#071126]">
            <div className="flex flex-wrap gap-2 border-b border-slate-200 p-3 dark:border-slate-800">
              {["pipeline", "module_a", "module_b", "module_c"].map(
                (module) => (
                  <button
                    key={module}
                    onClick={() => setSelectedLog(module)}
                    className={`rounded-lg px-3 py-2 text-xs font-medium transition ${
                      selectedLog === module
                        ? "bg-blue-500/10 text-blue-500"
                        : "text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-900"
                    }`}
                  >
                    {module === "pipeline"
                      ? "Pipeline"
                      : module.replace("module_", "Module ").toUpperCase()}
                  </button>
                ),
              )}
            </div>

            <div className="p-4">
              <div className="mb-3 flex items-center gap-2 text-xs text-slate-500">
                <Terminal size={14} />
                {selectedLog}
              </div>

              <pre className="max-h-[500px] overflow-auto rounded-xl border border-slate-800 bg-[#020617] p-4 font-mono text-[11px] leading-5 text-slate-300">
                {logs[selectedLog] || "No log output available yet."}
              </pre>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
