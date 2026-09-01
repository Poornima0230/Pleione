# ============================================================
# SIH 26170
# MODULE F: VALIDATION & PERFORMANCE EVALUATION
# ============================================================
#
# PURPOSE
# ------------------------------------------------------------
# Evaluate the complete early-screening system against
# known ground truth.
#
# IMPORTANT:
# ------------------------------------------------------------
# Module F is an OFFLINE EVALUATION module.
#
# Ground truth and actual future measurements are used ONLY
# for evaluation.
#
# They are NOT used to make Module A/B/C/D decisions.
#
#
# INPUTS
# ------------------------------------------------------------
#
# Raw dataset:
#   data/sih_26170_burn_in_synthetic_dataset.csv
#
# Module B:
#   data/module_B_drift_predictions.csv
#
# Module C:
#   data/final_risk_assessment.csv
#
#
# OUTPUTS
# ------------------------------------------------------------
#
# data/module_F_metrics.csv
# data/module_F_confusion_matrix.csv
# data/module_F_component_evaluation.csv
#
# data/module_F_plots/
#   prediction_performance.png
#   prediction_error.png
#   risk_distribution.png
#   confusion_matrix.png
#   defect_detection.png
#   screening_workload.png
#
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score
)


# ============================================================
# CONFIGURATION
# ============================================================

DATA_DIR = "data"

RAW_DATA_PATH = os.path.join(
    DATA_DIR,
    "sih_26170_burn_in_synthetic_dataset.csv"
)

MODULE_B_PATH = os.path.join(
    DATA_DIR,
    "module_B_drift_predictions.csv"
)

MODULE_C_PATH = os.path.join(
    DATA_DIR,
    "final_risk_assessment.csv"
)

OUTPUT_METRICS = os.path.join(
    DATA_DIR,
    "module_F_metrics.csv"
)

OUTPUT_CONFUSION = os.path.join(
    DATA_DIR,
    "module_F_confusion_matrix.csv"
)

OUTPUT_COMPONENTS = os.path.join(
    DATA_DIR,
    "module_F_component_evaluation.csv"
)

PLOT_DIR = os.path.join(
    DATA_DIR,
    "module_F_plots"
)


# ============================================================
# CREATE OUTPUT DIRECTORY
# ============================================================

os.makedirs(
    PLOT_DIR,
    exist_ok=True
)


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("SIH 26170")
print("MODULE F: VALIDATION & PERFORMANCE EVALUATION")
print("=" * 70)


# ============================================================
# STEP 1: LOAD DATA
# ============================================================

print("\nLoading evaluation data...")


raw = pd.read_csv(
    RAW_DATA_PATH
)

module_b = pd.read_csv(
    MODULE_B_PATH
)

module_c = pd.read_csv(
    MODULE_C_PATH
)


print(
    f"Raw dataset components : {len(raw)}"
)

print(
    f"Module B components    : {len(module_b)}"
)

print(
    f"Module C components    : {len(module_c)}"
)


# ============================================================
# STEP 2: VALIDATE REQUIRED COLUMNS
# ============================================================

raw_required = [

    "component_id",

    "iddq_168h_uA",

    "ground_truth",

    "absolute_limit_uA"

]


module_b_required = [

    "component_id",

    "predicted_168h_uA"

]


module_c_required = [

    "component_id",

    "final_risk_level",

    "final_decision"

]


missing_raw = [

    col

    for col in raw_required

    if col not in raw.columns

]


missing_b = [

    col

    for col in module_b_required

    if col not in module_b.columns

]


missing_c = [

    col

    for col in module_c_required

    if col not in module_c.columns

]


if missing_raw:

    raise ValueError(
        "Missing raw dataset columns: "
        + str(missing_raw)
    )


if missing_b:

    raise ValueError(
        "Missing Module B columns: "
        + str(missing_b)
    )


if missing_c:

    raise ValueError(
        "Missing Module C columns: "
        + str(missing_c)
    )


print(
    "\nRequired column validation: PASS"
)


# ============================================================
# STEP 3: CHECK DUPLICATE IDS
# ============================================================

for name, dataframe in [

    ("Raw dataset", raw),

    ("Module B", module_b),

    ("Module C", module_c)

]:

    if dataframe[
        "component_id"
    ].duplicated().any():

        raise ValueError(
            f"Duplicate component IDs found in {name}."
        )


