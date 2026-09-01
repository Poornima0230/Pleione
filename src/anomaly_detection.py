# ============================================================
# SIH 26170
# MODULE A: DYNAMIC ANOMALY DETECTION
# ============================================================
#
# Purpose:
# Detect components whose behavior is unusual compared with
# similar components in their manufacturing lot.
#
# IMPORTANT:
#
# Module A is a RETROSPECTIVE dynamic anomaly detector.
#
# It uses the available burn-in history:
#
#       0h -> 24h -> 96h -> 168h
#
# to determine whether a component behaved abnormally.
#
# Module B will separately predict 168h using early data.
#
# Methods:
#
# 1. Data validation
# 2. Lot-level robust baseline
# 3. Multi-timepoint anomaly detection
# 4. Z-score detection
# 5. IQR detection
# 6. Time-series drift analysis
# 7. Isolation Forest
# 8. Evidence fusion
# 9. Risk/severity classification
# 10. Static vs dynamic screening
# 11. Explainability
# 12. Overall evaluation
# 13. Latent-defect evaluation
# 14. Results export
#
# ============================================================

import os

import pandas as pd
import numpy as np

from sklearn.ensemble import IsolationForest

from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    precision_score,
    recall_score,
    f1_score
)


# ============================================================
# CONFIGURATION
# ============================================================

FILE_PATH = "data/sih_26170_burn_in_synthetic_dataset.csv"

OUTPUT_PATH = "data/module_A_anomaly_results.csv"

# ------------------------------------------------------------
# Measurement columns
# ------------------------------------------------------------

TIMEPOINTS = {
    "0h": "iddq_0h_uA",
    "24h": "iddq_24h_uA",
    "96h": "iddq_96h_uA",
    "168h": "iddq_168h_uA"
}

MEASUREMENT_FEATURES = list(TIMEPOINTS.values())

# ------------------------------------------------------------
# Statistical thresholds
# ------------------------------------------------------------

Z_THRESHOLD = 3.0

IQR_MULTIPLIER = 1.5

DRIFT_Z_THRESHOLD = 3.0

# ------------------------------------------------------------
# Isolation Forest configuration
# ------------------------------------------------------------

ISOLATION_N_ESTIMATORS = 300

# This is a prototype contamination value.
# It should be tuned using validation data later.
ISOLATION_CONTAMINATION = 0.10

RANDOM_STATE = 42


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_divide(numerator, denominator):
    """
    Safe division.
    Returns NaN where denominator is zero.
    """
    denominator = denominator.replace(0, np.nan)

    return numerator / denominator


def robust_zscore(series):
    """
    Robust Z-score based on Median Absolute Deviation (MAD).

    Formula:

        robust_z = 0.6745 * (x - median) / MAD

    This is more resistant to outliers than the traditional
    mean/std Z-score.
    """

    median = series.median()

    mad = np.median(
        np.abs(series - median)
    )

    if mad == 0 or np.isnan(mad):
        return pd.Series(
            np.zeros(len(series)),
            index=series.index
        )

    return (
        0.6745 *
        (series - median) /
        mad
    )


def calculate_severity(row):

    # Absolute specification failure has highest priority.
    if row["absolute_limit_exceeded"]:

        return "CRITICAL"

    evidence = row["anomaly_evidence_count"]

    score = row["anomaly_score"]

    # Strong dynamic evidence
    if evidence >= 3 and score >= 0.75:
        return "CRITICAL"

    if evidence >= 3:
        return "HIGH"

    if evidence == 2 and score >= 0.50:
        return "HIGH"

    if evidence == 2:
        return "MEDIUM"

    if evidence == 1:
        return "LOW"

    return "NORMAL"


