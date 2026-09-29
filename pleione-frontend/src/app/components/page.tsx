// // "use client";

// // import { useEffect, useMemo, useState } from "react";
// // import Link from "next/link";

// // type ComponentRow = {
// //   component_id: string;
// //   lot_id: string;
// //   component_type: string;

// //   temperature_C: number;
// //   voltage_V: number;

// //   iddq_168h_uA: number;
// //   leakage_168h_uA: number;

// //   anomaly_flag: number | boolean;
// //   combined_anomaly_score: number;

// //   risk_score_100: number;
// //   risk_level: string;

// //   limit_violation: number | boolean;
// //   screening_decision: string;

// //   explanation?: string;
// // };

// // type ComponentsResponse = {
// //   total: number;
// //   page: number;
// //   limit: number;
// //   filter_options?: {
// //     lots?: string[];
// //     component_types?: string[];
// //     screening_decisions?: string[];
// //   };
// //   data: ComponentRow[];
// // };

// // const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// // const PAGE_SIZE = 25;

// // function formatNumber(value: number | undefined | null, digits = 2) {
// //   if (value === undefined || value === null || Number.isNaN(value)) {
// //     return "—";
// //   }

// //   return value.toFixed(digits);
// // }

// // function isAnomaly(value: number | boolean) {
// //   return value === true || value === 1;
// // }

// // function normalizeDecision(value?: string) {
// //   return (value || "").toUpperCase();
// // }

// // function decisionClass(decision: string) {
// //   switch (decision) {
// //     case "REJECT":
// //       return "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400";

// //     case "REVIEW":
// //       return "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400";

// //     case "PASS":
// //       return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400";

// //     default:
// //       return "border-slate-300 bg-slate-100 text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300";
// //   }
// // }

// // function riskClass(level?: string) {
// //   switch ((level || "").toUpperCase()) {
// //     case "CRITICAL":
// //       return "text-red-600 dark:text-red-400";

// //     case "HIGH":
// //       return "text-orange-600 dark:text-orange-400";

// //     case "MEDIUM":
// //       return "text-amber-600 dark:text-amber-400";

// //     case "LOW":
// //       return "text-emerald-600 dark:text-emerald-400";

// //     default:
// //       return "text-slate-600 dark:text-slate-300";
// //   }
// // }

// // function LoadingRows() {
// //   return (
// //     <div className="divide-y divide-slate-200 dark:divide-white/[0.06]">
// //       {Array.from({ length: 8 }).map((_, index) => (
// //         <div
// //           key={index}
// //           className="grid grid-cols-[1.4fr_1fr_0.8fr_1fr_0.8fr_0.8fr_1fr_70px] gap-4 px-5 py-4"
// //         >
// //           {Array.from({ length: 8 }).map((__, cell) => (
// //             <div
// //               key={cell}
// //               className="h-4 animate-pulse rounded bg-slate-200 dark:bg-white/[0.06]"
// //             />
// //           ))}
// //         </div>
// //       ))}
// //     </div>
// //   );
// // }

// // export default function ComponentsPage() {
// //   const [components, setComponents] = useState<ComponentRow[]>([]);
// //   const [total, setTotal] = useState(0);

// //   const [page, setPage] = useState(1);

// //   const [componentId, setComponentId] = useState("");
// //   const [lotId, setLotId] = useState("");
// //   const [componentType, setComponentType] = useState("");
// //   const [decision, setDecision] = useState("");

// //   const [lots, setLots] = useState<string[]>([]);
// //   const [componentTypes, setComponentTypes] = useState<string[]>([]);
// //   const [decisions, setDecisions] = useState<string[]>([]);

// //   const [loading, setLoading] = useState(true);
// //   const [error, setError] = useState("");

// //   const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

// //   async function loadComponents() {
// //     try {
// //       setLoading(true);
// //       setError("");

// //       const params = new URLSearchParams({
// //         page: String(page),
// //         limit: String(PAGE_SIZE),
// //       });

// //       if (componentId.trim()) {
// //         params.set("component_id", componentId.trim());
// //       }

// //       if (lotId) {
// //         params.set("lot_id", lotId);
// //       }

// //       if (componentType) {
// //         params.set("component_type", componentType);
// //       }

// //       if (decision) {
// //         params.set("screening_decision", decision);
// //       }

// //       const response = await fetch(
// //         `${API_BASE}/api/components/?${params.toString()}`,
// //         {
// //           cache: "no-store",
// //         },
// //       );

// //       if (!response.ok) {
// //         throw new Error(`Backend returned ${response.status}`);
// //       }

// //       const result: ComponentsResponse = await response.json();

// //       setComponents(result.data || []);
// //       setTotal(result.total || 0);

// //       if (result.filter_options) {
// //         setLots(result.filter_options.lots || []);
// //         setComponentTypes(result.filter_options.component_types || []);
// //         setDecisions(result.filter_options.screening_decisions || []);
// //       }
// //     } catch (err) {
// //       console.error(err);
// //       setError(
// //         "Unable to load component data. Check that the FastAPI backend is running.",
// //       );
// //       setComponents([]);
// //       setTotal(0);
// //     } finally {
// //       setLoading(false);
// //     }
// //   }

// //   useEffect(() => {
// //     loadComponents();
// //   }, [page, componentId, lotId, componentType, decision]);

// //   function resetFilters() {
// //     setComponentId("");
// //     setLotId("");
// //     setComponentType("");
// //     setDecision("");
// //     setPage(1);
// //   }

// //   const showingStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
// //   const showingEnd = Math.min(page * PAGE_SIZE, total);

// //   const hasFilters = componentId || lotId || componentType || decision;

// //   const pageNumbers = useMemo(() => {
// //     const pages: number[] = [];

// //     const start = Math.max(1, page - 2);
// //     const end = Math.min(totalPages, page + 2);

// //     for (let i = start; i <= end; i++) {
// //       pages.push(i);
// //     }

// //     return pages;
// //   }, [page, totalPages]);

// //   return (
// //     <main className="min-h-full bg-slate-50 text-slate-900 dark:bg-[#020618] dark:text-white">
// //       <div className="mx-auto w-full max-w-[1600px] px-5 pb-10 pt-5 lg:px-7">
// //         {/* Header */}
// //         <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
// //           <div>
// //             <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
// //               <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
// //               Screening fleet
// //             </div>

// //             <h1 className="text-2xl font-semibold tracking-tight">
// //               Components
// //             </h1>

// //             <p className="mt-1 max-w-2xl text-sm text-slate-500 dark:text-slate-400">
// //               Find components that require inspection and open an individual
// //               investigation when deeper evidence is needed.
// //             </p>
// //           </div>

// //           <div className="text-sm text-slate-500 dark:text-slate-400">
// //             Showing{" "}
// //             <span className="font-medium text-slate-900 dark:text-white">
// //               {showingStart}–{showingEnd}
// //             </span>{" "}
// //             of{" "}
// //             <span className="font-medium text-slate-900 dark:text-white">
// //               {total}
// //             </span>
// //           </div>
// //         </div>

// //         {/* Filters */}
// //         <section className="mb-5 rounded-xl border border-slate-200 bg-white     dark:border-slate-800 dark:bg-slate-900">
// //           <div className="flex flex-col gap-3 p-4 xl:flex-row xl:items-center">
// //             {/* Component search */}
// //             <div className="relative min-w-0 flex-1 xl:max-w-[310px]">
// //               <svg
// //                 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
// //                 viewBox="0 0 24 24"
// //                 fill="none"
// //                 stroke="currentColor"
// //                 strokeWidth="1.8"
// //               >
// //                 <circle cx="11" cy="11" r="7" />
// //                 <path d="m20 20-4-4" />
// //               </svg>

// //               <input
// //                 value={componentId}
// //                 onChange={(e) => {
// //                   setComponentId(e.target.value);
// //                   setPage(1);
// //                 }}
// //                 placeholder="Search component ID"
// //                 className="h-10 w-full rounded-lg border border-slate-200 bg-slate-50 pl-9 pr-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-slate-400 dark:border-white/[0.08] dark:bg-white/[0.025] dark:placeholder:text-slate-500 dark:focus:border-white/20"
// //               />
// //             </div>

// //             <select
// //               value={lotId}
// //               onChange={(e) => {
// //                 setLotId(e.target.value);
// //                 setPage(1);
// //               }}
// //               className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-white/[0.025] dark:text-slate-300"
// //             >
// //               <option value="">All lots</option>
// //               {lots.map((lot) => (
// //                 <option key={lot} value={lot}>
// //                   {lot}
// //                 </option>
// //               ))}
// //             </select>