print(
    "Duplicate component ID validation: PASS"
)


# ============================================================
# STEP 4: MERGE EVALUATION DATA
# ============================================================
#
# Ground truth is introduced ONLY here.
#
# This merged dataset is for evaluation.
#
# It is NOT fed back into Module C.
#
# ============================================================

print(
    "\nBuilding independent evaluation dataset..."
)


evaluation = raw[
    [
        "component_id",
        "iddq_168h_uA",
        "ground_truth",
        "absolute_limit_uA"
    ]
].copy()


evaluation = evaluation.merge(

    module_b[
        [
            "component_id",
            "predicted_168h_uA"
        ]
    ],

    on="component_id",

    how="inner"

)


evaluation = evaluation.merge(

    module_c[
        [
            "component_id",
            "final_risk_level",
            "final_decision"
        ]
    ],

    on="component_id",

    how="inner"

)


print(
    f"Evaluation components: {len(evaluation)}"
)


if len(evaluation) == 0:

    raise ValueError(
        "No components could be matched for evaluation."
    )


# ============================================================
# STEP 5: FORECASTING PERFORMANCE
# ============================================================

print("\n" + "=" * 70)
print("1. FUTURE PREDICTION PERFORMANCE")
print("=" * 70)


actual_168h = evaluation[
    "iddq_168h_uA"
].astype(float)


predicted_168h = evaluation[
    "predicted_168h_uA"
].astype(float)


mae = mean_absolute_error(
    actual_168h,
    predicted_168h
)


rmse = np.sqrt(
    mean_squared_error(
        actual_168h,
        predicted_168h
    )
)


r2 = r2_score(
    actual_168h,
    predicted_168h
)


print(
    f"\nMAE  : {mae:.4f} µA"
)

print(
    f"RMSE : {rmse:.4f} µA"
)

print(
    f"R²   : {r2:.4f}"
)


# ============================================================
# STEP 6: PREDICTION ERROR
# ============================================================

evaluation[
    "prediction_error_uA"
] = (

    evaluation[
        "predicted_168h_uA"
    ]

    -

    evaluation[
        "iddq_168h_uA"
    ]

)


evaluation[
    "absolute_prediction_error_uA"
] = (

    evaluation[
        "prediction_error_uA"
    ]
    .abs()

)


error_50 = evaluation[
    "absolute_prediction_error_uA"
].quantile(0.50)


error_90 = evaluation[
    "absolute_prediction_error_uA"
].quantile(0.90)


error_95 = evaluation[
    "absolute_prediction_error_uA"
].quantile(0.95)


print(
    "\nPrediction error percentiles:"
)

print(
    f"50th percentile : {error_50:.4f} µA"
)

print(
    f"90th percentile : {error_90:.4f} µA"
)

print(
    f"95th percentile : {error_95:.4f} µA"
)


# ============================================================
# STEP 7: ACTUAL FUTURE FAILURE
# ============================================================
#
# This is evaluation-only ground truth.
#
# ============================================================

evaluation[
    "actual_future_failure"
] = (

    evaluation[
        "iddq_168h_uA"
    ]

    >

    evaluation[
        "absolute_limit_uA"
    ]

)


# ============================================================
# STEP 8: PREDICTED FUTURE FAILURE
# ============================================================

evaluation[
    "predicted_future_failure"
] = (

    evaluation[
        "predicted_168h_uA"
    ]

    >

    evaluation[
        "absolute_limit_uA"
    ]

)


# ============================================================
# STEP 9: BINARY FAILURE METRICS
# ============================================================

print("\n" + "=" * 70)
print("2. FUTURE FAILURE DETECTION")
print("=" * 70)


y_actual_failure = evaluation[
    "actual_future_failure"
].astype(int)


y_pred_failure = evaluation[
    "predicted_future_failure"
].astype(int)


failure_accuracy = accuracy_score(
    y_actual_failure,
    y_pred_failure
)


failure_precision = precision_score(
    y_actual_failure,
    y_pred_failure,
    zero_division=0
)


failure_recall = recall_score(
    y_actual_failure,
    y_pred_failure,
    zero_division=0
)


failure_f1 = f1_score(
    y_actual_failure,
    y_pred_failure,
    zero_division=0
)


print(
    f"\nAccuracy  : {failure_accuracy:.4f}"
)

print(
    f"Precision : {failure_precision:.4f}"
)

