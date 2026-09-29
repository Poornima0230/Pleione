import os
import random

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_DIR = "../data"

NUM_BATCHES = 5
ROWS_PER_BATCH = 2000

RANDOM_SEED = 42

COMPONENT_TYPES = ["TypeA", "TypeB", "TypeC"]

# Synthetic population proportions.
#
# These are intentionally not equal.
# Most components should be healthy, while a smaller
# percentage should require investigation/future screening.
BEHAVIOR_PROBABILITIES = {
    "Normal": 0.60,
    "High_Stable": 0.12,
    "Latent_Defect": 0.10,
    "Sudden_Anomaly": 0.08,
    "Absolute_Failure": 0.10,
}

BEHAVIORS = list(BEHAVIOR_PROBABILITIES.keys())

ABSOLUTE_LIMIT_UA = 50.0


# ============================================================
# REPRODUCIBILITY
# ============================================================

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def rounded(value, digits=2):
    return round(float(value), digits)


# ============================================================
# BASE 0h IDDQ
# ============================================================

def generate_base_iddq(temperature, voltage):
    """
    Generate the initial 0h IDDQ.

    IMPORTANT:

    ground_truth is NOT used here.

    Therefore the 0h measurement itself does not directly
    reveal whether the component will eventually fail.
    """

    temperature_effect = 0.08 * (temperature - 30.0)

    voltage_effect = 2.0 * (voltage - 1.15)

    random_variation = np.random.normal(
        loc=0.0,
        scale=0.75
    )

    base = (
        11.5
        + temperature_effect
        + voltage_effect
        + random_variation
    )

    return clamp(base, 8.0, 15.0)


# ============================================================
# BEHAVIOR SELECTION
# ============================================================

def generate_behavior():
    """
    Select ground-truth behavior using the configured
    synthetic population distribution.
    """

    return random.choices(
        population=BEHAVIORS,
        weights=[
            BEHAVIOR_PROBABILITIES[b]
            for b in BEHAVIORS
        ],
        k=1
    )[0]


# ============================================================
# IDDQ TRAJECTORY GENERATION
# ============================================================

