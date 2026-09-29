import os

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

DATA_DIR = "../data"

BATCH_FILES = [
    os.path.join(DATA_DIR, "batch_1.csv"),
    os.path.join(DATA_DIR, "batch_2.csv"),
    os.path.join(DATA_DIR, "batch_3.csv"),
    os.path.join(DATA_DIR, "batch_4.csv"),
    os.path.join(DATA_DIR, "batch_5.csv"),
]


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 72)
print("STEP 2 FINAL VALIDATION - EARLY SIGNAL ANALYSIS")
print("=" * 72)

batches = []

for batch_number, path in enumerate(BATCH_FILES, start=1):

    print()
    print(f"Loading Batch {batch_number}:")
    print(path)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    df = pd.read_csv(path)

    print(f"Rows: {len(df):,}")

    if len(df) != 2000:
        raise ValueError(
            f"Batch {batch_number} must contain 2,000 rows."
        )

    df["batch_number"] = batch_number

    batches.append(df)


data = pd.concat(
    batches,
    ignore_index=True
)


# ============================================================
# BASIC VALIDATION
# ============================================================

print()
print("-" * 72)
print(f"Total components: {len(data):,}")
print("-" * 72)

if len(data) != 10000:
    raise ValueError(
        "Expected exactly 10,000 components."
    )

duplicate_ids = data[
    "component_id"
].duplicated().sum()

print(
    f"Duplicate component IDs: {duplicate_ids}"
)

if duplicate_ids != 0:
    raise ValueError(
        "Duplicate component IDs detected."
    )

missing_values = data.isna().sum().sum()

print(
    f"Missing values: {missing_values}"
)

if missing_values != 0:
    raise ValueError(
        "Missing values detected."
    )


# ============================================================
# DERIVED FEATURES
# ============================================================

data["delta_0_24_uA"] = (
    data["iddq_24h_uA"]
    - data["iddq_0h_uA"]
)

data["leakage_delta_0_24_uA"] = (
    data["leakage_24h_uA"]
    - data["leakage_0h_uA"]
)

data["actual_168h_violation"] = (
    data["iddq_168h_uA"]
    > data["absolute_limit_uA"]
)


# ============================================================
# BATCH 5 ONLY
# ============================================================

test = data[
    data["batch_number"] == 5
].copy()

print()
print("=" * 72)
print("BATCH 5 ANALYSIS")
print("=" * 72)

print(
    f"Batch 5 components: {len(test):,}"
)

violators = test[
    test["actual_168h_violation"]
]

non_violators = test[
    ~test["actual_168h_violation"]
]

print(
    f"Actual 168h violators     : "
    f"{len(violators):,}"
)