print(
    f"Recall    : {failure_recall:.4f}"
)

print(
    f"F1-score  : {failure_f1:.4f}"
)


actual_failures = int(
    y_actual_failure.sum()
)


predicted_failures = int(
    y_pred_failure.sum()
)


print(
    f"\nActual future failures    : {actual_failures}"
)

print(
    f"Predicted future failures : {predicted_failures}"
)


# ============================================================
# STEP 10: RISK-LEVEL EVALUATION
# ============================================================
#
# For screening evaluation:
#
# NORMAL = no abnormality
#
# Any other ground-truth class =
# screening-relevant abnormal behavior.
#
# ============================================================

print("\n" + "=" * 70)
print("3. RISK SCREENING PERFORMANCE")
print("=" * 70)


evaluation[
    "actual_abnormal"
] = (

    evaluation[
        "ground_truth"
    ]

    !=

    "Normal"

)


evaluation[
    "predicted_abnormal"
] = (

    evaluation[
        "final_risk_level"
    ]

    !=

    "LOW"

)


y_actual_abnormal = evaluation[
    "actual_abnormal"
].astype(int)


y_pred_abnormal = evaluation[
    "predicted_abnormal"
].astype(int)


risk_accuracy = accuracy_score(
    y_actual_abnormal,
    y_pred_abnormal
)


risk_precision = precision_score(
    y_actual_abnormal,
    y_pred_abnormal,
    zero_division=0
)


risk_recall = recall_score(
    y_actual_abnormal,
    y_pred_abnormal,
    zero_division=0
)


risk_f1 = f1_score(
    y_actual_abnormal,
    y_pred_abnormal,
    zero_division=0
)


print(
    f"\nAccuracy  : {risk_accuracy:.4f}"
)

print(
    f"Precision : {risk_precision:.4f}"
)

print(
    f"Recall    : {risk_recall:.4f}"
)

print(
    f"F1-score  : {risk_f1:.4f}"
)


# ============================================================
# STEP 11: CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(

    y_actual_abnormal,

    y_pred_abnormal,

    labels=[0, 1]

)


confusion_df = pd.DataFrame(

    cm,

    index=[
        "Actual_Normal",
        "Actual_Abnormal"
    ],

    columns=[
        "Predicted_Normal",
        "Predicted_Abnormal"
    ]

)


confusion_df.to_csv(
    OUTPUT_CONFUSION
)


print(
    "\nConfusion matrix:"
)

print(
    confusion_df
)


# ============================================================
# STEP 12: LATENT DEFECT ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("4. LATENT DEFECT DETECTION")
print("=" * 70)


latent = evaluation[
    evaluation[
        "ground_truth"
    ]
    == "Latent_Defect"
].copy()


latent_total = len(
    latent
)


latent_detected = (

    latent[
        "predicted_abnormal"
    ].sum()

)


latent_detection_rate = (

    latent_detected
    /
    latent_total
    if latent_total > 0
    else 0

)


print(
    f"\nTotal latent defects : {latent_total}"
)

print(
    f"Detected dynamically : {latent_detected}"
)

print(
    f"Detection rate       : "
    f"{latent_detection_rate * 100:.2f}%"
)


# ============================================================
# STEP 13: ABSOLUTE FAILURE ANALYSIS
# ============================================================

absolute_failure = evaluation[
    evaluation[
        "ground_truth"
    ]
    == "Absolute_Failure"
].copy()


absolute_failure_total = len(
    absolute_failure
)


absolute_failure_detected = (

    absolute_failure[
        "predicted_future_failure"
    ].sum()

)


absolute_failure_detection_rate = (

    absolute_failure_detected
    /
    absolute_failure_total

    if absolute_failure_total > 0

    else 0

)


print(
    "\nAbsolute failure components:"
)

print(
    f"Total     : {absolute_failure_total}"
)

print(
    f"Detected  : {absolute_failure_detected}"
)

print(
    f"Detection : "
    f"{absolute_failure_detection_rate * 100:.2f}%"
)


# ============================================================
# STEP 14: GROUND-TRUTH DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("5. GROUND-TRUTH DISTRIBUTION")
print("=" * 70)


ground_truth_distribution = (

    evaluation[
        "ground_truth"
    ]
    .value_counts()

)


print(
    ground_truth_distribution
)


# ============================================================
# STEP 15: RISK DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("6. SCREENING RISK DISTRIBUTION")
print("=" * 70)


