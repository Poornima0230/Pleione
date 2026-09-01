# ============================================================
# SIH 26170
# MODULE B: TIME-SERIES DRIFT PREDICTOR
#
# PURPOSE
# ------------------------------------------------------------
# Predict future 168h Iddq behavior using ONLY early
# burn-in measurements available at 0h and 24h.
#
# MAIN PIPELINE
#
#       0h + 24h
#           |
#           v
#    ML Prediction Model
#           |
#           v
#     Predict 168h Iddq
#           |
#           v
#      Estimate Drift
#           |
#           +----------------------+
#           |                      |
#           v                      v
#   Dynamic Safety Slope     Absolute Limit
#           |                      |
#           +----------+-----------+
#                      |
#                      v
#              Risk Decision
#                      |
#            +---------+---------+
#            |         |         |
#           NORMAL   EARLY    PREDICTED
#                    DRIFT     FAILURE
#
#
# MODELS
# ------------------------------------------------------------
# 1. Linear Regression
# 2. Random Forest Regressor
# 3. HistGradientBoosting Regressor
#
#
# DATA SPLIT
# ------------------------------------------------------------
# Training      : 60%
# Calibration   : 20%
# Final Testing : 20%
#
#
# IMPORTANT
# ------------------------------------------------------------
# Actual 168h measurements are NEVER used as model inputs.
#
# Actual 168h values are used only for:
# - supervised training target
# - evaluation
# - reference drift calculation
# - uncertainty calibration
# - post-prediction validation
#
#
# SAFETY NOTE
# ------------------------------------------------------------
# Dynamic safety slope is a PROTOTYPE statistical boundary.
# It is NOT an ISRO-qualified aerospace engineering limit.
# ============================================================


# ============================================================
# IMPORTS
# ============================================================

import os
import joblib

import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split

from sklearn.linear_model import LinearRegression

from sklearn.ensemble import (
    RandomForestRegressor,
    HistGradientBoostingRegressor
)

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score
)


# ============================================================
# CONFIGURATION
# ============================================================

FILE_PATH = "data/sih_26170_burn_in_synthetic_dataset.csv"

OUTPUT_PATH = "data/module_B_drift_predictions.csv"

MODEL_PATH = "data/module_B_model.pkl"

RANDOM_STATE = 42

TEST_SIZE = 0.20

# 20% calibration from total dataset.
# Development set = 80%.
# Therefore calibration fraction inside development set:
#
# 20 / 80 = 0.25
#
CALIBRATION_FRACTION = 0.25

# Prototype dynamic safety boundary
SAFETY_PERCENTILE = 95

# Prediction interval confidence
PREDICTION_INTERVAL_CONFIDENCE = 0.90

# Reference population
REFERENCE_CLASSES = [
    "Normal",
    "High_Stable"
]

# Classes treated as abnormal for binary risk evaluation
#
# NOTE:
# High_Stable is retained here to preserve your original
# evaluation logic.
#
ABNORMAL_CLASSES = [
    "High_Stable",
    "Latent_Defect",
    "Absolute_Failure",
    "Sudden_Anomaly"
]


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("SIH 26170")
print("MODULE B: TIME-SERIES DRIFT PREDICTOR")
print("=" * 70)


# ============================================================
# STEP 1: LOAD DATASET
# ============================================================

df = pd.read_csv(FILE_PATH)

print("\nDataset loaded successfully.")

print(
    f"Number of components: {len(df)}"
)

print(
    f"Number of columns: {len(df.columns)}"
)


# ============================================================
# STEP 2: REQUIRED COLUMNS
# ============================================================

required_columns = [

    "component_id",

    "lot_id",

    "ground_truth",

    "absolute_limit_uA",

    "iddq_0h_uA",

    "iddq_24h_uA",

    "iddq_168h_uA"

]


missing_columns = [

    column

    for column in required_columns

    if column not in df.columns

]


if missing_columns:

    raise ValueError(

        "Missing required columns: "
        + str(missing_columns)

    )


# ============================================================
# STEP 3: DEFINE INPUT FEATURES
# ============================================================

input_features = [

    "iddq_0h_uA",

    "iddq_24h_uA"

]


target = "iddq_168h_uA"


print("\nInput features:")

for feature in input_features:

    print(
        " -",
        feature
    )


