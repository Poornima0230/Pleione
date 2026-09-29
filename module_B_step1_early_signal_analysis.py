from pathlib import Path
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(r"C:\Users\peris\Desktop\SIH2k26")

DATA_DIR = BASE_DIR / "data"

BATCH_FILES = [
    DATA_DIR / "batch_1.csv",
    DATA_DIR / "batch_2.csv",
    DATA_DIR / "batch_3.csv",
    DATA_DIR / "batch_4.csv",
    DATA_DIR / "batch_5.csv",
]

OUTPUT_DIR = DATA_DIR / "module_B"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "step1_early_signal_analysis.csv"


# ============================================================
# REQUIRED COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "component_id",
    "lot_id",
    "component_type",
    "temperature_C",
    "voltage_V",
    "iddq_0h_uA",
    "iddq_24h_uA",
    "iddq_168h_uA",
    "leakage_0h_uA",
    "leakage_24h_uA",
    "absolute_limit_uA",
]


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 80)
print("STEP 1 - EARLY SIGNAL ANALYSIS")
print("=" * 80)

frames = []

for batch_number, file_path in enumerate(BATCH_FILES, start=1):

    print(f"\nLoading Batch {batch_number}:")
    print(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"Batch file not found:\n{file_path}"
        )

    df = pd.read_csv(file_path)

    print(f"Rows: {len(df)}")

    if len(df) != 2000:
        raise ValueError(
            f"Batch {batch_number} must contain exactly 2,000 rows."
        )

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Batch {batch_number} is missing columns: {missing}"
        )

    df["batch_number"] = batch_number

    frames.append(df)


raw = pd.concat(
    frames,
    ignore_index=True
)

print("\n" + "-" * 80)
print(f"Total components: {len(raw):,}")
print("-" * 80)


# ============================================================
# DERIVE EARLY FEATURES
# ============================================================

raw["delta_0_24_uA"] = (
    raw["iddq_24h_uA"]
    - raw["iddq_0h_uA"]
)

raw["leakage_delta_0_24_uA"] = (
    raw["leakage_24h_uA"]
    - raw["leakage_0h_uA"]
)


# ============================================================
# EVALUATION-ONLY FUTURE LABEL
# ============================================================
#
# IMPORTANT:
#
# This label is created ONLY for analysis.
#
# It is NOT used as a model input.
#
# We are asking:
#
# "Could the early measurements distinguish components
# that eventually exceed the 168h specification?"
#
# ============================================================

raw["actual_168h_violation"] = (
    raw["iddq_168h_uA"]
    > raw["absolute_limit_uA"]
)


print("\nActual 168h specification status:")
print(
    raw["actual_168h_violation"]
    .value_counts()
    .rename(
        {
            False: "No violation",
            True: "Violation",
        }
    )
)


# ============================================================
# BATCH 5 ONLY
# ============================================================
#
# Batch 5 is our independent unseen test set.
#
# ============================================================

test = raw[
    raw["batch_number"] == 5
].copy()

print("\n" + "=" * 80)
print("BATCH 5 ANALYSIS")
print("=" * 80)

print(f"Batch 5 components: {len(test):,}")

violators = test[
    test["actual_168h_violation"]
].copy()

non_violators = test[
    ~test["actual_168h_violation"]
].copy()


print(
    f"Actual 168h violators     : {len(violators):,}"
)

print(
    f"Actual 168h non-violators : {len(non_violators):,}"
)


# ============================================================
# FEATURE COMPARISON
# ============================================================

FEATURES = [
    "iddq_0h_uA",
    "iddq_24h_uA",
    "delta_0_24_uA",
    "leakage_0h_uA",
    "leakage_24h_uA",
    "leakage_delta_0_24_uA",
    "temperature_C",
    "voltage_V",
]


print("\n" + "=" * 80)
print("EARLY FEATURE COMPARISON")
print("=" * 80)

results = []


for feature in FEATURES:

    violation_values = violators[feature].astype(float)
    non_violation_values = non_violators[feature].astype(float)

    violation_mean = violation_values.mean()
    non_violation_mean = non_violation_values.mean()

    violation_median = violation_values.median()
    non_violation_median = non_violation_values.median()

    violation_std = violation_values.std()
    non_violation_std = non_violation_values.std()

    # Difference in means
    mean_difference = (
        violation_mean
        - non_violation_mean
    )

    # Pooled standard deviation
    n1 = len(violation_values)
    n2 = len(non_violation_values)

    s1 = violation_values.std()
    s2 = non_violation_values.std()

    pooled_std = np.sqrt(
        (
            ((n1 - 1) * s1 ** 2)
            +
            ((n2 - 1) * s2 ** 2)
        )
        /
        (n1 + n2 - 2)
    )

    if pooled_std > 0:
        standardized_difference = (
            mean_difference / pooled_std
        )
    else:
        standardized_difference = 0.0

    result = {
        "feature": feature,

        "violator_mean": violation_mean,
        "non_violator_mean": non_violation_mean,

        "violator_median": violation_median,
        "non_violator_median": non_violation_median,

        "violator_std": violation_std,
        "non_violator_std": non_violation_std,

        "mean_difference": mean_difference,

        "standardized_difference": standardized_difference,
    }

    results.append(result)

    print("\n" + "-" * 80)
    print(feature)
    print("-" * 80)

    print(
        f"Violators mean       : "
        f"{violation_mean:.4f}"
    )

    print(
        f"Non-violators mean   : "
        f"{non_violation_mean:.4f}"
    )

    print(
        f"Violators median     : "
        f"{violation_median:.4f}"
    )

    print(
        f"Non-violators median : "
        f"{non_violation_median:.4f}"
    )

    print(
        f"Mean difference      : "
        f"{mean_difference:.4f}"
    )

    print(
        f"Standardized diff.   : "
        f"{standardized_difference:.4f}"
    )