risk_distribution = (

    evaluation[
        "final_risk_level"
    ]
    .value_counts()

)


print(
    risk_distribution
)


# ============================================================
# STEP 16: SCREENING WORKLOAD
# ============================================================
#
# Priority screening:
#
# HIGH + CRITICAL
#
# Immediate review:
#
# CRITICAL
#
# ============================================================

total_components = len(
    evaluation
)


priority_components = (

    evaluation[
        "final_risk_level"
    ]
    .isin(
        [
            "HIGH",
            "CRITICAL"
        ]
    )
    .sum()

)


critical_components = (

    evaluation[
        "final_risk_level"
    ]
    == "CRITICAL"
).sum()


monitoring_components = (

    evaluation[
        "final_risk_level"
    ]
    .isin(
        [
            "WATCH",
            "MEDIUM"
        ]
    )
    .sum()

)


normal_components = (

    evaluation[
        "final_risk_level"
    ]
    == "LOW"
).sum()


screening_workload_percentage = (

    priority_components
    /
    total_components
    *
    100

)


screening_reduction_percentage = (

    100
    -
    screening_workload_percentage

)


print(
    f"\nTotal components          : "
    f"{total_components}"
)

print(
    f"Normal                    : "
    f"{normal_components}"
)

print(
    f"Monitoring                : "
    f"{monitoring_components}"
)

print(
    f"Priority screening        : "
    f"{priority_components}"
)

print(
    f"Immediate review          : "
    f"{critical_components}"
)

print(
    f"\nPriority screening load  : "
    f"{screening_workload_percentage:.2f}%"
)

print(
    f"Components filtered from "
    f"priority screening       : "
    f"{screening_reduction_percentage:.2f}%"
)


# ============================================================
# STEP 17: COMPONENT TYPE PERFORMANCE
# ============================================================

print("\n" + "=" * 70)
print("7. PERFORMANCE BY COMPONENT TYPE")
print("=" * 70)


component_type_results = []


if "component_type" in raw.columns:

    type_mapping = raw[
        [
            "component_id",
            "component_type"
        ]
    ]


    evaluation = evaluation.merge(

        type_mapping,

        on="component_id",

        how="left",

        suffixes=(
            "",
            "_raw"
        )

    )


    for component_type, group in evaluation.groupby(
        "component_type"
    ):

        type_actual = group[
            "iddq_168h_uA"
        ]

        type_predicted = group[
            "predicted_168h_uA"
        ]


        type_mae = mean_absolute_error(

            type_actual,

            type_predicted

        )


        type_rmse = np.sqrt(

            mean_squared_error(

                type_actual,

                type_predicted

            )

        )


        actual_abnormal_count = group[
            "actual_abnormal"
        ].sum()


        predicted_abnormal_count = group[
            "predicted_abnormal"
        ].sum()


        component_type_results.append({

            "component_type":
                component_type,

            "count":
                len(group),

            "MAE_uA":
                type_mae,

            "RMSE_uA":
                type_rmse,

            "actual_abnormal":
                actual_abnormal_count,

            "predicted_abnormal":
                predicted_abnormal_count

        })


    component_type_df = pd.DataFrame(
        component_type_results
    )


    print(
        component_type_df.to_string(
            index=False
        )
    )


# ============================================================
# STEP 18: SAVE COMPONENT-LEVEL EVALUATION
# ============================================================

evaluation.to_csv(

    OUTPUT_COMPONENTS,

    index=False

)


# ============================================================
# STEP 19: CREATE METRICS TABLE
# ============================================================

