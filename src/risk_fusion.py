# ============================================================
# SIH 26170
# MODULE C: RISK FUSION & EARLY SCREENING DECISION ENGINE
#
# PURPOSE
# ------------------------------------------------------------
# Combine:
#
#   MODULE A
#       Current anomaly evidence from 0h + 24h
#
#   MODULE B
#       Predicted future 168h behavior
#
# to produce one final early-risk assessment.
#
#
# IMPORTANT
# ------------------------------------------------------------
# This module is designed for EARLY screening.
#
# Therefore, the final decision DOES NOT use:
#
#   - actual 96h Iddq
#   - actual 168h Iddq
#   - 96h anomaly flags
#   - 168h anomaly flags
#   - ground_truth
#
# Actual 168h values may exist in the source CSV, but they
# are NOT selected into the Module C decision pipeline.
#
#
# MODULE A CONTRIBUTES
# ------------------------------------------------------------
#   0h anomaly indicators
#   24h anomaly indicators
#   0h -> 24h drift
#   absolute specification limit
#
#
# MODULE B CONTRIBUTES
# ------------------------------------------------------------
#   predicted 168h Iddq
#   prediction interval
#   predicted drift
#   dynamic safety slope
#   future drift risk
#   predicted failure
#
#
# OUTPUT
# ------------------------------------------------------------
# final_risk_assessment.csv
#
#
# RISK LEVELS
# ------------------------------------------------------------
# LOW
# WATCH
# MEDIUM
# HIGH
# CRITICAL
#
#
# IMPORTANT ARCHITECTURE RULE
# ------------------------------------------------------------
# Fields common to both modules must NOT be duplicated.
#
# absolute_limit_uA is taken ONLY from Module A.
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

import os

import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

MODULE_A_PATH = (
    "data/module_A_anomaly_results.csv"
)

MODULE_B_PATH = (
    "data/module_B_drift_predictions.csv"
)

OUTPUT_PATH = (
    "data/final_risk_assessment.csv"
)


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("SIH 26170")
print("MODULE C: RISK FUSION & EARLY SCREENING")
print("=" * 70)


# ============================================================
# STEP 1: LOAD MODULE A
# ============================================================

print("\nLoading Module A results...")

module_a = pd.read_csv(
    MODULE_A_PATH
)

print(
    f"Module A components: {len(module_a)}"
)


# ============================================================
# STEP 2: LOAD MODULE B
# ============================================================

print("\nLoading Module B results...")

module_b = pd.read_csv(
    MODULE_B_PATH
)

print(
    f"Module B components: {len(module_b)}"
)


# ============================================================
# STEP 3: VALIDATE COMPONENT IDs
# ============================================================

if "component_id" not in module_a.columns:

    raise ValueError(
        "Module A does not contain component_id."
    )


if "component_id" not in module_b.columns:

    raise ValueError(
        "Module B does not contain component_id."
    )


if module_a["component_id"].duplicated().any():

    raise ValueError(
        "Duplicate component IDs found in Module A."
    )


if module_b["component_id"].duplicated().any():

    raise ValueError(
        "Duplicate component IDs found in Module B."
    )


# ============================================================
# STEP 4: REQUIRED MODULE A COLUMNS
# ============================================================
#
# ONLY EARLY 0h / 24h information is selected.
#
# NOTE:
#
# absolute_limit_uA is deliberately owned by Module A.
#
# ============================================================

module_a_required = [

    "component_id",

    "lot_id",

    "component_type",

    "temperature_C",

    "voltage_V",

    "iddq_0h_uA",

    "iddq_24h_uA",

    "absolute_limit_uA",

    "drift_0_24_uA_per_h",

    "zscore_0h",

    "robust_zscore_0h",

    "z_anomaly_0h",

    "robust_z_anomaly_0h",

    "iqr_anomaly_0h",

    "zscore_24h",

    "robust_zscore_24h",

    "z_anomaly_24h",

    "robust_z_anomaly_24h",

    "iqr_anomaly_24h"
]


missing_a = [

    column

    for column in module_a_required

    if column not in module_a.columns
]


if missing_a:

    raise ValueError(

        "Missing required Module A columns: "
        + str(missing_a)

    )