print("\nPrediction target:")

print(
    " -",
    target
)


# ============================================================
# STEP 4: DATA VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("DATA VALIDATION")
print("=" * 70)


print("\nMissing values:")

print(

    df[
        input_features + [target]
    ].isnull().sum()

)


print("\nDuplicate component IDs:")

print(

    df[
        "component_id"
    ].duplicated().sum()

)


print("\nNumber of lots:")

print(

    df[
        "lot_id"
    ].nunique()

)


print("\nGround-truth distribution:")

print(

    df[
        "ground_truth"
    ].value_counts()

)


# ============================================================
# STEP 5: CLEAN NUMERIC DATA
# ============================================================

X = df[
    input_features
].copy()


y = df[
    target
].copy()


# Replace infinity

X = X.replace(

    [np.inf, -np.inf],

    np.nan

)


y = y.replace(

    [np.inf, -np.inf],

    np.nan

)


# Keep only valid rows

valid_rows = (

    X.notnull().all(axis=1)

    &

    y.notnull()

)


X = X.loc[
    valid_rows
].copy()


y = y.loc[
    valid_rows
].copy()


df = df.loc[
    valid_rows
].copy()


# Reset indices so that positional indexing is safe

df = df.reset_index(
    drop=True
)

X = X.reset_index(
    drop=True
)

y = y.reset_index(
    drop=True
)


print(
    "\nValid samples:",
    len(df)
)


# ============================================================
# STEP 6: CREATE ACTUAL ABNORMAL LABEL
# ============================================================
#
# IMPORTANT:
# Create this BEFORE creating test_evaluation_df.
#
# This fixes the KeyError:
#
#     'actual_abnormal'
#
# ============================================================

df["actual_abnormal"] = (

    df[
        "ground_truth"
    ].isin(
        ABNORMAL_CLASSES
    )

)


# ============================================================
# STEP 7: STRATIFIED TRAIN / CALIBRATION / TEST SPLIT
# ============================================================

indices = np.arange(
    len(df)
)


stratification_labels = (

    df[
        "ground_truth"
    ]

)


# ------------------------------------------------------------
# FIRST SPLIT
#
# 80% development
# 20% final test
# ------------------------------------------------------------

development_indices, test_indices = train_test_split(

    indices,

    test_size=TEST_SIZE,

    random_state=RANDOM_STATE,

    stratify=stratification_labels

)


# ------------------------------------------------------------
# SECOND SPLIT
#
# 75% of development -> training
# 25% of development -> calibration
#
# Total:
#
# Training      = 60%
# Calibration   = 20%
# Testing       = 20%
# ------------------------------------------------------------

development_labels = (

    df.iloc[
        development_indices
    ][
        "ground_truth"
    ]

)


train_indices, calibration_indices = train_test_split(

    development_indices,

    test_size=CALIBRATION_FRACTION,

    random_state=RANDOM_STATE,

    stratify=development_labels

)


# ============================================================
# CREATE DATA SPLITS
# ============================================================

X_train = X.iloc[
    train_indices
].copy()


y_train = y.iloc[
    train_indices
].copy()


X_calibration = X.iloc[
    calibration_indices
].copy()


y_calibration = y.iloc[
    calibration_indices
].copy()


X_test = X.iloc[
    test_indices
].copy()


y_test = y.iloc[
    test_indices
].copy()


print("\n" + "=" * 70)
print("DATA SPLIT")
print("=" * 70)


print(
    f"\nTraining samples    : {len(X_train)}"
)


print(
    f"Calibration samples : {len(X_calibration)}"
)


print(
    f"Testing samples     : {len(X_test)}"
)


# ============================================================
# STEP 8: DEFINE MODELS
# ============================================================

models = {

    "Linear Regression":

        LinearRegression(),


    "Random Forest":

        RandomForestRegressor(

            n_estimators=400,

            max_depth=12,

            min_samples_leaf=3,

            random_state=RANDOM_STATE,

            n_jobs=-1

        ),


    "Gradient Boosting":

        HistGradientBoostingRegressor(

            max_iter=300,

            learning_rate=0.05,

            max_leaf_nodes=15,

            random_state=RANDOM_STATE

        )

}


# ============================================================
# STEP 9: TRAIN MODELS
# ============================================================

results = []