def generate_explanation(row):

    reasons = []

    # --------------------------------------------------------
    # Static limit
    # --------------------------------------------------------

    if row["absolute_limit_exceeded"]:

        reasons.append(
            "168h Iddq exceeded the absolute specification limit"
        )

    # --------------------------------------------------------
    # Timepoint statistical anomalies
    # --------------------------------------------------------

    abnormal_timepoints = []

    for timepoint in ["0h", "24h", "96h", "168h"]:

        column = f"z_anomaly_{timepoint}"

        if column in row.index and row[column]:

            abnormal_timepoints.append(timepoint)

    if abnormal_timepoints:

        reasons.append(
            "Lot-level statistical anomaly at "
            + ", ".join(abnormal_timepoints)
        )

    # --------------------------------------------------------
    # IQR anomalies
    # --------------------------------------------------------

    iqr_timepoints = []

    for timepoint in ["0h", "24h", "96h", "168h"]:

        column = f"iqr_anomaly_{timepoint}"

        if column in row.index and row[column]:

            iqr_timepoints.append(timepoint)

    if iqr_timepoints:

        reasons.append(
            "Value outside lot IQR range at "
            + ", ".join(iqr_timepoints)
        )

    # --------------------------------------------------------
    # Drift anomaly
    # --------------------------------------------------------

    if row["drift_anomaly"]:

        reasons.append(
            "Unusually high positive burn-in drift"
        )

    # --------------------------------------------------------
    # Isolation Forest
    # --------------------------------------------------------

    if row["isolation_anomaly"]:

        reasons.append(
            "Isolation Forest detected unusual multi-feature behavior"
        )

    # --------------------------------------------------------
    # Latent-risk explanation
    # --------------------------------------------------------

    if (
        row["dynamic_anomaly"]
        and
        not row["absolute_limit_exceeded"]
    ):

        reasons.append(
            "Dynamic anomaly detected while remaining below "
            "the absolute specification limit"
        )

    # --------------------------------------------------------
    # Normal
    # --------------------------------------------------------

    if not reasons:

        return (
            "No significant abnormal behavior detected "
            "relative to the lot baseline."
        )

    return "; ".join(reasons)


# ============================================================
# STEP 1: LOAD DATASET
# ============================================================

print("=" * 75)
print("SIH 26170")
print("MODULE A: DYNAMIC ANOMALY DETECTION")
print("=" * 75)

print("\nLoading dataset...")

if not os.path.exists(FILE_PATH):

    raise FileNotFoundError(
        f"Dataset not found: {FILE_PATH}"
    )

df = pd.read_csv(FILE_PATH)

print("\nDataset loaded successfully.")

print(
    f"Number of components: {len(df)}"
)

print(
    f"Number of columns: {len(df.columns)}"
)


# ============================================================
# STEP 2: REQUIRED COLUMN VALIDATION
# ============================================================

print("\n" + "=" * 75)
print("COLUMN VALIDATION")
print("=" * 75)

required_columns = [
    "component_id",
    "lot_id",
    "absolute_limit_uA",
    "ground_truth"
] + MEASUREMENT_FEATURES

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    raise ValueError(
        "Missing required columns:\n"
        + "\n".join(missing_columns)
    )

print("\nAll required columns are present.")


# ============================================================
# STEP 3: BASIC DATA VALIDATION
# ============================================================

print("\n" + "=" * 75)
print("DATA VALIDATION")
print("=" * 75)

print("\nMissing measurement values:")

missing_values = (
    df[MEASUREMENT_FEATURES]
    .isnull()
    .sum()
)

print(missing_values)

print("\nDuplicate component IDs:")

duplicate_count = (
    df["component_id"]
    .duplicated()
    .sum()
)

print(duplicate_count)

print("\nNumber of lots:")

print(
    df["lot_id"].nunique()
)

print("\nMeasurement features:")

for timepoint, column in TIMEPOINTS.items():

    print(
        f" - {timepoint}: {column}"
    )


# ============================================================
# STEP 4: DATA CLEANING FOR NUMERIC FEATURES
# ============================================================

for column in MEASUREMENT_FEATURES:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

df["absolute_limit_uA"] = pd.to_numeric(
    df["absolute_limit_uA"],
    errors="coerce"
)

print("\nNumeric validation completed.")


# ============================================================
# STEP 5: LOT-LEVEL ROBUST BASELINES
# ============================================================
#
# Instead of relying only on mean/std, we calculate:
#
# median
# MAD
# Q1
# Q3
# IQR
#
# separately for every lot and every time point.
#
# This makes the baseline less sensitive to extreme values.
# ============================================================

