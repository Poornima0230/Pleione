interface ForecastFiltersProps {
  componentId: string;
  lotId: string;
  riskLevel: string;
  status: string;

  lots: string[];
  riskLevels: string[];
  statuses: string[];

  onComponentIdChange: (value: string) => void;
  onLotChange: (value: string) => void;
  onRiskChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onReset: () => void;
}

export default function ForecastFilters({
  componentId,
  lotId,
  riskLevel,
  status,
  lots,
  riskLevels,
  statuses,
  onComponentIdChange,
  onLotChange,
  onRiskChange,
  onStatusChange,
  onReset,
}: ForecastFiltersProps) {
  const hasFilters = Boolean(componentId || lotId || riskLevel || status);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-col gap-1">
        <h2 className="text-base font-semibold text-slate-900 dark:text-white">
          Filters
        </h2>

        <p className="text-sm text-slate-500 dark:text-slate-400">
          Narrow forecast results by component, lot, or future assessment.
        </p>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        <input
          type="text"
          value={componentId}
          onChange={(event) => onComponentIdChange(event.target.value)}
          placeholder="Component ID"
          className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:placeholder:text-slate-500"
        />

        <select
          value={lotId}
          onChange={(event) => onLotChange(event.target.value)}
          className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-white"
        >
          <option value="">All lots</option>

          {lots.map((lot) => (
            <option key={lot} value={lot}>
              {lot}
            </option>
          ))}
        </select>

        <select
          value={riskLevel}
          onChange={(event) => onRiskChange(event.target.value)}
          className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-white"
        >
          <option value="">All future risk</option>

          {riskLevels.map((risk) => (
            <option key={risk} value={risk}>
              {risk}
            </option>
          ))}
        </select>

        <select
          value={status}
          onChange={(event) => onStatusChange(event.target.value)}
          className="h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none dark:border-slate-700 dark:bg-slate-950 dark:text-white"
        >
          <option value="">All forecast status</option>

          {statuses.map((item) => (
            <option key={item} value={item}>
              {item}
            </option>
          ))}
        </select>
      </div>

      {hasFilters && (
        <div className="mt-3">
          <button
            type="button"
            onClick={onReset}
            className="text-sm font-medium text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  );
}