trained_models = {}

calibration_predictions = {}


print("\n" + "=" * 70)
print("MODEL COMPARISON")
print("=" * 70)


for name, model in models.items():

    print(
        f"\nTraining: {name}"
    )


    # --------------------------------------------------------
    # Train
    # --------------------------------------------------------

    model.fit(

        X_train,

        y_train

    )


    # --------------------------------------------------------
    # Calibration prediction
    # --------------------------------------------------------

    calibration_prediction = (

        model.predict(
            X_calibration
        )

    )


    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    calibration_mae = mean_absolute_error(

        y_calibration,

        calibration_prediction

    )


    calibration_rmse = np.sqrt(

        mean_squared_error(

            y_calibration,

            calibration_prediction

        )

    )


    calibration_r2 = r2_score(

        y_calibration,

        calibration_prediction

    )


    results.append({

        "Model":
            name,

        "Calibration_MAE":
            calibration_mae,

        "Calibration_RMSE":
            calibration_rmse,

        "Calibration_R2":
            calibration_r2

    })


    trained_models[
        name
    ] = model


    calibration_predictions[
        name
    ] = calibration_prediction


    print(
        f"MAE : {calibration_mae:.4f} µA"
    )


    print(
        f"RMSE: {calibration_rmse:.4f} µA"
    )


    print(
        f"R²  : {calibration_r2:.4f}"
    )


# ============================================================
# STEP 10: MODEL COMPARISON TABLE
# ============================================================

results_df = pd.DataFrame(
    results
)


results_df = results_df.sort_values(

    "Calibration_MAE"

)


print("\n" + "=" * 70)
print("MODEL PERFORMANCE")
print("=" * 70)


print(

    results_df.to_string(
        index=False
    )

)


# ============================================================
# STEP 11: SELECT BEST MODEL
# ============================================================

best_model_name = (

    results_df
    .iloc[0]
    ["Model"]

)


best_model = (

    trained_models[
        best_model_name
    ]

)


print("\n" + "=" * 70)

print(
    "BEST MODEL:",
    best_model_name
)

print("=" * 70)


# ============================================================
# STEP 12: PREDICTION UNCERTAINTY CALIBRATION
# ============================================================

print("\n" + "=" * 70)
print("PREDICTION UNCERTAINTY CALIBRATION")
print("=" * 70)


best_calibration_prediction = (

    calibration_predictions[
        best_model_name
    ]

)


calibration_absolute_errors = np.abs(

    y_calibration.to_numpy()

    -

    best_calibration_prediction

)


alpha = (

    1
    -
    PREDICTION_INTERVAL_CONFIDENCE

)


n_calibration = len(

    calibration_absolute_errors

)


# Finite-sample adjusted conformal-style quantile

conformal_quantile_level = min(

    1.0,

    np.ceil(

        (n_calibration + 1)

        *

        (1 - alpha)

    )
    /

    n_calibration

)


prediction_interval_radius = np.quantile(

    calibration_absolute_errors,

    conformal_quantile_level

)


print(

    f"\nPrediction interval confidence: "
    f"{PREDICTION_INTERVAL_CONFIDENCE * 100:.0f}%"

)


print(

    f"Prediction interval radius: "
    f"±{prediction_interval_radius:.4f} µA"

)


# ============================================================
# STEP 13: DYNAMIC SAFETY SLOPE
# ============================================================

print("\n" + "=" * 70)
print("DYNAMIC SAFETY SLOPE")
print("=" * 70)


# IMPORTANT:
#
# Safety slope is calculated ONLY from training data.
#

training_reference_df = (

    df.iloc[
        train_indices
    ].copy()

)


training_reference_df = (

    training_reference_df[

        training_reference_df[
            "ground_truth"
        ].isin(
            REFERENCE_CLASSES
        )

    ].copy()

)


print(

    "\nReference population:",
    len(training_reference_df)

)


print(
    "\nReference classes:"
)


print(

    training_reference_df[
        "ground_truth"
    ].value_counts()

)


if len(training_reference_df) == 0:

    raise ValueError(

        "No reference components available "
        "for dynamic safety slope calculation."

    )


# ------------------------------------------------------------
# Calculate reference drift rate
# ------------------------------------------------------------