metrics = [

    [
        "Prediction_MAE_uA",
        mae
    ],

    [
        "Prediction_RMSE_uA",
        rmse
    ],

    [
        "Prediction_R2",
        r2
    ],

    [
        "Prediction_Error_P50_uA",
        error_50
    ],

    [
        "Prediction_Error_P90_uA",
        error_90
    ],

    [
        "Prediction_Error_P95_uA",
        error_95
    ],

    [
        "Failure_Accuracy",
        failure_accuracy
    ],

    [
        "Failure_Precision",
        failure_precision
    ],

    [
        "Failure_Recall",
        failure_recall
    ],

    [
        "Failure_F1",
        failure_f1
    ],

    [
        "Actual_Future_Failures",
        actual_failures
    ],

    [
        "Predicted_Future_Failures",
        predicted_failures
    ],

    [
        "Risk_Accuracy",
        risk_accuracy
    ],

    [
        "Risk_Precision",
        risk_precision
    ],

    [
        "Risk_Recall",
        risk_recall
    ],

    [
        "Risk_F1",
        risk_f1
    ],

    [
        "Latent_Defects",
        latent_total
    ],

    [
        "Latent_Defects_Detected",
        latent_detected
    ],

    [
        "Latent_Defect_Detection_Rate",
        latent_detection_rate
    ],

    [
        "Absolute_Failures",
        absolute_failure_total
    ],

    [
        "Absolute_Failures_Detected",
        absolute_failure_detected
    ],

    [
        "Absolute_Failure_Detection_Rate",
        absolute_failure_detection_rate
    ],

    [
        "Total_Components",
        total_components
    ],

    [
        "Priority_Screening_Components",
        priority_components
    ],

    [
        "Priority_Screening_Load_Percent",
        screening_workload_percentage
    ],

    [
        "Screening_Reduction_Percent",
        screening_reduction_percentage
    ]

]


metrics_df = pd.DataFrame(

    metrics,

    columns=[
        "metric",
        "value"
    ]

)


metrics_df.to_csv(

    OUTPUT_METRICS,

    index=False

)


# ============================================================
# STEP 20: PLOT 1
# ACTUAL VS PREDICTED
# ============================================================

print(
    "\nGenerating plots..."
)


plt.figure(
    figsize=(8, 6)
)


plt.scatter(

    actual_168h,

    predicted_168h,

    alpha=0.35

)


minimum = min(

    actual_168h.min(),

    predicted_168h.min()

)


maximum = max(

    actual_168h.max(),

    predicted_168h.max()

)


plt.plot(

    [minimum, maximum],

    [minimum, maximum]

)


plt.xlabel(
    "Actual 168h Iddq (µA)"
)

plt.ylabel(
    "Predicted 168h Iddq (µA)"
)

plt.title(
    "Actual vs Predicted 168h Iddq"
)

plt.tight_layout()


plt.savefig(

    os.path.join(
        PLOT_DIR,
        "prediction_performance.png"
    ),

    dpi=200

)

plt.close()


# ============================================================
# STEP 21: PLOT 2
# PREDICTION ERROR
# ============================================================

plt.figure(
    figsize=(8, 6)
)


plt.hist(

    evaluation[
        "absolute_prediction_error_uA"
    ],

    bins=40

)


plt.xlabel(
    "Absolute Prediction Error (µA)"
)

plt.ylabel(
    "Number of Components"
)

plt.title(
    "Prediction Error Distribution"
)

plt.tight_layout()


plt.savefig(

    os.path.join(
        PLOT_DIR,
        "prediction_error.png"
    ),

    dpi=200

)

plt.close()


# ============================================================
# STEP 22: PLOT 3
# RISK DISTRIBUTION
# ============================================================

risk_order = [

    "LOW",

    "WATCH",

    "MEDIUM",

    "HIGH",

    "CRITICAL"

]


risk_counts = [

    risk_distribution.get(
        risk,
        0
    )

    for risk in risk_order

]


plt.figure(
    figsize=(8, 6)
)


plt.bar(

    risk_order,

    risk_counts

)


plt.xlabel(
    "Final Risk Level"
)

plt.ylabel(
    "Number of Components"
)

plt.title(
    "Final Screening Risk Distribution"
)

plt.tight_layout()


plt.savefig(

    os.path.join(
        PLOT_DIR,
        "risk_distribution.png"
    ),

    dpi=200

)

plt.close()


# ============================================================
# STEP 23: PLOT 4
# CONFUSION MATRIX
# ============================================================

plt.figure(
    figsize=(7, 6)
)


plt.imshow(
    cm
)


plt.xticks(

    [0, 1],

    [
        "Normal",
        "Abnormal"
    ]

)


plt.yticks(

    [0, 1],

    [
        "Normal",
        "Abnormal"
    ]

)


for i in range(2):

    for j in range(2):

        plt.text(

            j,

            i,

            cm[i, j],

            ha="center",

            va="center"

        )


plt.xlabel(
    "Predicted"
)

plt.ylabel(
    "Actual"
)

plt.title(
    "Screening Confusion Matrix"
)

plt.colorbar()

plt.tight_layout()