// //             <select
// //               value={componentType}
// //               onChange={(e) => {
// //                 setComponentType(e.target.value);
// //                 setPage(1);
// //               }}
// //               className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-white/[0.025] dark:text-slate-300"
// //             >
// //               <option value="">All types</option>
// //               {componentTypes.map((type) => (
// //                 <option key={type} value={type}>
// //                   {type}
// //                 </option>
// //               ))}
// //             </select>

// //             <select
// //               value={decision}
// //               onChange={(e) => {
// //                 setDecision(e.target.value);
// //                 setPage(1);
// //               }}
// //               className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-white/[0.025] dark:text-slate-300"
// //             >
// //               <option value="">All decisions</option>
// //               {decisions.map((item) => (
// //                 <option key={item} value={item}>
// //                   {item}
// //                 </option>
// //               ))}
// //             </select>

// //             {hasFilters ? (
// //               <button
// //                 onClick={resetFilters}
// //                 className="h-10 rounded-lg px-3 text-sm text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/[0.05] dark:hover:text-white"
// //               >
// //                 Clear filters
// //               </button>
// //             ) : null}
// //           </div>
// //         </section>

// //         {/* Error */}
// //         {error ? (
// //           <div className="mb-5 rounded-xl border border-red-500/20 bg-red-500/[0.06] px-4 py-3 text-sm text-red-600 dark:text-red-400">
// //             {error}
// //           </div>
// //         ) : null}

// //         {/* Main table */}
// //         <section className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
// //           <div className="overflow-x-auto">
// //             <div className="min-w-[1050px]">
// //               {/* Table header */}
// //               <div className="grid grid-cols-[1.4fr_1fr_0.8fr_1fr_0.8fr_0.8fr_1fr_70px] gap-4 border-b border-slate-200 bg-slate-50/70 px-5 py-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-400 dark:border-white/[0.06] dark:bg-white/[0.015]">
// //                 <div>Component</div>
// //                 <div>Lot</div>
// //                 <div>Type</div>
// //                 <div>168H Iddq</div>
// //                 <div>Anomaly</div>
// //                 <div>Risk</div>
// //                 <div>Decision</div>
// //                 <div />
// //               </div>

// //               {loading ? (
// //                 <LoadingRows />
// //               ) : components.length === 0 ? (
// //                 <div className="flex min-h-[280px] items-center justify-center px-5">
// //                   <div className="text-center">
// //                     <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 dark:border-white/10">
// //                       <svg
// //                         className="h-5 w-5 text-slate-400"
// //                         viewBox="0 0 24 24"
// //                         fill="none"
// //                         stroke="currentColor"
// //                         strokeWidth="1.6"
// //                       >
// //                         <circle cx="11" cy="11" r="7" />
// //                         <path d="m20 20-4-4" />
// //                       </svg>
// //                     </div>

// //                     <p className="text-sm font-medium">No components found</p>

// //                     <p className="mt-1 text-xs text-slate-400">
// //                       Try changing or clearing your filters.
// //                     </p>
// //                   </div>
// //                 </div>
// //               ) : (
// //                 <div className="divide-y divide-slate-200 dark:divide-white/[0.06]">
// //                   {components.map((component) => {
// //                     const anomaly = isAnomaly(component.anomaly_flag);
// //                     const currentDecision = normalizeDecision(
// //                       component.screening_decision,
// //                     );

// //                     return (
// //                       <div
// //                         key={component.component_id}
// //                         className="grid grid-cols-[1.4fr_1fr_0.8fr_1fr_0.8fr_0.8fr_1fr_70px] items-center gap-4 px-5 py-4 transition hover:bg-slate-50 dark:hover:bg-white/[0.025]"
// //                       >
// //                         {/* Component */}
// //                         <div className="min-w-0">
// //                           <Link
// //                             href={`/components/${encodeURIComponent(
// //                               component.component_id,
// //                             )}`}
// //                             className="group inline-flex items-center gap-2"
// //                           >
// //                             <span className="h-1.5 w-1.5 rounded-full bg-slate-300 transition group-hover:bg-emerald-500 dark:bg-slate-600" />

// //                             <span className="truncate text-sm font-medium text-slate-900 group-hover:text-emerald-600 dark:text-slate-100 dark:group-hover:text-emerald-400">
// //                               {component.component_id}
// //                             </span>
// //                           </Link>
// //                         </div>

// //                         {/* Lot */}
// //                         <div className="text-sm text-slate-500 dark:text-slate-400">
// //                           {component.lot_id}
// //                         </div>

// //                         {/* Type */}
// //                         <div className="text-sm text-slate-500 dark:text-slate-400">
// //                           {component.component_type}
// //                         </div>

// //                         {/* 168H */}
// //                         <div>
// //                           <span className="font-mono text-sm text-slate-800 dark:text-slate-200">
// //                             {formatNumber(component.iddq_168h_uA)}
// //                           </span>
// //                           <span className="ml-1 text-[11px] text-slate-400">
// //                             µA
// //                           </span>
// //                         </div>

// //                         {/* Anomaly */}
// //                         <div>
// //                           {anomaly ? (
// //                             <span className="inline-flex items-center gap-1.5 text-sm font-medium text-amber-600 dark:text-amber-400">
// //                               <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
// //                               Detected
// //                             </span>
// //                           ) : (
// //                             <span className="text-sm text-slate-400">—</span>
// //                           )}
// //                         </div>

// //                         {/* Risk */}
// //                         <div>
// //                           <div
// //                             className={`font-mono text-sm font-medium ${riskClass(
// //                               component.risk_level,
// //                             )}`}
// //                           >
// //                             {formatNumber(component.risk_score_100, 1)}
// //                           </div>

// //                           <div className="mt-0.5 text-[10px] uppercase tracking-wider text-slate-400">
// //                             {component.risk_level || "—"}
// //                           </div>
// //                         </div>

// //                         {/* Decision */}
// //                         <div>
// //                           <span
// //                             className={`inline-flex rounded-md border px-2 py-1 text-[10px] font-semibold tracking-[0.08em] ${decisionClass(
// //                               currentDecision,
// //                             )}`}
// //                           >
// //                             {currentDecision || "—"}
// //                           </span>
// //                         </div>

// //                         {/* Inspect */}
// //                         <div className="text-right">
// //                           <Link
// //                             href={`/components/${encodeURIComponent(
// //                               component.component_id,
// //                             )}`}
// //                             className="group inline-flex items-center gap-2"
// //                           >
// //                             <div className="inline-flex h-8 items-center justify-center rounded-md border border-slate-200 px-2.5 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 dark:border-white/[0.08] dark:text-slate-400 dark:hover:border-white/15 dark:hover:bg-white/[0.04] dark:hover:text-white">
// //                               Inspect
// //                             </div>
// //                           </Link>
// //                         </div>
// //                       </div>
// //                     );
// //                   })}
// //                 </div>
// //               )}
// //             </div>
// //           </div>

// //           {/* Pagination */}
// //           {!loading && total > 0 ? (
// //             <div className="flex flex-col gap-3 border-t border-slate-200 px-5 py-3 sm:flex-row sm:items-center sm:justify-between dark:border-white/[0.06]">
// //               <div className="text-xs text-slate-400">
// //                 Page {page} of {totalPages}
// //               </div>

// //               <div className="flex items-center gap-1">
// //                 <button
// //                   disabled={page === 1}
// //                   onClick={() => setPage((current) => current - 1)}
// //                   className="h-8 rounded-md border border-slate-200 px-2.5 text-xs text-slate-500 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
// //                 >
// //                   Previous
// //                 </button>

// //                 {pageNumbers.map((pageNumber) => (
// //                   <button
// //                     key={pageNumber}
// //                     onClick={() => setPage(pageNumber)}
// //                     className={`h-8 min-w-8 rounded-md border px-2 text-xs transition ${
// //                       pageNumber === page
// //                         ? "border-slate-900 bg-slate-900 text-white dark:border-white dark:bg-white dark:text-slate-900"
// //                         : "border-slate-200 text-slate-500 hover:bg-slate-50 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
// //                     }`}
// //                   >
// //                     {pageNumber}
// //                   </button>
// //                 ))}

// //                 <button
// //                   disabled={page === totalPages}
// //                   onClick={() => setPage((current) => current + 1)}
// //                   className="h-8 rounded-md border border-slate-200 px-2.5 text-xs text-slate-500 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
// //                 >
// //                   Next
// //                 </button>
// //               </div>
// //             </div>
// //           ) : null}
// //         </section>
// //       </div>
// //     </main>
// //   );
// // }

// //! changed
// // "use client";

// // import { useEffect, useMemo, useState } from "react";

// // import Link from "next/link";

