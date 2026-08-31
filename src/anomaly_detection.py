# ============================================================
# SIH 26170
# Module A: Dynamic Anomaly Detection
#
# Purpose:
# Detect components that behave unusually compared with
# similar components in their manufacturing lot.
#
# Methods:
# 1. Lot-level statistics
# 2. Z-score detection
# 3. IQR detection
# 4. Isolation Forest
# 5. Combined anomaly decision
# 6. Evaluation using synthetic ground truth
# ============================================================

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

# ------------------------------------------------------------
# STEP 1: LOAD DATASET
# ------------------------------------------------------------

FILE_PATH = "data/sih_26170_burn_in_synthetic_dataset.csv"

df = pd.read_csv(FILE_PATH)

print("=" * 70)
print("MODULE A: DYNAMIC ANOMALY DETECTION")
print("=" * 70)

print("\nDataset loaded successfully.")
print(f"Number of components: {len(df)}")
print(f"Number of columns: {len(df.columns)}")


# ------------------------------------------------------------
# STEP 2: DEFINE MEASUREMENT FEATURES
# ------------------------------------------------------------

measurement_features = [
    "iddq_0h_uA",
    "iddq_24h_uA",
    "iddq_96h_uA",
    "iddq_168h_uA"
]

print("\nMeasurement features:")
for feature in measurement_features:
    print(" -", feature)


# ------------------------------------------------------------
# STEP 3: BASIC DATA VALIDATION
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("DATA VALIDATION")
print("=" * 70)

print("\nMissing values:")

missing_values = df[measurement_features].isnull().sum()

print(missing_values)

print("\nDuplicate component IDs:")
print(df["component_id"].duplicated().sum())

print("\nNumber of lots:")
print(df["lot_id"].nunique())


# ------------------------------------------------------------
# STEP 4: LOT-LEVEL STATISTICS
# ------------------------------------------------------------
#
# We calculate statistics separately for each lot.
#
# This is important because a component should be compared
# with similar components rather than blindly comparing it
# with every component in the entire dataset.
# ------------------------------------------------------------

lot_stats = (
    df.groupby("lot_id")["iddq_24h_uA"]
    .agg(
        lot_mean="mean",
        lot_median="median",
        lot_std="std",
        lot_min="min",
        lot_max="max"
    )
    .reset_index()
)

df = df.merge(lot_stats, on="lot_id", how="left")

print("\nExample lot statistics:")
print(lot_stats.head())


# ------------------------------------------------------------
# STEP 5: Z-SCORE
# ------------------------------------------------------------
#
# Formula:
#
# Z = (component_value - lot_mean) / lot_standard_deviation
#
# A large positive Z-score means the component is much higher
# than the normal behavior of its lot.
# ------------------------------------------------------------

df["zscore_24h"] = (
    df["iddq_24h_uA"] - df["lot_mean"]
) / df["lot_std"].replace(0, np.nan)

df["zscore_24h"] = df["zscore_24h"].fillna(0)

# Threshold used for prototype
Z_THRESHOLD = 3.0

df["zscore_anomaly"] = (
    df["zscore_24h"].abs() > Z_THRESHOLD
)

print("\nZ-score threshold:", Z_THRESHOLD)

print(
    "Z-score anomalies:",
    df["zscore_anomaly"].sum()
)


# ------------------------------------------------------------
# STEP 6: IQR ANOMALY DETECTION
# ------------------------------------------------------------
#
# Calculate Q1, Q3 and IQR separately for every lot.
#
# We use transform() instead of groupby().apply() so that
# the original dataframe structure remains unchanged.
# ------------------------------------------------------------

# First quartile
df["Q1_24h"] = (
    df.groupby("lot_id")["iddq_24h_uA"]
    .transform("quantile", 0.25)
)

# Third quartile
df["Q3_24h"] = (
    df.groupby("lot_id")["iddq_24h_uA"]
    .transform("quantile", 0.75)
)

# Interquartile range
df["IQR_24h"] = (
    df["Q3_24h"] - df["Q1_24h"]
)

# IQR limits
df["iqr_lower"] = (
    df["Q1_24h"] - 1.5 * df["IQR_24h"]
)

df["iqr_upper"] = (
    df["Q3_24h"] + 1.5 * df["IQR_24h"]
)

# IQR anomaly
df["iqr_anomaly"] = (
    (df["iddq_24h_uA"] < df["iqr_lower"])
    |
    (df["iddq_24h_uA"] > df["iqr_upper"])
)

print(
    "IQR anomalies:",
    df["iqr_anomaly"].sum()
)


# ------------------------------------------------------------
# STEP 7: CREATE TIME-SERIES FEATURES
# ------------------------------------------------------------