training_reference_drift_rate = (

    training_reference_df[
        "iddq_168h_uA"
    ]

    -

    training_reference_df[
        "iddq_0h_uA"
    ]

) / 168


# ------------------------------------------------------------
# Calculate safety slope
# ------------------------------------------------------------

safety_slope = np.percentile(

    training_reference_drift_rate,

    SAFETY_PERCENTILE

)


print(

    f"\nSafety percentile: "
    f"{SAFETY_PERCENTILE}th"

)


print(

    f"Dynamic safety slope: "
    f"{safety_slope:.6f} µA/hour"

)


print("\nNOTE:")

print(

    "This is a prototype statistical boundary."

)


print(

    "It is NOT an ISRO-qualified engineering limit."

)


# ============================================================
# STEP 14: ADD SAFETY SLOPE TO DATAFRAME
# ============================================================
#
# IMPORTANT:
#
# This is done BEFORE the TOP EARLY-RISK section.
#
# This fixes the previous:
#
# KeyError: ['safety_slope'] not in index
#
# ============================================================

df["safety_slope"] = float(
    safety_slope
)


# ============================================================
# STEP 15: GENERATE PREDICTIONS
# ============================================================

df["predicted_168h_uA"] = (

    best_model.predict(

        df[
            input_features
        ]

    )

)


# ============================================================
# STEP 16: PREDICTION INTERVAL
# ============================================================

df["prediction_lower_uA"] = (

    df[
        "predicted_168h_uA"
    ]

    -

    prediction_interval_radius

)


df["prediction_upper_uA"] = (

    df[
        "predicted_168h_uA"
    ]

    +

    prediction_interval_radius

)


# ============================================================
# STEP 17: PREDICTION ERROR
# ============================================================

df["prediction_error_uA"] = (

    df[
        "predicted_168h_uA"
    ]

    -

    df[
        "iddq_168h_uA"
    ]

)


df["absolute_prediction_error_uA"] = (

    df[
        "prediction_error_uA"
    ].abs()

)


# ============================================================
# STEP 18: PREDICTED DRIFT
# ============================================================

df["predicted_drift_uA"] = (

    df[
        "predicted_168h_uA"
    ]

    -

    df[
        "iddq_0h_uA"
    ]

)


df["predicted_drift_rate"] = (

    df[
        "predicted_drift_uA"
    ]

    /

    168

)


# ============================================================
# STEP 19: PREDICTED RELATIVE DRIFT
# ============================================================

df["predicted_relative_drift"] = np.where(

    df[
        "iddq_0h_uA"
    ] != 0,

    (

        df[
            "predicted_168h_uA"
        ]

        -

        df[
            "iddq_0h_uA"
        ]

    )

    /

    df[
        "iddq_0h_uA"
    ],

    0

)


# ============================================================
# STEP 20: ACTUAL DRIFT
# ============================================================

df["actual_drift_uA"] = (

    df[
        "iddq_168h_uA"
    ]

    -

    df[
        "iddq_0h_uA"
    ]

)


df["actual_drift_rate"] = (

    df[
        "actual_drift_uA"
    ]

    /

    168

)


# ============================================================
# STEP 21: DRIFT SLOPE EXCESS
# ============================================================

df["drift_slope_excess"] = (

    df[
        "predicted_drift_rate"
    ]

    -

    df[
        "safety_slope"
    ]

)


# ============================================================
# STEP 22: EARLY DRIFT FLAG
# ============================================================

df["early_drift_flag"] = (

    df[
        "predicted_drift_rate"
    ]

    >

    df[
        "safety_slope"
    ]

)


# ============================================================
# STEP 23: STATIC LIMIT CHECK
# ============================================================

df["predicted_limit_exceeded"] = (

    df[
        "predicted_168h_uA"
    ]

    >

    df[
        "absolute_limit_uA"
    ]

)


# ============================================================
# STEP 24: UNCERTAINTY-ADJUSTED FAILURE
# ============================================================

df["uncertainty_adjusted_failure"] = (

    df[
        "prediction_upper_uA"
    ]

    >

    df[
        "absolute_limit_uA"
    ]

)


# ============================================================
# STEP 25: LIMIT MARGINS
# ============================================================

df["limit_margin_uA"] = (

    df[
        "absolute_limit_uA"
    ]

    -

    df[
        "predicted_168h_uA"
    ]

)


