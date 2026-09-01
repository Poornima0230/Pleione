# ============================================================
# SIH 26170
# MODULE D: EXPLAINABILITY & SCREENING REPORT
#
# PURPOSE
# ------------------------------------------------------------
# Convert Module C numerical risk results into:
#
#   1. Human-readable explanations
#   2. Recommended screening actions
#   3. Priority screening list
#   4. Component-level reports
#
# IMPORTANT
# ------------------------------------------------------------
# Module D does NOT:
#
#   - train another ML model
#   - use actual 96h measurements
#   - use actual 168h measurements
#   - use ground_truth for decisions
#
# It only explains the EARLY-SCREENING decision
# produced by Module C.
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

INPUT_PATH = (
    "data/final_risk_assessment.csv"
)

OUTPUT_PATH = (
    "data/module_D_explanations.csv"
)

PRIORITY_OUTPUT_PATH = (
    "data/priority_screening_list.csv"
)

REPORT_DIRECTORY = (
    "data/component_reports"
)


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("SIH 26170")
print("MODULE D: EXPLAINABILITY & SCREENING REPORT")
print("=" * 70)


# ============================================================
# STEP 1: LOAD MODULE C
# ============================================================

print("\nLoading Module C results...")

if not os.path.exists(INPUT_PATH):

    raise FileNotFoundError(
        f"Module C output not found: {INPUT_PATH}"
    )


df = pd.read_csv(INPUT_PATH)

print(
    f"Module C components: {len(df)}"
)


# ============================================================
# STEP 2: REQUIRED COLUMNS
# ============================================================

required_columns = [

    # Identification
    "component_id",
    "lot_id",
    "component_type",

    # Early measurements
    "iddq_0h_uA",
    "iddq_24h_uA",
    "drift_0_24_uA_per_h",

    # Current anomaly
    "anomaly_score",
    "current_anomaly_level",

    # Future prediction
    "predicted_168h_uA",
    "prediction_lower_uA",
    "prediction_upper_uA",

    # Specification
    "absolute_limit_uA",

    # Future drift
    "predicted_drift_rate",
    "safety_slope",
    "drift_slope_excess",
    "future_drift_risk",

    # Failure indicators
    "predicted_limit_exceeded",
    "uncertainty_adjusted_failure",

    # Final decision
    "risk_score",
    "final_risk_level",
    "final_decision"

]


missing_columns = [

    column

    for column in required_columns

    if column not in df.columns

]


if missing_columns:

    raise ValueError(

        "Missing required Module C columns: "
        + str(missing_columns)

    )


print(
    "Required column validation: PASS"
)


# ============================================================
# STEP 3: DATA TYPE CLEANUP
# ============================================================

boolean_columns = [

    "predicted_limit_exceeded",
    "uncertainty_adjusted_failure"

]


for column in boolean_columns:

    if df[column].dtype != bool:

        df[column] = (

            df[column]
            .astype(str)
            .str.lower()
            .isin(
                [
                    "true",
                    "1",
                    "yes"
                ]
            )

        )


numeric_columns = [

    "iddq_0h_uA",
    "iddq_24h_uA",
    "drift_0_24_uA_per_h",
    "anomaly_score",
    "predicted_168h_uA",
    "prediction_lower_uA",
    "prediction_upper_uA",
    "absolute_limit_uA",
    "predicted_drift_rate",
    "safety_slope",
    "drift_slope_excess",
    "risk_score"

]


for column in numeric_columns:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ============================================================
# STEP 4: CALCULATE ADDITIONAL EXPLAINABILITY METRICS
# ============================================================

# ------------------------------------------------------------
# Early Iddq change
# ------------------------------------------------------------

df["early_iddq_change_uA"] = (

    df["iddq_24h_uA"]

    -

    df["iddq_0h_uA"]

)


# ------------------------------------------------------------
# Predicted margin from specification limit
#
# Positive = below limit
# Negative = above limit
# ------------------------------------------------------------