print("\n" + "=" * 75)
print("LOT-LEVEL BASELINE CALCULATION")
print("=" * 75)

for timepoint, column in TIMEPOINTS.items():

    prefix = timepoint.replace("h", "")

    # --------------------------------------------------------
    # Median
    # --------------------------------------------------------

    df[f"lot_median_{timepoint}"] = (
        df.groupby("lot_id")[column]
        .transform("median")
    )

    # --------------------------------------------------------
    # Mean
    # --------------------------------------------------------

    df[f"lot_mean_{timepoint}"] = (
        df.groupby("lot_id")[column]
        .transform("mean")
    )

    # --------------------------------------------------------
    # Standard deviation
    # --------------------------------------------------------

    df[f"lot_std_{timepoint}"] = (
        df.groupby("lot_id")[column]
        .transform("std")
    )

    # --------------------------------------------------------
    # Q1
    # --------------------------------------------------------

    df[f"Q1_{timepoint}"] = (
        df.groupby("lot_id")[column]
        .transform(
            "quantile",
            0.25
        )
    )

    # --------------------------------------------------------
    # Q3
    # --------------------------------------------------------

    df[f"Q3_{timepoint}"] = (
        df.groupby("lot_id")[column]
        .transform(
            "quantile",
            0.75
        )
    )

    # --------------------------------------------------------
    # IQR
    # --------------------------------------------------------

    df[f"IQR_{timepoint}"] = (
        df[f"Q3_{timepoint}"]
        -
        df[f"Q1_{timepoint}"]
    )

    # --------------------------------------------------------
    # IQR limits
    # --------------------------------------------------------

    df[f"iqr_lower_{timepoint}"] = (
        df[f"Q1_{timepoint}"]
        -
        IQR_MULTIPLIER *
        df[f"IQR_{timepoint}"]
    )

    df[f"iqr_upper_{timepoint}"] = (
        df[f"Q3_{timepoint}"]
        +
        IQR_MULTIPLIER *
        df[f"IQR_{timepoint}"]
    )


print("\nRobust lot baselines created.")


# ============================================================
# STEP 6: MULTI-TIMEPOINT Z-SCORE DETECTION
# ============================================================
#
# Detect abnormal values at:
#
# 0h
# 24h
# 96h
# 168h
#
# The component is compared with its own manufacturing lot.
# ============================================================

print("\n" + "=" * 75)
print("MULTI-TIMEPOINT STATISTICAL ANOMALY DETECTION")
print("=" * 75)

for timepoint, column in TIMEPOINTS.items():

    # --------------------------------------------------------
    # Traditional Z-score
    # --------------------------------------------------------

    df[f"zscore_{timepoint}"] = (
        df[column] -
        df[f"lot_mean_{timepoint}"]
    ) / df[
        f"lot_std_{timepoint}"
    ].replace(
        0,
        np.nan
    )

    df[f"zscore_{timepoint}"] = (
        df[f"zscore_{timepoint}"]
        .replace(
            [np.inf, -np.inf],
            np.nan
        )
        .fillna(0)
    )

    # --------------------------------------------------------
    # Robust Z-score
    # --------------------------------------------------------

    robust_scores = (
        df.groupby("lot_id")[column]
        .transform(
            robust_zscore
        )
    )

    df[f"robust_zscore_{timepoint}"] = (
        robust_scores
    )

    # --------------------------------------------------------
    # Traditional Z-score anomaly
    # --------------------------------------------------------

    df[f"z_anomaly_{timepoint}"] = (
        df[f"zscore_{timepoint}"]
        .abs()
        >
        Z_THRESHOLD
    )

    # --------------------------------------------------------
    # Robust Z-score anomaly
    # --------------------------------------------------------

    df[f"robust_z_anomaly_{timepoint}"] = (
        df[f"robust_zscore_{timepoint}"]
        .abs()
        >
        Z_THRESHOLD
    )

    # --------------------------------------------------------
    # IQR anomaly
    # --------------------------------------------------------

    df[f"iqr_anomaly_{timepoint}"] = (
        (
            df[column]
            <
            df[f"iqr_lower_{timepoint}"]
        )
        |
        (
            df[column]
            >
            df[f"iqr_upper_{timepoint}"]
        )
    )

    print(
        f"\n{timepoint}:"
    )

    print(
        "  Z-score anomalies:",
        int(
            df[f"z_anomaly_{timepoint}"]
            .sum()
        )
    )

    print(
        "  Robust Z-score anomalies:",
        int(
            df[f"robust_z_anomaly_{timepoint}"]
            .sum()
        )
    )

    print(
        "  IQR anomalies:",
        int(
            df[f"iqr_anomaly_{timepoint}"]
            .sum()
        )
    )


