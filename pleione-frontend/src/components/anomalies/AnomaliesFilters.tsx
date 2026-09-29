"use client";

type Props = {
  componentId: string;
  lotId: string;
  componentType: string;

  lotOptions: string[];
  componentTypeOptions: string[];

  onComponentIdChange: (value: string) => void;

  onLotIdChange: (value: string) => void;

  onComponentTypeChange: (value: string) => void;

  onClear: () => void;
};

export default function AnomaliesFilters({
  componentId,
  lotId,
  componentType,
  lotOptions,
  componentTypeOptions,
  onComponentIdChange,
  onLotIdChange,
  onComponentTypeChange,
  onClear,
}: Props) {
  const hasFilters =
    componentId.trim() !== "" ||
    lotId.trim() !== "" ||
    componentType.trim() !== "";

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-col gap-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
            Filters
          </h2>

          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Find specific anomaly records by component, lot, or type.
          </p>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          {/* Component ID */}
          <div>
            <label
              htmlFor="anomaly-component-id"
              className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-300"
            >
              Component ID
            </label>

            <input
              id="anomaly-component-id"
              type="text"
              value={componentId}
              onChange={(event) => onComponentIdChange(event.target.value)}
              placeholder="Search component"
              className="h-10 w-full rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-slate-500"
            />
          </div>

          {/* Lot */}
          <div>
            <label
              htmlFor="anomaly-lot-id"
              className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-300"
            >
              Lot
            </label>

            <select
              id="anomaly-lot-id"
              value={lotId}
              onChange={(event) => onLotIdChange(event.target.value)}
              className="h-10 w-full appearance-none rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:border-slate-500"
            >
              <option value="">All lots</option>

              {lotOptions.map((lot) => (
                <option key={lot} value={lot}>
                  {lot}
                </option>
              ))}
            </select>
          </div>

          {/* Component Type */}
          <div>
            <label
              htmlFor="anomaly-component-type"
              className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-300"
            >
              Component type
            </label>

            <select
              id="anomaly-component-type"
              value={componentType}
              onChange={(event) => onComponentTypeChange(event.target.value)}
              className="h-10 w-full appearance-none rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:border-slate-500"
            >
              <option value="">All component types</option>

              {componentTypeOptions.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>
        </div>

        {hasFilters && (
          <div>
            <button
              type="button"
              onClick={onClear}
              className="text-xs font-medium text-slate-600 transition hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
            >
              Clear filters
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
