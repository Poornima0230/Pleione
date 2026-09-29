"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock3,
  Eye,
  Play,
  RefreshCw,
  ServerCog,
  XCircle,
  Zap,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type RunStatus = "not_started" | "queued" | "running" | "completed" | "failed";

type ModuleStatus =
  | "not_started"
  | "queued"
  | "running"
  | "completed"
  | "failed";

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
  artifacts: unknown[];
  summary: RunSummary;
  error: string | null;
};

type RunsResponse = {
  page: number;
  limit: number;
  pages: number;
  total: number;
  runs: ScreeningRun[];
};

type CurrentResponse = {
  active: boolean;
  run: ScreeningRun | null;
};

function formatDate(value: string | null) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "—";

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

function statusLabel(status: RunStatus | ModuleStatus) {
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

function statusClass(status: RunStatus | ModuleStatus) {
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

function StatusIcon({ status }: { status: RunStatus | ModuleStatus }) {
  if (status === "completed") {
    return <CheckCircle2 size={15} />;
  }

  if (status === "failed") {
    return <XCircle size={15} />;
  }

  if (status === "running") {
    return <Activity size={15} />;
  }

  if (status === "queued") {
    return <Clock3 size={15} />;
  }

  return <ServerCog size={15} />;
}

function ModuleMini({ module }: { module: ModuleState | undefined }) {
  if (!module) {
    return <span className="text-xs text-slate-600">—</span>;
  }

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-medium ${statusClass(
        module.status,
      )}`}
    >
      <StatusIcon status={module.status} />
      {module.label}
    </span>
  );
}

export default function ScreeningRunsPage() {
  const [runs, setRuns] = useState<ScreeningRun[]>([]);
  const [activeRun, setActiveRun] = useState<ScreeningRun | null>(null);

  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");

  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);

  const loadRuns = useCallback(async () => {
    try {
      const response = await fetch(
        `${API_BASE}/api/screening-runs/?page=${page}&limit=10`,
        {
          cache: "no-store",
        },
      );

      if (!response.ok) {
        throw new Error("Unable to load screening runs.");
      }

      const data: RunsResponse = await response.json();

      setRuns(data.runs);
      setPages(data.pages);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to load screening runs.",
      );
    } finally {
      setLoading(false);
    }
  }, [page]);

  const loadCurrentRun = useCallback(async () => {
    try {
      const response = await fetch(
        `${API_BASE}/api/screening-runs/status/current`,
        {
          cache: "no-store",
        },
      );

      if (!response.ok) return;

      const data: CurrentResponse = await response.json();

      setActiveRun(data.active ? data.run : null);
    } catch {
      // Keep existing UI state.
    }
  }, []);

  useEffect(() => {
    loadRuns();
    loadCurrentRun();
  }, [loadRuns, loadCurrentRun]);

  useEffect(() => {
    if (!activeRun) return;

    if (activeRun.status !== "queued" && activeRun.status !== "running") {
      return;
    }

    const interval = window.setInterval(() => {
      loadCurrentRun();
      loadRuns();
    }, 2500);

    return () => {
      window.clearInterval(interval);
    };
  }, [activeRun, loadCurrentRun, loadRuns]);

  const startNewRun = async () => {
    setStarting(true);
    setError("");

    try {
      const createResponse = await fetch(`${API_BASE}/api/screening-runs/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          lot_id: null,
          notes: null,
        }),
      });

      if (!createResponse.ok) {
        const body = await createResponse.json().catch(() => null);

        throw new Error(body?.detail || "Unable to create screening run.");
      }

      const created: ScreeningRun = await createResponse.json();

      const startResponse = await fetch(
        `${API_BASE}/api/screening-runs/${created.run_id}/start`,
        {
          method: "POST",
        },
      );

      if (!startResponse.ok) {
        const body = await startResponse.json().catch(() => null);

        throw new Error(body?.detail || "Unable to start screening run.");
      }

      const started: ScreeningRun = await startResponse.json();

      setActiveRun(started);

      await loadRuns();
      await loadCurrentRun();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to start screening run.",
      );
    } finally {
      setStarting(false);
    }
  };

  const completedCount = useMemo(
    () => runs.filter((run) => run.status === "completed").length,
    [runs],
  );

  const failedCount = useMemo(
    () => runs.filter((run) => run.status === "failed").length,
    [runs],
  );

  const activeModules = useMemo(() => {
    if (!activeRun) return [];

    return [
      activeRun.pipeline.module_a,
      activeRun.pipeline.module_b,
      activeRun.pipeline.module_c,
    ].filter(Boolean);
  }, [activeRun]);

  return (
    <main className="min-h-screen bg-white px-5 py-8 text-slate-900 dark:bg-[#020618] dark:text-slate-100 md:px-8 lg:px-10">
      <div className="mx-auto max-w-[1500px]">
        {/* HEADER */}
        <div className="mb-8 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-3 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-blue-500 dark:text-blue-400">
              <Zap size={14} />
              Screening execution
            </div>

            <h1 className="text-3xl font-semibold tracking-tight">
              Screening Runs
            </h1>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
              Execute and trace the complete burn-in screening pipeline from
              anomaly detection through final risk assessment.
            </p>
          </div>

          <button
            onClick={startNewRun}
            disabled={starting || !!activeRun}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {starting ? (
              <RefreshCw size={17} className="animate-spin" />
            ) : (
              <Play size={17} />
            )}

            {starting ? "Starting..." : "Start screening run"}
          </button>
        </div>

        {/* ERROR */}
        {error && (
          <div className="mb-6 flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-400">
            <AlertCircle size={18} className="mt-0.5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* ACTIVE RUN */}
        {activeRun && (
          <section className="mb-8 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-[#071126]">
            <div className="flex flex-col gap-4 border-b border-slate-200 p-5 dark:border-slate-800 md:flex-row md:items-center md:justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <h2 className="text-base font-semibold">
                    Active screening run
                  </h2>

                  <span
                    className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium ${statusClass(
                      activeRun.status,
                    )}`}
                  >
                    <StatusIcon status={activeRun.status} />
                    {statusLabel(activeRun.status)}
                  </span>
                </div>

                <p className="mt-1 font-mono text-xs text-slate-500 dark:text-slate-500">
                  {activeRun.run_id}
                </p>
              </div>

              <Link
                href={`/screening-runs/${activeRun.run_id}`}
                className="inline-flex items-center gap-2 text-sm font-medium text-blue-500 hover:text-blue-400"
              >
                Open run details
                <Eye size={16} />
              </Link>
            </div>

            <div className="grid gap-4 p-5 md:grid-cols-3">
              {activeModules.map((module) => (
                <div
                  key={module.key}
                  className="rounded-xl border border-slate-200 p-4 dark:border-slate-800 dark:bg-[#02091a]"
                >
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-sm font-semibold">
                      {module.label}
                    </span>

                    <span
                      className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 text-[10px] font-medium ${statusClass(
                        module.status,
                      )}`}
                    >
                      <StatusIcon status={module.status} />
                      {statusLabel(module.status)}
                    </span>
                  </div>

                  <p className="text-xs leading-5 text-slate-500 dark:text-slate-400">
                    {module.description}
                  </p>

                  {module.artifact?.row_count !== null &&
                    module.artifact?.row_count !== undefined && (
                      <p className="mt-3 text-xs text-slate-500">
                        Output rows:{" "}
                        <span className="font-semibold text-slate-700 dark:text-slate-300">
                          {module.artifact.row_count.toLocaleString()}
                        </span>
                      </p>
                    )}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* OVERVIEW */}
        <div className="mb-8 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-[#071126]">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm text-slate-500 dark:text-slate-400">
                Total runs
              </span>
              <ServerCog size={18} className="text-slate-400" />
            </div>

            <p className="text-2xl font-semibold">
              {loading ? "—" : runs.length}
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-[#071126]">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm text-slate-500 dark:text-slate-400">
                Completed on page
              </span>
              <CheckCircle2 size={18} className="text-emerald-400" />
            </div>

            <p className="text-2xl font-semibold">{completedCount}</p>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-[#071126]">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-sm text-slate-500 dark:text-slate-400">
                Failed on page
              </span>
              <XCircle size={18} className="text-red-400" />
            </div>

            <p className="text-2xl font-semibold">{failedCount}</p>
          </div>
        </div>

        {/* PIPELINE */}
        <section className="mb-8">
          <div className="mb-4">
            <h2 className="text-lg font-semibold">Pipeline</h2>

            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              Each screening run executes the current full-dataset pipeline in
              sequence.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                title: "Module A",
                text: "0h peer-based anomaly detection",
              },
              {
                title: "Module B",
                text: "0h + 24h prediction toward 168h",
              },
              {
                title: "Module C",
                text: "Final PASS / REVIEW / REJECT assessment",
              },
            ].map((item, index) => (
              <div
                key={item.title}
                className="relative rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-[#071126]"
              >
                <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg bg-blue-500/10 text-sm font-bold text-blue-500">
                  0{index + 1}
                </div>

                <h3 className="font-semibold">{item.title}</h3>

                <p className="mt-1 text-sm leading-5 text-slate-500 dark:text-slate-400">
                  {item.text}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* HISTORY */}
        <section>
          <div className="mb-4 flex items-end justify-between">
            <div>
              <h2 className="text-lg font-semibold">Run history</h2>

              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                Previous pipeline executions and their generated artifacts.
              </p>
            </div>

            <button
              onClick={() => {
                loadRuns();
                loadCurrentRun();
              }}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-400 dark:hover:bg-slate-900"
            >
              <RefreshCw size={14} />
              Refresh
            </button>
          </div>

          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-[#071126]">
            {loading ? (
              <div className="p-8 text-center text-sm text-slate-500">
                Loading screening runs...
              </div>
            ) : runs.length === 0 ? (
              <div className="p-12 text-center">
                <ServerCog size={32} className="mx-auto mb-3 text-slate-500" />

                <p className="font-medium">No screening runs yet</p>

                <p className="mt-1 text-sm text-slate-500">
                  Start the first full screening pipeline run.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[900px] text-left">
                  <thead className="border-b border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-[#02091a]">
                    <tr className="text-[11px] uppercase tracking-wider text-slate-500">
                      <th className="px-5 py-4">Run</th>
                      <th className="px-5 py-4">Status</th>
                      <th className="px-5 py-4">Scope</th>
                      <th className="px-5 py-4">Components</th>
                      <th className="px-5 py-4">Pipeline</th>
                      <th className="px-5 py-4">Duration</th>
                      <th className="px-5 py-4">Created</th>
                      <th className="px-5 py-4">Action</th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                    {runs.map((run) => (
                      <tr
                        key={run.run_id}
                        className="transition hover:bg-slate-50 dark:hover:bg-[#09152c]"
                      >
                        <td className="px-5 py-4">
                          <p className="font-mono text-xs text-slate-700 dark:text-slate-300">
                            {run.run_id}
                          </p>
                        </td>

                        <td className="px-5 py-4">
                          <span
                            className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium ${statusClass(
                              run.status,
                            )}`}
                          >
                            <StatusIcon status={run.status} />
                            {statusLabel(run.status)}
                          </span>
                        </td>

                        <td className="px-5 py-4 text-xs text-slate-500 dark:text-slate-400">
                          {run.scope}
                        </td>

                        <td className="px-5 py-4 text-sm font-medium">
                          {run.component_count
                            ? run.component_count.toLocaleString()
                            : "—"}
                        </td>

                        <td className="px-5 py-4">
                          <div className="flex gap-1.5">
                            <ModuleMini module={run.pipeline?.module_a} />
                            <ModuleMini module={run.pipeline?.module_b} />
                            <ModuleMini module={run.pipeline?.module_c} />
                          </div>
                        </td>

                        <td className="px-5 py-4 text-xs text-slate-500">
                          {formatDuration(run.total_duration_seconds)}
                        </td>

                        <td className="px-5 py-4 text-xs text-slate-500">
                          {formatDate(run.created_at)}
                        </td>

                        <td className="px-5 py-4">
                          <Link
                            href={`/screening-runs/${run.run_id}`}
                            className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-500 hover:text-blue-400"
                          >
                            View
                            <Eye size={14} />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* PAGINATION */}
          {pages > 1 && (
            <div className="mt-5 flex items-center justify-between">
              <button
                disabled={page <= 1}
                onClick={() => setPage((value) => value - 1)}
                className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-medium disabled:opacity-40 dark:border-slate-800"
              >
                Previous
              </button>

              <span className="text-xs text-slate-500">
                Page {page} of {pages}
              </span>

              <button
                disabled={page >= pages}
                onClick={() => setPage((value) => value + 1)}
                className="rounded-lg border border-slate-200 px-4 py-2 text-xs font-medium disabled:opacity-40 dark:border-slate-800"
              >
                Next
              </button>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
