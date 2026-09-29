"use client";

function clampNonNegative(value: unknown) {
  const number = Number(value);

  if (!Number.isFinite(number)) {
    return 0;
  }

  return Math.max(0, number);
}

function formatMicroAmp(value: unknown) {
  return `${clampNonNegative(value).toFixed(2)} µA`;
}

type Props = {
  component: any;
  prediction: any;
  risk: any;
};

export default function MeasurementsAndPrediction({
  component,
  prediction,
  risk,
}: Props) {
  const iddq0 = clampNonNegative(
    prediction?.iddq_0h_uA ?? component?.iddq_0h_uA,
  );

  const iddq24 = clampNonNegative(
    prediction?.iddq_24h_uA ?? component?.iddq_24h_uA,
  );

  const leakage0 = clampNonNegative(
    prediction?.leakage_0h_uA ?? component?.leakage_0h_uA,
  );

  const leakage24 = clampNonNegative(
    prediction?.leakage_24h_uA ?? component?.leakage_24h_uA,
  );

  const delta = Math.max(0, iddq24 - iddq0);

  const predicted = clampNonNegative(prediction?.predicted_168h_uA);

  const lower = clampNonNegative(prediction?.prediction_lower_uA);

  const upper = clampNonNegative(prediction?.prediction_upper_uA);

  const limit = clampNonNegative(
    prediction?.absolute_limit_uA ?? component?.absolute_limit_uA,
  );

  const probability = Math.min(
    1,
    Math.max(
      0,
      Number(prediction?.failure_probability ?? risk?.failure_probability ?? 0),
    ),
  );

  return (
    <section>
      <SectionHeading
        title="Measurements & Prediction"
        description="Observed screening measurements and the model's future estimate."
      />

      <div className="mt-5 grid gap-x-10 gap-y-8 md:grid-cols-2 xl:grid-cols-3">
        <Measurement
          label="IDDQ · 0H"
          value={formatMicroAmp(iddq0)}
          type="observed"
        />

        <Measurement
          label="IDDQ · 24H"
          value={formatMicroAmp(iddq24)}
          type="observed"
        />

        <Measurement
          label="0H → 24H change"
          value={`+${delta.toFixed(2)} µA`}
          type="observed"
        />

        <Measurement
          label="Leakage · 0H"
          value={formatMicroAmp(leakage0)}
          type="observed"
        />

        <Measurement
          label="Leakage · 24H"
          value={formatMicroAmp(leakage24)}
          type="observed"
        />

        <Measurement
          label="Predicted · 168H"
          value={formatMicroAmp(predicted)}
          type="prediction"
        />

        <Measurement
          label="Prediction interval"
          value={`${lower.toFixed(2)} — ${upper.toFixed(2)} µA`}
          type="prediction"
        />

        <Measurement
          label="Specification limit"
          value={formatMicroAmp(limit)}
          type="limit"
        />

        <Measurement
          label="Future failure probability"
          value={`${(probability * 100).toFixed(1)}%`}
          type="risk"
        />
      </div>
    </section>
  );
}

function SectionHeading({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div>
      <h2 className="text-base font-semibold text-white">{title}</h2>

      <p className="mt-1 text-sm text-slate-500">{description}</p>
    </div>
  );
}

function Measurement({
  label,
  value,
  type,
}: {
  label: string;
  value: string;
  type: "observed" | "prediction" | "limit" | "risk";
}) {
  const labelColor =
    type === "prediction"
      ? "text-sky-400"
      : type === "limit"
        ? "text-slate-500"
        : type === "risk"
          ? "text-amber-400"
          : "text-slate-500";

  return (
    <div className="border-b border-slate-800/70 pb-4">
      <p
        className={`text-[11px] font-semibold uppercase tracking-[0.16em] ${labelColor}`}
      >
        {label}
      </p>

      <p className="mt-2 font-mono tabular-nums text-xl font-semibold tracking-tight text-slate-100">
        {value}
      </p>
    </div>
  );
}