// // type ComponentRow = {
// //   component_id: string;
// //   lot_id: string;
// //   component_type: string;
// //   temperature_C: number;
// //   voltage_V: number;
// //   iddq_0h_uA: number;

// //   anomaly_flag: number | boolean;
// //   combined_anomaly_score: number;

// //   risk_score_100: number;
// //   risk_level: string;

// //   screening_decision: string;
// // };

// // type ComponentsResponse = {
// //   total: number;
// //   page: number;
// //   limit: number;

// //   filter_options?: {
// //     lots?: string[];
// //     component_types?: string[];
// //     screening_decisions?: string[];
// //   };

// //   data: ComponentRow[];
// // };

// // const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// // const PAGE_SIZE = 25;

// // function formatNumber(value: number | undefined | null, digits = 2) {
// //   if (value === undefined || value === null || Number.isNaN(value)) {
// //     return "—";
// //   }

// //   return value.toFixed(digits);
// // }

// // function isAnomaly(value: number | boolean) {
// //   return value === true || value === 1;
// // }

// // function normalizeDecision(value?: string) {
// //   return (value || "").toUpperCase();
// // }

// // function decisionClass(decision: string) {
// //   switch (decision) {
// //     case "REJECT":
// //       return "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400";

// //     case "REVIEW":
// //       return "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400";

// //     case "PASS":
// //       return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400";

// //     default:
// //       return "border-slate-300 bg-slate-100 text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300";
// //   }
// // }

// // function riskClass(level?: string) {
// //   switch ((level || "").toUpperCase()) {
// //     case "CRITICAL":
// //       return "text-red-600 dark:text-red-400";

// //     case "HIGH":
// //       return "text-orange-600 dark:text-orange-400";

// //     case "MEDIUM":
// //       return "text-amber-600 dark:text-amber-400";

// //     case "LOW":
// //       return "text-emerald-600 dark:text-emerald-400";

// //     default:
// //       return "text-slate-600 dark:text-slate-300";
// //   }
// // }

// // function LoadingRows() {
// //   return (
// //     <div className="divide-y divide-slate-200 dark:divide-white/[0.06]">
// //       {Array.from({ length: 8 }).map((_, index) => (
// //         <div
// //           key={index}
// //           className="grid grid-cols-[1.4fr_1fr_0.8fr_1fr_0.8fr_0.8fr_1fr_70px] gap-3 px-5 py-4"
// //         >
// //           {Array.from({ length: 8 }).map((__, cell) => (
// //             <div
// //               key={cell}
// //               className="h-4 animate-pulse rounded bg-slate-200 dark:bg-white/[0.06]"
// //             />
// //           ))}
// //         </div>
// //       ))}
// //     </div>
// //   );
// // }

// // export default function ComponentsPage() {
// //   const [components, setComponents] = useState<ComponentRow[]>([]);
// //   const [total, setTotal] = useState(0);

// //   const [page, setPage] = useState(1);

// //   const [componentId, setComponentId] = useState("");
// //   const [lotId, setLotId] = useState("");
// //   const [componentType, setComponentType] = useState("");
// //   const [decision, setDecision] = useState("");

// //   const [lots, setLots] = useState<string[]>([]);
// //   const [componentTypes, setComponentTypes] = useState<string[]>([]);
// //   const [decisions, setDecisions] = useState<string[]>([]);

// //   const [loading, setLoading] = useState(true);
// //   const [error, setError] = useState("");

// //   const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

// //   async function loadComponents() {
// //     try {
// //       setLoading(true);
// //       setError("");

// //       const params = new URLSearchParams({
// //         page: String(page),
// //         limit: String(PAGE_SIZE),
// //       });

// //       if (componentId.trim()) {
// //         params.set("component_id", componentId.trim());
// //       }

// //       if (lotId) {
// //         params.set("lot_id", lotId);
// //       }

// //       if (componentType) {
// //         params.set("component_type", componentType);
// //       }

// //       if (decision) {
// //         params.set("screening_decision", decision);
// //       }

// //       const response = await fetch(
// //         `${API_BASE}/api/components/?${params.toString()}`,
// //         {
// //           cache: "no-store",
// //         },
// //       );

// //       if (!response.ok) {
// //         throw new Error(`Backend returned ${response.status}`);
// //       }

// //       const result: ComponentsResponse = await response.json();

// //       setComponents(result.data || []);
// //       setTotal(result.total || 0);

// //       if (result.filter_options) {
// //         setLots(result.filter_options.lots || []);

// //         setComponentTypes(result.filter_options.component_types || []);

// //         setDecisions(result.filter_options.screening_decisions || []);
// //       }
// //     } catch (err) {
// //       console.error(err);

// //       setError(
// //         "Unable to load component data. Check that the FastAPI backend is running.",
// //       );

// //       setComponents([]);
// //       setTotal(0);
// //     } finally {
// //       setLoading(false);
// //     }
// //   }

// //   useEffect(() => {
// //     loadComponents();
// //   }, [page, componentId, lotId, componentType, decision]);

// //   function resetFilters() {
// //     setComponentId("");
// //     setLotId("");
// //     setComponentType("");
// //     setDecision("");
// //     setPage(1);
// //   }

// //   const showingStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;

// //   const showingEnd = Math.min(page * PAGE_SIZE, total);

// //   const hasFilters = componentId || lotId || componentType || decision;

// //   const pageNumbers = useMemo(() => {
// //     const pages: number[] = [];

// //     const start = Math.max(1, page - 2);
// //     const end = Math.min(totalPages, page + 2);

// //     for (let i = start; i <= end; i++) {
// //       pages.push(i);
// //     }

// //     return pages;
// //   }, [page, totalPages]);

// //   return (
// //     <main className="min-h-full bg-slate-50 text-slate-900 dark:bg-[#020618] dark:text-white">
// //       <div className="mx-auto w-full max-w-[1600px] px-5 pb-10 pt-5 lg:px-7">
// //         {/* Header */}

// //         <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
// //           <div>
// //             <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
// //               <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
// //               Screening fleet
// //             </div>

// //             <h1 className="text-2xl font-semibold tracking-tight">
// //               Components
// //             </h1>

// //             <p className="mt-1 max-w-2xl text-sm text-slate-500 dark:text-slate-400">
// //               Find components that require inspection and open an individual
// //               investigation when deeper evidence is needed.
// //             </p>
// //           </div>

// //           <div className="text-sm text-slate-500 dark:text-slate-400">
// //             Showing{" "}
// //             <span className="font-medium text-slate-900 dark:text-white">
// //               {showingStart}–{showingEnd}
// //             </span>{" "}
// //             of{" "}
// //             <span className="font-medium text-slate-900 dark:text-white">
// //               {total}
// //             </span>
// //           </div>
// //         </div>

// //         {/* Filters */}

// //         <section className="mb-5 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
// //           <div className="flex flex-col gap-3 p-4 xl:flex-row xl:items-center">
// //             {/* Component search */}

// //             <div className="relative min-w-0 flex-1 xl:max-w-[310px]">
// //               <svg
// //                 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
// //                 viewBox="0 0 24 24"
// //                 fill="none"
// //                 stroke="currentColor"
// //                 strokeWidth="1.8"
// //               >
// //                 <circle cx="11" cy="11" r="7" />
// //                 <path d="m20 20-4-4" />
// //               </svg>

// //               <input
// //                 value={componentId}
// //                 onChange={(e) => {
// //                   setComponentId(e.target.value);
// //                   setPage(1);
// //                 }}
// //                 placeholder="Search component ID"
// //                 className="h-10 w-full rounded-lg border border-slate-200 bg-slate-50 pl-9 pr-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-slate-400 dark:border-white/[0.08] dark:bg-white/[0.025] dark:placeholder:text-slate-500 dark:focus:border-white/20"
// //               />
// //             </div>

// //             <select
// //               value={lotId}
// //               onChange={(e) => {
// //                 setLotId(e.target.value);
// //                 setPage(1);
// //               }}
// //               className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-white/[0.025] dark:text-slate-300"
// //             >
// //               <option value="">All lots</option>

// //               {lots.map((lot) => (
// //                 <option key={lot} value={lot}>
// //                   {lot}
// //                 </option>
// //               ))}
// //             </select>

// //             <select
// //               value={componentType}
// //               onChange={(e) => {
// //                 setComponentType(e.target.value);
// //                 setPage(1);
// //               }}
// //               className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-white/[0.025] dark:text-slate-300"
// //             >
// //               <option value="">All types</option>

// //               {componentTypes.map((type) => (
// //                 <option key={type} value={type}>
// //                   {type}
// //                 </option>
// //               ))}
// //             </select>