def generate_trajectory(base, behavior):
    """
    Generate IDDQ at:

        0h
        24h
        96h
        168h

    Design principle:

        Early measurements contain partial information.

        Later measurements reveal the eventual trajectory.

    Different behaviors intentionally overlap during early life.
    """

    iddq_0h = base

    # ========================================================
    # NORMAL
    # ========================================================

    if behavior == "Normal":

        early_drift = np.random.uniform(
            0.20,
            1.40
        )

        iddq_24h = (
            iddq_0h
            + early_drift
            + np.random.normal(0.0, 0.20)
        )

        mid_drift = np.random.uniform(
            0.20,
            1.20
        )

        iddq_96h = (
            iddq_24h
            + mid_drift
            + np.random.normal(0.0, 0.30)
        )

        late_drift = np.random.uniform(
            0.20,
            1.50
        )

        iddq_168h = (
            iddq_96h
            + late_drift
            + np.random.normal(0.0, 0.35)
        )

    # ========================================================
    # HIGH STABLE
    # ========================================================

    elif behavior == "High_Stable":

        early_drift = np.random.uniform(
            -0.20,
            0.50
        )

        iddq_24h = (
            iddq_0h
            + early_drift
            + np.random.normal(0.0, 0.15)
        )

        iddq_96h = (
            iddq_24h
            + np.random.uniform(-0.30, 0.50)
            + np.random.normal(0.0, 0.18)
        )

        iddq_168h = (
            iddq_96h
            + np.random.uniform(-0.30, 0.60)
            + np.random.normal(0.0, 0.20)
        )

    # ========================================================
    # LATENT DEFECT
    # ========================================================

    elif behavior == "Latent_Defect":

        # Early signal overlaps somewhat with Normal.
        early_drift = np.random.uniform(
            0.80,
            2.00
        )

        iddq_24h = (
            iddq_0h
            + early_drift
            + np.random.normal(0.0, 0.25)
        )

        # Degradation becomes more visible.
        mid_acceleration = np.random.uniform(
            2.00,
            5.00
        )

        iddq_96h = (
            iddq_24h
            + mid_acceleration
            + np.random.normal(0.0, 0.40)
        )

        late_acceleration = np.random.uniform(
            3.00,
            8.00
        )

        iddq_168h = (
            iddq_96h
            + late_acceleration
            + np.random.normal(0.0, 0.50)
        )

    # ========================================================
    # ABSOLUTE FAILURE
    # ========================================================

    elif behavior == "Absolute_Failure":

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # Not every failure gets the same early trajectory.
        #
        # Some have:
        #   strong early warning
        #
        # Some have:
        #   moderate early warning
        #
        # Some have:
        #   weak early warning
        #
        # This makes Module B a real prediction problem.
        # ----------------------------------------------------

        failure_profile = random.choices(
            [
                "early_warning",
                "moderate_warning",
                "late_acceleration",
            ],
            weights=[
                0.35,
                0.40,
                0.25,
            ],
            k=1
        )[0]

        # ----------------------------------------------------
        # Early warning failure
        # ----------------------------------------------------

        if failure_profile == "early_warning":

            early_drift = np.random.uniform(
                1.50,
                3.00
            )

            iddq_24h = (
                iddq_0h
                + early_drift
                + np.random.normal(0.0, 0.25)
            )

            mid_acceleration = np.random.uniform(
                5.00,
                10.00
            )

            iddq_96h = (
                iddq_24h
                + mid_acceleration
                + np.random.normal(0.0, 0.50)
            )

            final_acceleration = np.random.uniform(
                20.00,
                32.00
            )

            iddq_168h = (
                iddq_96h
                + final_acceleration
                + np.random.normal(0.0, 0.80)
            )

        # ----------------------------------------------------
        # Moderate warning failure
        # ----------------------------------------------------

        elif failure_profile == "moderate_warning":

            early_drift = np.random.uniform(
                0.90,
                2.20
            )

            iddq_24h = (
                iddq_0h
                + early_drift
                + np.random.normal(0.0, 0.25)
            )

            mid_acceleration = np.random.uniform(
                6.00,
                13.00
            )

            iddq_96h = (
                iddq_24h
                + mid_acceleration
                + np.random.normal(0.0, 0.60)
            )

            final_acceleration = np.random.uniform(
                18.00,
                35.00
            )

            iddq_168h = (
                iddq_96h
                + final_acceleration
                + np.random.normal(0.0, 0.90)
            )

        # ----------------------------------------------------
        # Late acceleration failure
        # ----------------------------------------------------

        else:

            early_drift = np.random.uniform(
                0.40,
                1.50
            )

            iddq_24h = (
                iddq_0h
                + early_drift
                + np.random.normal(0.0, 0.22)
            )

            mid_acceleration = np.random.uniform(
                3.00,
                8.00
            )

            iddq_96h = (
                iddq_24h
                + mid_acceleration
                + np.random.normal(0.0, 0.55)
            )

            final_acceleration = np.random.uniform(
                25.00,
                40.00
            )

            iddq_168h = (
                iddq_96h
                + final_acceleration
                + np.random.normal(0.0, 1.00)
            )

        # ----------------------------------------------------
        # Guarantee actual specification violation.
        #
        # This is what makes Absolute_Failure a genuine
        # eventual specification failure.
        # ----------------------------------------------------

        if iddq_168h <= ABSOLUTE_LIMIT_UA:

            iddq_168h = np.random.uniform(
                50.5,
                65.0
            )

    # ========================================================
    # SUDDEN ANOMALY
    # ========================================================

    elif behavior == "Sudden_Anomaly":

        # ----------------------------------------------------
        # Early measurements intentionally resemble Normal.
        #
        # The later anomaly is not fully predictable from
        # 0h + 24h.
        # ----------------------------------------------------

        early_drift = np.random.uniform(
            0.30,
            1.60
        )

        iddq_24h = (
            iddq_0h
            + early_drift
            + np.random.normal(0.0, 0.22)
        )

        normal_late_drift = np.random.uniform(
            0.40,
            2.50
        )

        iddq_96h = (
            iddq_24h
            + normal_late_drift
            + np.random.normal(0.0, 0.35)
        )

        sudden_jump = np.random.uniform(
            12.00,
            28.00
        )

        iddq_168h = (
            iddq_96h
            + sudden_jump
            + np.random.normal(0.0, 0.90)
        )

    else:

        raise ValueError(
            f"Unknown behavior: {behavior}"
        )

    # --------------------------------------------------------
    # Physical sanity
    # --------------------------------------------------------

    iddq_24h = max(
        0.1,
        iddq_24h
    )

    iddq_96h = max(
        0.1,
        iddq_96h
    )

    iddq_168h = max(
        0.1,
        iddq_168h
    )

    return (
        rounded(iddq_0h),
        rounded(iddq_24h),
        rounded(iddq_96h),
        rounded(iddq_168h),
    )