# ============================================================
# STEP 7: MULTI-TIMEPOINT STATISTICAL EVIDENCE
# ============================================================
#
# For each time point we combine:
#
# Robust Z-score
# OR
# IQR
#
# This gives statistical evidence that a measurement is unusual.
# ============================================================

for timepoint in TIMEPOINTS:

    df[f"statistical_anomaly_{timepoint}"] = (
        df[f"robust_z_anomaly_{timepoint}"]
        |
        df[f"iqr_anomaly_{timepoint}"]
    )


# Count abnormal time points

df["abnormal_timepoint_count"] = sum(
    df[
        f"statistical_anomaly_{timepoint}"
    ].astype(int)
    for timepoint in TIMEPOINTS
)

df["statistical_anomaly"] = (
    df["abnormal_timepoint_count"] >= 1
)

print("\nStatistical anomaly calculation completed.")


# ============================================================
# STEP 8: TIME-SERIES DRIFT FEATURES
# ============================================================

print("\n" + "=" * 75)
print("TIME-SERIES DRIFT ANALYSIS")
print("=" * 75)

# ------------------------------------------------------------
# Interval drift rates
# ------------------------------------------------------------

df["drift_0_24"] = (
    df["iddq_24h_uA"]
    -
    df["iddq_0h_uA"]
) / 24

df["drift_24_96"] = (
    df["iddq_96h_uA"]
    -
    df["iddq_24h_uA"]
) / 72

df["drift_96_168"] = (
    df["iddq_168h_uA"]
    -
    df["iddq_96h_uA"]
) / 72

# ------------------------------------------------------------
# Overall drift rate
# ------------------------------------------------------------

df["overall_drift"] = (
    df["iddq_168h_uA"]
    -
    df["iddq_0h_uA"]
) / 168


# ============================================================
# STEP 9: LOT-LEVEL DRIFT BASELINE
# ============================================================

df["drift_mean"] = (
    df.groupby("lot_id")["overall_drift"]
    .transform("mean")
)

df["drift_median"] = (
    df.groupby("lot_id")["overall_drift"]
    .transform("median")
)

df["drift_std"] = (
    df.groupby("lot_id")["overall_drift"]
    .transform("std")
)


# ============================================================
# STEP 10: DRIFT Z-SCORE
# ============================================================

df["drift_zscore"] = (
    df["overall_drift"]
    -
    df["drift_mean"]
) / df[
    "drift_std"
].replace(
    0,
    np.nan
)

df["drift_zscore"] = (
    df["drift_zscore"]
    .replace(
        [np.inf, -np.inf],
        np.nan
    )
    .fillna(0)
)


# ------------------------------------------------------------
# Robust drift Z-score
# ------------------------------------------------------------

df["robust_drift_zscore"] = (
    df.groupby("lot_id")["overall_drift"]
    .transform(
        robust_zscore
    )
)


# ------------------------------------------------------------
# Positive drift anomaly
#
# We are particularly interested in components whose
# electrical parameter increases abnormally during burn-in.
# ------------------------------------------------------------

df["drift_anomaly"] = (
    df["robust_drift_zscore"]
    >
    DRIFT_Z_THRESHOLD
)


print(
    "\nHigh-drift components:",
    int(
        df["drift_anomaly"].sum()
    )
)


# ============================================================
# STEP 11: ISOLATION FOREST
# ============================================================
#
# Module A has access to the complete burn-in history.
#
# Therefore Isolation Forest can use:
#
# 0h
# 24h
# 96h
# 168h
# interval drift
# overall drift
#
# This is NOT the same as Module B.
#
# Module B will use early measurements to predict 168h.
# ============================================================