// //             <select
// //               value={decision}
// //               onChange={(e) => {
// //                 setDecision(e.target.value);
// //                 setPage(1);
// //               }}
// //               className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-white/[0.025] dark:text-slate-300"
// //             >
// //               <option value="">All decisions</option>

// //               {decisions.map((item) => (
// //                 <option key={item} value={item}>
// //                   {item}
// //                 </option>
// //               ))}
// //             </select>

// //             {hasFilters ? (
// //               <button
// //                 onClick={resetFilters}
// //                 className="h-10 rounded-lg px-3 text-sm text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/[0.05] dark:hover:text-white"
// //               >
// //                 Clear filters
// //               </button>
// //             ) : null}
// //           </div>
// //         </section>

// //         {/* Error */}

// //         {error ? (
// //           <div className="mb-5 rounded-xl border border-red-500/20 bg-red-500/[0.06] px-4 py-3 text-sm text-red-600 dark:text-red-400">
// //             {error}
// //           </div>
// //         ) : null}

// //         {/* Main table */}

// //         <section className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
// //           <div className="w-full">
// //             <div className="w-full">
// //               {/* Table header */}

// //               <div className="grid grid-cols-[1.4fr_1fr_0.8fr_1fr_0.8fr_0.8fr_1fr_70px] gap-3 border-b border-slate-200 bg-slate-50/70 px-5 py-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-400 dark:border-white/[0.06] dark:bg-white/[0.015]">
// //                 <div>Component</div>
// //                 <div>Lot</div>
// //                 <div>Type</div>
// //                 <div>0H Iddq</div>
// //                 <div>Anomaly</div>
// //                 <div>Risk</div>
// //                 <div>Decision</div>
// //                 <div />
// //               </div>

// //               {loading ? (
// //                 <LoadingRows />
// //               ) : components.length === 0 ? (
// //                 <div className="flex min-h-[280px] items-center justify-center px-5">
// //                   <div className="text-center">
// //                     <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 dark:border-white/10">
// //                       <svg
// //                         className="h-5 w-5 text-slate-400"
// //                         viewBox="0 0 24 24"
// //                         fill="none"
// //                         stroke="currentColor"
// //                         strokeWidth="1.6"
// //                       >
// //                         <circle cx="11" cy="11" r="7" />
// //                         <path d="m20 20-4-4" />
// //                       </svg>
// //                     </div>

// //                     <p className="text-sm font-medium">No components found</p>

// //                     <p className="mt-1 text-xs text-slate-400">
// //                       Try changing or clearing your filters.
// //                     </p>
// //                   </div>
// //                 </div>
// //               ) : (
// //                 <div className="divide-y divide-slate-200 dark:divide-white/[0.06]">
// //                   {components.map((component) => {
// //                     const anomaly = isAnomaly(component.anomaly_flag);

// //                     const currentDecision = normalizeDecision(
// //                       component.screening_decision,
// //                     );

// //                     return (
// //                       <div
// //                         key={component.component_id}
// //                         className="grid grid-cols-[1.4fr_1fr_0.8fr_1fr_0.8fr_0.8fr_1fr_70px] items-center gap-3 px-5 py-4 transition hover:bg-slate-50 dark:hover:bg-white/[0.025]"
// //                       >
// //                         {/* Component */}

// //                         <div className="min-w-0">
// //                           <Link
// //                             href={`/components/${encodeURIComponent(
// //                               component.component_id,
// //                             )}`}
// //                             className="group inline-flex items-center gap-2"
// //                           >
// //                             <span className="h-1.5 w-1.5 rounded-full bg-slate-300 transition group-hover:bg-emerald-500 dark:bg-slate-600" />

// //                             <span className="truncate text-sm font-medium text-slate-900 group-hover:text-emerald-600 dark:text-slate-100 dark:group-hover:text-emerald-400">
// //                               {component.component_id}
// //                             </span>
// //                           </Link>
// //                         </div>

// //                         {/* Lot */}

// //                         <div className="text-sm text-slate-500 dark:text-slate-400">
// //                           {component.lot_id}
// //                         </div>

// //                         {/* Type */}

// //                         <div className="text-sm text-slate-500 dark:text-slate-400">
// //                           {component.component_type}
// //                         </div>

// //                         {/* 0H Iddq */}

// //                         <div>
// //                           <span className="font-mono text-sm text-slate-800 dark:text-slate-200">
// //                             {formatNumber(component.iddq_0h_uA)}
// //                           </span>

// //                           <span className="ml-1 text-[11px] text-slate-400">
// //                             µA
// //                           </span>
// //                         </div>

// //                         {/* Anomaly */}

// //                         <div>
// //                           {anomaly ? (
// //                             <span className="inline-flex items-center gap-1.5 text-sm font-medium text-amber-600 dark:text-amber-400">
// //                               <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
// //                               Detected
// //                             </span>
// //                           ) : (
// //                             <span className="text-sm text-slate-400">—</span>
// //                           )}
// //                         </div>

// //                         {/* Risk */}

// //                         <div>
// //                           <div
// //                             className={`font-mono text-sm font-medium ${riskClass(
// //                               component.risk_level,
// //                             )}`}
// //                           >
// //                             {formatNumber(component.risk_score_100, 1)}
// //                           </div>

// //                           <div className="mt-0.5 text-[10px] uppercase tracking-wider text-slate-400">
// //                             {component.risk_level || "—"}
// //                           </div>
// //                         </div>

// //                         {/* Decision */}

// //                         <div>
// //                           <span
// //                             className={`inline-flex rounded-md border px-2 py-1 text-[10px] font-semibold tracking-[0.08em] ${decisionClass(
// //                               currentDecision,
// //                             )}`}
// //                           >
// //                             {currentDecision || "—"}
// //                           </span>
// //                         </div>

// //                         {/* Inspect */}

// //                         <div className="text-right">
// //                           <Link
// //                             href={`/components/${encodeURIComponent(
// //                               component.component_id,
// //                             )}`}
// //                             className="group inline-flex items-center gap-2"
// //                           >
// //                             <div className="inline-flex h-8 items-center justify-center rounded-md border border-slate-200 px-2.5 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 dark:border-white/[0.08] dark:text-slate-400 dark:hover:border-white/15 dark:hover:bg-white/[0.04] dark:hover:text-white">
// //                               Inspect
// //                             </div>
// //                           </Link>
// //                         </div>
// //                       </div>
// //                     );
// //                   })}
// //                 </div>
// //               )}
// //             </div>
// //           </div>

// //           {/* Pagination */}

// //           {!loading && total > 0 ? (
// //             <div className="flex flex-col gap-3 border-t border-slate-200 px-5 py-3 sm:flex-row sm:items-center sm:justify-between dark:border-white/[0.06]">
// //               <div className="text-xs text-slate-400">
// //                 Page {page} of {totalPages}
// //               </div>

// //               <div className="flex items-center gap-1">
// //                 <button
// //                   disabled={page === 1}
// //                   onClick={() => setPage((current) => current - 1)}
// //                   className="h-8 rounded-md border border-slate-200 px-2.5 text-xs text-slate-500 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
// //                 >
// //                   Previous
// //                 </button>

// //                 {pageNumbers.map((pageNumber) => (
// //                   <button
// //                     key={pageNumber}
// //                     onClick={() => setPage(pageNumber)}
// //                     className={`h-8 min-w-8 rounded-md border px-2 text-xs transition ${
// //                       pageNumber === page
// //                         ? "border-slate-900 bg-slate-900 text-white dark:border-white dark:bg-white dark:text-slate-900"
// //                         : "border-slate-200 text-slate-500 hover:bg-slate-50 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
// //                     }`}
// //                   >
// //                     {pageNumber}
// //                   </button>
// //                 ))}

// //                 <button
// //                   disabled={page === totalPages}
// //                   onClick={() => setPage((current) => current + 1)}
// //                   className="h-8 rounded-md border border-slate-200 px-2.5 text-xs text-slate-500 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
// //                 >
// //                   Next
// //                 </button>
// //               </div>
// //             </div>
// //           ) : null}
// //         </section>
// //       </div>
// //     </main>
// //   );
// // }

// //! second change
// // "use client";

// // import { useEffect, useMemo, useState } from "react";

// // import Link from "next/link";

// // type ComponentRow = {
// //   component_id: string;
// //   lot_id: string;
// //   component_type: string;
// //   temperature_C: number;
// //   voltage_V: number;
// //   iddq_0h_uA: number;

// //   anomaly_flag: number | boolean;
// //   combined_anomaly_score: number;

// //   risk_score: number | null;
// //   risk_bucket: string | null;

// //   qa_classification: string | null;
// //   final_decision: string | null;
// // };

