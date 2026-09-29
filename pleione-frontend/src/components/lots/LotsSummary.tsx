interface SummaryCardProps {
  label: string;
  value: string;
  description: string;
}

function SummaryCard({ label, value, description }: SummaryCardProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-5 py-4 dark:border-slate-800 dark:bg-slate-900">
      <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
        {label}
      </p>

      <div className="mt-2 flex items-baseline gap-2">
        <p className="text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
          {value}
        </p>
      </div>

      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
        {description}
      </p>
    </div>
  );
}

interface LotsSummaryProps {
  totalLots: number;
  totalComponents: number;
  totalAnomalies: number;
  anomalyRate: number;
}

export default function LotsSummary({
  totalLots,
  totalComponents,
  totalAnomalies,
  anomalyRate,
}: LotsSummaryProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <SummaryCard
        label="Total lots"
        value={totalLots.toLocaleString()}
        description="Screening lots available"
      />

      <SummaryCard
        label="Components"
        value={totalComponents.toLocaleString()}
        description="Components across all lots"
      />

      <SummaryCard
        label="Anomalies"
        value={totalAnomalies.toLocaleString()}
        description="Detected across all lots"
      />

      <SummaryCard
        label="Anomaly rate"
        value={`${anomalyRate.toFixed(2)}%`}
        description="Across all screened components"
      />
    </div>
  );
}