# ============================================================
# STEP 5: REQUIRED MODULE B COLUMNS
# ============================================================
#
# IMPORTANT:
#
# absolute_limit_uA is NOT included here.
#
# Module A already owns that field.
#
# ============================================================

module_b_required = [

    "component_id",

    "predicted_168h_uA",

    "prediction_lower_uA",

    "prediction_upper_uA",

    "predicted_drift_uA",

    "predicted_drift_rate",

    "safety_slope",

    "drift_slope_excess",

    "early_drift_flag",

    "predicted_limit_exceeded",

    "uncertainty_adjusted_failure",

    "limit_margin_uA",

    "upper_bound_limit_margin_uA",

    "future_drift_risk",

    "module_b_status",

    "module_b_explanation"
]


missing_b = [

    column

    for column in module_b_required

    if column not in module_b.columns
]


if missing_b:

    raise ValueError(

        "Missing required Module B columns: "
        + str(missing_b)

    )


# ============================================================
# STEP 6: SELECT MODULE A
# ============================================================
#
# Deliberately NOT selecting:
#
#   iddq_96h_uA
#   iddq_168h_uA
#   zscore_96h
#   zscore_168h
#   z_anomaly_96h
#   z_anomaly_168h
#   robust_zscore_96h
#   robust_zscore_168h
#   iqr_anomaly_96h
#   iqr_anomaly_168h
#
# ============================================================

a = module_a[
    module_a_required
].copy()


# ============================================================
# STEP 7: SELECT MODULE B
# ============================================================
#
# Module B contains ONLY prediction-related information
# needed by Module C.
#
# ============================================================

b = module_b[
    module_b_required
].copy()


# ============================================================
# STEP 8: CHECK FOR DUPLICATE COLUMN OWNERSHIP
# ============================================================
#
# component_id is expected to overlap.
#
# Other columns should not overlap.
#
# ============================================================

common_columns = (

    set(a.columns)
    &
    set(b.columns)

)


unexpected_common_columns = (

    common_columns
    -
    {"component_id"}

)


if unexpected_common_columns:

    raise ValueError(

        "Unexpected duplicate columns between "
        "Module A and Module B: "
        + str(
            sorted(
                unexpected_common_columns
            )
        )

    )


print("\nColumn ownership check: PASS")

print(
    "Common merge key: component_id"
)

print(
    "absolute_limit_uA source: Module A"
)


# ============================================================
# STEP 9: MERGE MODULE A + MODULE B
# ============================================================

print("\nMerging Module A and Module B...")


df = pd.merge(

    a,

    b,

    on="component_id",

    how="inner"

)


print(
    f"Merged components: {len(df)}"
)


# ============================================================
# STEP 10: CHECK MERGE
# ============================================================

if len(df) == 0:

    raise ValueError(
        "No components matched between Module A and Module B."
    )


if len(df) < len(module_a):

    print(
        "\nWARNING:"
    )

    print(
        "Some Module A components were not found in Module B."
    )


# ============================================================
# STEP 11: FINAL COLUMN VALIDATION
# ============================================================

required_final_columns = [

    "component_id",

    "absolute_limit_uA",

    "iddq_0h_uA",

    "iddq_24h_uA",

    "predicted_168h_uA",

    "prediction_upper_uA",

    "predicted_drift_rate",

    "safety_slope"

]


missing_final = [

    column

    for column in required_final_columns

    if column not in df.columns

]


if missing_final:

    raise ValueError(

        "Required columns missing after merge: "
        + str(missing_final)

    )


print(
    "\nFinal column validation: PASS"
)


# ============================================================
# STEP 12: CURRENT ANOMALY SCORE
# ============================================================
#
# ONLY:
#
#   0h anomaly indicators
#   24h anomaly indicators
#
# Maximum evidence = 6
#
# ============================================================

anomaly_columns = [

    "z_anomaly_0h",

    "robust_z_anomaly_0h",

    "iqr_anomaly_0h",

    "z_anomaly_24h",

    "robust_z_anomaly_24h",

    "iqr_anomaly_24h"

]


for column in anomaly_columns:

    df[column] = (

        df[column]
        .astype(bool)

    )