// // type ComponentsResponse = {
// //   total: number;
// //   page: number;
// //   limit: number;

// //   filter_options?: {
// //     lots?: string[];
// //     component_types?: string[];
// //     screening_decisions?: string[];
// //   };

// //   data: ComponentRow[];
// // };

// // const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// // const PAGE_SIZE = 25;

// // function formatNumber(value: number | undefined | null, digits = 2) {
// //   if (value === undefined || value === null || Number.isNaN(value)) {
// //     return "—";
// //   }

// //   return value.toFixed(digits);
// // }

// // function isAnomaly(value: number | boolean) {
// //   return value === true || value === 1;
// // }

// // function normalizeDecision(value?: string | null) {
// //   return (value || "").toUpperCase();
// // }

// // function decisionClass(decision: string) {
// //   switch (decision) {
// //     case "REJECT":
// //       return "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400";

// //     case "REVIEW":
// //       return "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400";

// //     case "PASS":
// //       return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400";

// //     case "PRIORITY_SCREENING":
// //       return "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400";

// //     case "ENHANCED_MONITORING":
// //       return "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400";

// //     case "IMMEDIATE_REVIEW":
// //       return "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400";

// //     case "MONITOR":
// //       return "border-slate-300 bg-slate-100 text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300";

// //     case "NORMAL":
// //       return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400";

// //     default:
// //       return "border-slate-300 bg-slate-100 text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300";
// //   }
// // }

// // function riskClass(level?: string | null) {
// //   switch ((level || "").toUpperCase()) {
// //     case "CRITICAL":
// //       return "text-red-600 dark:text-red-400";

// //     case "HIGH":
// //       return "text-orange-600 dark:text-orange-400";

// //     case "MEDIUM":
// //       return "text-amber-600 dark:text-amber-400";

// //     case "LOW":
// //       return "text-emerald-600 dark:text-emerald-400";

// //     default:
// //       return "text-slate-600 dark:text-slate-300";
// //   }
// // }

// // function LoadingRows() {
// //   return (
// //     <div className="divide-y divide-slate-200 dark:divide-white/[0.06]">
// //       {Array.from({ length: 8 }).map((_, index) => (
// //         <div
// //           key={index}
// //           className="grid grid-cols-[1.4fr_1fr_0.8fr_1fr_0.8fr_0.8fr_1fr_70px] gap-3 px-5 py-4"
// //         >
// //           {Array.from({ length: 8 }).map((__, cell) => (
// //             <div
// //               key={cell}
// //               className="h-4 animate-pulse rounded bg-slate-200 dark:bg-white/[0.06]"
// //             />
// //           ))}
// //         </div>
// //       ))}
// //     </div>
// //   );
// // }

// // export default function ComponentsPage() {
// //   const [components, setComponents] = useState<ComponentRow[]>([]);

// //   const [total, setTotal] = useState(0);
// //   const [page, setPage] = useState(1);

// //   const [componentId, setComponentId] = useState("");
// //   const [lotId, setLotId] = useState("");
// //   const [componentType, setComponentType] = useState("");
// //   const [decision, setDecision] = useState("");

// //   const [lots, setLots] = useState<string[]>([]);
// //   const [componentTypes, setComponentTypes] = useState<string[]>([]);
// //   const [decisions, setDecisions] = useState<string[]>([]);

// //   const [loading, setLoading] = useState(true);
// //   const [error, setError] = useState("");

// //   const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

// //   async function loadComponents() {
// //     try {
// //       setLoading(true);
// //       setError("");

// //       const params = new URLSearchParams({
// //         page: String(page),
// //         limit: String(PAGE_SIZE),
// //       });

// //       if (componentId.trim()) {
// //         params.set("component_id", componentId.trim());
// //       }

// //       if (lotId) {
// //         params.set("lot_id", lotId);
// //       }

// //       if (componentType) {
// //         params.set("component_type", componentType);
// //       }

// //       if (decision) {
// //         params.set("screening_decision", decision);
// //       }

// //       const response = await fetch(
// //         `${API_BASE}/api/components/?${params.toString()}`,
// //         {
// //           cache: "no-store",
// //         },
// //       );

// //       if (!response.ok) {
// //         throw new Error(`Backend returned ${response.status}`);
// //       }

// //       const result: ComponentsResponse = await response.json();

// //       setComponents(result.data || []);
// //       setTotal(result.total || 0);

// //       if (result.filter_options) {
// //         setLots(result.filter_options.lots || []);

// //         setComponentTypes(result.filter_options.component_types || []);

// //         setDecisions(result.filter_options.screening_decisions || []);
// //       }
// //     } catch (err) {
// //       console.error(err);

// //       setError(
// //         "Unable to load component data. Check that the FastAPI backend is running.",
// //       );

// //       setComponents([]);
// //       setTotal(0);
// //     } finally {
// //       setLoading(false);
// //     }
// //   }

// //   useEffect(() => {
// //     loadComponents();
// //   }, [page, componentId, lotId, componentType, decision]);

// //   function resetFilters() {
// //     setComponentId("");
// //     setLotId("");
// //     setComponentType("");
// //     setDecision("");
// //     setPage(1);
// //   }

// //   const showingStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;

// //   const showingEnd = Math.min(page * PAGE_SIZE, total);

// //   const hasFilters = componentId || lotId || componentType || decision;

// //   const pageNumbers = useMemo(() => {
// //     const pages: number[] = [];

// //     const start = Math.max(1, page - 2);

// //     const end = Math.min(totalPages, page + 2);

// //     for (let i = start; i <= end; i++) {
// //       pages.push(i);
// //     }

// //     return pages;
// //   }, [page, totalPages]);

// //   return (
// //     <main className="min-h-full bg-slate-50 text-slate-900 dark:bg-[#020618] dark:text-white">
// //       <div className="mx-auto w-full max-w-[1600px] px-5 pb-10 pt-5 lg:px-7">
// //         {/* Header */}

// //         <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
// //           <div>
// //             <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
// //               <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
// //               Screening fleet
// //             </div>

// //             <h1 className="text-2xl font-semibold tracking-tight">
// //               Components
// //             </h1>

// //             <p className="mt-1 max-w-2xl text-sm text-slate-500 dark:text-slate-400">
// //               Find components that require inspection and open an individual
// //               investigation when deeper evidence is needed.
// //             </p>
// //           </div>

// //           <div className="text-sm text-slate-500 dark:text-slate-400">
// //             Showing{" "}
// //             <span className="font-medium text-slate-900 dark:text-white">
// //               {showingStart}–{showingEnd}
// //             </span>{" "}
// //             of{" "}
// //             <span className="font-medium text-slate-900 dark:text-white">
// //               {total}
// //             </span>
// //           </div>
// //         </div>

// //         {/* Filters */}

// //         <section className="mb-5 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
// //           <div className="flex flex-col gap-3 p-4 xl:flex-row xl:items-center">
// //             {/* Component search */}

// //             <div className="relative min-w-0 flex-1 xl:max-w-[310px]">
// //               <svg
// //                 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
// //                 viewBox="0 0 24 24"
// //                 fill="none"
// //                 stroke="currentColor"
// //                 strokeWidth="1.8"
// //               >
// //                 <circle cx="11" cy="11" r="7" />
// //                 <path d="m20 20-4-4" />
// //               </svg>

// //               <input
// //                 value={componentId}
// //                 onChange={(e) => {
// //                   setComponentId(e.target.value);
// //                   setPage(1);
// //                 }}
// //                 placeholder="Search component ID"
// //                 className="h-10 w-full rounded-lg border border-slate-200 bg-slate-50 pl-9 pr-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-slate-400 dark:border-white/[0.08] dark:bg-white/[0.025] dark:placeholder:text-slate-500 dark:focus:border-white/20"
// //               />
// //             </div>

// //             <select
// //               value={lotId}
// //               onChange={(e) => {
// //                 setLotId(e.target.value);
// //                 setPage(1);
// //               }}
// //               className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-white/[0.025] dark:text-slate-300"
// //             >
// //               <option value="">All lots</option>

// //               {lots.map((lot) => (
// //                 <option key={lot} value={lot}>
// //                   {lot}
// //                 </option>
// //               ))}
// //             </select>

// //             <select
// //               value={componentType}
// //               onChange={(e) => {
// //                 setComponentType(e.target.value);
// //                 setPage(1);
// //               }}
// //               className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-white/[0.025] dark:text-slate-300"
// //             >
// //               <option value="">All types</option>

// //               {componentTypes.map((type) => (
// //                 <option key={type} value={type}>
// //                   {type}
// //                 </option>
// //               ))}
// //             </select>

