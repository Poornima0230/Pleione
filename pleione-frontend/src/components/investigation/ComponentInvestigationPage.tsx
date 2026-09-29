"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import InvestigationHeader from "./InvestigationHeader";
import InvestigationSnapshot from "./InvestigationSnapshot";
import MeasurementsAndPrediction from "./MeasurementsAndPrediction";
import TrajectoryChart from "./TrajectoryChart";
import DecisionEvidence from "./DecisionEvidence";
import EngineeringEvidence from "./EngineeringEvidence";
import InvestigationFooter from "./InvestigationFooter";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type InvestigationData = {
  component: any;
  module_a: any;
  prediction: any;
  risk: any;
  investigation: any;
};

export default function ComponentInvestigationPage() {
  const params = useParams<{ component_id: string }>();

  const componentId = params.component_id;

  const [data, setData] = useState<InvestigationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!componentId) {
      setLoading(false);
      setError("Component ID was not found in the URL.");
      return;
    }

    const controller = new AbortController();

    async function loadInvestigation() {
      try {
        setLoading(true);
        setError(null);
        setData(null);

        const url = `${API_BASE}/api/component-analysis/${encodeURIComponent(componentId)}`;

        console.log("Loading component investigation:", url);

        const response = await fetch(url, {
          signal: controller.signal,
          headers: {
            Accept: "application/json",
          },
        });

        if (!response.ok) {
          let message = `Unable to load component ${componentId}.`;

          try {
            const body = await response.json();

            if (body?.detail) {
              message = body.detail;
            }
          } catch {
            // Ignore invalid error response.
          }

          throw new Error(message);
        }

        const result: InvestigationData = await response.json();

        if (!controller.signal.aborted) {
          setData(result);
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return;
        }

        if (!controller.signal.aborted) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load component investigation.",
          );
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadInvestigation();

    return () => {
      controller.abort();
    };
  }, [componentId]);

  if (loading) {
    return (
      <main className="min-h-screen bg-[#020618] text-slate-100">
        <div className="mx-auto max-w-7xl px-5 py-8 sm:px-6 lg:px-8">
          <div className="space-y-8">
            <div>
              <div className="h-7 w-64 animate-pulse rounded bg-slate-800/70" />
              <div className="mt-3 h-4 w-96 max-w-full animate-pulse rounded bg-slate-800/50" />
            </div>

            <div className="h-28 animate-pulse rounded-2xl border border-slate-800 bg-slate-900/40" />

            <div className="h-56 animate-pulse rounded-2xl border border-slate-800 bg-slate-900/40" />

            <div className="h-72 animate-pulse rounded-2xl border border-slate-800 bg-slate-900/40" />
          </div>
        </div>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="min-h-screen bg-[#020618] text-slate-100">
        <div className="mx-auto max-w-3xl px-6 py-20">
          <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-red-400">
              Investigation unavailable
            </p>

            <h1 className="mt-3 text-2xl font-semibold text-white">
              Unable to load component investigation
            </h1>

            <p className="mt-3 text-sm leading-6 text-slate-400">
              {error ||
                "The component investigation data could not be retrieved."}
            </p>
          </div>
        </div>
      </main>
    );
  }

  const { component, module_a, prediction, risk, investigation } = data;

  return (
    <main className="min-h-screen bg-[#020618] text-slate-100">
      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-6 lg:px-8">
        <InvestigationHeader
          component={component}
          investigation={investigation}
          risk={risk}
        />

        <div className="mt-8 space-y-8">
          <InvestigationSnapshot
            component={component}
            prediction={prediction}
            risk={risk}
            investigation={investigation}
          />

          <MeasurementsAndPrediction
            component={component}
            prediction={prediction}
            risk={risk}
          />

          <TrajectoryChart component={component} prediction={prediction} />

          <DecisionEvidence
            component={component}
            moduleA={module_a}
            prediction={prediction}
            risk={risk}
            investigation={investigation}
          />

          <EngineeringEvidence
            component={component}
            prediction={prediction}
            risk={risk}
            investigation={investigation}
          />

          <InvestigationFooter
            component={component}
            moduleA={module_a}
            prediction={prediction}
            risk={risk}
          />
        </div>
      </div>
    </main>
  );
}