df["drift_0_24"] = (
    df["iddq_24h_uA"] -
    df["iddq_0h_uA"]
) / 24

df["drift_24_96"] = (
    df["iddq_96h_uA"] -
    df["iddq_24h_uA"]
) / 72

df["drift_96_168"] = (
    df["iddq_168h_uA"] -
    df["iddq_96h_uA"]
) / 72

df["overall_drift"] = (
    df["iddq_168h_uA"] -
    df["iddq_0h_uA"]
) / 168

print("\nDrift features created.")


# ------------------------------------------------------------
# STEP 8: PREPARE FEATURES FOR ISOLATION FOREST
# ------------------------------------------------------------

features = [
    "iddq_0h_uA",
    "iddq_24h_uA",
    "iddq_96h_uA",
    "iddq_168h_uA",
    "drift_0_24",
    "drift_24_96",
    "drift_96_168",
    "overall_drift"
]

X = df[features].copy()

X = X.replace(
    [np.inf, -np.inf],
    np.nan
)

X = X.fillna(
    X.median()
)


# ------------------------------------------------------------
# STEP 9: ISOLATION FOREST
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("ISOLATION FOREST")
print("=" * 70)

model = IsolationForest(
    n_estimators=300,
    contamination=0.10,
    random_state=42,
    n_jobs=-1
)

model.fit(X)


# ------------------------------------------------------------
# STEP 10: ISOLATION FOREST PREDICTIONS
# ------------------------------------------------------------

df["isolation_prediction"] = (
    model.predict(X)
)

df["isolation_anomaly"] = (
    df["isolation_prediction"] == -1
)

print(
    "Isolation Forest anomalies:",
    df["isolation_anomaly"].sum()
)


# ------------------------------------------------------------
# STEP 11: ANOMALY SCORE
# ------------------------------------------------------------

df["raw_anomaly_score"] = (
    -model.decision_function(X)
)

score_min = df["raw_anomaly_score"].min()
score_max = df["raw_anomaly_score"].max()

if score_max > score_min:

    df["anomaly_score"] = (
        (df["raw_anomaly_score"] - score_min)
        /
        (score_max - score_min)
    )

else:

    df["anomaly_score"] = 0.0

print("\nAnomaly score generated.")

print(
    df["anomaly_score"].describe()
)


# ------------------------------------------------------------
# STEP 12: LOT-LEVEL DRIFT ANALYSIS
# ------------------------------------------------------------
#
# We calculate the average drift and standard deviation
# separately for each lot.
#
# transform() preserves the original dataframe.
# ------------------------------------------------------------

df["drift_mean"] = (
    df.groupby("lot_id")["overall_drift"]
    .transform("mean")
)

df["drift_std"] = (
    df.groupby("lot_id")["overall_drift"]
    .transform("std")
)

# Calculate drift Z-score
df["drift_zscore"] = (
    df["overall_drift"] -
    df["drift_mean"]
) / df["drift_std"].replace(0, np.nan)

df["drift_zscore"] = (
    df["drift_zscore"].fillna(0)
)

# Prototype threshold
DRIFT_Z_THRESHOLD = 3.0

df["drift_anomaly"] = (
    df["drift_zscore"] >
    DRIFT_Z_THRESHOLD
)

print(
    "High-drift components:",
    df["drift_anomaly"].sum()
)


# ------------------------------------------------------------
# STEP 13: COMBINED ANOMALY SCORE
# ------------------------------------------------------------
#
# We combine:
#
# Isolation Forest
# Z-score
# IQR
# Drift
#
# This is a prototype decision layer.
# It is NOT a learned ML model.
# ------------------------------------------------------------

df["statistical_anomaly"] = (
    df["zscore_anomaly"]
    |
    df["iqr_anomaly"]
)

df["combined_anomaly"] = (
    df["isolation_anomaly"]
    |
    df["statistical_anomaly"]
    |
    df["drift_anomaly"]
)


# ------------------------------------------------------------
# STEP 14: ANOMALY SEVERITY
# ------------------------------------------------------------

def calculate_severity(row):

    score = row["anomaly_score"]

    if row["combined_anomaly"] and score >= 0.75:
        return "CRITICAL"

    elif row["combined_anomaly"] and score >= 0.50:
        return "HIGH"

    elif row["combined_anomaly"]:
        return "MEDIUM"

    else:
        return "NORMAL"


df["anomaly_severity"] = df.apply(
    calculate_severity,
    axis=1
)


# ------------------------------------------------------------
# STEP 15: FINAL SCREENING STATUS
# ------------------------------------------------------------

def screening_status(row):

    # Absolute specification failure
    if row["iddq_168h_uA"] > row["absolute_limit_uA"]:
        return "REJECT"

    # Dynamic anomaly
    if row["combined_anomaly"]:
        return "REVIEW"

    return "PASS"


