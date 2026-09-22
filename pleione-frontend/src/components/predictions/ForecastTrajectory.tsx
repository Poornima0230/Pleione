"use client";

type ForecastTrajectoryProps = {
  iddq0?: number;
  iddq24?: number;
  predicted168?: number;
  lower168?: number;
  upper168?: number;
  absoluteLimit?: number;
};

export default function ForecastTrajectory({
  iddq0,
  iddq24,
  predicted168,
  lower168,
  upper168,
  absoluteLimit,
}: ForecastTrajectoryProps) {
  const values = [
    iddq0,
    iddq24,
    predicted168,
    lower168,
    upper168,
    absoluteLimit,
  ].filter(
    (value): value is number =>
      value !== undefined && value !== null && Number.isFinite(value),
  );

  if (values.length === 0) {
    return (
      <div className="flex h-[360px] items-center justify-center border border-black/10 bg-white/30 text-sm text-black/40">
        No trajectory data available.
      </div>
    );
  }

  const minimum = Math.min(...values);
  const maximum = Math.max(...values);

  const padding = Math.max((maximum - minimum) * 0.2, 1);

  const minY = minimum - padding;
  const maxY = maximum + padding;

  const chartLeft = 70;
  const chartRight = 700;
  const chartTop = 30;
  const chartBottom = 280;

  const chartWidth = chartRight - chartLeft;

  const chartHeight = chartBottom - chartTop;

  function xPosition(hour: number) {
    return chartLeft + (hour / 168) * chartWidth;
  }

  function yPosition(value?: number) {
    if (value === undefined || value === null) {
      return null;
    }

    return chartBottom - ((value - minY) / (maxY - minY)) * chartHeight;
  }

  const x0 = xPosition(0);
  const x24 = xPosition(24);
  const x96 = xPosition(96);
  const x168 = xPosition(168);

  const y0 = yPosition(iddq0);
  const y24 = yPosition(iddq24);
  const yPredicted = yPosition(predicted168);

  const yLower = yPosition(lower168);

  const yUpper = yPosition(upper168);

  const yLimit = yPosition(absoluteLimit);

  const actualPath =
    y0 !== null && y24 !== null ? `M ${x0} ${y0} L ${x24} ${y24}` : "";

  const forecastPath =
    y24 !== null && yPredicted !== null
      ? `M ${x24} ${y24} L ${x168} ${yPredicted}`
      : "";

  const uncertaintyTop =
    yUpper !== null ? Math.min(yUpper, yLower ?? yUpper) : null;

  const uncertaintyBottom =
    yLower !== null ? Math.max(yUpper ?? yLower, yLower) : null;

  return (
    <div className="border border-black/10 bg-white/30 p-6">
      {/* HEADER */}

      <div className="mb-5 flex items-start justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-[0.2em] text-black/35">
            Burn-In Trajectory
          </div>

          <h3 className="mt-1 text-lg font-medium">Observed → Forecast</h3>
        </div>

        <div className="text-right">
          <div className="text-[10px] uppercase tracking-[0.2em] text-black/35">
            Horizon
          </div>

          <div className="mt-1 font-mono text-sm">168H</div>
        </div>
      </div>

      {/* CHART */}

      <div className="overflow-x-auto">
        <svg
          viewBox="0 0 760 340"
          className="h-auto min-w-[680px] w-full"
          role="img"
          aria-label="Component Iddq burn-in trajectory and 168 hour forecast"
        >
          {/* GRID */}

          {[0, 25, 50, 75, 100].map((percent) => {
            const y = chartBottom - (percent / 100) * chartHeight;

            return (
              <line
                key={percent}
                x1={chartLeft}
                x2={chartRight}
                y1={y}
                y2={y}
                stroke="currentColor"
                strokeOpacity="0.08"
                strokeWidth="1"
              />
            );
          })}

          {/* TIME GRID */}

          {[0, 24, 96, 168].map((hour) => {
            const x = xPosition(hour);

            return (
              <line
                key={hour}
                x1={x}
                x2={x}
                y1={chartTop}
                y2={chartBottom}
                stroke="currentColor"
                strokeOpacity="0.06"
                strokeWidth="1"
                strokeDasharray="3 4"
              />
            );
          })}

          {/* AXIS */}

          <line
            x1={chartLeft}
            x2={chartRight}
            y1={chartBottom}
            y2={chartBottom}
            stroke="currentColor"
            strokeOpacity="0.2"
          />

          <line
            x1={chartLeft}
            x2={chartLeft}
            y1={chartTop}
            y2={chartBottom}
            stroke="currentColor"
            strokeOpacity="0.2"
          />

          {/* ABSOLUTE LIMIT */}

          {yLimit !== null && (
            <>
              <line
                x1={chartLeft}
                x2={chartRight}
                y1={yLimit}
                y2={yLimit}
                stroke="currentColor"
                strokeOpacity="0.55"
                strokeWidth="1.5"
                strokeDasharray="6 5"
              />

              <text
                x={chartRight}
                y={yLimit - 8}
                textAnchor="end"
                fontSize="10"
                fill="currentColor"
                fillOpacity="0.55"
              >
                ABSOLUTE LIMIT
              </text>
            </>
          )}

          {/* FORECAST UNCERTAINTY */}

          {yLower !== null && yUpper !== null && (
            <rect
              x={x24}
              y={uncertaintyTop ?? 0}
              width={x168 - x24}
              height={(uncertaintyBottom ?? 0) - (uncertaintyTop ?? 0)}
              fill="currentColor"
              fillOpacity="0.06"
            />
          )}

          {/* ACTUAL TRAJECTORY */}

          {actualPath && (
            <path
              d={actualPath}
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
            />
          )}

          {/* FORECAST TRAJECTORY */}

          {forecastPath && (
            <path
              d={forecastPath}
              fill="none"
              stroke="currentColor"
              strokeWidth="3"
              strokeDasharray="7 5"
            />
          )}

          {/* 0H POINT */}

          {y0 !== null && <circle cx={x0} cy={y0} r="5" fill="currentColor" />}

          {/* 24H POINT */}

          {y24 !== null && (
            <circle cx={x24} cy={y24} r="5" fill="currentColor" />
          )}

          {/* 168H FORECAST POINT */}

          {yPredicted !== null && (
            <>
              <circle
                cx={x168}
                cy={yPredicted}
                r="7"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              />

              <circle cx={x168} cy={yPredicted} r="3" fill="currentColor" />
            </>
          )}

          {/* UPPER INTERVAL */}

          {yUpper !== null && (
            <line
              x1={x168 - 12}
              x2={x168 + 12}
              y1={yUpper}
              y2={yUpper}
              stroke="currentColor"
              strokeOpacity="0.35"
            />
          )}

          {/* LOWER INTERVAL */}

          {yLower !== null && (
            <line
              x1={x168 - 12}
              x2={x168 + 12}
              y1={yLower}
              y2={yLower}
              stroke="currentColor"
              strokeOpacity="0.35"
            />
          )}

          {/* Y LABELS */}

          <text
            x="8"
            y={chartTop + 4}
            fontSize="10"
            fill="currentColor"
            fillOpacity="0.4"
          >
            {maxY.toFixed(1)} µA
          </text>

          <text
            x="8"
            y={chartBottom}
            fontSize="10"
            fill="currentColor"
            fillOpacity="0.4"
          >
            {minY.toFixed(1)} µA
          </text>

          {/* X LABELS */}

          <text
            x={x0}
            y="305"
            textAnchor="middle"
            fontSize="10"
            fill="currentColor"
            fillOpacity="0.45"
          >
            0H
          </text>

          <text
            x={x24}
            y="305"
            textAnchor="middle"
            fontSize="10"
            fill="currentColor"
            fillOpacity="0.45"
          >
            24H
          </text>

          <text
            x={x96}
            y="305"
            textAnchor="middle"
            fontSize="10"
            fill="currentColor"
            fillOpacity="0.45"
          >
            96H
          </text>

          <text
            x={x168}
            y="305"
            textAnchor="middle"
            fontSize="10"
            fill="currentColor"
            fillOpacity="0.45"
          >
            168H
          </text>

          {/* LABELS */}

          {y24 !== null && (
            <text
              x={x24}
              y={y24 - 14}
              textAnchor="middle"
              fontSize="10"
              fill="currentColor"
              fillOpacity="0.6"
            >
              OBSERVED
            </text>
          )}

          {yPredicted !== null && (
            <text
              x={x168 - 8}
              y={yPredicted - 16}
              textAnchor="end"
              fontSize="10"
              fill="currentColor"
              fillOpacity="0.65"
            >
              PREDICTED
            </text>
          )}
        </svg>
      </div>

      {/* LEGEND */}

      <div className="mt-5 flex flex-wrap gap-x-6 gap-y-3 border-t border-black/10 pt-4">
        <Legend label="Observed" dashed={false} />

        <Legend label="Forecast" dashed />

        <Legend label="Prediction interval" interval />

        <Legend label="Absolute limit" limit />
      </div>

      {/* VALUES */}

      <div className="mt-5 grid grid-cols-2 border-t border-black/10 pt-4 md:grid-cols-4">
        <Value label="0H Observed" value={iddq0} />

        <Value label="24H Observed" value={iddq24} />

        <Value label="168H Predicted" value={predicted168} />

        <Value label="Absolute Limit" value={absoluteLimit} />
      </div>
    </div>
  );
}

/* ============================================================
   LEGEND
   ============================================================ */

function Legend({
  label,
  dashed = false,
  interval = false,
  limit = false,
}: {
  label: string;
  dashed?: boolean;
  interval?: boolean;
  limit?: boolean;
}) {
  return (
    <div className="flex items-center gap-2 text-[10px] uppercase tracking-wider text-black/40">
      <span
        className={`relative block h-px w-7 ${
          dashed
            ? "border-t border-dashed border-black/60"
            : interval
              ? "bg-black/15"
              : limit
                ? "border-t border-dashed border-black/60"
                : "bg-black"
        }`}
      />

      {label}
    </div>
  );
}

/* ============================================================
   VALUE
   ============================================================ */

function Value({ label, value }: { label: string; value?: number }) {
  return (
    <div className="border-r border-black/10 px-4 first:pl-0 last:border-r-0">
      <div className="text-[9px] uppercase tracking-[0.15em] text-black/35">
        {label}
      </div>

      <div className="mt-1 font-mono text-sm">
        {value !== undefined && value !== null && Number.isFinite(value)
          ? `${value.toFixed(2)} µA`
          : "—"}
      </div>
    </div>
  );
}