// //             <select
// //               value={decision}
// //               onChange={(e) => {
// //                 setDecision(e.target.value);
// //                 setPage(1);
// //               }}
// //               className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-white/[0.025] dark:text-slate-300"
// //             >
// //               <option value="">All decisions</option>

// //               {decisions.map((item) => (
// //                 <option key={item} value={item}>
// //                   {item}
// //                 </option>
// //               ))}
// //             </select>

// //             {hasFilters ? (
// //               <button
// //                 onClick={resetFilters}
// //                 className="h-10 rounded-lg px-3 text-sm text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/[0.05] dark:hover:text-white"
// //               >
// //                 Clear filters
// //               </button>
// //             ) : null}
// //           </div>
// //         </section>

// //         {/* Error */}

// //         {error ? (
// //           <div className="mb-5 rounded-xl border border-red-500/20 bg-red-500/[0.06] px-4 py-3 text-sm text-red-600 dark:text-red-400">
// //             {error}
// //           </div>
// //         ) : null}

// //         {/* Main table */}

// //         <section className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
// //           <div className="w-full">
// //             <div className="w-full">
// //               {/* Table header */}

// //               <div className="grid grid-cols-[1.4fr_1fr_0.8fr_1fr_0.8fr_0.8fr_1fr_70px] gap-3 border-b border-slate-200 bg-slate-50/70 px-5 py-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-400 dark:border-white/[0.06] dark:bg-white/[0.015]">
// //                 <div>Component</div>
// //                 <div>Lot</div>
// //                 <div>Type</div>
// //                 <div>0H Iddq</div>
// //                 <div>Anomaly</div>
// //                 <div>Risk</div>
// //                 <div>Decision</div>
// //                 <div />
// //               </div>

// //               {loading ? (
// //                 <LoadingRows />
// //               ) : components.length === 0 ? (
// //                 <div className="flex min-h-[280px] items-center justify-center px-5">
// //                   <div className="text-center">
// //                     <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 dark:border-white/10">
// //                       <svg
// //                         className="h-5 w-5 text-slate-400"
// //                         viewBox="0 0 24 24"
// //                         fill="none"
// //                         stroke="currentColor"
// //                         strokeWidth="1.6"
// //                       >
// //                         <circle cx="11" cy="11" r="7" />
// //                         <path d="m20 20-4-4" />
// //                       </svg>
// //                     </div>

// //                     <p className="text-sm font-medium">No components found</p>

// //                     <p className="mt-1 text-xs text-slate-400">
// //                       Try changing or clearing your filters.
// //                     </p>
// //                   </div>
// //                 </div>
// //               ) : (
// //                 <div className="divide-y divide-slate-200 dark:divide-white/[0.06]">
// //                   {components.map((component) => {
// //                     const anomaly = isAnomaly(component.anomaly_flag);

// //                     const currentDecision = normalizeDecision(
// //                       component.final_decision,
// //                     );

// //                     return (
// //                       <div
// //                         key={component.component_id}
// //                         className="grid grid-cols-[1.4fr_1fr_0.8fr_1fr_0.8fr_0.8fr_1fr_70px] items-center gap-3 px-5 py-4 transition hover:bg-slate-50 dark:hover:bg-white/[0.025]"
// //                       >
// //                         {/* Component */}

// //                         <div className="min-w-0">
// //                           <Link
// //                             href={`/components/${encodeURIComponent(
// //                               component.component_id,
// //                             )}`}
// //                             className="group inline-flex items-center gap-2"
// //                           >
// //                             <span className="h-1.5 w-1.5 rounded-full bg-slate-300 transition group-hover:bg-emerald-500 dark:bg-slate-600" />

// //                             <span className="truncate text-sm font-medium text-slate-900 group-hover:text-emerald-600 dark:text-slate-100 dark:group-hover:text-emerald-400">
// //                               {component.component_id}
// //                             </span>
// //                           </Link>
// //                         </div>

// //                         {/* Lot */}

// //                         <div className="text-sm text-slate-500 dark:text-slate-400">
// //                           {component.lot_id}
// //                         </div>

// //                         {/* Type */}

// //                         <div className="text-sm text-slate-500 dark:text-slate-400">
// //                           {component.component_type}
// //                         </div>

// //                         {/* 0H Iddq */}

// //                         <div>
// //                           <span className="font-mono text-sm text-slate-800 dark:text-slate-200">
// //                             {formatNumber(component.iddq_0h_uA)}
// //                           </span>

// //                           <span className="ml-1 text-[11px] text-slate-400">
// //                             µA
// //                           </span>
// //                         </div>

// //                         {/* Anomaly */}

// //                         <div>
// //                           {anomaly ? (
// //                             <span className="inline-flex items-center gap-1.5 text-sm font-medium text-amber-600 dark:text-amber-400">
// //                               <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
// //                               Detected
// //                             </span>
// //                           ) : (
// //                             <span className="inline-flex items-center gap-1.5 text-sm text-slate-400">
// //                               <span className="h-1.5 w-1.5 rounded-full bg-slate-300 dark:bg-slate-600" />
// //                               Normal
// //                             </span>
// //                           )}
// //                         </div>

// //                         {/* Risk */}

// //                         <div>
// //                           <div
// //                             className={`font-mono text-sm font-medium ${riskClass(
// //                               component.risk_bucket,
// //                             )}`}
// //                           >
// //                             {formatNumber(component.risk_score, 1)}
// //                           </div>

// //                           <div className="mt-0.5 text-[10px] uppercase tracking-wider text-slate-400">
// //                             {component.risk_bucket || "—"}
// //                           </div>
// //                         </div>

// //                         {/* Decision */}

// //                         <div>
// //                           <span
// //                             className={`inline-flex rounded-md border px-2 py-1 text-[10px] font-semibold tracking-[0.08em] ${decisionClass(
// //                               currentDecision,
// //                             )}`}
// //                           >
// //                             {currentDecision || "—"}
// //                           </span>
// //                         </div>

// //                         {/* Inspect */}

// //                         <div className="text-right">
// //                           <Link
// //                             href={`/components/${encodeURIComponent(
// //                               component.component_id,
// //                             )}`}
// //                             className="group inline-flex items-center gap-2"
// //                           >
// //                             <div className="inline-flex h-8 items-center justify-center rounded-md border border-slate-200 px-2.5 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 dark:border-white/[0.08] dark:text-slate-400 dark:hover:border-white/15 dark:hover:bg-white/[0.04] dark:hover:text-white">
// //                               Inspect
// //                             </div>
// //                           </Link>
// //                         </div>
// //                       </div>
// //                     );
// //                   })}
// //                 </div>
// //               )}
// //             </div>
// //           </div>

// //           {/* Pagination */}

// //           {!loading && total > 0 ? (
// //             <div className="flex flex-col gap-3 border-t border-slate-200 px-5 py-3 sm:flex-row sm:items-center sm:justify-between dark:border-white/[0.06]">
// //               <div className="text-xs text-slate-400">
// //                 Page {page} of {totalPages}
// //               </div>

// //               <div className="flex items-center gap-1">
// //                 <button
// //                   disabled={page === 1}
// //                   onClick={() => setPage((current) => current - 1)}
// //                   className="h-8 rounded-md border border-slate-200 px-2.5 text-xs text-slate-500 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
// //                 >
// //                   Previous
// //                 </button>

// //                 {pageNumbers.map((pageNumber) => (
// //                   <button
// //                     key={pageNumber}
// //                     onClick={() => setPage(pageNumber)}
// //                     className={`h-8 min-w-8 rounded-md border px-2 text-xs transition ${
// //                       pageNumber === page
// //                         ? "border-slate-900 bg-slate-900 text-white dark:border-white dark:bg-white dark:text-slate-900"
// //                         : "border-slate-200 text-slate-500 hover:bg-slate-50 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
// //                     }`}
// //                   >
// //                     {pageNumber}
// //                   </button>
// //                 ))}

// //                 <button
// //                   disabled={page === totalPages}
// //                   onClick={() => setPage((current) => current + 1)}
// //                   className="h-8 rounded-md border border-slate-200 px-2.5 text-xs text-slate-500 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
// //                 >
// //                   Next
// //                 </button>
// //               </div>
// //             </div>
// //           ) : null}
// //         </section>
// //       </div>
// //     </main>
// //   );
// // }

// //! updated third code maybe
// "use client";

// import { useEffect, useMemo, useState } from "react";
// import Link from "next/link";

// type ComponentRow = {
//   component_id: string;
//   lot_id: string;
//   component_type: string;
//   temperature_C: number;
//   voltage_V: number;
//   iddq_0h_uA: number;
//   anomaly_flag: number | boolean;
//   combined_anomaly_score: number;
//   risk_score: number | null;
//   risk_bucket: string | null;
//   qa_classification: string | null;
//   final_decision: string | null;
// };