df["upper_bound_limit_margin_uA"] = (

    df[
        "absolute_limit_uA"
    ]

    -

    df[
        "prediction_upper_uA"
    ]

)


# ============================================================
# STEP 26: FUTURE DRIFT RISK
# ============================================================

def calculate_drift_risk(row):

    slope = row[
        "predicted_drift_rate"
    ]


    if (

        row[
            "uncertainty_adjusted_failure"
        ]

        or

        row[
            "predicted_limit_exceeded"
        ]

    ):

        return "HIGH"


    elif (

        slope

        >

        row[
            "safety_slope"
        ]

    ):

        return "MEDIUM"


    elif (

        slope

        >

        row[
            "safety_slope"
        ] * 0.80

    ):

        return "WATCH"


    else:

        return "LOW"


df["future_drift_risk"] = df.apply(

    calculate_drift_risk,

    axis=1

)


# ============================================================
# STEP 27: FINAL MODULE B DECISION
# ============================================================

def module_b_decision(row):

    # --------------------------------------------------------
    # Highest priority:
    # uncertainty-adjusted failure
    # --------------------------------------------------------

    if row[
        "uncertainty_adjusted_failure"
    ]:

        return "PREDICTED_FAILURE"


    # --------------------------------------------------------
    # Point prediction failure
    # --------------------------------------------------------

    elif row[
        "predicted_limit_exceeded"
    ]:

        return "PREDICTED_FAILURE"


    # --------------------------------------------------------
    # Dynamic drift risk
    # --------------------------------------------------------

    elif row[
        "early_drift_flag"
    ]:

        return "EARLY_DRIFT_RISK"


    # --------------------------------------------------------
    # Normal
    # --------------------------------------------------------

    else:

        return "NORMAL"


df["module_b_status"] = df.apply(

    module_b_decision,

    axis=1

)


# ============================================================
# STEP 28: EXPLANATION
# ============================================================

def module_b_explanation(row):

    reasons = []


    if row[
        "predicted_limit_exceeded"
    ]:

        reasons.append(

            "Point prediction exceeds absolute "
            "specification limit"

        )


    if row[
        "uncertainty_adjusted_failure"
    ]:

        reasons.append(

            "Prediction uncertainty interval "
            "reaches or exceeds absolute limit"

        )


    if row[
        "early_drift_flag"
    ]:

        reasons.append(

            "Predicted future drift exceeds "
            "dynamic safety boundary"

        )


    if (

        row[
            "early_drift_flag"
        ]

        and

        not row[
            "predicted_limit_exceeded"
        ]

    ):

        reasons.append(

            "Component is below static limit "
            "but shows abnormal future drift"

        )


    if len(reasons) == 0:

        return (

            "Predicted 168h behavior remains "
            "within the dynamic safety boundary."

        )


    return "; ".join(
        reasons
    )


df["module_b_explanation"] = df.apply(

    module_b_explanation,

    axis=1

)


# ============================================================
# STEP 29: FINAL TEST SET EVALUATION
# ============================================================

print("\n" + "=" * 70)
print("FINAL TEST SET PERFORMANCE")
print("=" * 70)


test_prediction = (

    best_model.predict(
        X_test
    )

)


test_mae = mean_absolute_error(

    y_test,

    test_prediction

)


test_rmse = np.sqrt(

    mean_squared_error(

        y_test,

        test_prediction

    )

)


test_r2 = r2_score(

    y_test,

    test_prediction

)


print(

    f"\nTest MAE : "
    f"{test_mae:.4f} µA"

)


print(

    f"Test RMSE: "
    f"{test_rmse:.4f} µA"

)


print(

    f"Test R²  : "
    f"{test_r2:.4f}"

)


# ============================================================
# STEP 30: TEST ERROR PERCENTILES
# ============================================================

test_absolute_errors = np.abs(

    y_test.to_numpy()

    -

    test_prediction

)


print("\nTest prediction error percentiles:")


print(

    f"50th percentile : "
    f"{np.percentile(test_absolute_errors, 50):.4f} µA"

)


print(

    f"90th percentile : "
    f"{np.percentile(test_absolute_errors, 90):.4f} µA"

)


print(

    f"95th percentile : "
    f"{np.percentile(test_absolute_errors, 95):.4f} µA"

)


