"use client";

import { memo, useMemo } from "react";

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function clampNonNegative(value: unknown) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return 0;
  }

  return Math.max(0, number);
}

type Props = {
  component: any;
  prediction: any;
};

type ChartPoint = {
  time: string;
  observed: number | null;
  forecast: number | null;
  lower: number | null;
  upper: number | null;
};

function TrajectoryChart({ component, prediction }: Props) {
  const chartData = useMemo<ChartPoint[]>(() => {
    const iddq0 = clampNonNegative(
      prediction?.iddq_0h_uA ?? component?.iddq_0h_uA,
    );

    const iddq24 = clampNonNegative(
      prediction?.iddq_24h_uA ?? component?.iddq_24h_uA,
    );

    const predicted = clampNonNegative(prediction?.predicted_168h_uA);

    const rawLower = clampNonNegative(prediction?.prediction_lower_uA);

    const rawUpper = clampNonNegative(prediction?.prediction_upper_uA);

    const lower = Math.min(rawLower, rawUpper);

    const upper = Math.max(rawLower, rawUpper);

    return [
      {
        time: "0H",
        observed: iddq0,
        forecast: null,
        lower: null,
        upper: null,
      },
      {
        time: "24H",
        observed: iddq24,
        forecast: iddq24,
        lower: iddq24,
        upper: iddq24,
      },
      {
        time: "168H",
        observed: null,
        forecast: predicted,
        lower,
        upper,
      },
    ];
  }, [
    component?.iddq_0h_uA,
    prediction?.iddq_0h_uA,
    prediction?.iddq_24h_uA,
    prediction?.predicted_168h_uA,
    prediction?.prediction_lower_uA,
    prediction?.prediction_upper_uA,
  ]);

  const limit = useMemo(
    () =>
      clampNonNegative(
        prediction?.absolute_limit_uA ?? component?.absolute_limit_uA,
      ),
    [component?.absolute_limit_uA, prediction?.absolute_limit_uA],
  );

  const yMax = useMemo(() => {
    const values = chartData.flatMap((point) => [
      point.observed ?? 0,
      point.forecast ?? 0,
      point.lower ?? 0,
      point.upper ?? 0,
    ]);

    const maxValue = Math.max(limit, ...values, 1);

    return maxValue * 1.18;
  }, [chartData, limit]);

  return (
    <section>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-white">
            IDDQ Trajectory
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Observed at 0H and 24H, then projected to 168H.
          </p>
        </div>

        <div className="flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-500">
          <LegendItem label="Observed" />
          <LegendItem label="Forecast" />
          <LegendItem label="Uncertainty" />
          <LegendItem label="Limit" />
        </div>
      </div>

      <div className="mt-6 h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%" debounce={80}>
          <LineChart
            data={chartData}
            margin={{
              top: 10,
              right: 15,
              left: 0,
              bottom: 5,
            }}
          >
            <CartesianGrid
              stroke="#1e293b"
              strokeDasharray="3 3"
              vertical={false}
            />

            <XAxis
              dataKey="time"
              tick={{
                fill: "#64748b",
                fontSize: 12,
              }}
              axisLine={false}
              tickLine={false}
            />

            <YAxis
              domain={[0, yMax]}
              tick={{
                fill: "#64748b",
                fontSize: 11,
              }}
              axisLine={false}
              tickLine={false}
              width={45}
            />

            <Tooltip
              contentStyle={{
                background: "#020617",
                border: "1px solid #1e293b",
                borderRadius: "10px",
                color: "#e2e8f0",
              }}
              formatter={(value: any) =>
                typeof value === "number"
                  ? `${Math.max(0, value).toFixed(2)} µA`
                  : value
              }
            />

            <ReferenceLine y={limit} stroke="#ef4444" strokeDasharray="5 5" />

            <Line
              type="monotone"
              dataKey="observed"
              stroke="#e2e8f0"
              strokeWidth={2.5}
              dot={{
                r: 4,
                fill: "#e2e8f0",
              }}
              connectNulls
              isAnimationActive={false}
            />

            <Line
              type="monotone"
              dataKey="forecast"
              stroke="#38bdf8"
              strokeWidth={2.5}
              strokeDasharray="7 5"
              dot={{
                r: 4,
                fill: "#38bdf8",
              }}
              connectNulls
              isAnimationActive={false}
            />

            <Line
              type="monotone"
              dataKey="lower"
              stroke="#f59e0b"
              strokeWidth={1}
              strokeDasharray="3 4"
              dot={false}
              connectNulls
              isAnimationActive={false}
            />

            <Line
              type="monotone"
              dataKey="upper"
              stroke="#f59e0b"
              strokeWidth={1}
              strokeDasharray="3 4"
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 flex flex-col gap-1 text-xs text-slate-600 sm:flex-row sm:items-center sm:justify-between">
        <span>Decision inputs: 0H + 24H</span>

        <span>96H measurements are not used at screening time.</span>
      </div>
    </section>
  );
}

function LegendItem({ label }: { label: string }) {
  return (
    <span className="flex items-center gap-2">
      <span
        className={`h-1.5 w-5 rounded-full ${
          label === "Observed"
            ? "bg-slate-300"
            : label === "Forecast"
              ? "bg-sky-400"
              : label === "Uncertainty"
                ? "bg-amber-400"
                : "bg-red-400"
        }`}
      />

      {label}
    </span>
  );
}

export default memo(TrajectoryChart);