print("\n" + "=" * 75)
print("ISOLATION FOREST")
print("=" * 75)


isolation_features = [
    "iddq_0h_uA",
    "iddq_24h_uA",
    "iddq_96h_uA",
    "iddq_168h_uA",
    "drift_0_24",
    "drift_24_96",
    "drift_96_168",
    "overall_drift"
]

X = df[isolation_features].copy()

X = X.replace(
    [np.inf, -np.inf],
    np.nan
)

X = X.fillna(
    X.median()
)


model = IsolationForest(
    n_estimators=ISOLATION_N_ESTIMATORS,
    contamination=ISOLATION_CONTAMINATION,
    random_state=RANDOM_STATE,
    n_jobs=-1
)

model.fit(X)


# ============================================================
# STEP 12: ISOLATION FOREST PREDICTION
# ============================================================

df["isolation_prediction"] = (
    model.predict(X)
)

df["isolation_anomaly"] = (
    df["isolation_prediction"]
    ==
    -1
)

print(
    "Isolation Forest anomalies:",
    int(
        df["isolation_anomaly"].sum()
    )
)


# ============================================================
# STEP 13: ISOLATION FOREST ANOMALY SCORE
# ============================================================

df["raw_anomaly_score"] = (
    -model.decision_function(X)
)

score_min = (
    df["raw_anomaly_score"]
    .min()
)

score_max = (
    df["raw_anomaly_score"]
    .max()
)

if score_max > score_min:

    df["anomaly_score"] = (
        (
            df["raw_anomaly_score"]
            -
            score_min
        )
        /
        (
            score_max
            -
            score_min
        )
    )

else:

    df["anomaly_score"] = 0.0


print("\nAnomaly score generated.")

print(
    df["anomaly_score"]
    .describe()
)


# ============================================================
# STEP 14: STATIC SPECIFICATION CHECK
# ============================================================
#
# Static screening:
#
# Is the measured 168h value above the absolute limit?
#
# This represents traditional pass/fail screening.
# ============================================================

df["absolute_limit_exceeded"] = (
    df["iddq_168h_uA"]
    >
    df["absolute_limit_uA"]
)

print("\n" + "=" * 75)
print("STATIC SPECIFICATION CHECK")
print("=" * 75)

print(
    "\nComponents exceeding absolute limit:",
    int(
        df["absolute_limit_exceeded"].sum()
    )
)


# ============================================================
# STEP 15: DYNAMIC EVIDENCE FUSION
# ============================================================
#
# IMPORTANT:
#
# We don't simply use:
#
#     A OR B OR C
#
# because that can generate excessive false positives.
#
# Instead we count independent evidence sources.
#
# Evidence:
#
# 1. Multi-timepoint statistical anomaly
# 2. Abnormal burn-in drift
# 3. Isolation Forest anomaly
#
# The final decision requires at least TWO independent
# dynamic signals.
#
# However, a component with an extreme statistical anomaly
# at multiple time points can still be flagged.
# ============================================================

df["statistical_evidence"] = (
    df["statistical_anomaly"]
    .astype(int)
)

df["drift_evidence"] = (
    df["drift_anomaly"]
    .astype(int)
)

df["isolation_evidence"] = (
    df["isolation_anomaly"]
    .astype(int)
)


df["anomaly_evidence_count"] = (
    df["statistical_evidence"]
    +
    df["drift_evidence"]
    +
    df["isolation_evidence"]
)


# ------------------------------------------------------------
# Strong repeated statistical anomaly
# ------------------------------------------------------------

df["repeated_statistical_anomaly"] = (
    df["abnormal_timepoint_count"]
    >=
    2
)


# ------------------------------------------------------------
# Dynamic anomaly decision
# ------------------------------------------------------------
#
# Rule 1:
# At least two independent evidence sources.
#
# OR
#
# Rule 2:
# Strong repeated statistical abnormality across
# multiple burn-in checkpoints.
#
# This keeps the system sensitive to evolving defects
# while reducing one-signal false positives.
# ------------------------------------------------------------

df["dynamic_anomaly"] = (
    (
        df["anomaly_evidence_count"]
        >=
        2
    )
    |
    (
        df["repeated_statistical_anomaly"]
        &
        (
            df["anomaly_score"]
            >=
            0.50
        )
    )
)