# ============================================================
# STEP 31: CREATE TEST EVALUATION DATAFRAME
# ============================================================
#
# IMPORTANT:
#
# actual_abnormal has ALREADY been created in df.
#
# Therefore test_evaluation_df now contains it.
#
# ============================================================

test_evaluation_df = (

    df.iloc[
        test_indices
    ].copy()

)


# ============================================================
# STEP 32: TEST ERROR BY GROUND-TRUTH CLASS
# ============================================================

print("\n" + "=" * 70)
print("TEST-SET PREDICTION ERROR BY COMPONENT TYPE")
print("=" * 70)


class_results = []


for component_type, group in (

    test_evaluation_df.groupby(
        "ground_truth"
    )

):

    class_mae = mean_absolute_error(

        group[
            "iddq_168h_uA"
        ],

        group[
            "predicted_168h_uA"
        ]

    )


    class_rmse = np.sqrt(

        mean_squared_error(

            group[
                "iddq_168h_uA"
            ],

            group[
                "predicted_168h_uA"
            ]

        )

    )


    class_results.append({

        "Component Type":
            component_type,

        "Count":
            len(group),

        "MAE":
            class_mae,

        "RMSE":
            class_rmse

    })


class_results_df = pd.DataFrame(

    class_results

)


print(

    class_results_df.to_string(
        index=False
    )

)


# ============================================================
# STEP 33: LATENT DEFECT ANALYSIS
# ============================================================

print("\n" + "=" * 70)
print("LATENT DEFECT ANALYSIS")
print("=" * 70)


latent_df = df[

    df[
        "ground_truth"
    ]

    ==

    "Latent_Defect"

].copy()


print(

    "\nTotal latent defects:",
    len(latent_df)

)


# ------------------------------------------------------------
# Actual 168h value below static limit
# ------------------------------------------------------------

latent_below_limit = latent_df[

    latent_df[
        "iddq_168h_uA"
    ]

    <=

    latent_df[
        "absolute_limit_uA"
    ]

].copy()


print(

    "\nLatent defects below static limit:",
    len(latent_below_limit)

)


# ------------------------------------------------------------
# Dynamic detection
# ------------------------------------------------------------

latent_dynamic_detected = (

    latent_below_limit[
        "early_drift_flag"
    ]

    ==

    True

).sum()


if len(latent_below_limit) > 0:

    latent_detection_rate = (

        latent_dynamic_detected

        /

        len(latent_below_limit)

    ) * 100

else:

    latent_detection_rate = 0


print(

    "\nLatent defects dynamically detected:",
    latent_dynamic_detected

)


print(

    f"Dynamic latent-defect detection rate: "
    f"{latent_detection_rate:.2f}%"

)


# ============================================================
# STEP 34: UNSEEN TEST-SET LATENT DEFECT ANALYSIS
# ============================================================

test_latent = test_evaluation_df[

    test_evaluation_df[
        "ground_truth"
    ]

    ==

    "Latent_Defect"

].copy()


test_latent_below_limit = test_latent[

    test_latent[
        "iddq_168h_uA"
    ]

    <=

    test_latent[
        "absolute_limit_uA"
    ]

].copy()


test_latent_detected = (

    test_latent_below_limit[
        "early_drift_flag"
    ]

    ==

    True

).sum()


if len(test_latent_below_limit) > 0:

    test_latent_detection_rate = (

        test_latent_detected

        /

        len(test_latent_below_limit)

    ) * 100

else:

    test_latent_detection_rate = 0


print("\n" + "-" * 70)
print("UNSEEN TEST-SET LATENT DEFECT DETECTION")
print("-" * 70)


print(

    f"\nTest latent defects below limit: "
    f"{len(test_latent_below_limit)}"

)


print(

    f"Detected dynamically: "
    f"{test_latent_detected}"

)


print(

    f"Detection rate: "
    f"{test_latent_detection_rate:.2f}%"

)


# ============================================================
# STEP 35: TEST-SET RISK CLASSIFICATION
# ============================================================
#
# IMPORTANT:
#
# Evaluate classification ONLY on the unseen test set.
#
# This is more honest than evaluating the entire dataset.
#
# ============================================================

print("\n" + "=" * 70)
print("TEST-SET RISK CLASSIFICATION")
print("=" * 70)