# ============================================================
# LEAKAGE GENERATION
# ============================================================

def generate_leakage(iddq_values):
    """
    Generate leakage values correlated with IDDQ.

    Leakage is approximately related to IDDQ but contains
    independent measurement/process noise.

    It is intentionally NOT exactly IDDQ * 0.1.
    """

    leakage_values = []

    for iddq in iddq_values:

        base_leakage = iddq * 0.10

        noise = np.random.normal(
            0.0,
            0.025
        )

        leakage = max(
            0.05,
            base_leakage + noise
        )

        leakage_values.append(
            rounded(leakage)
        )

    return leakage_values


# ============================================================
# COMPONENT GENERATION
# ============================================================

def generate_component(component_id, batch_number):

    component_type = random.choice(
        COMPONENT_TYPES
    )

    temperature = rounded(
        np.random.uniform(
            25.0,
            35.0
        ),
        2
    )

    voltage = rounded(
        np.random.uniform(
            1.00,
            1.30
        ),
        2
    )

    behavior = generate_behavior()

    # IMPORTANT:
    # The behavior is NOT passed into the 0h baseline generator.
    base = generate_base_iddq(
        temperature,
        voltage
    )

    (
        iddq_0h,
        iddq_24h,
        iddq_96h,
        iddq_168h,
    ) = generate_trajectory(
        base,
        behavior
    )

    (
        leakage_0h,
        leakage_24h,
        leakage_96h,
        leakage_168h,
    ) = generate_leakage(
        [
            iddq_0h,
            iddq_24h,
            iddq_96h,
            iddq_168h,
        ]
    )

    return {
        "component_id": f"C{component_id}",
        "lot_id": f"L{batch_number}",
        "component_type": component_type,

        "temperature_C": temperature,
        "voltage_V": voltage,

        "iddq_0h_uA": iddq_0h,
        "iddq_24h_uA": iddq_24h,
        "iddq_96h_uA": iddq_96h,
        "iddq_168h_uA": iddq_168h,

        "leakage_0h_uA": leakage_0h,
        "leakage_24h_uA": leakage_24h,
        "leakage_96h_uA": leakage_96h,
        "leakage_168h_uA": leakage_168h,

        "ground_truth": behavior,

        "absolute_limit_uA": ABSOLUTE_LIMIT_UA,
    }


# ============================================================
# VALIDATE GENERATED DATA
# ============================================================

