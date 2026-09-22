"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";

type ComponentRow = {
  component_id: string;
  lot_id: string;
  component_type: string;

  temperature_C: number;
  voltage_V: number;

  iddq_168h_uA: number;
  leakage_168h_uA: number;

  anomaly_flag: number | boolean;
  combined_anomaly_score: number;

  risk_score_100: number;
  risk_level: string;

  limit_violation: number | boolean;
  screening_decision: string;

  explanation?: string;
};

type ComponentsResponse = {
  total: number;
  page: number;
  limit: number;
  filter_options?: {
    lots?: string[];
    component_types?: string[];
    screening_decisions?: string[];
  };
  data: ComponentRow[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const PAGE_SIZE = 25;

function formatNumber(value: number | undefined | null, digits = 2) {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "—";
  }

  return value.toFixed(digits);
}

function isAnomaly(value: number | boolean) {
  return value === true || value === 1;
}

function normalizeDecision(value?: string) {
  return (value || "").toUpperCase();
}

function decisionClass(decision: string) {
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

function riskClass(level?: string) {
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

function LoadingRows() {
  return (
    <div className="divide-y divide-slate-200 dark:divide-white/[0.06]">
      {Array.from({ length: 8 }).map((_, index) => (
        <div
          key={index}
          className="grid grid-cols-[1.4fr_1fr_0.8fr_1fr_0.8fr_0.8fr_1fr_70px] gap-4 px-5 py-4"
        >
          {Array.from({ length: 8 }).map((__, cell) => (
            <div
              key={cell}
              className="h-4 animate-pulse rounded bg-slate-200 dark:bg-white/[0.06]"
            />
          ))}
        </div>
      ))}
    </div>
  );
}

export default function ComponentsPage() {
  const [components, setComponents] = useState<ComponentRow[]>([]);
  const [total, setTotal] = useState(0);

  const [page, setPage] = useState(1);

  const [componentId, setComponentId] = useState("");
  const [lotId, setLotId] = useState("");
  const [componentType, setComponentType] = useState("");
  const [decision, setDecision] = useState("");

  const [lots, setLots] = useState<string[]>([]);
  const [componentTypes, setComponentTypes] = useState<string[]>([]);
  const [decisions, setDecisions] = useState<string[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  async function loadComponents() {
    try {
      setLoading(true);
      setError("");

      const params = new URLSearchParams({
        page: String(page),
        limit: String(PAGE_SIZE),
      });

      if (componentId.trim()) {
        params.set("component_id", componentId.trim());
      }

      if (lotId) {
        params.set("lot_id", lotId);
      }

      if (componentType) {
        params.set("component_type", componentType);
      }

      if (decision) {
        params.set("screening_decision", decision);
      }

      const response = await fetch(
        `${API_BASE}/api/components/?${params.toString()}`,
        {
          cache: "no-store",
        },
      );

      if (!response.ok) {
        throw new Error(`Backend returned ${response.status}`);
      }

      const result: ComponentsResponse = await response.json();

      setComponents(result.data || []);
      setTotal(result.total || 0);

      if (result.filter_options) {
        setLots(result.filter_options.lots || []);
        setComponentTypes(result.filter_options.component_types || []);
        setDecisions(result.filter_options.screening_decisions || []);
      }
    } catch (err) {
      console.error(err);
      setError(
        "Unable to load component data. Check that the FastAPI backend is running.",
      );
      setComponents([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadComponents();
  }, [page, componentId, lotId, componentType, decision]);

  function resetFilters() {
    setComponentId("");
    setLotId("");
    setComponentType("");
    setDecision("");
    setPage(1);
  }

  const showingStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const showingEnd = Math.min(page * PAGE_SIZE, total);

  const hasFilters = componentId || lotId || componentType || decision;

  const pageNumbers = useMemo(() => {
    const pages: number[] = [];

    const start = Math.max(1, page - 2);
    const end = Math.min(totalPages, page + 2);

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    return pages;
  }, [page, totalPages]);

  return (
    <main className="min-h-full bg-slate-50 text-slate-900 dark:bg-[#020618] dark:text-white">
      <div className="mx-auto w-full max-w-[1600px] px-5 pb-10 pt-5 lg:px-7">
        {/* Header */}
        <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
              Screening fleet
            </div>

            <h1 className="text-2xl font-semibold tracking-tight">
              Components
            </h1>

            <p className="mt-1 max-w-2xl text-sm text-slate-500 dark:text-slate-400">
              Find components that require inspection and open an individual
              investigation when deeper evidence is needed.
            </p>
          </div>

          <div className="text-sm text-slate-500 dark:text-slate-400">
            Showing{" "}
            <span className="font-medium text-slate-900 dark:text-white">
              {showingStart}–{showingEnd}
            </span>{" "}
            of{" "}
            <span className="font-medium text-slate-900 dark:text-white">
              {total}
            </span>
          </div>
        </div>

        {/* Filters */}
        <section className="mb-5 rounded-xl border border-slate-200 bg-white     dark:border-slate-800 dark:bg-slate-900">
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
                onChange={(e) => {
                  setComponentId(e.target.value);
                  setPage(1);
                }}
                placeholder="Search component ID"
                className="h-10 w-full rounded-lg border border-slate-200 bg-slate-50 pl-9 pr-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-slate-400 dark:border-white/[0.08] dark:bg-white/[0.025] dark:placeholder:text-slate-500 dark:focus:border-white/20"
              />
            </div>

            <select
              value={lotId}
              onChange={(e) => {
                setLotId(e.target.value);
                setPage(1);
              }}
              className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-white/[0.025] dark:text-slate-300"
            >
              <option value="">All lots</option>
              {lots.map((lot) => (
                <option key={lot} value={lot}>
                  {lot}
                </option>
              ))}
            </select>

            <select
              value={componentType}
              onChange={(e) => {
                setComponentType(e.target.value);
                setPage(1);
              }}
              className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-white/[0.025] dark:text-slate-300"
            >
              <option value="">All types</option>
              {componentTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>

            <select
              value={decision}
              onChange={(e) => {
                setDecision(e.target.value);
                setPage(1);
              }}
              className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-white/[0.025] dark:text-slate-300"
            >
              <option value="">All decisions</option>
              {decisions.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>

            {hasFilters ? (
              <button
                onClick={resetFilters}
                className="h-10 rounded-lg px-3 text-sm text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/[0.05] dark:hover:text-white"
              >
                Clear filters
              </button>
            ) : null}
          </div>
        </section>

        {/* Error */}
        {error ? (
          <div className="mb-5 rounded-xl border border-red-500/20 bg-red-500/[0.06] px-4 py-3 text-sm text-red-600 dark:text-red-400">
            {error}
          </div>
        ) : null}

        {/* Main table */}
        <section className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <div className="overflow-x-auto">
            <div className="min-w-[1050px]">
              {/* Table header */}
              <div className="grid grid-cols-[1.4fr_1fr_0.8fr_1fr_0.8fr_0.8fr_1fr_70px] gap-4 border-b border-slate-200 bg-slate-50/70 px-5 py-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-400 dark:border-white/[0.06] dark:bg-white/[0.015]">
                <div>Component</div>
                <div>Lot</div>
                <div>Type</div>
                <div>168H Iddq</div>
                <div>Anomaly</div>
                <div>Risk</div>
                <div>Decision</div>
                <div />
              </div>

              {loading ? (
                <LoadingRows />
              ) : components.length === 0 ? (
                <div className="flex min-h-[280px] items-center justify-center px-5">
                  <div className="text-center">
                    <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 dark:border-white/10">
                      <svg
                        className="h-5 w-5 text-slate-400"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.6"
                      >
                        <circle cx="11" cy="11" r="7" />
                        <path d="m20 20-4-4" />
                      </svg>
                    </div>

                    <p className="text-sm font-medium">No components found</p>

                    <p className="mt-1 text-xs text-slate-400">
                      Try changing or clearing your filters.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="divide-y divide-slate-200 dark:divide-white/[0.06]">
                  {components.map((component) => {
                    const anomaly = isAnomaly(component.anomaly_flag);
                    const currentDecision = normalizeDecision(
                      component.screening_decision,
                    );

                    return (
                      <div
                        key={component.component_id}
                        className="grid grid-cols-[1.4fr_1fr_0.8fr_1fr_0.8fr_0.8fr_1fr_70px] items-center gap-4 px-5 py-4 transition hover:bg-slate-50 dark:hover:bg-white/[0.025]"
                      >
                        {/* Component */}
                        <div className="min-w-0">
                          <Link
                            href={`/components/${encodeURIComponent(
                              component.component_id,
                            )}`}
                            className="group inline-flex items-center gap-2"
                          >
                            <span className="h-1.5 w-1.5 rounded-full bg-slate-300 transition group-hover:bg-emerald-500 dark:bg-slate-600" />

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
                        <div className="text-sm text-slate-500 dark:text-slate-400">
                          {component.component_type}
                        </div>

                        {/* 168H */}
                        <div>
                          <span className="font-mono text-sm text-slate-800 dark:text-slate-200">
                            {formatNumber(component.iddq_168h_uA)}
                          </span>
                          <span className="ml-1 text-[11px] text-slate-400">
                            µA
                          </span>
                        </div>

                        {/* Anomaly */}
                        <div>
                          {anomaly ? (
                            <span className="inline-flex items-center gap-1.5 text-sm font-medium text-amber-600 dark:text-amber-400">
                              <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                              Detected
                            </span>
                          ) : (
                            <span className="text-sm text-slate-400">—</span>
                          )}
                        </div>

                        {/* Risk */}
                        <div>
                          <div
                            className={`font-mono text-sm font-medium ${riskClass(
                              component.risk_level,
                            )}`}
                          >
                            {formatNumber(component.risk_score_100, 1)}
                          </div>

                          <div className="mt-0.5 text-[10px] uppercase tracking-wider text-slate-400">
                            {component.risk_level || "—"}
                          </div>
                        </div>

                        {/* Decision */}
                        <div>
                          <span
                            className={`inline-flex rounded-md border px-2 py-1 text-[10px] font-semibold tracking-[0.08em] ${decisionClass(
                              currentDecision,
                            )}`}
                          >
                            {currentDecision || "—"}
                          </span>
                        </div>

                        {/* Inspect */}
                        <div className="text-right">
                          <div className="inline-flex h-8 items-center justify-center rounded-md border border-slate-200 px-2.5 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 dark:border-white/[0.08] dark:text-slate-400 dark:hover:border-white/15 dark:hover:bg-white/[0.04] dark:hover:text-white">
                            Inspect
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Pagination */}
          {!loading && total > 0 ? (
            <div className="flex flex-col gap-3 border-t border-slate-200 px-5 py-3 sm:flex-row sm:items-center sm:justify-between dark:border-white/[0.06]">
              <div className="text-xs text-slate-400">
                Page {page} of {totalPages}
              </div>

              <div className="flex items-center gap-1">
                <button
                  disabled={page === 1}
                  onClick={() => setPage((current) => current - 1)}
                  className="h-8 rounded-md border border-slate-200 px-2.5 text-xs text-slate-500 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
                >
                  Previous
                </button>

                {pageNumbers.map((pageNumber) => (
                  <button
                    key={pageNumber}
                    onClick={() => setPage(pageNumber)}
                    className={`h-8 min-w-8 rounded-md border px-2 text-xs transition ${
                      pageNumber === page
                        ? "border-slate-900 bg-slate-900 text-white dark:border-white dark:bg-white dark:text-slate-900"
                        : "border-slate-200 text-slate-500 hover:bg-slate-50 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
                    }`}
                  >
                    {pageNumber}
                  </button>
                ))}

                <button
                  disabled={page === totalPages}
                  onClick={() => setPage((current) => current + 1)}
                  className="h-8 rounded-md border border-slate-200 px-2.5 text-xs text-slate-500 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
                >
                  Next
                </button>
              </div>
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}
// "use client";

// import { useEffect, useMemo, useState } from "react";
// import Link from "next/link";
// import {
//   getComponents,
//   type Component,
//   type ComponentListResponse,
// } from "@/lib/api";

// const PAGE_SIZE = 25;

// function formatNumber(value: number | null | undefined, digits = 2) {
//   if (value === null || value === undefined || Number.isNaN(Number(value))) {
//     return "—";
//   }

//   return Number(value).toFixed(digits);
// }

// function decisionClass(decision: string) {
//   switch (decision.toUpperCase()) {
//     case "PASS":
//       return "text-emerald-600 dark:text-emerald-400";

//     case "REVIEW":
//       return "text-amber-600 dark:text-amber-400";

//     case "REJECT":
//       return "text-red-600 dark:text-red-400";

//     default:
//       return "text-slate-600 dark:text-slate-400";
//   }
// }

// function riskClass(level: string) {
//   switch (level.toUpperCase()) {
//     case "CRITICAL":
//       return "text-red-600 dark:text-red-400";

//     case "HIGH":
//       return "text-orange-600 dark:text-orange-400";

//     case "MEDIUM":
//       return "text-amber-600 dark:text-amber-400";

//     case "LOW":
//       return "text-emerald-600 dark:text-emerald-400";

//     default:
//       return "text-slate-600 dark:text-slate-400";
//   }
// }

// function anomalyClass(anomaly: boolean) {
//   return anomaly
//     ? "text-amber-600 dark:text-amber-400"
//     : "text-slate-400 dark:text-slate-500";
// }

// export default function ComponentsPage() {
//   const [response, setResponse] = useState<ComponentListResponse | null>(null);

//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState("");

//   const [componentId, setComponentId] = useState("");

//   const [lotId, setLotId] = useState("");

//   const [componentType, setComponentType] = useState("");

//   const [decision, setDecision] = useState("");

//   const [page, setPage] = useState(1);

//   async function loadComponents() {
//     try {
//       setLoading(true);
//       setError("");

//       const result = await getComponents({
//         page,
//         limit: PAGE_SIZE,
//         component_id: componentId.trim() || undefined,
//         lot_id: lotId || undefined,
//         component_type: componentType || undefined,
//         screening_decision: decision || undefined,
//       });

//       setResponse(result);
//     } catch (err) {
//       console.error("Components loading error:", err);

//       setError(
//         err instanceof Error ? err.message : "Unable to load components.",
//       );
//     } finally {
//       setLoading(false);
//     }
//   }

//   useEffect(() => {
//     loadComponents();
//   }, [page, lotId, componentType, decision]);

//   const filterOptions = response?.filter_options;

//   const totalPages = useMemo(() => {
//     if (!response?.total) return 1;

//     return Math.max(1, Math.ceil(response.total / PAGE_SIZE));
//   }, [response?.total]);

//   function submitSearch(event: React.FormEvent) {
//     event.preventDefault();

//     setPage(1);
//     loadComponents();
//   }

//   function clearFilters() {
//     setComponentId("");
//     setLotId("");
//     setComponentType("");
//     setDecision("");
//     setPage(1);
//   }

//   return (
//     <main className="min-h-screen pb-10">
//       {/* =====================================================
//           HEADER
//       ===================================================== */}

//       <section className="mb-7 border-b border-slate-200 pb-6 dark:border-slate-800">
//         <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500">
//           Screening Records
//         </p>

//         <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
//           <div>
//             <h1 className="text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
//               Components
//             </h1>

//             <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
//               Inspect burn-in measurements, anomaly evidence, risk, and
//               screening decisions.
//             </p>
//           </div>

//           <div className="text-sm text-slate-500 dark:text-slate-400">
//             {response?.total ?? 0} matching components
//           </div>
//         </div>
//       </section>

//       {/* =====================================================
//           FILTERS
//       ===================================================== */}

//       <section className="mb-6">
//         <form
//           onSubmit={submitSearch}
//           className="flex flex-col gap-3 lg:flex-row"
//         >
//           <div className="flex-1">
//             <input
//               type="text"
//               value={componentId}
//               onChange={(event) => setComponentId(event.target.value)}
//               placeholder="Search component ID"
//               className="h-10 w-full border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100 dark:placeholder:text-slate-600 dark:focus:border-slate-600"
//             />
//           </div>

//           <select
//             value={lotId}
//             onChange={(event) => {
//               setLotId(event.target.value);
//               setPage(1);
//             }}
//             className="h-10 border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300"
//           >
//             <option value="">All lots</option>

//             {filterOptions?.lots?.map((lot) => (
//               <option key={lot} value={lot}>
//                 {lot}
//               </option>
//             ))}
//           </select>

//           <select
//             value={componentType}
//             onChange={(event) => {
//               setComponentType(event.target.value);
//               setPage(1);
//             }}
//             className="h-10 border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300"
//           >
//             <option value="">All types</option>

//             {filterOptions?.component_types?.map((type) => (
//               <option key={type} value={type}>
//                 {type}
//               </option>
//             ))}
//           </select>

//           <select
//             value={decision}
//             onChange={(event) => {
//               setDecision(event.target.value);
//               setPage(1);
//             }}
//             className="h-10 border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300"
//           >
//             <option value="">All decisions</option>

//             {filterOptions?.screening_decisions?.map((item) => (
//               <option key={item} value={item}>
//                 {item}
//               </option>
//             ))}
//           </select>

//           <button
//             type="submit"
//             className="h-10 border border-slate-900 bg-slate-900 px-5 text-sm font-medium text-white transition hover:bg-slate-700 dark:border-slate-100 dark:bg-slate-100 dark:text-slate-950 dark:hover:bg-slate-300"
//           >
//             Search
//           </button>

//           <button
//             type="button"
//             onClick={clearFilters}
//             className="h-10 px-3 text-sm text-slate-500 transition hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
//           >
//             Clear
//           </button>
//         </form>
//       </section>

//       {/* =====================================================
//           ERROR
//       ===================================================== */}

//       {error && (
//         <section className="mb-6 border border-red-200 bg-red-50 p-5 dark:border-red-900/60 dark:bg-red-950/20">
//           <p className="text-sm font-medium text-red-700 dark:text-red-400">
//             Unable to load components
//           </p>

//           <p className="mt-1 text-xs text-red-600 dark:text-red-400">{error}</p>

//           <button
//             type="button"
//             onClick={loadComponents}
//             className="mt-4 text-xs font-medium text-red-700 underline dark:text-red-400"
//           >
//             Retry
//           </button>
//         </section>
//       )}

//       {/* =====================================================
//           TABLE
//       ===================================================== */}

//       <section className="overflow-hidden border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
//         <div className="overflow-x-auto">
//           <table className="w-full min-w-[900px] border-collapse">
//             <thead>
//               <tr className="border-b border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900/50">
//                 <th className="px-5 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
//                   Component
//                 </th>

//                 <th className="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
//                   Lot
//                 </th>

//                 <th className="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
//                   Type
//                 </th>

//                 <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
//                   168H Iddq
//                 </th>

//                 <th className="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
//                   Anomaly
//                 </th>

//                 <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
//                   Risk
//                 </th>

//                 <th className="px-4 py-3 text-left text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
//                   Decision
//                 </th>

//                 <th className="px-5 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">
//                   Inspect
//                 </th>
//               </tr>
//             </thead>

//             <tbody>
//               {loading ? (
//                 Array.from({ length: 8 }).map((_, index) => (
//                   <tr
//                     key={index}
//                     className="border-b border-slate-100 dark:border-slate-900"
//                   >
//                     {Array.from({
//                       length: 8,
//                     }).map((_, cellIndex) => (
//                       <td key={cellIndex} className="px-4 py-4">
//                         <div className="h-3 animate-pulse rounded bg-slate-100 dark:bg-slate-900" />
//                       </td>
//                     ))}
//                   </tr>
//                 ))
//               ) : response?.data?.length ? (
//                 response.data.map((component: Component) => (
//                   <ComponentRow
//                     key={component.component_id}
//                     component={component}
//                   />
//                 ))
//               ) : (
//                 <tr>
//                   <td colSpan={8} className="px-5 py-16 text-center">
//                     <p className="text-sm font-medium text-slate-600 dark:text-slate-300">
//                       No components found
//                     </p>

//                     <p className="mt-1 text-xs text-slate-400">
//                       Try changing the current filters.
//                     </p>
//                   </td>
//                 </tr>
//               )}
//             </tbody>
//           </table>
//         </div>

//         {/* =================================================
//             PAGINATION
//         ================================================= */}

//         <div className="flex items-center justify-between border-t border-slate-200 px-5 py-4 dark:border-slate-800">
//           <p className="text-xs text-slate-500 dark:text-slate-400">
//             Page {response?.page ?? page} of {totalPages}
//           </p>

//           <div className="flex items-center gap-2">
//             <button
//               type="button"
//               disabled={page <= 1 || loading}
//               onClick={() => setPage((current) => Math.max(1, current - 1))}
//               className="border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-800 dark:text-slate-300"
//             >
//               Previous
//             </button>

//             <button
//               type="button"
//               disabled={page >= totalPages || loading}
//               onClick={() =>
//                 setPage((current) => Math.min(totalPages, current + 1))
//               }
//               className="border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-800 dark:text-slate-300"
//             >
//               Next
//             </button>
//           </div>
//         </div>
//       </section>
//     </main>
//   );
// }

// function ComponentRow({ component }: { component: Component }) {
//   return (
//     <tr className="border-b border-slate-100 transition hover:bg-slate-50 dark:border-slate-900 dark:hover:bg-slate-900/40">
//       <td className="px-5 py-4">
//         <Link
//           href={`/components/${encodeURIComponent(component.component_id)}`}
//           className="text-sm font-medium text-slate-900 hover:underline dark:text-slate-100"
//         >
//           {component.component_id}
//         </Link>
//       </td>

//       <td className="px-4 py-4 text-sm text-slate-600 dark:text-slate-400">
//         {component.lot_id}
//       </td>

//       <td className="px-4 py-4 text-sm text-slate-600 dark:text-slate-400">
//         {component.component_type}
//       </td>

//       <td className="px-4 py-4 text-right text-sm tabular-nums text-slate-700 dark:text-slate-300">
//         {formatNumber(component.iddq_168h_uA)}{" "}
//         <span className="text-xs text-slate-400">µA</span>
//       </td>

//       <td className="px-4 py-4">
//         <span
//           className={`text-xs font-medium ${anomalyClass(
//             component.anomaly_flag,
//           )}`}
//         >
//           {component.anomaly_flag ? "Detected" : "None"}
//         </span>
//       </td>

//       <td className="px-4 py-4 text-right">
//         <div className="text-sm font-medium tabular-nums text-slate-800 dark:text-slate-200">
//           {formatNumber(component.risk_score_100)}
//         </div>

//         <div
//           className={`mt-0.5 text-[10px] uppercase ${riskClass(
//             component.risk_level,
//           )}`}
//         >
//           {component.risk_level}
//         </div>
//       </td>

//       <td className="px-4 py-4">
//         <span
//           className={`text-xs font-semibold ${decisionClass(
//             component.screening_decision,
//           )}`}
//         >
//           {component.screening_decision}
//         </span>
//       </td>

//       <td className="px-5 py-4 text-right">
//         <Link
//           href={`/components/${encodeURIComponent(component.component_id)}`}
//           className="text-xs font-medium text-slate-500 transition hover:text-slate-950 dark:text-slate-400 dark:hover:text-white"
//         >
//           Inspect →
//         </Link>
//       </td>
//     </tr>
//   );
// }