// type ComponentsResponse = {
//   total: number;
//   page: number;
//   limit: number;
//   filter_options?: {
//     lots?: string[];
//     component_types?: string[];
//     screening_decisions?: string[];
//   };
//   data: ComponentRow[];
// };

// const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// const PAGE_SIZE = 25;

// function formatNumber(value: number | undefined | null, digits = 2) {
//   if (value === undefined || value === null || Number.isNaN(value)) {
//     return "—";
//   }

//   return value.toFixed(digits);
// }

// function isAnomaly(value: number | boolean) {
//   return value === true || value === 1;
// }

// function normalizeDecision(value?: string | null) {
//   return (value || "").toUpperCase();
// }

// function decisionClass(decision: string) {
//   switch (decision) {
//     case "REJECT":
//       return "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400";

//     case "REVIEW":
//       return "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400";

//     case "PASS":
//       return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400";

//     case "PRIORITY_SCREENING":
//       return "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400";

//     case "ENHANCED_MONITORING":
//       return "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400";

//     case "IMMEDIATE_REVIEW":
//       return "border-red-500/30 bg-red-500/10 text-red-600 dark:text-red-400";

//     case "MONITOR":
//       return "border-slate-300 bg-slate-100 text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300";

//     case "NORMAL":
//       return "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400";

//     default:
//       return "border-slate-300 bg-slate-100 text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300";
//   }
// }

// function riskClass(level?: string | null) {
//   switch ((level || "").toUpperCase()) {
//     case "CRITICAL":
//       return "text-red-600 dark:text-red-400";

//     case "HIGH":
//       return "text-orange-600 dark:text-orange-400";

//     case "MEDIUM":
//       return "text-amber-600 dark:text-amber-400";

//     case "LOW":
//       return "text-emerald-600 dark:text-emerald-400";

//     default:
//       return "text-slate-600 dark:text-slate-300";
//   }
// }

// function LoadingRows() {
//   return (
//     <div className="divide-y divide-slate-200 dark:divide-white/[0.06]">
//       {Array.from({ length: 8 }).map((_, index) => (
//         <div
//           key={index}
//           className="grid grid-cols-[1.5fr_0.9fr_0.9fr_1fr_1fr_0.8fr_1.2fr_80px] gap-3 px-5 py-4"
//         >
//           {Array.from({ length: 8 }).map((__, cell) => (
//             <div
//               key={cell}
//               className="h-4 animate-pulse rounded bg-slate-200 dark:bg-white/[0.06]"
//             />
//           ))}
//         </div>
//       ))}
//     </div>
//   );
// }

// export default function ComponentsPage() {
//   const [components, setComponents] = useState<ComponentRow[]>([]);
//   const [total, setTotal] = useState(0);
//   const [page, setPage] = useState(1);

//   const [componentId, setComponentId] = useState("");
//   const [lotId, setLotId] = useState("");
//   const [componentType, setComponentType] = useState("");
//   const [decision, setDecision] = useState("");

//   const [lots, setLots] = useState<string[]>([]);
//   const [componentTypes, setComponentTypes] = useState<string[]>([]);
//   const [decisions, setDecisions] = useState<string[]>([]);

//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState("");

//   const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

//   async function loadComponents() {
//     try {
//       setLoading(true);
//       setError("");

//       const params = new URLSearchParams({
//         page: String(page),
//         limit: String(PAGE_SIZE),
//       });

//       if (componentId.trim()) {
//         params.set("component_id", componentId.trim());
//       }

//       if (lotId) {
//         params.set("lot_id", lotId);
//       }

//       if (componentType) {
//         params.set("component_type", componentType);
//       }

//       if (decision) {
//         params.set("screening_decision", decision);
//       }

//       const response = await fetch(
//         `${API_BASE}/api/components/?${params.toString()}`,
//         {
//           cache: "no-store",
//         },
//       );

//       if (!response.ok) {
//         throw new Error(`Backend returned ${response.status}`);
//       }

//       const result: ComponentsResponse = await response.json();

//       setComponents(result.data || []);
//       setTotal(result.total || 0);

//       if (result.filter_options) {
//         setLots(result.filter_options.lots || []);

//         setComponentTypes(result.filter_options.component_types || []);

//         setDecisions(result.filter_options.screening_decisions || []);
//       }
//     } catch (err) {
//       console.error(err);

//       setError(
//         "Unable to load component data. Check that the FastAPI backend is running.",
//       );

//       setComponents([]);
//       setTotal(0);
//     } finally {
//       setLoading(false);
//     }
//   }

//   useEffect(() => {
//     loadComponents();
//   }, [page, componentId, lotId, componentType, decision]);

//   function resetFilters() {
//     setComponentId("");
//     setLotId("");
//     setComponentType("");
//     setDecision("");
//     setPage(1);
//   }

//   const showingStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;

//   const showingEnd = Math.min(page * PAGE_SIZE, total);

//   const hasFilters = componentId || lotId || componentType || decision;

//   const pageNumbers = useMemo(() => {
//     const pages: number[] = [];

//     const start = Math.max(1, page - 2);

//     const end = Math.min(totalPages, page + 2);

//     for (let i = start; i <= end; i++) {
//       pages.push(i);
//     }

//     return pages;
//   }, [page, totalPages]);

//   return (
//     <main className="min-h-full bg-slate-50 text-slate-900 dark:bg-[#020618] dark:text-white">
//       <div className="mx-auto w-full max-w-[1600px] px-5 pb-10 pt-5 lg:px-7">
//         {/* Header */}
//         <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
//           <div>
//             <div className="mb-2 flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-400">
//               <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
//               Screening fleet
//             </div>

//             <h1 className="text-2xl font-semibold tracking-tight">
//               Components
//             </h1>

//             <p className="mt-1 max-w-2xl text-sm text-slate-500 dark:text-slate-400">
//               Find components that require inspection and open an individual
//               investigation when deeper evidence is needed.
//             </p>
//           </div>

//           <div className="text-sm text-slate-500 dark:text-slate-400">
//             Showing{" "}
//             <span className="font-medium text-slate-900 dark:text-white">
//               {showingStart}–{showingEnd}
//             </span>{" "}
//             of{" "}
//             <span className="font-medium text-slate-900 dark:text-white">
//               {total}
//             </span>
//           </div>
//         </div>

//         {/* Filters */}
//         <section className="mb-5 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
//           <div className="flex flex-col gap-3 p-4 xl:flex-row xl:items-center">
//             {/* Component search */}
//             <div className="relative min-w-0 flex-1 xl:max-w-[310px]">
//               <svg
//                 className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
//                 viewBox="0 0 24 24"
//                 fill="none"
//                 stroke="currentColor"
//                 strokeWidth="1.8"
//               >
//                 <circle cx="11" cy="11" r="7" />
//                 <path d="m20 20-4-4" />
//               </svg>

//               <input
//                 value={componentId}
//                 onChange={(e) => {
//                   setComponentId(e.target.value);
//                   setPage(1);
//                 }}
//                 placeholder="Search component ID"
//                 className="h-10 w-full rounded-lg border border-slate-200 bg-slate-50 pl-9 pr-3 text-sm outline-none transition placeholder:text-slate-400 focus:border-slate-400 dark:border-white/[0.08] dark:bg-white/[0.025] dark:placeholder:text-slate-500 dark:focus:border-white/20"
//               />
//             </div>

//             {/* Lot */}
//             <select
//               value={lotId}
//               onChange={(e) => {
//                 setLotId(e.target.value);
//                 setPage(1);
//               }}
//               className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-[#020618] dark:text-slate-200"
//             >
//               <option
//                 value=""
//                 className="bg-white text-slate-700 dark:bg-[#020618] dark:text-slate-200"
//               >
//                 All lots
//               </option>

//               {lots.map((lot) => (
//                 <option
//                   key={lot}
//                   value={lot}
//                   className="bg-white text-slate-700 dark:bg-[#020618] dark:text-slate-200"
//                 >
//                   {lot}
//                 </option>
//               ))}
//             </select>

//             {/* Component Type */}
//             <select
//               value={componentType}
//               onChange={(e) => {
//                 setComponentType(e.target.value);
//                 setPage(1);
//               }}
//               className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-[#020618] dark:text-slate-200"
//             >
//               <option
//                 value=""
//                 className="bg-white text-slate-700 dark:bg-[#020618] dark:text-slate-200"
//               >
//                 All types
//               </option>