df["anomaly_evidence_count"] = (

    df[
        anomaly_columns
    ]
    .sum(axis=1)

)


df["anomaly_score"] = (

    df["anomaly_evidence_count"]

    /

    len(anomaly_columns)

)


# ============================================================
# STEP 13: CURRENT ANOMALY LEVEL
# ============================================================

def classify_current_anomaly(score):

    if score >= 0.67:

        return "HIGH"

    elif score >= 0.34:

        return "MEDIUM"

    elif score > 0:

        return "LOW"

    else:

        return "NONE"


df["current_anomaly_level"] = (

    df[
        "anomaly_score"
    ]
    .apply(
        classify_current_anomaly
    )

)


# ============================================================
# STEP 14: EARLY 0h -> 24h TREND
# ============================================================

df["early_drift_direction"] = np.where(

    df[
        "drift_0_24_uA_per_h"
    ] > 0,

    "INCREASING",

    np.where(

        df[
            "drift_0_24_uA_per_h"
        ] < 0,

        "DECREASING",

        "STABLE"

    )

)


# ============================================================
# STEP 15: FUTURE DRIFT EVIDENCE
# ============================================================

df["future_drift_abnormal"] = (

    df[
        "early_drift_flag"
    ].astype(bool)

)


# ============================================================
# STEP 16: FUTURE FAILURE EVIDENCE
# ============================================================

df["future_failure_predicted"] = (

    df[
        "predicted_limit_exceeded"
    ].astype(bool)

    |

    df[
        "uncertainty_adjusted_failure"
    ].astype(bool)

)


# ============================================================
# STEP 17: RISK SCORE
# ============================================================
#
# Weighted evidence:
#
# Current anomaly = 30%
# Future drift    = 30%
# Future failure  = 40%
#
# Total = 100
#
# ============================================================

df["current_anomaly_contribution"] = (

    df[
        "anomaly_score"
    ]

    *

    30

)


df["future_drift_contribution"] = np.where(

    df[
        "future_drift_abnormal"
    ],

    30,

    0

)


df["future_failure_contribution"] = np.where(

    df[
        "future_failure_predicted"
    ],

    40,

    0

)


df["risk_score"] = (

    df[
        "current_anomaly_contribution"
    ]

    +

    df[
        "future_drift_contribution"
    ]

    +

    df[
        "future_failure_contribution"
    ]

)


# ============================================================
# STEP 18: DRIFT SEVERITY
# ============================================================

def calculate_drift_severity(row):

    if row[
        "future_failure_predicted"
    ]:

        return "CRITICAL"


    elif row[
        "future_drift_abnormal"
    ]:

        return "HIGH"


    elif (

        row[
            "predicted_drift_rate"
        ]

        >

        row[
            "safety_slope"
        ]

        *

        0.80

    ):

        return "WATCH"


    else:

        return "LOW"


df["drift_severity"] = df.apply(

    calculate_drift_severity,

    axis=1

)


# ============================================================
# STEP 19: FINAL RISK CLASSIFICATION
# ============================================================
#
# Safety override:
#
# Future predicted failure always results in CRITICAL.
#
# ============================================================

def final_risk_classification(row):

    # --------------------------------------------------------
    # CRITICAL
    # --------------------------------------------------------

    if row[
        "future_failure_predicted"
    ]:

        return "CRITICAL"


    # --------------------------------------------------------
    # HIGH
    # --------------------------------------------------------

    if (

        row[
            "future_drift_abnormal"
        ]

        and

        row[
            "current_anomaly_level"
        ]

        ==

        "HIGH"

    ):

        return "HIGH"


    if row[
        "risk_score"
    ] >= 60:

        return "HIGH"


    # --------------------------------------------------------
    # MEDIUM
    # --------------------------------------------------------

    if row[
        "risk_score"
    ] >= 30:

        return "MEDIUM"


    # --------------------------------------------------------
    # WATCH
    # --------------------------------------------------------

    if row[
        "risk_score"
    ] > 0:

        return "WATCH"


    # --------------------------------------------------------
    # LOW
    # --------------------------------------------------------

    return "LOW"


df["final_risk_level"] = df.apply(

    final_risk_classification,

    axis=1

)