test_actual_binary = (

    test_evaluation_df[
        "actual_abnormal"
    ].astype(int)

)


test_predicted_binary = (

    test_evaluation_df[
        "module_b_predicted_risk"
    ].astype(int)

    if
    "module_b_predicted_risk"
    in
    test_evaluation_df.columns

    else

    (
        test_evaluation_df[
            "module_b_status"
        ]

        !=

        "NORMAL"

    ).astype(int)

)


# Store predicted risk explicitly

test_evaluation_df[
    "module_b_predicted_risk"
] = (

    test_evaluation_df[
        "module_b_status"
    ]

    !=

    "NORMAL"

)


test_predicted_binary = (

    test_evaluation_df[
        "module_b_predicted_risk"
    ].astype(int)

)


classification_precision = precision_score(

    test_actual_binary,

    test_predicted_binary,

    zero_division=0

)


classification_recall = recall_score(

    test_actual_binary,

    test_predicted_binary,

    zero_division=0

)


classification_f1 = f1_score(

    test_actual_binary,

    test_predicted_binary,

    zero_division=0

)


cm = confusion_matrix(

    test_actual_binary,

    test_predicted_binary

)


print(

    f"\nTest Precision: "
    f"{classification_precision:.4f}"

)


print(

    f"Test Recall   : "
    f"{classification_recall:.4f}"

)


print(

    f"Test F1 Score : "
    f"{classification_f1:.4f}"

)


print("\nTest Confusion Matrix:")


print(cm)


# ============================================================
# STEP 36: FALSE NEGATIVE ANALYSIS
# ============================================================
#
# Only the unseen test set is used.
#
# ============================================================

test_false_negatives = test_evaluation_df[

    test_evaluation_df[
        "actual_abnormal"
    ]

    &

    (
        ~test_evaluation_df[
            "module_b_predicted_risk"
        ]
    )

].copy()


print("\n" + "=" * 70)
print("TEST-SET FALSE NEGATIVE ANALYSIS")
print("=" * 70)


print(

    "\nActual abnormal components:",
    test_evaluation_df[
        "actual_abnormal"
    ].sum()

)


print(

    "Abnormal components flagged:",
    test_evaluation_df[
        "module_b_predicted_risk"
    ].sum()

)


print(

    "Potential false negatives:",
    len(test_false_negatives)

)


# ============================================================
# STEP 37: FULL DATASET FALSE NEGATIVES
# ============================================================
#
# Keep a separate full-dataset analysis for debugging/
# prototype monitoring.
#
# ============================================================

false_negatives = df[

    df[
        "actual_abnormal"
    ]

    &

    (
        ~(
            df[
                "module_b_status"
            ]

            !=

            "NORMAL"

        )

    )

].copy()


# ============================================================
# STEP 38: MODULE B STATUS SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("MODULE B STATUS SUMMARY")
print("=" * 70)


print(

    df[
        "module_b_status"
    ].value_counts()

)


# ============================================================
# STEP 39: FUTURE DRIFT RISK SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("FUTURE DRIFT RISK")
print("=" * 70)


print(

    df[
        "future_drift_risk"
    ].value_counts()

)


# ============================================================
# STEP 40: PREDICTED LIMIT SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("PREDICTED LIMIT ANALYSIS")
print("=" * 70)


print(
    "\nPoint prediction exceeds limit:"
)


print(

    df[
        "predicted_limit_exceeded"
    ].value_counts()

)


print(

    "\nUncertainty-adjusted prediction exceeds limit:"

)


print(

    df[
        "uncertainty_adjusted_failure"
    ].value_counts()

)


# ============================================================
# STEP 41: TOP EARLY-RISK COMPONENTS
# ============================================================

print("\n" + "=" * 70)
print("TOP EARLY-RISK COMPONENTS")
print("=" * 70)


early_risk_components = (

    df[

        df[
            "module_b_status"
        ]

        !=

        "NORMAL"

    ][

        [

            "component_id",

            "lot_id",

            "ground_truth",

            "iddq_0h_uA",

            "iddq_24h_uA",

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

            "module_b_status",

            "module_b_explanation"

        ]

    ]

    .sort_values(

        "drift_slope_excess",

        ascending=False

    )

    .head(20)

)