# ============================================================
# STEP 16: FINAL CLASSIFICATION
# ============================================================

df["combined_anomaly"] = (
    df["dynamic_anomaly"]
)


# ============================================================
# STEP 17: LATENT-RISK FLAG
# ============================================================
#
# A particularly important case:
#
#       dynamic anomaly = TRUE
#
#       BUT
#
#       absolute specification limit = NOT exceeded
#
# This represents the type of subtle abnormal behavior
# the project is designed to identify.
# ============================================================

df["latent_risk_flag"] = (
    df["dynamic_anomaly"]
    &
    ~df["absolute_limit_exceeded"]
)


# ============================================================
# STEP 18: SEVERITY
# ============================================================

df["anomaly_severity"] = df.apply(
    calculate_severity,
    axis=1
)


# ============================================================
# STEP 19: FINAL SCREENING STATUS
# ============================================================
#
# REJECT:
# Absolute specification failure.
#
# REVIEW:
# Dynamic anomaly detected before/without absolute failure.
#
# PASS:
# No significant abnormal behavior.
# ============================================================

def screening_status(row):

    if row["absolute_limit_exceeded"]:

        return "REJECT"

    if row["dynamic_anomaly"]:

        return "REVIEW"

    return "PASS"


df["screening_status"] = df.apply(
    screening_status,
    axis=1
)


# ============================================================
# STEP 20: EXPLAINABILITY
# ============================================================

df["explanation"] = df.apply(
    generate_explanation,
    axis=1
)


# ============================================================
# STEP 21: RISK SCORE
# ============================================================
#
# This is a transparent prototype risk score.
#
# It is NOT another ML model.
#
# It combines:
#
# Isolation Forest score
# statistical evidence
# drift evidence
# repeated abnormality
#
# Score range: 0 - 100
# ============================================================

df["risk_score"] = (
    50 * df["anomaly_score"]
    +
    15 * df["statistical_evidence"]
    +
    20 * df["drift_evidence"]
    +
    15 * df["repeated_statistical_anomaly"].astype(int)
)

df["risk_score"] = (
    df["risk_score"]
    .clip(
        lower=0,
        upper=100
    )
)


# ============================================================
# STEP 22: FINAL RESULTS SUMMARY
# ============================================================

print("\n" + "=" * 75)
print("MODULE A RESULTS")
print("=" * 75)

print("\nIsolation Forest anomalies:")

print(
    df["isolation_anomaly"]
    .value_counts()
)


print("\nStatistical anomalies:")

print(
    df["statistical_anomaly"]
    .value_counts()
)


print("\nDrift anomalies:")

print(
    df["drift_anomaly"]
    .value_counts()
)


print("\nDynamic anomalies:")

print(
    df["dynamic_anomaly"]
    .value_counts()
)


print("\nLatent-risk components:")

print(
    df["latent_risk_flag"]
    .value_counts()
)


print("\nFinal screening status:")

print(
    df["screening_status"]
    .value_counts()
)


print("\nAnomaly severity:")

print(
    df["anomaly_severity"]
    .value_counts()
)


# ============================================================
# STEP 23: GROUND-TRUTH EVALUATION
# ============================================================
#
# IMPORTANT:
#
# ground_truth is NOT an input to the ML model.
#
# It is used only AFTER prediction for evaluation.
#
# This column represents information available to us because
# this is a synthetic development dataset.
#
# A real deployed system will NOT receive ground_truth.
# ============================================================

print("\n" + "=" * 75)
print("MODEL EVALUATION")
print("=" * 75)


abnormal_classes = [
    "High_Stable",
    "Latent_Defect",
    "Absolute_Failure",
    "Sudden_Anomaly"
]


df["actual_anomaly"] = (
    df["ground_truth"]
    .isin(abnormal_classes)
    .astype(int)
)


df["predicted_anomaly"] = (
    df["dynamic_anomaly"]
    .astype(int)
)


# ============================================================
# STEP 24: CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    df["actual_anomaly"],
    df["predicted_anomaly"]
)


print("\nConfusion Matrix:")