# ============================================================
# STEP 20: FINAL DECISION
# ============================================================

def final_decision(row):

    risk = row[
        "final_risk_level"
    ]


    if risk == "CRITICAL":

        return "IMMEDIATE_REVIEW"


    elif risk == "HIGH":

        return "PRIORITY_SCREENING"


    elif risk == "MEDIUM":

        return "ENHANCED_MONITORING"


    elif risk == "WATCH":

        return "MONITOR"


    else:

        return "NORMAL"


df["final_decision"] = df.apply(

    final_decision,

    axis=1

)


# ============================================================
# STEP 21: GENERATE EXPLANATION
# ============================================================

def generate_explanation(row):

    reasons = []


    # --------------------------------------------------------
    # Current anomaly
    # --------------------------------------------------------

    if row[
        "current_anomaly_level"
    ] != "NONE":

        reasons.append(

            f"Current anomaly evidence: "
            f"{row['current_anomaly_level']}"

        )


    # --------------------------------------------------------
    # Early drift
    # --------------------------------------------------------

    if row[
        "future_drift_abnormal"
    ]:

        reasons.append(

            "Predicted future drift exceeds "
            "dynamic safety boundary"

        )


    # --------------------------------------------------------
    # Future failure
    # --------------------------------------------------------

    if row[
        "predicted_limit_exceeded"
    ]:

        reasons.append(

            "Point prediction exceeds "
            "absolute specification limit"

        )


    # --------------------------------------------------------
    # Uncertainty
    # --------------------------------------------------------

    if row[
        "uncertainty_adjusted_failure"
    ]:

        reasons.append(

            "Prediction uncertainty interval "
            "reaches or exceeds absolute limit"

        )


    # --------------------------------------------------------
    # Early increase
    # --------------------------------------------------------

    if row[
        "drift_0_24_uA_per_h"
    ] > 0:

        reasons.append(

            "Iddq increased between 0h and 24h"

        )


    # --------------------------------------------------------
    # Normal
    # --------------------------------------------------------

    if len(reasons) == 0:

        return (

            "No significant early abnormality "
            "or future drift risk detected."

        )


    return "; ".join(
        reasons
    )


df["risk_explanation"] = df.apply(

    generate_explanation,

    axis=1

)


# ============================================================
# STEP 22: RISK PRIORITY
# ============================================================

risk_priority = {

    "CRITICAL": 1,

    "HIGH": 2,

    "MEDIUM": 3,

    "WATCH": 4,

    "LOW": 5

}


df["risk_priority"] = (

    df[
        "final_risk_level"
    ]
    .map(
        risk_priority
    )

)


# ============================================================
# STEP 23: SORT BY RISK
# ============================================================

df = df.sort_values(

    [

        "risk_priority",

        "risk_score",

        "drift_slope_excess"

    ],

    ascending=[

        True,

        False,

        False

    ]

)


# ============================================================
# STEP 24: DISPLAY SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("MODULE C RISK SUMMARY")
print("=" * 70)


print(
    "\nFinal risk distribution:"
)


print(

    df[
        "final_risk_level"
    ].value_counts()

)


print(
    "\nFinal decisions:"
)


print(

    df[
        "final_decision"
    ].value_counts()

)


# ============================================================
# STEP 25: CURRENT ANOMALY SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("CURRENT ANOMALY SUMMARY")
print("=" * 70)


print(

    df[
        "current_anomaly_level"
    ].value_counts()

)


# ============================================================
# STEP 26: FUTURE FAILURE SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("FUTURE FAILURE SUMMARY")
print("=" * 70)


print(

    "Point-predicted failures:",

    df[
        "predicted_limit_exceeded"
    ].sum()

)


print(

    "Uncertainty-adjusted failures:",

    df[
        "uncertainty_adjusted_failure"
    ].sum()

)


print(

    "Future drift risks:",

    df[
        "future_drift_abnormal"
    ].sum()

)


# ============================================================
# STEP 27: TOP PRIORITY COMPONENTS
# ============================================================

print("\n" + "=" * 70)
print("TOP PRIORITY COMPONENTS")
print("=" * 70)