df["predicted_limit_margin_uA"] = (

    df["absolute_limit_uA"]

    -

    df["predicted_168h_uA"]

)


# ------------------------------------------------------------
# Upper prediction bound margin
# ------------------------------------------------------------

df["upper_limit_margin_uA"] = (

    df["absolute_limit_uA"]

    -

    df["prediction_upper_uA"]

)


# ------------------------------------------------------------
# Prediction interval width
# ------------------------------------------------------------

df["prediction_interval_width_uA"] = (

    df["prediction_upper_uA"]

    -

    df["prediction_lower_uA"]

)


# ------------------------------------------------------------
# Percentage of limit used by prediction
# ------------------------------------------------------------

df["predicted_limit_utilization_percent"] = np.where(

    df["absolute_limit_uA"] > 0,

    (
        df["predicted_168h_uA"]
        /
        df["absolute_limit_uA"]
        *
        100
    ),

    np.nan

)


# ------------------------------------------------------------
# Percentage of limit used by upper uncertainty bound
# ------------------------------------------------------------

df["upper_limit_utilization_percent"] = np.where(

    df["absolute_limit_uA"] > 0,

    (
        df["prediction_upper_uA"]
        /
        df["absolute_limit_uA"]
        *
        100
    ),

    np.nan

)


# ============================================================
# STEP 5: BUILD EVIDENCE LIST
# ============================================================

def generate_evidence(row):

    evidence = []


    # --------------------------------------------------------
    # Current anomaly
    # --------------------------------------------------------

    if row["current_anomaly_level"] == "HIGH":

        evidence.append(
            "Multiple early anomaly indicators triggered"
        )

    elif row["current_anomaly_level"] == "MEDIUM":

        evidence.append(
            "Some early anomaly indicators triggered"
        )

    elif row["current_anomaly_level"] == "LOW":

        evidence.append(
            "Mild early anomaly evidence detected"
        )


    # --------------------------------------------------------
    # Early Iddq trend
    # --------------------------------------------------------

    if row["early_iddq_change_uA"] > 0:

        evidence.append(
            "Iddq increased between 0h and 24h"
        )

    elif row["early_iddq_change_uA"] < 0:

        evidence.append(
            "Iddq decreased between 0h and 24h"
        )


    # --------------------------------------------------------
    # Future prediction
    # --------------------------------------------------------

    if row["predicted_limit_exceeded"]:

        evidence.append(
            "Predicted 168h Iddq exceeds specification limit"
        )


    # --------------------------------------------------------
    # Prediction uncertainty
    # --------------------------------------------------------

    if row["uncertainty_adjusted_failure"]:

        evidence.append(
            "Upper prediction bound reaches or exceeds specification limit"
        )


    # --------------------------------------------------------
    # Future drift
    # --------------------------------------------------------

    if row["future_drift_risk"]:

        evidence.append(
            "Predicted future drift exceeds dynamic safety boundary"
        )


    # --------------------------------------------------------
    # No evidence
    # --------------------------------------------------------

    if len(evidence) == 0:

        evidence.append(
            "No significant early abnormality detected"
        )


    return evidence


df["evidence_list"] = df.apply(
    generate_evidence,
    axis=1
)


# ============================================================
# STEP 6: CREATE HUMAN-READABLE EVIDENCE
# ============================================================

df["evidence_summary"] = (

    df["evidence_list"]

    .apply(
        lambda items:
        " | ".join(
            items
        )
    )

)


# ============================================================
# STEP 7: DETERMINE PRIMARY RISK DRIVER
# ============================================================