def validate_dataset(df):

    expected_columns = [
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

    print()
    print("=" * 72)
    print("DATASET VALIDATION")
    print("=" * 72)

    # --------------------------------------------------------
    # Schema
    # --------------------------------------------------------

    schema_ok = (
        list(df.columns)
        == expected_columns
    )

    print(
        f"Column schema           : "
        f"{'PASS' if schema_ok else 'FAIL'}"
    )

    if not schema_ok:
        raise ValueError(
            "Column schema mismatch."
        )

    # --------------------------------------------------------
    # Row count
    # --------------------------------------------------------

    expected_rows = (
        NUM_BATCHES
        * ROWS_PER_BATCH
    )

    print(
        f"Total rows              : "
        f"{len(df):,}"
    )

    if len(df) != expected_rows:
        raise ValueError(
            "Incorrect total row count."
        )

    print(
        "Total row count         : PASS"
    )

    # --------------------------------------------------------
    # Duplicate IDs
    # --------------------------------------------------------

    duplicate_ids = (
        df["component_id"]
        .duplicated()
        .sum()
    )

    print(
        f"Duplicate component IDs : "
        f"{duplicate_ids}"
    )

    if duplicate_ids != 0:
        raise ValueError(
            "Duplicate component IDs detected."
        )

    print(
        "Component ID check      : PASS"
    )

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    missing = (
        df.isna()
        .sum()
        .sum()
    )

    print(
        f"Missing values          : "
        f"{missing}"
    )

    if missing != 0:
        raise ValueError(
            "Missing values detected."
        )

    print(
        "Missing-value check     : PASS"
    )

    # --------------------------------------------------------
    # Batch size
    # --------------------------------------------------------

    batch_counts = (
        df["lot_id"]
        .value_counts()
        .sort_index()
    )

    print()
    print("Batch sizes:")
    print(
        batch_counts.to_string()
    )

    if not all(
        count == ROWS_PER_BATCH
        for count in batch_counts
    ):
        raise ValueError(
            "Incorrect batch size."
        )

    print(
        "Batch-size check        : PASS"
    )

    # --------------------------------------------------------
    # Ground truth
    # --------------------------------------------------------

    invalid_ground_truth = (
        set(df["ground_truth"])
        - set(BEHAVIORS)
    )

    if invalid_ground_truth:
        raise ValueError(
            f"Invalid ground-truth classes: "
            f"{invalid_ground_truth}"
        )

    print(
        "Ground-truth check      : PASS"
    )

    # --------------------------------------------------------
    # Component types
    # --------------------------------------------------------

    invalid_types = (
        set(df["component_type"])
        - set(COMPONENT_TYPES)
    )

    if invalid_types:
        raise ValueError(
            f"Invalid component types: "
            f"{invalid_types}"
        )

    print(
        "Component-type check    : PASS"
    )

    # --------------------------------------------------------
    # Specification
    # --------------------------------------------------------

    if not np.allclose(
        df["absolute_limit_uA"],
        ABSOLUTE_LIMIT_UA
    ):
        raise ValueError(
            "Invalid absolute specification limit."
        )

    print(
        "Specification check     : PASS"
    )

    # --------------------------------------------------------
    # Numeric sanity
    # --------------------------------------------------------

    measurement_columns = [
        "iddq_0h_uA",
        "iddq_24h_uA",
        "iddq_96h_uA",
        "iddq_168h_uA",
        "leakage_0h_uA",
        "leakage_24h_uA",
        "leakage_96h_uA",
        "leakage_168h_uA",
    ]

    negative_count = (
        (
            df[measurement_columns]
            < 0
        )
        .sum()
        .sum()
    )

    print(
        f"Negative measurements   : "
        f"{negative_count}"
    )

    if negative_count != 0:
        raise ValueError(
            "Negative measurements detected."
        )

    print(
        "Measurement-range check : PASS"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 72)
    print("SIH COMPONENT BURN-IN DATASET GENERATOR")
    print("=" * 72)

    print()
    print("Configuration")
    print("-" * 72)

    print(
        f"Batches              : "
        f"{NUM_BATCHES}"
    )

    print(
        f"Rows per batch       : "
        f"{ROWS_PER_BATCH}"
    )

    print(
        f"Total components     : "
        f"{NUM_BATCHES * ROWS_PER_BATCH}"
    )

    print(
        f"Random seed          : "
        f"{RANDOM_SEED}"
    )

    print(
        f"Absolute limit       : "
        f"{ABSOLUTE_LIMIT_UA} µA"
    )

    print(
        f"Output directory     : "
        f"{os.path.abspath(OUTPUT_DIR)}"
    )

    print()
    print("Synthetic population")
    print("-" * 72)

    for behavior, probability in (
        BEHAVIOR_PROBABILITIES.items()
    ):
        print(
            f"{behavior:<20} "
            f"{probability * 100:>6.1f}%"
        )

    component_counter = 1

    all_data = []

    # ========================================================
    # GENERATE BATCHES
    # ========================================================

    for batch_number in range(
        1,
        NUM_BATCHES + 1
    ):

        batch_data = []

        for _ in range(
            ROWS_PER_BATCH
        ):

            row = generate_component(
                component_counter,
                batch_number
            )

            batch_data.append(row)
            all_data.append(row)

            component_counter += 1

        df_batch = pd.DataFrame(
            batch_data
        )

        file_path = os.path.join(
            OUTPUT_DIR,
            f"batch_{batch_number}.csv"
        )

        df_batch.to_csv(
            file_path,
            index=False
        )

        print()
        print(
            f"Generated batch_{batch_number}.csv "
            f"→ {len(df_batch):,} components"
        )

        print(
            df_batch[
                "ground_truth"
            ]
            .value_counts()
            .sort_index()
            .to_string()
        )

    # ========================================================
    # COMBINE
    # ========================================================

    combined_df = pd.DataFrame(
        all_data
    )

    validate_dataset(
        combined_df
    )

    # ========================================================
    # EARLY SIGNAL ANALYSIS
    # ========================================================

    print()
    print("=" * 72)
    print("EARLY-SIGNAL SUMMARY")
    print("=" * 72)

    combined_df["delta_0_24_uA"] = (
        combined_df["iddq_24h_uA"]
        - combined_df["iddq_0h_uA"]
    )

    combined_df["delta_24_96_uA"] = (
        combined_df["iddq_96h_uA"]
        - combined_df["iddq_24h_uA"]
    )

    combined_df["delta_96_168_uA"] = (
        combined_df["iddq_168h_uA"]
        - combined_df["iddq_96h_uA"]
    )

    summary = (
        combined_df
        .groupby("ground_truth")[
            [
                "iddq_0h_uA",
                "iddq_24h_uA",
                "delta_0_24_uA",
                "delta_24_96_uA",
                "delta_96_168_uA",
                "iddq_168h_uA",
            ]
        ]
        .mean()
        .round(3)
    )

    print()
    print(
        summary.to_string()
    )

    # ========================================================
    # 168h SPECIFICATION
    # ========================================================

    combined_df[
        "actual_168h_violation"
    ] = (
        combined_df["iddq_168h_uA"]
        > combined_df["absolute_limit_uA"]
    )

    actual_violations = int(
        combined_df[
            "actual_168h_violation"
        ].sum()
    )

    total_components = len(
        combined_df
    )

    actual_nonviolations = (
        total_components
        - actual_violations
    )

    print()
    print("=" * 72)
    print("168h SPECIFICATION SUMMARY")
    print("=" * 72)

    print(
        f"Actual 168h violations    : "
        f"{actual_violations:,} "
        f"({actual_violations / total_components * 100:.2f}%)"
    )

    print(
        f"Actual 168h nonviolations : "
        f"{actual_nonviolations:,} "
        f"({actual_nonviolations / total_components * 100:.2f}%)"
    )

    # ========================================================
    # VIOLATIONS BY GROUND TRUTH
    # ========================================================

    print()
    print(
        "168h violations by behavior:"
    )

    violation_by_behavior = (
        combined_df
        .groupby("ground_truth")[
            "actual_168h_violation"
        ]
        .agg(
            total="count",
            violations="sum"
        )
    )

    violation_by_behavior[
        "violation_rate_pct"
    ] = (
        violation_by_behavior[
            "violations"
        ]
        / violation_by_behavior["total"]
        * 100
    )

    print(
        violation_by_behavior
        .round(2)
        .to_string()
    )

    # ========================================================
    # FINAL CLASS DISTRIBUTION
    # ========================================================

    print()
    print("=" * 72)
    print("FINAL GROUND-TRUTH DISTRIBUTION")
    print("=" * 72)

    class_counts = (
        combined_df[
            "ground_truth"
        ]
        .value_counts()
        .sort_index()
    )

    for behavior, count in (
        class_counts.items()
    ):

        percentage = (
            count
            / total_components
            * 100
        )

        print(
            f"{behavior:<20} "
            f"{count:>5,} "
            f"({percentage:>6.2f}%)"
        )

    # ========================================================
    # SAVE COMBINED DATASET
    # ========================================================

    expected_columns = [
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

    combined_path = os.path.join(
        OUTPUT_DIR,
        "all_batches_combined.csv"
    )

    combined_df[
        expected_columns
    ].to_csv(
        combined_path,
        index=False
    )

    print()
    print(
        f"Combined dataset saved : "
        f"{combined_path}"
    )

    # ========================================================
    # FINAL
    # ========================================================

    print()
    print("=" * 72)
    print("DATASET GENERATION COMPLETED")
    print("=" * 72)

    print()
    print("Generated:")
    print("  batch_1.csv → 2,000")
    print("  batch_2.csv → 2,000")
    print("  batch_3.csv → 2,000")
    print("  batch_4.csv → 2,000")
    print("  batch_5.csv → 2,000")
    print("  ----------------------")
    print("  Total       → 10,000")

    print()
    print("Information boundary:")
    print()
    print("  Module A → 0h only")
    print("  Module B → 0h + 24h")
    print("  Module B → predicts 168h")
    print("  Module C → Module A + Module B + specification")
    print()
    print("  96h / 168h → offline target/evaluation")
    print("  ground_truth → offline evaluation")
    print()
    print("=" * 72)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()