display_columns = [

    "component_id",

    "lot_id",

    "component_type",

    "iddq_0h_uA",

    "iddq_24h_uA",

    "drift_0_24_uA_per_h",

    "anomaly_score",

    "current_anomaly_level",

    "predicted_168h_uA",

    "prediction_lower_uA",

    "prediction_upper_uA",

    "absolute_limit_uA",

    "limit_margin_uA",

    "upper_bound_limit_margin_uA",

    "predicted_drift_rate",

    "safety_slope",

    "drift_slope_excess",

    "future_drift_risk",

    "risk_score",

    "final_risk_level",

    "final_decision",

    "risk_explanation"

]


# ------------------------------------------------------------
# Safety check before display
# ------------------------------------------------------------

missing_display_columns = [

    column

    for column in display_columns

    if column not in df.columns

]


if missing_display_columns:

    raise ValueError(

        "Display columns missing: "
        + str(missing_display_columns)

    )


top_components = (

    df[
        display_columns
    ]

    .head(20)

)


print(

    top_components.to_string(
        index=False
    )

)


# ============================================================
# STEP 28: EARLY-SCREENING DATA AUDIT
# ============================================================
#
# These columns must NOT be part of the Module C decision
# pipeline.
#
# ============================================================

forbidden_early_columns = [

    "iddq_96h_uA",

    "iddq_168h_uA",

    "zscore_96h",

    "zscore_168h",

    "z_anomaly_96h",

    "z_anomaly_168h",

    "robust_zscore_96h",

    "robust_zscore_168h",

    "iqr_anomaly_96h",

    "iqr_anomaly_168h"

]


used_forbidden_columns = [

    column

    for column in forbidden_early_columns

    if column in df.columns

]


print("\n" + "=" * 70)
print("EARLY-SCREENING DATA AUDIT")
print("=" * 70)


if len(used_forbidden_columns) == 0:

    print(
        "\nPASS:"
    )

    print(

        "No 96h/168h measurement or anomaly columns "
        "are present in the Module C decision dataset."

    )

else:

    print(
        "\nWARNING:"
    )

    print(

        "These later-stage columns are present:"
    )


    for column in used_forbidden_columns:

        print(
            " -",
            column
        )


# ============================================================
# STEP 29: DECISION FEATURE AUDIT
# ============================================================
#
# Explicitly document what Module C actually uses.
#
# ============================================================

decision_features = [

    # Module A
    "iddq_0h_uA",
    "iddq_24h_uA",
    "drift_0_24_uA_per_h",

    "z_anomaly_0h",
    "robust_z_anomaly_0h",
    "iqr_anomaly_0h",

    "z_anomaly_24h",
    "robust_z_anomaly_24h",
    "iqr_anomaly_24h",

    "absolute_limit_uA",

    # Module B
    "predicted_168h_uA",
    "prediction_lower_uA",
    "prediction_upper_uA",

    "predicted_drift_rate",
    "safety_slope",
    "drift_slope_excess",

    "early_drift_flag",

    "predicted_limit_exceeded",
    "uncertainty_adjusted_failure"

]


print("\n" + "=" * 70)
print("MODULE C DECISION FEATURES")
print("=" * 70)


for feature in decision_features:

    print(
        " -",
        feature
    )


# ============================================================
# STEP 30: SAVE FINAL RESULTS
# ============================================================

os.makedirs(

    "data",

    exist_ok=True

)


df.to_csv(

    OUTPUT_PATH,

    index=False

)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("MODULE C COMPLETED")
print("=" * 70)


print(

    f"\nComponents assessed:"
    f" {len(df)}"

)


print(

    f"Critical:"
    f" {(df['final_risk_level'] == 'CRITICAL').sum()}"

)


print(

    f"High:"
    f" {(df['final_risk_level'] == 'HIGH').sum()}"

)


print(

    f"Medium:"
    f" {(df['final_risk_level'] == 'MEDIUM').sum()}"

)


print(

    f"Watch:"
    f" {(df['final_risk_level'] == 'WATCH').sum()}"

)


print(

    f"Low:"
    f" {(df['final_risk_level'] == 'LOW').sum()}"

)


print(

    f"\nResults saved to:"
    f"\n{OUTPUT_PATH}"

)


print("\n" + "=" * 70)