print(
    f"Actual 168h non-violators : "
    f"{len(non_violators):,}"
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


print()
print("=" * 72)
print("EARLY FEATURE COMPARISON")
print("=" * 72)


summary_rows = []


for feature in FEATURES:

    violation_mean = violators[
        feature
    ].mean()

    non_violation_mean = non_violators[
        feature
    ].mean()

    violation_median = violators[
        feature
    ].median()

    non_violation_median = non_violators[
        feature
    ].median()

    violation_std = violators[
        feature
    ].std()

    non_violation_std = non_violators[
        feature
    ].std()

    pooled_std = np.sqrt(
        (
            violation_std ** 2
            + non_violation_std ** 2
        )
        / 2
    )

    if pooled_std == 0:
        standardized_difference = 0.0
    else:
        standardized_difference = (
            violation_mean
            - non_violation_mean
        ) / pooled_std

    mean_difference = (
        violation_mean
        - non_violation_mean
    )

    print()
    print("-" * 72)
    print(feature)
    print("-" * 72)

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

    summary_rows.append(
        {
            "feature": feature,
            "violator_mean": violation_mean,
            "non_violator_mean": non_violation_mean,
            "mean_difference": mean_difference,
            "standardized_difference":
                standardized_difference,
        }
    )


# ============================================================
# FEATURE SEPARATION SUMMARY
# ============================================================

summary = pd.DataFrame(
    summary_rows
)

summary = summary.sort_values(
    "standardized_difference",
    key=lambda x: x.abs(),
    ascending=False
)

print()
print("=" * 72)
print("FEATURE SEPARATION SUMMARY")
print("=" * 72)

print(
    summary.round(4).to_string(
        index=False
    )
)


# ============================================================
# DELTA THRESHOLD ANALYSIS
# ============================================================

print()
print("=" * 72)
print("EARLY DELTA THRESHOLD ANALYSIS")
print("=" * 72)

thresholds = [
    0.0,
    0.5,
    1.0,
    1.5,
    2.0,
    2.5,
    3.0,
]


threshold_rows = []


for threshold in thresholds:

    predicted_positive = (
        test["delta_0_24_uA"]
        >= threshold
    )

    actual_positive = (
        test["actual_168h_violation"]
    )

    tp = int(
        (
            predicted_positive
            & actual_positive
        ).sum()
    )

    fp = int(
        (
            predicted_positive
            & ~actual_positive
        ).sum()
    )

    fn = int(
        (
            ~predicted_positive
            & actual_positive
        ).sum()
    )

    tn = int(
        (
            ~predicted_positive
            & ~actual_positive
        ).sum()
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0.0
    )

    false_positive_rate = (
        fp / (fp + tn)
        if (fp + tn) > 0
        else 0.0
    )

    threshold_rows.append(
        {
            "threshold": threshold,
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "TN": tn,
            "precision": precision,
            "recall": recall,
            "false_positive_rate":
                false_positive_rate,
        }
    )


threshold_df = pd.DataFrame(
    threshold_rows
)

print(
    threshold_df.to_string(
        index=False,
        float_format=lambda x: f"{x:.4f}"
    )
)


# ============================================================
# GROUND-TRUTH DISTRIBUTION IN BATCH 5
# ============================================================

print()
print("=" * 72)
print("BATCH 5 GROUND-TRUTH DISTRIBUTION")
print("=" * 72)

print(
    test[
        "ground_truth"
    ]
    .value_counts()
    .sort_index()
    .to_string()
)


# ============================================================
# GROUND TRUTH VS EARLY DELTA
# ============================================================

print()
print("=" * 72)
print("GROUND TRUTH VS EARLY DELTA")
print("=" * 72)

ground_truth_delta = (
    test
    .groupby("ground_truth")[
        [
            "iddq_0h_uA",
            "iddq_24h_uA",
            "delta_0_24_uA",
            "iddq_168h_uA",
        ]
    ]
    .agg(
        [
            "mean",
            "median",
            "std",
        ]
    )
)

print(
    ground_truth_delta.round(3).to_string()
)


# ============================================================
# SUDDEN ANOMALY CHECK
# ============================================================

print()
print("=" * 72)
print("SUDDEN ANOMALY EARLY-SIGNAL CHECK")
print("=" * 72)

sudden = test[
    test["ground_truth"]
    == "Sudden_Anomaly"
]

normal = test[
    test["ground_truth"]
    == "Normal"
]

print(
    f"Sudden Anomaly count : "
    f"{len(sudden)}"
)

print(
    f"Normal count         : "
    f"{len(normal)}"
)

print()

print(
    "Sudden Anomaly early delta:"
)

print(
    sudden[
        "delta_0_24_uA"
    ].describe().round(3).to_string()
)

print()

print(
    "Normal early delta:"
)

print(
    normal[
        "delta_0_24_uA"
    ].describe().round(3).to_string()
)


# ============================================================
# FINAL INTERPRETATION HELPERS
# ============================================================

largest_effect = summary.iloc[0]

print()
print("=" * 72)
print("VALIDATION INTERPRETATION")
print("=" * 72)

print()
print(
    "Largest early-feature separation:"
)

print(
    f"  {largest_effect['feature']}"
)

print(
    f"  Standardized difference: "
    f"{largest_effect['standardized_difference']:.4f}"
)

print()
print(
    "Dataset is intended to have:"
)

print(
    "  - useful early warning for some future failures"
)

print(
    "  - overlap between healthy and abnormal components"
)

print(
    "  - genuinely difficult Sudden Anomaly cases"
)

print(
    "  - no future measurements used as early inputs"
)

print()
print(
    "NEXT STEP:"
)

print(
    "If the early-signal separation is reasonable, "
    "rebuild Module A using 0h only."
)

print()
print("=" * 72)
print("STEP 2 FINAL VALIDATION COMPLETED")
print("=" * 72)