def determine_primary_driver(row):

    if row["predicted_limit_exceeded"]:

        return "PREDICTED_FUTURE_FAILURE"


    if row["uncertainty_adjusted_failure"]:

        return "UNCERTAINTY_ADJUSTED_FUTURE_FAILURE"


    if row["future_drift_risk"]:

        return "FUTURE_DRIFT"


    if row["current_anomaly_level"] == "HIGH":

        return "CURRENT_ANOMALY"


    if row["current_anomaly_level"] == "MEDIUM":

        return "CURRENT_ANOMALY"


    if row["current_anomaly_level"] == "LOW":

        return "MILD_CURRENT_ANOMALY"


    return "NO_SIGNIFICANT_RISK"


df["primary_risk_driver"] = df.apply(

    determine_primary_driver,

    axis=1

)


# ============================================================
# STEP 8: SCREENING RECOMMENDATION
# ============================================================

def screening_recommendation(row):

    risk = row["final_risk_level"]


    # --------------------------------------------------------
    # CRITICAL
    # --------------------------------------------------------

    if risk == "CRITICAL":

        return (
            "IMMEDIATE ENGINEERING REVIEW: "
            "Prioritize this component for confirmatory screening "
            "and investigate the predicted future failure risk."
        )


    # --------------------------------------------------------
    # HIGH
    # --------------------------------------------------------

    if risk == "HIGH":

        return (
            "PRIORITY SCREENING: "
            "Perform enhanced screening and monitor the component "
            "for abnormal drift."
        )


    # --------------------------------------------------------
    # MEDIUM
    # --------------------------------------------------------

    if risk == "MEDIUM":

        return (
            "ENHANCED MONITORING: "
            "Continue monitoring and consider additional screening "
            "if abnormal behavior persists."
        )


    # --------------------------------------------------------
    # WATCH
    # --------------------------------------------------------

    if risk == "WATCH":

        return (
            "MONITOR: "
            "Track the component during subsequent screening stages."
        )


    # --------------------------------------------------------
    # LOW
    # --------------------------------------------------------

    return (
        "NORMAL MONITORING: "
        "No significant early risk identified."
    )


df["screening_recommendation"] = df.apply(

    screening_recommendation,

    axis=1

)


# ============================================================
# STEP 9: GENERATE ENGINEER-FRIENDLY EXPLANATION
# ============================================================

def generate_detailed_explanation(row):

    explanation = []


    # --------------------------------------------------------
    # Opening
    # --------------------------------------------------------

    explanation.append(

        f"Component {row['component_id']} "
        f"has been classified as "
        f"{row['final_risk_level']} risk."
    )


    # --------------------------------------------------------
    # Current behavior
    # --------------------------------------------------------

    explanation.append(

        f"Early Iddq changed from "
        f"{row['iddq_0h_uA']:.2f} µA at 0h "
        f"to "
        f"{row['iddq_24h_uA']:.2f} µA at 24h."
    )


    explanation.append(

        f"The early drift rate is "
        f"{row['drift_0_24_uA_per_h']:.4f} µA/hour."
    )


    # --------------------------------------------------------
    # Current anomaly
    # --------------------------------------------------------

    explanation.append(

        f"Current anomaly level is "
        f"{row['current_anomaly_level']} "
        f"with an anomaly evidence score of "
        f"{row['anomaly_score']:.2f}."
    )


    # --------------------------------------------------------
    # Future prediction
    # --------------------------------------------------------

    explanation.append(

        f"The model predicts "
        f"{row['predicted_168h_uA']:.2f} µA "
        f"at 168h."
    )


    # --------------------------------------------------------
    # Limit
    # --------------------------------------------------------

    explanation.append(

        f"The applicable prototype specification limit is "
        f"{row['absolute_limit_uA']:.2f} µA."
    )


    # --------------------------------------------------------
    # Prediction margin
    # --------------------------------------------------------

    margin = row["predicted_limit_margin_uA"]


    if margin < 0:

        explanation.append(

            f"The prediction is "
            f"{abs(margin):.2f} µA above "
            f"the limit."
        )

    else:

        explanation.append(

            f"The prediction remains "
            f"{margin:.2f} µA below "
            f"the limit."
        )


    # --------------------------------------------------------
    # Uncertainty
    # --------------------------------------------------------

    explanation.append(

        f"The 90% prediction interval is approximately "
        f"{row['prediction_lower_uA']:.2f} to "
        f"{row['prediction_upper_uA']:.2f} µA."
    )


    # --------------------------------------------------------
    # Drift
    # --------------------------------------------------------

    if row["future_drift_risk"]:

        explanation.append(

            "The predicted future drift is above "
            "the dynamic safety boundary."
        )


    # --------------------------------------------------------
    # Final decision
    # --------------------------------------------------------

    explanation.append(

        f"Final screening decision: "
        f"{row['final_decision']}."
    )


    return " ".join(explanation)