df["screening_status"] = df.apply(
    screening_status,
    axis=1
)


# ------------------------------------------------------------
# STEP 16: EXPLANATION
# ------------------------------------------------------------

def generate_explanation(row):

    reasons = []

    if row["iddq_24h_uA"] > row["lot_mean"] + 3 * row["lot_std"]:
        reasons.append(
            "24h Iddq significantly higher than lot baseline"
        )

    if row["iqr_anomaly"]:
        reasons.append(
            "24h Iddq outside lot IQR range"
        )

    if row["drift_anomaly"]:
        reasons.append(
            "Unusually high overall drift"
        )

    if row["isolation_anomaly"]:
        reasons.append(
            "Isolation Forest detected unusual behavior"
        )

    if row["iddq_168h_uA"] > row["absolute_limit_uA"]:
        reasons.append(
            "Absolute specification limit exceeded"
        )

    if len(reasons) == 0:
        return "No significant abnormal behavior detected."

    return "; ".join(reasons)


df["explanation"] = df.apply(
    generate_explanation,
    axis=1
)


# ------------------------------------------------------------
# STEP 17: DISPLAY SUMMARY
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("MODULE A RESULTS")
print("=" * 70)

print("\nIsolation Forest anomalies:")
print(df["isolation_anomaly"].value_counts())

print("\nStatistical anomalies:")
print(df["statistical_anomaly"].value_counts())

print("\nDrift anomalies:")
print(df["drift_anomaly"].value_counts())

print("\nCombined anomalies:")
print(df["combined_anomaly"].value_counts())

print("\nFinal screening status:")
print(df["screening_status"].value_counts())

print("\nAnomaly severity:")
print(df["anomaly_severity"].value_counts())


# ------------------------------------------------------------
# STEP 18: EVALUATION
# ------------------------------------------------------------
#
# Our synthetic dataset contains ground_truth.
#
# IMPORTANT:
# ground_truth is NOT used to train the model.
#
# It is used only AFTER prediction to evaluate the model.
#
# For anomaly evaluation:
#
# Normal = 0
# Everything abnormal = 1
# ------------------------------------------------------------

abnormal_classes = [
    "High_Stable",
    "Latent_Defect",
    "Absolute_Failure",
    "Sudden_Anomaly"
]

df["actual_anomaly"] = (
    df["ground_truth"].isin(abnormal_classes)
).astype(int)

df["predicted_anomaly"] = (
    df["combined_anomaly"]
).astype(int)


# ------------------------------------------------------------
# STEP 19: CONFUSION MATRIX
# ------------------------------------------------------------

cm = confusion_matrix(
    df["actual_anomaly"],
    df["predicted_anomaly"]
)

print("\n" + "=" * 70)
print("CONFUSION MATRIX")
print("=" * 70)

print("\n             Predicted")
print("             Normal  Anomaly")

print(
    "Actual Normal   ",
    cm[0][0],
    "     ",
    cm[0][1]
)

print(
    "Actual Anomaly  ",
    cm[1][0],
    "     ",
    cm[1][1]
)


# ------------------------------------------------------------
# STEP 20: PRECISION / RECALL / F1
# ------------------------------------------------------------

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

print("\n" + "=" * 70)
print("ANOMALY DETECTION METRICS")
print("=" * 70)

print(f"\nPrecision : {precision:.4f}")
print(f"Recall    : {recall:.4f}")
print(f"F1 Score  : {f1:.4f}")


# ------------------------------------------------------------
# STEP 21: FULL CLASSIFICATION REPORT
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# STEP 22: CRITICAL COMPONENTS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("TOP SUSPICIOUS COMPONENTS")
print("=" * 70)

top_anomalies = (
    df[
        [
            "component_id",
            "lot_id",
            "iddq_0h_uA",
            "iddq_24h_uA",
            "iddq_96h_uA",
            "iddq_168h_uA",
            "anomaly_score",
            "anomaly_severity",
            "screening_status",
            "ground_truth",
            "explanation"
        ]
    ]
    .sort_values(
        "anomaly_score",
        ascending=False
    )
    .head(20)
)

print(
    top_anomalies.to_string(index=False)
)


# ------------------------------------------------------------
# STEP 23: SAVE RESULTS
# ------------------------------------------------------------

OUTPUT_PATH = "data/module_A_anomaly_results.csv"

df.to_csv(
    OUTPUT_PATH,
    index=False
)

print("\n" + "=" * 70)
print("MODULE A COMPLETED")
print("=" * 70)

print(
    f"\nResults saved to:\n{OUTPUT_PATH}"
)