plt.savefig(

    os.path.join(
        PLOT_DIR,
        "confusion_matrix.png"
    ),

    dpi=200

)

plt.close()


# ============================================================
# STEP 24: PLOT 5
# DEFECT DETECTION
# ============================================================

defect_categories = [

    "Latent_Defect",

    "Absolute_Failure",

    "Sudden_Anomaly",

    "High_Stable"

]


detection_rates = []


for category in defect_categories:

    group = evaluation[
        evaluation[
            "ground_truth"
        ]
        == category
    ]


    if len(group) == 0:

        detection_rates.append(0)

    else:

        detection_rates.append(

            group[
                "predicted_abnormal"
            ].mean()
            *
            100

        )


plt.figure(
    figsize=(9, 6)
)


plt.bar(

    defect_categories,

    detection_rates

)


plt.ylabel(
    "Detection Rate (%)"
)

plt.xlabel(
    "Component Type"
)

plt.title(
    "Early Screening Detection by Ground-Truth Class"
)

plt.xticks(
    rotation=20
)

plt.tight_layout()


plt.savefig(

    os.path.join(
        PLOT_DIR,
        "defect_detection.png"
    ),

    dpi=200

)

plt.close()


# ============================================================
# STEP 25: PLOT 6
# SCREENING WORKLOAD
# ============================================================

workload_labels = [

    "Normal",

    "Monitoring",

    "Priority",

    "Immediate Review"

]


workload_values = [

    normal_components,

    monitoring_components,

    priority_components,

    critical_components

]


plt.figure(
    figsize=(8, 6)
)


plt.bar(

    workload_labels,

    workload_values

)


plt.xlabel(
    "Screening Category"
)

plt.ylabel(
    "Number of Components"
)

plt.title(
    "Screening Workload Distribution"
)

plt.tight_layout()


plt.savefig(

    os.path.join(
        PLOT_DIR,
        "screening_workload.png"
    ),

    dpi=200

)

plt.close()


# ============================================================
# STEP 26: FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("MODULE F VALIDATION SUMMARY")
print("=" * 70)


print(
    f"\nComponents evaluated : "
    f"{total_components}"
)


print(
    "\nFuture prediction:"
)


print(
    f"MAE  : {mae:.4f} µA"
)

print(
    f"RMSE : {rmse:.4f} µA"
)

print(
    f"R²   : {r2:.4f}"
)


print(
    "\nFuture failure detection:"
)


print(
    f"Accuracy  : {failure_accuracy:.4f}"
)

print(
    f"Precision : {failure_precision:.4f}"
)

print(
    f"Recall    : {failure_recall:.4f}"
)

print(
    f"F1        : {failure_f1:.4f}"
)


print(
    "\nRisk screening:"
)


print(
    f"Accuracy  : {risk_accuracy:.4f}"
)

print(
    f"Precision : {risk_precision:.4f}"
)

print(
    f"Recall    : {risk_recall:.4f}"
)

print(
    f"F1        : {risk_f1:.4f}"
)


print(
    "\nLatent defect detection:"
)


print(
    f"{latent_detection_rate * 100:.2f}%"
)


print(
    "\nScreening workload:"
)


print(
    f"Priority screening: "
    f"{priority_components}"
)


print(
    f"Priority load: "
    f"{screening_workload_percentage:.2f}%"
)


# ============================================================
# OUTPUT FILES
# ============================================================

print("\n" + "=" * 70)
print("MODULE F OUTPUTS")
print("=" * 70)


print(
    "\nMetrics:"
)

print(
    OUTPUT_METRICS
)


print(
    "\nConfusion matrix:"
)

print(
    OUTPUT_CONFUSION
)


print(
    "\nComponent evaluation:"
)

print(
    OUTPUT_COMPONENTS
)


print(
    "\nPlots:"
)

print(
    PLOT_DIR
)


# ============================================================
# IMPORTANT EVALUATION NOTE
# ============================================================

print("\n" + "=" * 70)
print("IMPORTANT")
print("=" * 70)


print(
    """
Module F uses actual future measurements and ground truth
ONLY for offline evaluation.

These values are NOT used by Module A, B, C, D or E
to make early-screening decisions.

Metrics represent performance on the supplied dataset
and should NOT be interpreted as ISRO-qualified
engineering performance.
"""
)


print("\n" + "=" * 70)
print("MODULE F COMPLETED")
print("=" * 70)