df["detailed_explanation"] = df.apply(

    generate_detailed_explanation,

    axis=1

)


# ============================================================
# STEP 10: CREATE SCREENING CATEGORY
# ============================================================

def screening_category(row):

    risk = row["final_risk_level"]


    if risk == "CRITICAL":

        return "IMMEDIATE_REVIEW"


    if risk == "HIGH":

        return "PRIORITY_SCREENING"


    if risk == "MEDIUM":

        return "ENHANCED_MONITORING"


    if risk == "WATCH":

        return "MONITOR"


    return "NORMAL"


df["screening_category"] = df.apply(

    screening_category,

    axis=1

)


# ============================================================
# STEP 11: RISK PRIORITY
# ============================================================

priority_map = {

    "CRITICAL": 1,

    "HIGH": 2,

    "MEDIUM": 3,

    "WATCH": 4,

    "LOW": 5

}


df["screening_priority"] = (

    df["final_risk_level"]

    .map(priority_map)

)


# ============================================================
# STEP 12: SORT COMPONENTS
# ============================================================

df = df.sort_values(

    [

        "screening_priority",

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
# STEP 13: SELECT OUTPUT COLUMNS
# ============================================================

output_columns = [

    # Identification
    "component_id",
    "lot_id",
    "component_type",

    # Early measurements
    "iddq_0h_uA",
    "iddq_24h_uA",
    "early_iddq_change_uA",
    "drift_0_24_uA_per_h",

    # Current anomaly
    "anomaly_score",
    "current_anomaly_level",

    # Future prediction
    "predicted_168h_uA",
    "prediction_lower_uA",
    "prediction_upper_uA",

    # Specification
    "absolute_limit_uA",
    "predicted_limit_margin_uA",
    "upper_limit_margin_uA",

    # Prediction information
    "predicted_limit_utilization_percent",
    "upper_limit_utilization_percent",
    "prediction_interval_width_uA",

    # Drift
    "predicted_drift_rate",
    "safety_slope",
    "drift_slope_excess",
    "future_drift_risk",

    # Risk
    "risk_score",
    "final_risk_level",
    "final_decision",

    # Explainability
    "primary_risk_driver",
    "evidence_summary",
    "screening_category",
    "screening_recommendation",
    "detailed_explanation"

]


explanations_df = df[
    output_columns
].copy()


# ============================================================
# STEP 14: SAVE EXPLANATION DATASET
# ============================================================

os.makedirs(
    "data",
    exist_ok=True
)

explanations_df.to_csv(

    OUTPUT_PATH,

    index=False

)


# ============================================================
# STEP 15: CREATE PRIORITY SCREENING LIST
# ============================================================

priority_df = explanations_df[

    explanations_df[
        "final_risk_level"
    ].isin(
        [
            "CRITICAL",
            "HIGH"
        ]
    )

].copy()


priority_columns = [

    "component_id",
    "lot_id",
    "component_type",

    "iddq_0h_uA",
    "iddq_24h_uA",

    "predicted_168h_uA",
    "absolute_limit_uA",

    "predicted_limit_margin_uA",

    "prediction_upper_uA",

    "upper_limit_margin_uA",

    "predicted_drift_rate",
    "safety_slope",

    "risk_score",
    "final_risk_level",
    "final_decision",

    "primary_risk_driver",

    "screening_recommendation"

]


priority_df = priority_df[
    priority_columns
]


priority_df.to_csv(

    PRIORITY_OUTPUT_PATH,

    index=False

)


# ============================================================
# STEP 16: CREATE COMPONENT REPORT DIRECTORY
# ============================================================

os.makedirs(

    REPORT_DIRECTORY,

    exist_ok=True

)


# ============================================================
# STEP 17: GENERATE INDIVIDUAL COMPONENT REPORTS
# ============================================================

print("\nGenerating component reports...")


for _, row in explanations_df.iterrows():

    component_id = str(
        row["component_id"]
    )


    report_path = os.path.join(

        REPORT_DIRECTORY,

        f"{component_id}.txt"

    )


    report = []

    report.append(
        "=" * 70
    )

    report.append(
        "SIH 26170 - COMPONENT SCREENING REPORT"
    )

    report.append(
        "=" * 70
    )

    report.append("")

    report.append(
        f"Component ID       : {component_id}"
    )

    report.append(
        f"Lot                 : {row['lot_id']}"
    )

    report.append(
        f"Component Type     : {row['component_type']}"
    )

    report.append("")

    report.append(
        "-" * 70
    )

    report.append(
        "EARLY MEASUREMENTS"
    )

    report.append(
        "-" * 70
    )

    report.append(
        f"Iddq at 0h          : "
        f"{row['iddq_0h_uA']:.3f} µA"
    )

    report.append(
        f"Iddq at 24h         : "
        f"{row['iddq_24h_uA']:.3f} µA"
    )

    report.append(
        f"Early change        : "
        f"{row['early_iddq_change_uA']:.3f} µA"
    )

    report.append(
        f"Early drift rate    : "
        f"{row['drift_0_24_uA_per_h']:.6f} µA/hour"
    )

    report.append("")

    report.append(
        "-" * 70
    )

    report.append(
        "CURRENT ANOMALY"
    )

    report.append(
        "-" * 70
    )

    report.append(
        f"Anomaly score       : "
        f"{row['anomaly_score']:.3f}"
    )

    report.append(
        f"Anomaly level       : "
        f"{row['current_anomaly_level']}"
    )

    report.append("")

    report.append(
        "-" * 70
    )

    report.append(
        "FUTURE PREDICTION"
    )

    report.append(
        "-" * 70
    )

    report.append(
        f"Predicted 168h Iddq : "
        f"{row['predicted_168h_uA']:.3f} µA"
    )

    report.append(
        f"Prediction lower    : "
        f"{row['prediction_lower_uA']:.3f} µA"
    )

    report.append(
        f"Prediction upper    : "
        f"{row['prediction_upper_uA']:.3f} µA"
    )

    report.append(
        f"Specification limit : "
        f"{row['absolute_limit_uA']:.3f} µA"
    )

    report.append(
        f"Prediction margin   : "
        f"{row['predicted_limit_margin_uA']:.3f} µA"
    )

    report.append("")

    report.append(
        "-" * 70
    )

    report.append(
        "FUTURE DRIFT"
    )

    report.append(
        "-" * 70
    )

    report.append(
        f"Predicted drift     : "
        f"{row['predicted_drift_rate']:.6f}"
    )

    report.append(
        f"Safety slope        : "
        f"{row['safety_slope']:.6f}"
    )

    report.append(
        f"Drift slope excess  : "
        f"{row['drift_slope_excess']:.6f}"
    )

    report.append(
        f"Future drift risk   : "
        f"{row['future_drift_risk']}"
    )

    report.append("")

    report.append(
        "-" * 70
    )

    report.append(
        "RISK ASSESSMENT"
    )

    report.append(
        "-" * 70
    )

    report.append(
        f"Risk score          : "
        f"{row['risk_score']:.2f}"
    )

    report.append(
        f"Risk level          : "
        f"{row['final_risk_level']}"
    )

    report.append(
        f"Decision            : "
        f"{row['final_decision']}"
    )

    report.append(
        f"Primary driver      : "
        f"{row['primary_risk_driver']}"
    )

    report.append("")

    report.append(
        "-" * 70
    )

    report.append(
        "WHY WAS THIS COMPONENT FLAGGED?"
    )

    report.append(
        "-" * 70
    )

    report.append(
        row["evidence_summary"]
    )

    report.append("")

    report.append(
        "-" * 70
    )

    report.append(
        "SCREENING RECOMMENDATION"
    )

    report.append(
        "-" * 70
    )

    report.append(
        row["screening_recommendation"]
    )

    report.append("")

    report.append(
        "-" * 70
    )

    report.append(
        "DETAILED EXPLANATION"
    )

    report.append(
        "-" * 70
    )

    report.append(
        row["detailed_explanation"]
    )

    report.append("")

    report.append(
        "=" * 70
    )

    report.append(
        "Prototype screening result."
    )

    report.append(
        "Not an ISRO-qualified engineering limit or decision."
    )

    report.append(
        "=" * 70
    )


    with open(

        report_path,

        "w",

        encoding="utf-8"

    ) as file:

        file.write(
            "\n".join(report)
        )


# ============================================================
# STEP 18: SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("MODULE D SUMMARY")
print("=" * 70)


print(
    "\nComponents explained:",
    len(explanations_df)
)


print(
    "\nRisk distribution:"
)


print(

    explanations_df[
        "final_risk_level"
    ].value_counts()

)


print(
    "\nPrimary risk drivers:"
)


print(

    explanations_df[
        "primary_risk_driver"
    ].value_counts()

)


print(
    "\nPriority components:",
    len(priority_df)
)


# ============================================================
# STEP 19: DISPLAY TOP PRIORITY COMPONENTS
# ============================================================

print("\n" + "=" * 70)
print("TOP PRIORITY SCREENING COMPONENTS")
print("=" * 70)


display_columns = [

    "component_id",
    "lot_id",
    "component_type",

    "predicted_168h_uA",
    "absolute_limit_uA",

    "predicted_limit_margin_uA",

    "risk_score",

    "final_risk_level",

    "final_decision",

    "primary_risk_driver"

]


print(

    priority_df[
        display_columns
    ]
    .head(20)
    .to_string(
        index=False
    )

)


# ============================================================
# STEP 20: EARLY-SCREENING AUDIT
# ============================================================

forbidden_columns = [

    "iddq_96h_uA",
    "iddq_168h_uA",

    "zscore_96h",
    "zscore_168h",

    "z_anomaly_96h",
    "z_anomaly_168h",

    "robust_zscore_96h",
    "robust_zscore_168h",

    "iqr_anomaly_96h",
    "iqr_anomaly_168h",

    "ground_truth"

]


used_forbidden = [

    column

    for column in forbidden_columns

    if column in explanations_df.columns

]


print("\n" + "=" * 70)
print("MODULE D EARLY-SCREENING AUDIT")
print("=" * 70)


if len(used_forbidden) == 0:

    print(
        "\nPASS:"
    )

    print(
        "No actual future measurements or ground-truth "
        "columns are included in Module D outputs."
    )

else:

    print(
        "\nWARNING:"
    )

    print(
        "Forbidden evaluation columns found:"
    )

    for column in used_forbidden:

        print(
            " -",
            column
        )


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 70)
print("MODULE D COMPLETED")
print("=" * 70)


print(
    "\nExplanation dataset:"
)

print(
    OUTPUT_PATH
)


print(
    "\nPriority screening list:"
)

print(
    PRIORITY_OUTPUT_PATH
)


print(
    "\nComponent reports:"
)

print(
    REPORT_DIRECTORY
)


print("\n" + "=" * 70)