# ============================================================
# SAVE FEATURE ANALYSIS
# ============================================================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    "standardized_difference",
    key=lambda x: x.abs(),
    ascending=False,
)

results_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n" + "=" * 80)
print("FEATURE SEPARATION SUMMARY")
print("=" * 80)

print(
    results_df[
        [
            "feature",
            "violator_mean",
            "non_violator_mean",
            "mean_difference",
            "standardized_difference",
        ]
    ].to_string(index=False)
)


# ============================================================
# GROUND-TRUTH BREAKDOWN
# ============================================================
#
# This is evaluation only.
#
# It helps us understand what the future failure groups
# actually look like using early measurements.
#
# ============================================================

print("\n" + "=" * 80)
print("BATCH 5 EARLY FEATURES BY GROUND TRUTH")
print("=" * 80)

ground_truth_features = [
    "iddq_0h_uA",
    "iddq_24h_uA",
    "delta_0_24_uA",
    "leakage_0h_uA",
    "leakage_24h_uA",
]


ground_truth_summary = (
    test
    .groupby("ground_truth")[ground_truth_features]
    .agg(["mean", "median"])
)

print(
    ground_truth_summary.to_string()
)


# ============================================================
# DELTA DISTRIBUTION
# ============================================================

print("\n" + "=" * 80)
print("0h → 24h IDDQ CHANGE")
print("=" * 80)

delta_summary = (
    test
    .groupby("ground_truth")["delta_0_24_uA"]
    .agg(
        [
            "count",
            "mean",
            "median",
            "std",
            "min",
            "max",
        ]
    )
)

print(
    delta_summary.to_string()
)


# ============================================================
# SIMPLE EARLY-SIGNAL CHECK
# ============================================================
#
# We calculate the percentage of future violators whose
# early delta is above different thresholds.
#
# This is NOT the final model.
#
# It is only diagnostic.
#
# ============================================================

print("\n" + "=" * 80)
print("EARLY DELTA THRESHOLD CHECK")
print("=" * 80)

thresholds = [
    0.0,
    0.5,
    1.0,
    1.5,
    2.0,
    3.0,
    5.0,
]


threshold_results = []

for threshold in thresholds:

    violator_detection_rate = (
        (
            violators["delta_0_24_uA"]
            >= threshold
        ).mean()
        if len(violators) > 0
        else 0
    )

    false_alarm_rate = (
        (
            non_violators["delta_0_24_uA"]
            >= threshold
        ).mean()
        if len(non_violators) > 0
        else 0
    )

    threshold_results.append(
        {
            "delta_threshold": threshold,
            "violator_detection_rate":
                violator_detection_rate,
            "false_alarm_rate":
                false_alarm_rate,
        }
    )

    print(
        f"\nThreshold >= {threshold:.1f} µA"
    )

    print(
        f"Future violators detected : "
        f"{violator_detection_rate * 100:.2f}%"
    )

    print(
        f"Non-violators flagged     : "
        f"{false_alarm_rate * 100:.2f}%"
    )


# ============================================================
# SAVE EVERYTHING
# ============================================================

threshold_df = pd.DataFrame(
    threshold_results
)

threshold_output = (
    OUTPUT_DIR
    / "step1_delta_threshold_analysis.csv"
)

threshold_df.to_csv(
    threshold_output,
    index=False
)


# ============================================================
# FINAL MESSAGE
# ============================================================

print("\n" + "=" * 80)
print("STEP 1 COMPLETED")
print("=" * 80)

print(
    f"\nFeature analysis saved to:\n"
    f"{OUTPUT_FILE}"
)

print(
    f"\nThreshold analysis saved to:\n"
    f"{threshold_output}"
)

print(
    "\nIMPORTANT:"
)

print(
    "This analysis does NOT modify the dataset."
)

print(
    "This analysis does NOT train a new model."
)

print(
    "It only tells us whether 0h + 24h "
    "contains useful early warning information."
)

print("\nNext step: send me the complete terminal output.")