//               {componentTypes.map((type) => (
//                 <option
//                   key={type}
//                   value={type}
//                   className="bg-white text-slate-700 dark:bg-[#020618] dark:text-slate-200"
//                 >
//                   {type}
//                 </option>
//               ))}
//             </select>

//             {/* Decision */}
//             <select
//               value={decision}
//               onChange={(e) => {
//                 setDecision(e.target.value);
//                 setPage(1);
//               }}
//               className="h-10 rounded-lg border border-slate-200 bg-slate-50 px-3 text-sm text-slate-700 outline-none dark:border-white/[0.08] dark:bg-[#020618] dark:text-slate-200"
//             >
//               <option
//                 value=""
//                 className="bg-white text-slate-700 dark:bg-[#020618] dark:text-slate-200"
//               >
//                 All decisions
//               </option>

//               {decisions.map((item) => (
//                 <option
//                   key={item}
//                   value={item}
//                   className="bg-white text-slate-700 dark:bg-[#020618] dark:text-slate-200"
//                 >
//                   {item}
//                 </option>
//               ))}
//             </select>

//             {hasFilters ? (
//               <button
//                 onClick={resetFilters}
//                 className="h-10 rounded-lg px-3 text-sm text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-white/[0.05] dark:hover:text-white"
//               >
//                 Clear filters
//               </button>
//             ) : null}
//           </div>
//         </section>

//         {/* Error */}
//         {error ? (
//           <div className="mb-5 rounded-xl border border-red-500/20 bg-red-500/[0.06] px-4 py-3 text-sm text-red-600 dark:text-red-400">
//             {error}
//           </div>
//         ) : null}

//         {/* Main table */}
//         <section className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
//           <div className="w-full">
//             <div className="w-full">
//               {/* Table header */}
//               <div className="grid grid-cols-[1.5fr_0.9fr_0.9fr_1fr_1fr_0.8fr_1.2fr_80px] gap-3 border-b border-slate-200 bg-slate-50/70 px-5 py-3 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-400 dark:border-white/[0.06] dark:bg-white/[0.015]">
//                 <div>Component</div>
//                 <div>Lot</div>
//                 <div>Type</div>
//                 <div>0H Iddq</div>
//                 <div>Anomaly</div>
//                 <div>Risk</div>
//                 <div>Decision</div>
//                 <div />
//               </div>

//               {loading ? (
//                 <LoadingRows />
//               ) : components.length === 0 ? (
//                 <div className="flex min-h-[280px] items-center justify-center px-5">
//                   <div className="text-center">
//                     <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 dark:border-white/10">
//                       <svg
//                         className="h-5 w-5 text-slate-400"
//                         viewBox="0 0 24 24"
//                         fill="none"
//                         stroke="currentColor"
//                         strokeWidth="1.6"
//                       >
//                         <circle cx="11" cy="11" r="7" />
//                         <path d="m20 20-4-4" />
//                       </svg>
//                     </div>

//                     <p className="text-sm font-medium">No components found</p>

//                     <p className="mt-1 text-xs text-slate-400">
//                       Try changing or clearing your filters.
//                     </p>
//                   </div>
//                 </div>
//               ) : (
//                 <div className="divide-y divide-slate-200 dark:divide-white/[0.06]">
//                   {components.map((component) => {
//                     const anomaly = isAnomaly(component.anomaly_flag);

//                     const currentDecision = normalizeDecision(
//                       component.final_decision,
//                     );

//                     return (
//                       <div
//                         key={component.component_id}
//                         className="grid grid-cols-[1.5fr_0.9fr_0.9fr_1fr_1fr_0.8fr_1.2fr_80px] items-center gap-3 px-5 py-4 transition hover:bg-slate-50 dark:hover:bg-white/[0.025]"
//                       >
//                         {/* Component */}
//                         <div className="min-w-0">
//                           <Link
//                             href={`/components/${encodeURIComponent(
//                               component.component_id,
//                             )}`}
//                             className="group inline-flex items-center gap-2"
//                           >
//                             <span className="h-1.5 w-1.5 rounded-full bg-slate-300 transition group-hover:bg-emerald-500 dark:bg-slate-600" />

//                             <span className="truncate text-sm font-medium text-slate-900 group-hover:text-emerald-600 dark:text-slate-100 dark:group-hover:text-emerald-400">
//                               {component.component_id}
//                             </span>
//                           </Link>
//                         </div>

//                         {/* Lot */}
//                         <div className="text-sm text-slate-500 dark:text-slate-400">
//                           {component.lot_id}
//                         </div>

//                         {/* Type */}
//                         <div className="text-sm text-slate-500 dark:text-slate-400">
//                           {component.component_type}
//                         </div>

//                         {/* 0H Iddq */}
//                         <div>
//                           <span className="font-mono text-sm text-slate-800 dark:text-slate-200">
//                             {formatNumber(component.iddq_0h_uA)}
//                           </span>

//                           <span className="ml-1 text-[11px] text-slate-400">
//                             µA
//                           </span>
//                         </div>

//                         {/* Anomaly */}
//                         <div>
//                           {anomaly ? (
//                             <span className="inline-flex items-center gap-1.5 text-sm font-medium text-amber-600 dark:text-amber-400">
//                               <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
//                               Detected
//                             </span>
//                           ) : (
//                             <span className="inline-flex items-center gap-1.5 text-sm text-slate-400">
//                               <span className="h-1.5 w-1.5 rounded-full bg-slate-300 dark:bg-slate-600" />
//                               Normal
//                             </span>
//                           )}
//                         </div>

//                         {/* Risk */}
//                         <div>
//                           <div
//                             className={`font-mono text-sm font-medium ${riskClass(
//                               component.risk_bucket,
//                             )}`}
//                           >
//                             {formatNumber(component.risk_score, 1)}
//                           </div>

//                           <div className="mt-0.5 text-[10px] uppercase tracking-wider text-slate-400">
//                             {component.risk_bucket || "—"}
//                           </div>
//                         </div>

//                         {/* Decision */}
//                         <div>
//                           <span
//                             className={`inline-flex rounded-md border px-2 py-1 text-[10px] font-semibold tracking-[0.08em] ${decisionClass(
//                               currentDecision,
//                             )}`}
//                           >
//                             {currentDecision || "—"}
//                           </span>
//                         </div>

//                         {/* Inspect */}
//                         <div className="flex justify-end">
//                           <Link
//                             href={`/components/${encodeURIComponent(
//                               component.component_id,
//                             )}`}
//                             className="group inline-flex items-center gap-2"
//                           >
//                             <div className="inline-flex h-8 items-center justify-center rounded-md border border-slate-200 px-2.5 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 dark:border-white/[0.08] dark:text-slate-400 dark:hover:border-white/15 dark:hover:bg-white/[0.04] dark:hover:text-white">
//                               Inspect
//                             </div>
//                           </Link>
//                         </div>
//                       </div>
//                     );
//                   })}
//                 </div>
//               )}
//             </div>
//           </div>

//           {/* Pagination */}
//           {!loading && total > 0 ? (
//             <div className="flex flex-col gap-3 border-t border-slate-200 px-5 py-3 sm:flex-row sm:items-center sm:justify-between dark:border-white/[0.06]">
//               <div className="text-xs text-slate-400">
//                 Page {page} of {totalPages}
//               </div>

//               <div className="flex items-center gap-1">
//                 <button
//                   disabled={page === 1}
//                   onClick={() => setPage((current) => current - 1)}
//                   className="h-8 rounded-md border border-slate-200 px-2.5 text-xs text-slate-500 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
//                 >
//                   Previous
//                 </button>

//                 {pageNumbers.map((pageNumber) => (
//                   <button
//                     key={pageNumber}
//                     onClick={() => setPage(pageNumber)}
//                     className={`h-8 min-w-8 rounded-md border px-2 text-xs transition ${
//                       pageNumber === page
//                         ? "border-slate-900 bg-slate-900 text-white dark:border-white dark:bg-white dark:text-slate-900"
//                         : "border-slate-200 text-slate-500 hover:bg-slate-50 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
//                     }`}
//                   >
//                     {pageNumber}
//                   </button>
//                 ))}

//                 <button
//                   disabled={page === totalPages}
//                   onClick={() => setPage((current) => current + 1)}
//                   className="h-8 rounded-md border border-slate-200 px-2.5 text-xs text-slate-500 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/[0.08] dark:hover:bg-white/[0.04]"
//                 >
//                   Next
//                 </button>
//               </div>
//             </div>
//           ) : null}
//         </section>
//       </div>
//     </main>
//   );
// }
import ComponentsPage from "@/components/components-list/ComponentsPage";

export default function Page() {
  return <ComponentsPage />;
}