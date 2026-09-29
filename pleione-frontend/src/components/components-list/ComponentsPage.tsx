"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import ComponentsFilters from "./ComponentsFilters";
import ComponentsPagination from "./ComponentsPagination";
import ComponentsTable from "./ComponentTable";

import type { ComponentsResponse, ComponentRow } from "./types";

import { getPageNumbers, PAGE_SIZE } from "./utils";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function ComponentsPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-full bg-slate-50 text-slate-900 dark:bg-[#020618] dark:text-white">
          <div className="mx-auto w-full max-w-[1600px] px-5 pb-10 pt-5 lg:px-7">
            <div className="mb-6">
              <div className="h-4 w-32 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
              <div className="mt-3 h-8 w-48 animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
              <div className="mt-2 h-4 w-96 max-w-full animate-pulse rounded bg-slate-200 dark:bg-slate-800" />
            </div>

            <div className="h-24 animate-pulse rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />

            <div className="mt-5 h-96 animate-pulse rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900" />
          </div>
        </main>
      }
    >
      <ComponentsPageContent />
    </Suspense>
  );
}

function ComponentsPageContent() {
  const searchParams = useSearchParams();

  const [components, setComponents] = useState<ComponentRow[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPagesFromApi, setTotalPagesFromApi] = useState(0);
  const [page, setPage] = useState(1);

  const [componentId, setComponentId] = useState("");
  const [lotId, setLotId] = useState("");
  const [componentType, setComponentType] = useState("");
  const [decision, setDecision] = useState("");

  const [lots, setLots] = useState<string[]>([]);
  const [componentTypes, setComponentTypes] = useState<string[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ============================================================
  // READ LOT FILTER FROM URL
  // ============================================================

  useEffect(() => {
    const urlLotId = searchParams.get("lot_id");

    if (urlLotId) {
      setLotId(urlLotId);
      setPage(1);
    } else {
      // Normal Components page = all components
      setLotId("");
      setPage(1);
    }
  }, [searchParams]);

  // ============================================================
  // TOTAL PAGES
  // ============================================================

  const totalPages = Math.max(
    1,
    totalPagesFromApi || Math.ceil(total / PAGE_SIZE),
  );

  // ============================================================
  // LOAD COMPONENTS
  // ============================================================

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

      if (lotId.trim()) {
        params.set("lot_id", lotId.trim());
      }

      if (componentType.trim()) {
        params.set("component_type", componentType.trim());
      }

      if (decision.trim()) {
        params.set("screening_decision", decision.trim());
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
      setTotalPagesFromApi(result.total_pages || 0);

      if (result.filter_options) {
        setLots(result.filter_options.lots || []);
        setComponentTypes(result.filter_options.component_types || []);
      }
    } catch (err) {
      console.error(err);

      setError(
        "Unable to load component data. Check that the FastAPI backend is running.",
      );

      setComponents([]);
      setTotal(0);
      setTotalPagesFromApi(0);
    } finally {
      setLoading(false);
    }
  }

  // ============================================================
  // FETCH WHEN PAGE OR FILTER CHANGES
  // ============================================================

  useEffect(() => {
    loadComponents();
  }, [page, componentId, lotId, componentType, decision]);

  // ============================================================
  // FILTER HANDLERS
  // ============================================================

  function handleComponentIdChange(value: string) {
    setComponentId(value);
    setPage(1);
  }

  function handleLotChange(value: string) {
    setLotId(value);
    setPage(1);
  }

  function handleComponentTypeChange(value: string) {
    setComponentType(value);
    setPage(1);
  }

  function handleDecisionChange(value: string) {
    setDecision(value);
    setPage(1);
  }

  // ============================================================
  // RESET FILTERS
  // ============================================================

  function resetFilters() {
    setComponentId("");
    setLotId("");
    setComponentType("");
    setDecision("");
    setPage(1);
  }

  // ============================================================
  // DISPLAY RANGE
  // ============================================================

  const showingStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;

  const showingEnd = Math.min(page * PAGE_SIZE, total);

  // ============================================================
  // ACTIVE FILTER STATE
  // ============================================================

  const hasFilters = Boolean(componentId || lotId || componentType || decision);

  // ============================================================
  // PAGINATION NUMBERS
  // ============================================================

  const pageNumbers = useMemo(
    () => getPageNumbers(page, totalPages),
    [page, totalPages],
  );

  // ============================================================
  // RENDER
  // ============================================================

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
        <ComponentsFilters
          componentId={componentId}
          lotId={lotId}
          componentType={componentType}
          decision={decision}
          lots={lots}
          componentTypes={componentTypes}
          hasFilters={hasFilters}
          onComponentIdChange={handleComponentIdChange}
          onLotChange={handleLotChange}
          onComponentTypeChange={handleComponentTypeChange}
          onDecisionChange={handleDecisionChange}
          onClear={resetFilters}
        />

        {/* Error */}
        {error ? (
          <div className="mb-5 rounded-xl border border-red-500/20 bg-red-500/[0.06] px-4 py-3 text-sm text-red-600 dark:text-red-400">
            {error}
          </div>
        ) : null}

        {/* Table */}
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
          <ComponentsTable components={components} loading={loading} />

          {/* Pagination */}
          <ComponentsPagination
            page={page}
            total={total}
            totalPages={totalPages}
            pageNumbers={pageNumbers}
            onPrevious={() => setPage((current) => Math.max(1, current - 1))}
            onNext={() =>
              setPage((current) => Math.min(totalPages, current + 1))
            }
            onPageChange={(nextPage) =>
              setPage(Math.min(totalPages, Math.max(1, nextPage)))
            }
          />
        </div>
      </div>
    </main>
  );
}