print("\n                 Predicted")

print(
    "                 Normal   Anomaly"
)

print(
    "Actual Normal    ",
    cm[0][0],
    "      ",
    cm[0][1]
)

print(
    "Actual Anomaly   ",
    cm[1][0],
    "      ",
    cm[1][1]
)


tn = cm[0][0]

fp = cm[0][1]

fn = cm[1][0]

tp = cm[1][1]


print("\nTrue Negatives :", tn)

print("False Positives:", fp)

print("False Negatives:", fn)

print("True Positives :", tp)


# ============================================================
# STEP 25: PRECISION / RECALL / F1
# ============================================================

precision = precision_score(
    df["actual_anomaly"],
    df["predicted_anomaly"],
    zero_division=0
)

recall = recall_score(
    df["actual_anomaly"],
    df["predicted_anomaly"],
    zero_division=0
)

f1 = f1_score(
    df["actual_anomaly"],
    df["predicted_anomaly"],
    zero_division=0
)


print("\n" + "=" * 75)
print("ANOMALY DETECTION METRICS")
print("=" * 75)

print(
    f"\nPrecision : {precision:.4f}"
)

print(
    f"Recall    : {recall:.4f}"
)

print(
    f"F1 Score  : {f1:.4f}"
)


# ============================================================
# STEP 26: CLASSIFICATION REPORT
# ============================================================

print("\nClassification Report:\n")

print(
    classification_report(
        df["actual_anomaly"],
        df["predicted_anomaly"],
        target_names=[
            "Normal",
            "Anomaly"
        ],
        zero_division=0
    )
)


# ============================================================
# STEP 27: LATENT DEFECT EVALUATION
# ============================================================
#
# This is one of the most important evaluations for the
# SIH problem.
#
# We ask:
#
# How many latent defects were detected?
#
# More importantly:
#
# How many latent defects were below the absolute static
# specification limit but still detected dynamically?
# ============================================================

print("\n" + "=" * 75)
print("LATENT DEFECT EVALUATION")
print("=" * 75)


latent_df = df[
    df["ground_truth"]
    ==
    "Latent_Defect"
].copy()


total_latent = len(latent_df)


detected_latent = (
    latent_df["dynamic_anomaly"]
    ==
    True
).sum()


missed_latent = (
    latent_df["dynamic_anomaly"]
    ==
    False
).sum()


print(
    f"\nTotal latent defects : {total_latent}"
)

print(
    f"Detected             : {detected_latent}"
)

print(
    f"Missed               : {missed_latent}"
)


if total_latent > 0:

    latent_detection_rate = (
        detected_latent /
        total_latent
    ) * 100

else:

    latent_detection_rate = 0


print(
    f"Detection rate       : "
    f"{latent_detection_rate:.2f}%"
)


# ============================================================
# STEP 28: LATENT DEFECTS BELOW STATIC LIMIT
# ============================================================

print("\n" + "=" * 75)
print("LATENT DEFECTS BELOW STATIC LIMIT")
print("=" * 75)


latent_below_limit = latent_df[
    ~latent_df["absolute_limit_exceeded"]
].copy()


total_latent_below_limit = (
    len(latent_below_limit)
)


detected_latent_below_limit = (
    latent_below_limit[
        "dynamic_anomaly"
    ]
    ==
    True
).sum()


missed_latent_below_limit = (
    latent_below_limit[
        "dynamic_anomaly"
    ]
    ==
    False
).sum()


print(
    f"\nLatent defects below limit : "
    f"{total_latent_below_limit}"
)

print(
    f"Detected dynamically       : "
    f"{detected_latent_below_limit}"
)

print(
    f"Missed                     : "
    f"{missed_latent_below_limit}"
)


if total_latent_below_limit > 0:

    early_detection_rate = (
        detected_latent_below_limit /
        total_latent_below_limit
    ) * 100

else:

    early_detection_rate = 0


print(
    f"Dynamic detection rate     : "
    f"{early_detection_rate:.2f}%"
)


# ============================================================
# STEP 29: FALSE NEGATIVE ANALYSIS
# ============================================================
#
# ISRO's problem statement emphasizes that missing a defective
# component is particularly serious.
#
# Therefore we explicitly show which anomalous components
# were missed.
# ============================================================

