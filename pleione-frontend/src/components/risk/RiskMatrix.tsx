"use client";

import Link from "next/link";

export type RiskMatrixItem = {
  component_id?: string;
  lot_id?: string;
  current_anomaly_level?: string;
  future_drift_risk?: string;
  risk_score?: number;
  final_risk_level?: string;
  final_decision?: string;
  primary_risk_driver?: string;
  upper_limit_utilization_percent?: number;
};

type RiskMatrixProps = {
  data: RiskMatrixItem[];
};

type RiskLevel = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "NORMAL";

const LEVELS: RiskLevel[] = ["NORMAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"];

export default function RiskMatrix({ data }: RiskMatrixProps) {
  const matrix = LEVELS.map((currentLevel) =>
    LEVELS.map(
      (futureLevel) =>
        data.filter((item) => {
          const current = normalizeRiskLevel(item.current_anomaly_level);

          const future = normalizeRiskLevel(
            item.final_risk_level ?? item.future_drift_risk,
          );

          return current === currentLevel && future === futureLevel;
        }).length,
    ),
  );

  const highestRiskItems = [...data]
    .sort((a, b) => getRiskScore(b) - getRiskScore(a))
    .slice(0, 10);

  return (
    <div className="space-y-6">
      {/* MATRIX */}

      <div className="border border-black/10 bg-white/40 p-6">
        <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
          <div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-black/35">
              Risk Population
            </div>

            <h2 className="mt-1 text-lg font-medium">
              Current State × Future Risk
            </h2>
          </div>

          <div className="font-mono text-xs text-black/35">
            {data.length} COMPONENTS
          </div>
        </div>

        <div className="mt-7 overflow-x-auto">
          <div className="min-w-[700px]">
            <div className="grid grid-cols-[100px_repeat(5,1fr)] gap-px border border-black/10 bg-black/10">
              <div className="bg-[#f4f4f1]" />

              {LEVELS.map((level) => (
                <MatrixHeader key={level} level={level} />
              ))}

              {LEVELS.map((currentLevel, rowIndex) => (
                <MatrixRow
                  key={currentLevel}
                  currentLevel={currentLevel}
                  values={matrix[rowIndex]}
                />
              ))}
            </div>

            <div className="mt-3 grid grid-cols-[100px_1fr]">
              <div />

              <div className="text-center text-[9px] uppercase tracking-[0.2em] text-black/35">
                Future Risk →
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6 border-t border-black/10 pt-5">
          <div className="text-[9px] uppercase tracking-[0.18em] text-black/35">
            How to read
          </div>

          <p className="mt-2 max-w-3xl text-xs leading-6 text-black/50">
            The vertical axis represents the component&apos;s current anomaly state.
            The horizontal axis represents the projected future risk state.
            Components moving toward the upper-right region require the greatest
            engineering attention.
          </p>
        </div>
      </div>

      {/* PRIORITY REGISTER */}

      <div className="border border-black/10 bg-white/40">
        <div className="border-b border-black/10 px-6 py-5">
          <div className="text-[10px] uppercase tracking-[0.2em] text-black/35">
            Priority Register
          </div>

          <h2 className="mt-1 text-lg font-medium">Highest Risk Components</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[950px] border-collapse">
            <thead>
              <tr className="border-b border-black/10 bg-black/[0.025] text-left">
                <Header>Component</Header>

                <Header>Lot</Header>

                <Header>Risk Score</Header>

                <Header>Current</Header>

                <Header>Future</Header>

                <Header>Limit Util.</Header>

                <Header>Driver</Header>

                <Header>Decision</Header>

                <Header>Inspect</Header>
              </tr>
            </thead>

            <tbody>
              {highestRiskItems.map((item) => (
                <tr
                  key={item.component_id}
                  className="border-b border-black/10 transition hover:bg-black/[0.025]"
                >
                  <Cell>
                    <span className="font-mono text-xs">
                      {item.component_id ?? "—"}
                    </span>
                  </Cell>

                  <Cell>
                    <span className="font-mono text-xs text-black/55">
                      {item.lot_id ?? "—"}
                    </span>
                  </Cell>

                  <Cell>
                    <RiskScore value={getRiskScore(item)} />
                  </Cell>

                  <Cell>
                    <RiskBadge
                      level={normalizeRiskLevel(item.current_anomaly_level)}
                    />
                  </Cell>

                  <Cell>
                    <RiskBadge
                      level={normalizeRiskLevel(
                        item.final_risk_level ?? item.future_drift_risk,
                      )}
                    />
                  </Cell>

                  <Cell>
                    <span className="font-mono text-xs">
                      {formatNumber(item.upper_limit_utilization_percent)}%
                    </span>
                  </Cell>

                  <Cell>
                    <span className="block max-w-[180px] text-xs text-black/50">
                      {item.primary_risk_driver ?? "No driver available"}
                    </span>
                  </Cell>

                  <Cell>
                    <span className="text-[10px] uppercase tracking-wider text-black/50">
                      {item.final_decision ?? "—"}
                    </span>
                  </Cell>

                  <Cell>
                    {item.component_id ? (
                      <Link
                        href={`/components/${item.component_id}`}
                        className="inline-flex h-8 w-8 items-center justify-center border border-black/10 text-black/45 transition hover:border-black/30 hover:text-black"
                      >
                        →
                      </Link>
                    ) : (
                      "—"
                    )}
                  </Cell>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* MATRIX                                                                      */
/* -------------------------------------------------------------------------- */

function MatrixHeader({ level }: { level: RiskLevel }) {
  return (
    <div
      className={`flex min-h-[54px] items-center justify-center px-2 text-center text-[8px] uppercase tracking-[0.12em] ${matrixHeaderClass(
        level,
      )}`}
    >
      {level}
    </div>
  );
}

function MatrixRow({
  currentLevel,
  values,
}: {
  currentLevel: RiskLevel;
  values: number[];
}) {
  return (
    <>
      <div className="flex min-h-[64px] items-center justify-center bg-[#f4f4f1] px-2 text-center text-[8px] uppercase tracking-[0.12em] text-black/35">
        {currentLevel}
      </div>

      {values.map((value, index) => {
        const futureLevel = LEVELS[index];

        return (
          <div
            key={`${currentLevel}-${futureLevel}`}
            className={`flex min-h-[64px] items-center justify-center border-none font-mono text-sm ${matrixCellClass(
              currentLevel,
              futureLevel,
            )}`}
          >
            {value}
          </div>
        );
      })}
    </>
  );
}

function matrixHeaderClass(level: RiskLevel) {
  if (level === "CRITICAL") {
    return "bg-red-500/[0.08] text-red-700";
  }

  if (level === "HIGH") {
    return "bg-orange-500/[0.07] text-orange-700";
  }

  if (level === "MEDIUM") {
    return "bg-amber-400/[0.08] text-amber-700";
  }

  if (level === "LOW") {
    return "bg-yellow-300/[0.08] text-yellow-700";
  }

  return "bg-emerald-500/[0.06] text-emerald-700";
}

function matrixCellClass(current: RiskLevel, future: RiskLevel) {
  const currentIndex = LEVELS.indexOf(current);

  const futureIndex = LEVELS.indexOf(future);

  const combined = currentIndex + futureIndex;

  if (current === "CRITICAL" || future === "CRITICAL") {
    return "bg-red-500/[0.10] text-red-700";
  }

  if (combined >= 6 || current === "HIGH" || future === "HIGH") {
    return "bg-orange-500/[0.08] text-orange-700";
  }

  if (combined >= 4) {
    return "bg-amber-400/[0.09] text-amber-700";
  }

  if (combined >= 2) {
    return "bg-yellow-300/[0.07] text-yellow-700";
  }

  return "bg-white/40 text-black/55";
}

/* -------------------------------------------------------------------------- */
/* RISK                                                                       */
/* -------------------------------------------------------------------------- */

function normalizeRiskLevel(value?: string): RiskLevel {
  const text = String(value ?? "")
    .trim()
    .toUpperCase();

  if (text.includes("CRITICAL")) {
    return "CRITICAL";
  }

  if (text.includes("HIGH")) {
    return "HIGH";
  }

  if (text.includes("MEDIUM")) {
    return "MEDIUM";
  }

  if (text.includes("LOW")) {
    return "LOW";
  }

  return "NORMAL";
}

function getRiskScore(item: RiskMatrixItem) {
  const value =
    typeof item.risk_score === "number" && Number.isFinite(item.risk_score)
      ? item.risk_score
      : 0;

  return Math.min(100, Math.max(0, value));
}

/* -------------------------------------------------------------------------- */
/* UI                                                                         */
/* -------------------------------------------------------------------------- */

function RiskBadge({ level }: { level: RiskLevel }) {
  const classes: Record<RiskLevel, string> = {
    CRITICAL: "border-red-500/30 bg-red-500/10 text-red-700",
    HIGH: "border-orange-500/30 bg-orange-500/10 text-orange-700",
    MEDIUM: "border-amber-500/30 bg-amber-500/10 text-amber-700",
    LOW: "border-yellow-500/30 bg-yellow-500/10 text-yellow-700",
    NORMAL: "border-emerald-500/30 bg-emerald-500/10 text-emerald-700",
  };

  return (
    <span
      className={`inline-flex border px-2 py-1 text-[9px] uppercase tracking-wider ${classes[level]}`}
    >
      {level}
    </span>
  );
}

function RiskScore({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-3">
      <div className="h-1 w-14 bg-black/5">
        <div
          className="h-full bg-black"
          style={{
            width: `${value}%`,
          }}
        />
      </div>

      <span className="font-mono text-xs">{value.toFixed(1)}</span>
    </div>
  );
}

function Header({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-3 text-[9px] font-normal uppercase tracking-[0.15em] text-black/35">
      {children}
    </th>
  );
}

function Cell({ children }: { children: React.ReactNode }) {
  return <td className="px-4 py-4 align-middle">{children}</td>;
}

function formatNumber(value?: number) {
  if (value === undefined || value === null || !Number.isFinite(value)) {
    return "—";
  }

  return value.toFixed(1);
}
