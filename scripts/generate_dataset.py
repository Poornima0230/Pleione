"""
Final synthetic dataset generator for SIH 2026 Pleione.

Problem:
AI-Driven Anomaly Detection in Component Burn-In & Screening

Dataset design
--------------
5 batches × 2,000 components = 10,000 components

Ground-truth behavior:
    Normal           ~60%
    High_Stable      ~12%
    Latent_Defect    ~10%
    Sudden_Anomaly    ~8%
    Absolute_Failure ~10%

Important deployment-time information boundary
----------------------------------------------
Module A:
    Uses ONLY 0h measurements to detect present abnormality.

Module B:
    Uses ONLY 0h + 24h measurements to predict 168h behavior.

96h and 168h values:
    Present in the dataset for offline training/evaluation targets,
    but MUST NOT be used as deployment-time inputs.

ground_truth:
    Used only for offline evaluation.
    It is NOT a model feature.

Output:
    data/batch_1.csv
    data/batch_2.csv
    data/batch_3.csv
    data/batch_4.csv
    data/batch_5.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 42

NUM_BATCHES = 5
ROWS_PER_BATCH = 2000

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data"

ABSOLUTE_LIMIT_UA = 50.0


# Exact output schema
COLUMNS = [
    "component_id",
    "lot_id",
    "component_type",
    "temperature_C",
    "voltage_V",
    "iddq_0h_uA",
    "iddq_24h_uA",
    "iddq_96h_uA",
    "iddq_168h_uA",
    "leakage_0h_uA",
    "leakage_24h_uA",
    "leakage_96h_uA",
    "leakage_168h_uA",
    "ground_truth",
    "absolute_limit_uA",
]


# ============================================================
# COMPONENT CONFIGURATION
# ============================================================

COMPONENT_TYPES = [
    "ASIC",
    "FPGA",
    "ADC",
    "DAC",
]


# Approximate population distribution.
GROUND_TRUTH_PROBABILITIES = {
    "Normal": 0.60,
    "High_Stable": 0.12,
    "Latent_Defect": 0.10,
    "Sudden_Anomaly": 0.08,
    "Absolute_Failure": 0.10,
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def choose_component_type(rng: np.random.Generator) -> str:
    """
    Select a component type.

    Slightly different population weights make the synthetic
    dataset less artificially uniform.
    """

    probabilities = np.array([
        0.30,  # ASIC
        0.28,  # FPGA
        0.22,  # ADC
        0.20,  # DAC
    ])

    return rng.choice(
        COMPONENT_TYPES,
        p=probabilities,
    )


def generate_temperature(
    component_type: str,
    rng: np.random.Generator,
) -> float:
    """
    Generate burn-in temperature.

    Values are centered around 125°C, representative of a
    high-temperature burn-in environment.
    """

    type_offsets = {
        "ASIC": 0.0,
        "FPGA": 0.3,
        "ADC": -0.2,
        "DAC": 0.1,
    }

    temperature = (
        125.0
        + type_offsets[component_type]
        + rng.normal(0.0, 0.8)
    )

    return round(float(temperature), 2)


def generate_voltage(
    component_type: str,
    rng: np.random.Generator,
) -> float:
    """
    Generate supply voltage.

    Small component-type differences are intentionally included
    so peer grouping has meaningful environmental context.
    """

    type_nominal = {
        "ASIC": 1.20,
        "FPGA": 1.10,
        "ADC": 1.80,
        "DAC": 1.80,
    }

    voltage = (
        type_nominal[component_type]
        + rng.normal(0.0, 0.015)
    )

    return round(float(voltage), 3)


def generate_base_iddq(
    component_type: str,
    temperature: float,
    voltage: float,
    rng: np.random.Generator,
) -> float:
    """
    Generate the 0h baseline IDDQ.

    IMPORTANT:
        This function does NOT depend on ground_truth behavior.

    This ensures that:
        - Module A has to detect anomalies from measurements.
        - ground_truth is not trivially encoded in the first
          measurement.
    """

    type_baseline = {
        "ASIC": 11.4,
        "FPGA": 11.6,
        "ADC": 11.3,
        "DAC": 11.5,
    }

    base = type_baseline[component_type]

    temperature_effect = (temperature - 125.0) * 0.025
    voltage_effect = (voltage - 1.20) * 0.8

    noise = rng.normal(0.0, 0.35)

    iddq = (
        base
        + temperature_effect
        + voltage_effect
        + noise
    )

    return max(2.0, float(iddq))


def generate_trajectory(
    behavior: str,
    iddq_0h: float,
    rng: np.random.Generator,
):
    """
    Generate the IDDQ trajectory:

        0h → 24h → 96h → 168h

    The trajectory is intentionally designed so that different
    failure modes emerge over time.

    Behavior definitions
    --------------------

    Normal:
        Small early drift and modest later drift.

    High_Stable:
        Starts slightly high but remains stable.

    Latent_Defect:
        Early warning is visible at 24h, followed by increasing
        degradation.

    Absolute_Failure:
        Eventually crosses the 50 µA absolute specification
        limit at 168h.

        Three profiles are used:
            - early_warning
            - moderate_warning
            - late_acceleration

    Sudden_Anomaly:
        Looks relatively reasonable early, then experiences a
        strong late-life jump between 96h and 168h.
    """

    # --------------------------------------------------------
    # NORMAL
    # --------------------------------------------------------

    if behavior == "Normal":

        drift_0_24 = rng.uniform(0.30, 1.20)

        drift_24_96 = rng.uniform(0.25, 1.20)

        drift_96_168 = rng.uniform(0.30, 1.50)

        iddq_24 = (
            iddq_0h
            + drift_0_24
            + rng.normal(0.0, 0.15)
        )

        iddq_96 = (
            iddq_24
            + drift_24_96
            + rng.normal(0.0, 0.20)
        )

        iddq_168 = (
            iddq_96
            + drift_96_168
            + rng.normal(0.0, 0.25)
        )

    # --------------------------------------------------------
    # HIGH STABLE
    # --------------------------------------------------------

    elif behavior == "High_Stable":

        # Starts somewhat high but remains stable.
        starting_offset = rng.uniform(0.0, 0.7)

        iddq_0h += starting_offset

        drift_0_24 = rng.uniform(0.02, 0.25)

        drift_24_96 = rng.uniform(0.02, 0.20)

        drift_96_168 = rng.uniform(0.02, 0.25)

        iddq_24 = (
            iddq_0h
            + drift_0_24
            + rng.normal(0.0, 0.12)
        )

        iddq_96 = (
            iddq_24
            + drift_24_96
            + rng.normal(0.0, 0.15)
        )

        iddq_168 = (
            iddq_96
            + drift_96_168
            + rng.normal(0.0, 0.20)
        )

    # --------------------------------------------------------
    # LATENT DEFECT
    # --------------------------------------------------------

    elif behavior == "Latent_Defect":

        # Early degradation is deliberately visible at 24h.
        drift_0_24 = rng.uniform(0.80, 2.00)

        # Degradation accelerates after 24h.
        drift_24_96 = rng.uniform(2.00, 5.00)

        drift_96_168 = rng.uniform(3.50, 8.00)

        iddq_24 = (
            iddq_0h
            + drift_0_24
            + rng.normal(0.0, 0.15)
        )

        iddq_96 = (
            iddq_24
            + drift_24_96
            + rng.normal(0.0, 0.25)
        )

        iddq_168 = (
            iddq_96
            + drift_96_168
            + rng.normal(0.0, 0.30)
        )

    # --------------------------------------------------------
    # ABSOLUTE FAILURE
    # --------------------------------------------------------

    elif behavior == "Absolute_Failure":

        # Three different temporal failure profiles.
        #
        # The final value is explicitly guaranteed to exceed
        # the 50 µA absolute specification.

        profile = rng.choice(
            [
                "early_warning",
                "moderate_warning",
                "late_acceleration",
            ],
            p=[
                0.35,
                0.40,
                0.25,
            ],
        )

        if profile == "early_warning":

            drift_0_24 = rng.uniform(1.50, 3.00)

            drift_24_96 = rng.uniform(5.00, 10.00)

            drift_96_168 = rng.uniform(20.00, 35.00)

        elif profile == "moderate_warning":

            drift_0_24 = rng.uniform(0.90, 2.20)

            drift_24_96 = rng.uniform(4.00, 8.00)

            drift_96_168 = rng.uniform(25.00, 38.00)

        else:

            drift_0_24 = rng.uniform(0.40, 1.50)

            drift_24_96 = rng.uniform(2.00, 5.00)

            drift_96_168 = rng.uniform(30.00, 42.00)

        iddq_24 = (
            iddq_0h
            + drift_0_24
            + rng.normal(0.0, 0.20)
        )

        iddq_96 = (
            iddq_24
            + drift_24_96
            + rng.normal(0.0, 0.30)
        )

        iddq_168 = (
            iddq_96
            + drift_96_168
            + rng.normal(0.0, 0.40)
        )

        # Guarantee the specification violation.
        if iddq_168 <= ABSOLUTE_LIMIT_UA:
            iddq_168 = (
                ABSOLUTE_LIMIT_UA
                + rng.uniform(1.0, 12.0)
            )

    # --------------------------------------------------------
    # SUDDEN ANOMALY
    # --------------------------------------------------------

    elif behavior == "Sudden_Anomaly":

        # Some early signal exists, but the defining behavior
        # is the large jump between 96h and 168h.

        drift_0_24 = rng.uniform(0.30, 1.60)

        drift_24_96 = rng.uniform(0.80, 2.80)

        sudden_jump = rng.uniform(12.00, 28.00)

        iddq_24 = (
            iddq_0h
            + drift_0_24
            + rng.normal(0.0, 0.15)
        )

        iddq_96 = (
            iddq_24
            + drift_24_96
            + rng.normal(0.0, 0.25)
        )

        iddq_168 = (
            iddq_96
            + sudden_jump
            + rng.normal(0.0, 0.35)
        )

    else:
        raise ValueError(
            f"Unknown ground truth behavior: {behavior}"
        )

    # Measurements cannot be negative.
    iddq_24 = max(0.1, iddq_24)
    iddq_96 = max(0.1, iddq_96)
    iddq_168 = max(0.1, iddq_168)

    return (
        float(iddq_0h),
        float(iddq_24),
        float(iddq_96),
        float(iddq_168),
    )


def generate_leakage(
    iddq_0h: float,
    iddq_24h: float,
    iddq_96h: float,
    iddq_168h: float,
    rng: np.random.Generator,
):
    """
    Generate leakage-current measurements correlated with IDDQ.

    Leakage is NOT simply IDDQ * constant.

    Noise and a small nonlinear component are added so the
    relationship is realistic enough for anomaly detection.
    """

    def leakage_from_iddq(iddq: float) -> float:
        nonlinear_effect = 0.0008 * (iddq ** 2)

        noise = rng.normal(
            0.0,
            0.025,
        )

        value = (
            0.095 * iddq
            + nonlinear_effect
            + noise
        )

        return max(0.01, float(value))

    leakage_0h = leakage_from_iddq(iddq_0h)

    leakage_24h = leakage_from_iddq(iddq_24h)

    leakage_96h = leakage_from_iddq(iddq_96h)

    leakage_168h = leakage_from_iddq(iddq_168h)

    return (
        leakage_0h,
        leakage_24h,
        leakage_96h,
        leakage_168h,
    )


def choose_ground_truth(
    rng: np.random.Generator,
) -> str:
    """
    Select ground-truth behavior according to the intended
    population distribution.
    """

    labels = list(
        GROUND_TRUTH_PROBABILITIES.keys()
    )

    probabilities = list(
        GROUND_TRUTH_PROBABILITIES.values()
    )

    return rng.choice(
        labels,
        p=probabilities,
    )


# ============================================================
# GENERATE ONE BATCH
# ============================================================

def generate_batch(
    batch_number: int,
    rng: np.random.Generator,
) -> pd.DataFrame:
    """
    Generate one 2,000-component batch.
    """

    rows = []

    lot_id = f"L{batch_number}"

    start_component_number = (
        (batch_number - 1) * ROWS_PER_BATCH
        + 1
    )

    for row_number in range(ROWS_PER_BATCH):

        component_number = (
            start_component_number
            + row_number
        )

        component_id = (
            f"C{component_number:05d}"
        )

        component_type = choose_component_type(
            rng
        )

        temperature = generate_temperature(
            component_type,
            rng,
        )

        voltage = generate_voltage(
            component_type,
            rng,
        )

        # Ground truth is assigned only after environmental
        # properties have been generated.
        behavior = choose_ground_truth(rng)

        # ----------------------------------------------------
        # 0h baseline
        # ----------------------------------------------------

        iddq_0h = generate_base_iddq(
            component_type=component_type,
            temperature=temperature,
            voltage=voltage,
            rng=rng,
        )

        # ----------------------------------------------------
        # Temporal IDDQ trajectory
        # ----------------------------------------------------

        (
            iddq_0h,
            iddq_24h,
            iddq_96h,
            iddq_168h,
        ) = generate_trajectory(
            behavior=behavior,
            iddq_0h=iddq_0h,
            rng=rng,
        )

        # ----------------------------------------------------
        # Leakage trajectory
        # ----------------------------------------------------

        (
            leakage_0h,
            leakage_24h,
            leakage_96h,
            leakage_168h,
        ) = generate_leakage(
            iddq_0h=iddq_0h,
            iddq_24h=iddq_24h,
            iddq_96h=iddq_96h,
            iddq_168h=iddq_168h,
            rng=rng,
        )

        rows.append(
            {
                "component_id": component_id,
                "lot_id": lot_id,
                "component_type": component_type,

                "temperature_C": round(
                    temperature,
                    2,
                ),

                "voltage_V": round(
                    voltage,
                    3,
                ),

                "iddq_0h_uA": round(
                    iddq_0h,
                    4,
                ),

                "iddq_24h_uA": round(
                    iddq_24h,
                    4,
                ),

                "iddq_96h_uA": round(
                    iddq_96h,
                    4,
                ),

                "iddq_168h_uA": round(
                    iddq_168h,
                    4,
                ),

                "leakage_0h_uA": round(
                    leakage_0h,
                    4,
                ),

                "leakage_24h_uA": round(
                    leakage_24h,
                    4,
                ),

                "leakage_96h_uA": round(
                    leakage_96h,
                    4,
                ),

                "leakage_168h_uA": round(
                    leakage_168h,
                    4,
                ),

                "ground_truth": behavior,

                "absolute_limit_uA": (
                    ABSOLUTE_LIMIT_UA
                ),
            }
        )

    return pd.DataFrame(
        rows,
        columns=COLUMNS,
    )


# ============================================================
# VALIDATION
# ============================================================

def validate_batch(
    df: pd.DataFrame,
    batch_number: int,
) -> None:
    """
    Validate a generated batch before saving it.
    """

    # Row count
    assert len(df) == ROWS_PER_BATCH, (
        f"Batch {batch_number}: expected "
        f"{ROWS_PER_BATCH} rows, got {len(df)}"
    )

    # Schema
    assert list(df.columns) == COLUMNS, (
        f"Batch {batch_number}: schema mismatch"
    )

    # Missing values
    assert not df.isnull().any().any(), (
        f"Batch {batch_number}: missing values found"
    )

    # Component IDs
    assert df["component_id"].is_unique, (
        f"Batch {batch_number}: duplicate component IDs"
    )

    # Lot
    expected_lot = f"L{batch_number}"

    assert (
        df["lot_id"] == expected_lot
    ).all(), (
        f"Batch {batch_number}: incorrect lot IDs"
    )

    # Component types
    assert df["component_type"].isin(
        COMPONENT_TYPES
    ).all(), (
        f"Batch {batch_number}: invalid component type"
    )

    # Ground truth
    assert df["ground_truth"].isin(
        GROUND_TRUTH_PROBABILITIES.keys()
    ).all(), (
        f"Batch {batch_number}: invalid ground truth"
    )

    # Numeric measurement checks
    numeric_columns = [
        "temperature_C",
        "voltage_V",
        "iddq_0h_uA",
        "iddq_24h_uA",
        "iddq_96h_uA",
        "iddq_168h_uA",
        "leakage_0h_uA",
        "leakage_24h_uA",
        "leakage_96h_uA",
        "leakage_168h_uA",
        "absolute_limit_uA",
    ]

    for column in numeric_columns:

        assert np.isfinite(
            df[column].to_numpy()
        ).all(), (
            f"Batch {batch_number}: "
            f"non-finite values in {column}"
        )

    # Positive current values
    current_columns = [
        "iddq_0h_uA",
        "iddq_24h_uA",
        "iddq_96h_uA",
        "iddq_168h_uA",
        "leakage_0h_uA",
        "leakage_24h_uA",
        "leakage_96h_uA",
        "leakage_168h_uA",
    ]

    for column in current_columns:

        assert (
            df[column] > 0
        ).all(), (
            f"Batch {batch_number}: "
            f"non-positive values in {column}"
        )

    # Specification
    assert (
        df["absolute_limit_uA"]
        == ABSOLUTE_LIMIT_UA
    ).all(), (
        f"Batch {batch_number}: "
        "incorrect absolute limit"
    )

    # Absolute failures should violate the specification.
    failures = df[
        df["ground_truth"]
        == "Absolute_Failure"
    ]

    assert (
        failures["iddq_168h_uA"]
        > ABSOLUTE_LIMIT_UA
    ).all(), (
        f"Batch {batch_number}: "
        "Absolute_Failure contains "
        "non-violating 168h values"
    )


# ============================================================
# SUMMARY
# ============================================================

def print_batch_summary(
    df: pd.DataFrame,
    batch_number: int,
) -> None:
    """
    Print useful validation information.
    """

    print()
    print("=" * 70)
    print(f"BATCH {batch_number}")
    print("=" * 70)

    print(f"Rows: {len(df)}")

    print()
    print("Ground-truth distribution:")

    distribution = (
        df["ground_truth"]
        .value_counts()
        .reindex(
            GROUND_TRUTH_PROBABILITIES.keys(),
            fill_value=0,
        )
    )

    for label, count in distribution.items():

        percentage = (
            count
            / len(df)
            * 100
        )

        print(
            f"  {label:<18} "
            f"{count:>4} "
            f"({percentage:>5.2f}%)"
        )

    violations = (
        df["iddq_168h_uA"]
        > df["absolute_limit_uA"]
    )

    print()
    print(
        "168h specification violations:",
        int(violations.sum()),
    )

    print()
    print(
        "Early-signal statistics:"
    )

    delta_0_24 = (
        df["iddq_24h_uA"]
        - df["iddq_0h_uA"]
    )

    print(
        f"  Mean IDDQ 0h: "
        f"{df['iddq_0h_uA'].mean():.4f} µA"
    )

    print(
        f"  Mean IDDQ 24h: "
        f"{df['iddq_24h_uA'].mean():.4f} µA"
    )

    print(
        f"  Mean Δ0→24h: "
        f"{delta_0_24.mean():.4f} µA"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("PLEIONE — FINAL SYNTHETIC DATASET GENERATOR")
    print("=" * 70)

    print()
    print(
        "Output directory:",
        OUTPUT_DIR,
    )

    print()
    print(
        "Dataset:",
        f"{NUM_BATCHES} batches × "
        f"{ROWS_PER_BATCH} rows = "
        f"{NUM_BATCHES * ROWS_PER_BATCH} rows",
    )

    print()
    print(
        "Ground-truth target distribution:"
    )

    for label, probability in (
        GROUND_TRUTH_PROBABILITIES.items()
    ):
        print(
            f"  {label:<18} "
            f"{probability * 100:>5.1f}%"
        )

    # Make sure output directory exists.
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # One deterministic RNG.
    rng = np.random.default_rng(SEED)

    all_batches = []

    # --------------------------------------------------------
    # Generate all batches
    # --------------------------------------------------------

    for batch_number in range(
        1,
        NUM_BATCHES + 1,
    ):

        df = generate_batch(
            batch_number=batch_number,
            rng=rng,
        )

        validate_batch(
            df,
            batch_number,
        )

        output_path = (
            OUTPUT_DIR
            / f"batch_{batch_number}.csv"
        )

        df.to_csv(
            output_path,
            index=False,
        )

        all_batches.append(df)

        print_batch_summary(
            df,
            batch_number,
        )

        print()
        print(
            f"Saved: {output_path}"
        )

    # --------------------------------------------------------
    # Combined validation
    # --------------------------------------------------------

    combined = pd.concat(
        all_batches,
        ignore_index=True,
    )

    print()
    print("=" * 70)
    print("COMBINED DATASET VALIDATION")
    print("=" * 70)

    print()
    print(
        f"Total rows: {len(combined)}"
    )

    assert (
        len(combined)
        == NUM_BATCHES * ROWS_PER_BATCH
    )

    assert (
        combined["component_id"].is_unique
    )

    assert not combined.isnull().any().any()

    # --------------------------------------------------------
    # Overall ground-truth distribution
    # --------------------------------------------------------

    print()
    print("Overall ground-truth distribution:")

    overall_distribution = (
        combined["ground_truth"]
        .value_counts()
        .reindex(
            GROUND_TRUTH_PROBABILITIES.keys(),
            fill_value=0,
        )
    )

    for label, count in (
        overall_distribution.items()
    ):

        percentage = (
            count
            / len(combined)
            * 100
        )

        print(
            f"  {label:<18} "
            f"{count:>5} "
            f"({percentage:>5.2f}%)"
        )

    # --------------------------------------------------------
    # 168h specification violations
    # --------------------------------------------------------

    violations = (
        combined["iddq_168h_uA"]
        > combined["absolute_limit_uA"]
    )

    print()
    print(
        "Overall 168h specification violations:",
        int(violations.sum()),
    )

    print(
        "Overall 168h non-violations:",
        int((~violations).sum()),
    )

    # Breakdown by ground truth
    print()
    print(
        "168h violations by ground truth:"
    )

    violation_summary = (
        combined.assign(
            violation=violations
        )
        .groupby("ground_truth")["violation"]
        .agg(
            total="count",
            violations="sum",
        )
        .reindex(
            GROUND_TRUTH_PROBABILITIES.keys()
        )
    )

    violation_summary[
        "violation_rate"
    ] = (
        violation_summary["violations"]
        / violation_summary["total"]
        * 100
    )

    for label, row in (
        violation_summary.iterrows()
    ):

        print(
            f"  {label:<18} "
            f"{int(row['violations']):>4}"
            f"/{int(row['total']):<4} "
            f"({row['violation_rate']:>6.2f}%)"
        )

    # --------------------------------------------------------
    # Early signal summary by ground truth
    # --------------------------------------------------------

    combined["delta_0_24"] = (
        combined["iddq_24h_uA"]
        - combined["iddq_0h_uA"]
    )

    print()
    print(
        "Early-signal summary by ground truth:"
    )

    early_summary = (
        combined
        .groupby("ground_truth")
        [
            [
                "iddq_0h_uA",
                "iddq_24h_uA",
                "delta_0_24",
                "iddq_96h_uA",
                "iddq_168h_uA",
            ]
        ]
        .mean()
        .reindex(
            GROUND_TRUTH_PROBABILITIES.keys()
        )
    )

    print(
        early_summary.to_string(
            float_format=lambda x: f"{x:.3f}"
        )
    )

    # --------------------------------------------------------
    # Save combined dataset
    #
    # This is an additional convenience file.
    # The five batch files remain the official split files.
    # --------------------------------------------------------

    combined_output = (
        OUTPUT_DIR
        / "all_batches_combined.csv"
    )

    # Do not include the derived delta column in the official
    # raw dataset because delta_0_24 is intended to be derived
    # by the model pipeline.
    combined_to_save = combined.drop(
        columns=["delta_0_24"]
    )

    combined_to_save.to_csv(
        combined_output,
        index=False,
    )

    print()
    print(
        f"Saved combined dataset: "
        f"{combined_output}"
    )

    # --------------------------------------------------------
    # Final checks
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("FINAL CHECKS")
    print("=" * 70)

    print()
    print("✓ 5 batches generated")
    print("✓ 2,000 rows per batch")
    print("✓ 10,000 total components")
    print("✓ Exact 15-column schema")
    print("✓ No missing values")
    print("✓ No duplicate component IDs")
    print("✓ 50 µA specification preserved")
    print("✓ Absolute failures exceed 50 µA at 168h")
    print("✓ Ground truth is not encoded directly in 0h baseline")
    print("✓ 96h/168h values are retained for offline evaluation")
    print("✓ Module A can use only 0h data")
    print("✓ Module B can use only 0h + 24h data")
    print("✓ ground_truth is evaluation-only")

    print()
    print("=" * 70)
    print("DATASET GENERATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()