print("\n" + "=" * 75)
print("FALSE NEGATIVE ANALYSIS")
print("=" * 75)


false_negatives = df[
    (
        df["actual_anomaly"] == 1
    )
    &
    (
        df["predicted_anomaly"] == 0
    )
].copy()


print(
    f"\nFalse negatives: "
    f"{len(false_negatives)}"
)


if len(false_negatives) > 0:

    print(
        "\nMissed anomalous components:"
    )

    print(
        false_negatives[
            [
                "component_id",
                "lot_id",
                "iddq_0h_uA",
                "iddq_24h_uA",
                "iddq_96h_uA",
                "iddq_168h_uA",
                "ground_truth",
                "anomaly_score",
                "anomaly_evidence_count"
            ]
        ]
        .head(20)
        .to_string(
            index=False
        )
    )


# ============================================================
# STEP 30: TOP SUSPICIOUS COMPONENTS
# ============================================================

print("\n" + "=" * 75)
print("TOP SUSPICIOUS COMPONENTS")
print("=" * 75)


top_anomalies = (
    df[
        [
            "component_id",
            "lot_id",
            "iddq_0h_uA",
            "iddq_24h_uA",
            "iddq_96h_uA",
            "iddq_168h_uA",
            "absolute_limit_uA",
            "anomaly_score",
            "risk_score",
            "abnormal_timepoint_count",
            "anomaly_evidence_count",
            "anomaly_severity",
            "latent_risk_flag",
            "screening_status",
            "ground_truth",
            "explanation"
        ]
    ]
    .sort_values(
        "risk_score",
        ascending=False
    )
    .head(20)
)


print(
    top_anomalies.to_string(
        index=False
    )
)


# ============================================================
# STEP 31: LATENT-RISK EXAMPLES
# ============================================================

print("\n" + "=" * 75)
print("TOP LATENT-RISK COMPONENTS")
print("=" * 75)


latent_risk_components = (
    df[
        df["latent_risk_flag"]
    ][
        [
            "component_id",
            "lot_id",
            "iddq_0h_uA",
            "iddq_24h_uA",
            "iddq_96h_uA",
            "iddq_168h_uA",
            "absolute_limit_uA",
            "anomaly_score",
            "risk_score",
            "anomaly_severity",
            "screening_status",
            "ground_truth",
            "explanation"
        ]
    ]
    .sort_values(
        "risk_score",
        ascending=False
    )
    .head(20)
)


if len(latent_risk_components) > 0:

    print(
        latent_risk_components.to_string(
            index=False
        )
    )

else:

    print(
        "\nNo latent-risk components detected."
    )


# ============================================================
# STEP 32: SAVE RESULTS
# ============================================================

print("\n" + "=" * 75)
print("SAVING RESULTS")
print("=" * 75)


df.to_csv(
    OUTPUT_PATH,
    index=False
)


print(
    f"\nResults saved to:\n{OUTPUT_PATH}"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 75)
print("MODULE A COMPLETED")
print("=" * 75)


print(
    "\nTotal components:",
    len(df)
)

print(
    "Dynamic anomalies:",
    int(
        df["dynamic_anomaly"].sum()
    )
)

print(
    "Latent-risk components:",
    int(
        df["latent_risk_flag"].sum()
    )
)

print(
    "Static-limit failures:",
    int(
        df["absolute_limit_exceeded"].sum()
    )
)

print(
    "Final PASS:",
    int(
        (
            df["screening_status"]
            ==
            "PASS"
        ).sum()
    )
)

print(
    "Final REVIEW:",
    int(
        (
            df["screening_status"]
            ==
            "REVIEW"
        ).sum()
    )
)

print(
    "Final REJECT:",
    int(
        (
            df["screening_status"]
            ==
            "REJECT"
        ).sum()
    )
)

print(
    "\nModule A pipeline completed successfully."
)

print(
    "\nRemember:"
)

print(
    "ground_truth is used ONLY for evaluation."
)

print(
    "It is NOT used as a model input."
)

print(
    "Module B will predict 168h using early measurements."
)

print("=" * 75)