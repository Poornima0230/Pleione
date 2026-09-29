
"""
MODULE C
Multi-Evidence Screening Risk Engine

Module C combines:

    Module A
        Current 0h anomaly evidence

    Module B Regression
        Predicted 168h value
        Conformal upper bound

    Module B Classifier
        Probability of future 168h specification violation

    Specification
        Absolute current specification limit

IMPORTANT:
    Actual 96h / 168h values and ground_truth are NEVER used
    to make Module C decisions.

They are used only later by the offline evaluation script.
"""

from pathlib import Path
import json

import pandas as pd
import numpy as np


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"

MODULE_A_PATH = (
    DATA_DIR
    / "module_A"
    / "module_A_batch5_results.csv"
)

MODULE_B_PATH = (
    DATA_DIR
    / "module_B"
    / "module_B_batch5_results.csv"
)

OUTPUT_DIR = (
    DATA_DIR
    / "module_C"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


OUTPUT_PATH = (
    OUTPUT_DIR
    / "module_C_batch5_results.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("MODULE C - MULTI-EVIDENCE RISK ENGINE")
print("=" * 70)

module_a = pd.read_csv(
    MODULE_A_PATH
)

module_b = pd.read_csv(
    MODULE_B_PATH
)


print("\nINPUTS")
print("-" * 70)

print(
    f"Module A rows: {len(module_a)}"
)

print(
    f"Module B rows: {len(module_b)}"
)


# ============================================================
# CHECK DUPLICATES
# ============================================================

if module_a["component_id"].duplicated().any():
    raise ValueError(
        "Duplicate component_id found in Module A."
    )

if module_b["component_id"].duplicated().any():
    raise ValueError(
        "Duplicate component_id found in Module B."
    )


# ============================================================
# SELECT ONLY DECISION COLUMNS
# ============================================================

a_columns = [
    "component_id",
    "module_a_score",
    "module_a_status",
    "peer_source",
    "peer_group_size",
]

b_columns = [
    "component_id",
    "predicted_168h_uA",
    "prediction_lower_uA",
    "prediction_upper_uA",
    "prediction_interval_width_uA",
    "failure_probability",
    "predicted_future_violation",
    "failure_risk",
    "absolute_limit_uA",
]


missing_a = [
    column
    for column in a_columns
    if column not in module_a.columns
]

missing_b = [
    column
    for column in b_columns
    if column not in module_b.columns
]

if missing_a:
    raise ValueError(
        f"Module A missing columns: {missing_a}"
    )

if missing_b:
    raise ValueError(
        f"Module B missing columns: {missing_b}"
    )


a = module_a[a_columns].copy()
b = module_b[b_columns].copy()


# ============================================================
# MERGE
# ============================================================

df = a.merge(
    b,
    on="component_id",
    how="inner",
    validate="one_to_one",
)


if len(df) != len(module_a):
    raise ValueError(
        "Module A and Module B do not contain "
        "the same components."
    )


print(
    f"Merged components: {len(df)}"
)


# ============================================================
# LIMIT
# ============================================================

df["limit_uA"] = (
    df["absolute_limit_uA"]
)


# ============================================================
# EVIDENCE FLAGS
# ============================================================

df["point_prediction_exceeds_limit"] = (
    df["predicted_168h_uA"]
    > df["limit_uA"]
)

df["uncertainty_crosses_limit"] = (
    df["prediction_upper_uA"]
    > df["limit_uA"]
)

df["classifier_high_risk"] = (
    df["failure_probability"]
    >= 0.75
)

df["classifier_medium_or_higher"] = (
    df["failure_probability"]
    >= 0.40
)

df["module_a_watch_or_higher"] = (
    df["module_a_status"]
    .isin(
        [
            "WATCH",
            "ANOMALOUS",
        ]
    )
)

df["module_a_anomalous"] = (
    df["module_a_status"]
    == "ANOMALOUS"
)


# ============================================================
# FINAL DECISION
# ============================================================

def determine_decision(row):

    predicted = row[
        "predicted_168h_uA"
    ]

    upper = row[
        "prediction_upper_uA"
    ]

    limit = row[
        "limit_uA"
    ]

    failure_probability = row[
        "failure_probability"
    ]

    module_a_status = row[
        "module_a_status"
    ]

    # --------------------------------------------------------
    # LEVEL 1
    # Direct projected specification violation
    # --------------------------------------------------------

    if predicted > limit:

        return (
            "REJECT",
            "CRITICAL",
            "Projected 168h value exceeds specification limit."
        )

    # --------------------------------------------------------
    # LEVEL 2
    # High future-risk evidence
    #
    # Classifier probability >= 75%
    #
    # This is REVIEW, NOT automatic rejection.
    # --------------------------------------------------------

    if failure_probability >= 0.75:

        return (
            "REVIEW",
            "HIGH",
            "High early probability of future specification violation."
        )

    # --------------------------------------------------------
    # LEVEL 3
    # Upper prediction crosses limit + current anomaly
    # --------------------------------------------------------

    if (
        upper > limit
        and module_a_status in [
            "WATCH",
            "ANOMALOUS",
        ]
    ):

        return (
            "REVIEW",
            "HIGH",
            "Prediction uncertainty crosses the limit and "
            "current anomaly evidence is present."
        )

    # --------------------------------------------------------
    # LEVEL 4
    # Medium future-risk probability
    # --------------------------------------------------------

    if failure_probability >= 0.40:

        return (
            "REVIEW",
            "MEDIUM",
            "Moderate early probability of future specification violation."
        )

    # --------------------------------------------------------
    # LEVEL 5
    # Prediction interval crosses limit
    # --------------------------------------------------------

    if upper > limit:

        return (
            "REVIEW",
            "MEDIUM",
            "Prediction interval crosses specification limit."
        )

    # --------------------------------------------------------
    # LEVEL 6
    # Current anomaly evidence
    # --------------------------------------------------------

    if module_a_status == "ANOMALOUS":

        return (
            "REVIEW",
            "MEDIUM",
            "Current 0h peer anomaly detected."
        )

    if module_a_status == "WATCH":

        return (
            "PASS",
            "LOW",
            "Current signal is under watch but future risk "
            "evidence remains below review threshold."
        )

    # --------------------------------------------------------
    # LEVEL 7
    # Normal
    # --------------------------------------------------------

    return (
        "PASS",
        "LOW",
        "No strong current or projected risk evidence detected."
    )


decisions = df.apply(
    determine_decision,
    axis=1,
    result_type="expand",
)

decisions.columns = [
    "final_decision",
    "future_risk",
    "decision_reason",
]


df = pd.concat(
    [
        df,
        decisions,
    ],
    axis=1,
)


# ============================================================
# EVIDENCE SUMMARY
# ============================================================

def evidence_level(row):

    evidence = 0

    if row["point_prediction_exceeds_limit"]:
        evidence += 3

    if row["uncertainty_crosses_limit"]:
        evidence += 1

    if row["classifier_high_risk"]:
        evidence += 2

    elif row["classifier_medium_or_higher"]:
        evidence += 1

    if row["module_a_anomalous"]:
        evidence += 2

    elif row["module_a_watch_or_higher"]:
        evidence += 1

    if evidence >= 5:
        return "STRONG"

    if evidence >= 3:
        return "HIGH"

    if evidence >= 2:
        return "MEDIUM"

    return "LOW"


df["evidence_level"] = df.apply(
    evidence_level,
    axis=1,
)


# ============================================================
# PRIMARY MODEL OUTPUT
# ============================================================

# Keep actual future measurements out of the decision columns.
#
# We intentionally do NOT use:
#   ground_truth
#   iddq_96h_uA
#   iddq_168h_uA
#
# for determining final_decision.


# ============================================================
# SAVE
# ============================================================

df.to_csv(
    OUTPUT_PATH,
    index=False,
)


# ============================================================
# SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("FINAL DECISION")
print("=" * 70)

print(
    df["final_decision"]
    .value_counts()
)

print("\n" + "=" * 70)
print("FUTURE RISK")
print("=" * 70)

print(
    df["future_risk"]
    .value_counts()
)

print("\n" + "=" * 70)
print("EVIDENCE LEVEL")
print("=" * 70)

print(
    df["evidence_level"]
    .value_counts()
)

print("\n" + "=" * 70)
print("MODULE A STATUS")
print("=" * 70)

print(
    df["module_a_status"]
    .value_counts()
)

print("\n" + "=" * 70)
print("MODULE B FAILURE RISK")
print("=" * 70)

print(
    df["failure_risk"]
    .value_counts()
)

print("\n" + "=" * 70)
print("POINT PREDICTION > LIMIT")
print("=" * 70)

print(
    df["point_prediction_exceeds_limit"]
    .value_counts()
)

print("\n" + "=" * 70)
print("UPPER BOUND > LIMIT")
print("=" * 70)

print(
    df["uncertainty_crosses_limit"]
    .value_counts()
)

print("\n" + "=" * 70)
print("CLASSIFIER >= 75%")
print("=" * 70)

print(
    df["classifier_high_risk"]
    .value_counts()
)

print("\n" + "=" * 70)
print("CLASSIFIER >= 40%")
print("=" * 70)

print(
    df["classifier_medium_or_higher"]
    .value_counts()
)

print("\n" + "=" * 70)
print("FILES")
print("=" * 70)

print(
    OUTPUT_PATH
)

print("\n" + "=" * 70)
print("MODULE C COMPLETE")
print("=" * 70)