if len(early_risk_components) > 0:

    print(

        early_risk_components.to_string(
            index=False
        )

    )

else:

    print(
        "No early-risk components detected."
    )


# ============================================================
# STEP 42: LATENT DEFECT EXAMPLES
# ============================================================

print("\n" + "=" * 70)
print("LATENT DEFECTS BELOW STATIC LIMIT")
print("=" * 70)


if len(latent_below_limit) > 0:

    latent_examples = (

        latent_below_limit[

            [

                "component_id",

                "lot_id",

                "iddq_0h_uA",

                "iddq_24h_uA",

                "predicted_168h_uA",

                "prediction_lower_uA",

                "prediction_upper_uA",

                "iddq_168h_uA",

                "absolute_limit_uA",

                "predicted_drift_rate",

                "drift_slope_excess",

                "early_drift_flag",

                "module_b_status"

            ]

        ]

        .sort_values(

            "drift_slope_excess",

            ascending=False

        )

        .head(20)

    )


    print(

        latent_examples.to_string(
            index=False
        )

    )

else:

    print(
        "No latent defects below static limit."
    )


# ============================================================
# STEP 43: TEST FALSE NEGATIVE EXAMPLES
# ============================================================

print("\n" + "=" * 70)
print("TEST-SET FALSE NEGATIVE EXAMPLES")
print("=" * 70)


if len(test_false_negatives) > 0:

    false_negative_examples = (

        test_false_negatives[

            [

                "component_id",

                "lot_id",

                "ground_truth",

                "iddq_0h_uA",

                "iddq_24h_uA",

                "predicted_168h_uA",

                "prediction_upper_uA",

                "iddq_168h_uA",

                "absolute_limit_uA",

                "predicted_drift_rate",

                "module_b_status"

            ]

        ]

        .head(20)

    )


    print(

        false_negative_examples.to_string(
            index=False
        )

    )

else:

    print(
        "No false negatives detected on final test set."
    )


# ============================================================
# STEP 44: SAVE MODEL PACKAGE
# ============================================================

os.makedirs(

    "data",

    exist_ok=True

)


model_package = {

    "model":
        best_model,

    "model_name":
        best_model_name,

    "input_features":
        input_features,

    "target":
        target,

    "safety_slope":
        float(safety_slope),

    "safety_percentile":
        SAFETY_PERCENTILE,

    "prediction_interval_confidence":
        PREDICTION_INTERVAL_CONFIDENCE,

    "prediction_interval_radius_uA":
        float(
            prediction_interval_radius
        ),

    "reference_classes":
        REFERENCE_CLASSES,

    "random_state":
        RANDOM_STATE

}


joblib.dump(

    model_package,

    MODEL_PATH

)


print("\n" + "=" * 70)
print("MODEL SAVED")
print("=" * 70)


print(

    f"\nModel saved to:\n"
    f"{MODEL_PATH}"

)


# ============================================================
# STEP 45: SAVE FINAL RESULTS
# ============================================================

df.to_csv(

    OUTPUT_PATH,

    index=False

)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("MODULE B COMPLETED")
print("=" * 70)


print(

    f"\nBest model:"
    f" {best_model_name}"

)


print(

    f"Test MAE:"
    f" {test_mae:.4f} µA"

)


print(

    f"Test RMSE:"
    f" {test_rmse:.4f} µA"

)


print(

    f"Test R²:"
    f" {test_r2:.4f}"

)


print(

    f"Dynamic safety slope:"
    f" {safety_slope:.6f} µA/hour"

)


print(

    f"Prediction interval:"
    f" ±{prediction_interval_radius:.4f} µA"

)


print(

    f"Test latent-defect detection rate:"
    f" {test_latent_detection_rate:.2f}%"

)


print(

    f"Test-set Precision:"
    f" {classification_precision:.4f}"

)


print(

    f"Test-set Recall:"
    f" {classification_recall:.4f}"

)


print(

    f"Test-set F1:"
    f" {classification_f1:.4f}"

)


print(

    f"Test-set potential false negatives:"
    f" {len(test_false_negatives)}"

)


print(

    f"\nResults saved to:"
    f"\n{OUTPUT_PATH}"

)


print(

    f"\nModel saved to:"
    f"\n{MODEL_PATH}"

)


print("\n" + "=" * 70)