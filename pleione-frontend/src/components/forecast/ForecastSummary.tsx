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

      <p className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
        {value}
      </p>

      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
        {description}
      </p>
    </div>
  );
}

interface ForecastSummaryProps {
  totalComponents: number;
  highRisk: number;
  predictedLimit: number;
  earlyDrift: number;
}

export default function ForecastSummary({
  totalComponents,
  highRisk,
  predictedLimit,
  earlyDrift,
}: ForecastSummaryProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <SummaryCard
        label="Predictions"
        value={totalComponents.toLocaleString()}
        description="Components with forecast data"
      />

      <SummaryCard
        label="High future risk"
        value={highRisk.toLocaleString()}
        description="Components with HIGH future drift risk"
      />

      <SummaryCard
        label="Limit concern"
        value={predictedLimit.toLocaleString()}
        description="Predicted future limit exceeded"
      />

      <SummaryCard
        label="Early drift"
        value={earlyDrift.toLocaleString()}
        description="Components showing early drift"
      />
    </div>
  );
}
