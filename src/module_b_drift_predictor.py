# ============================================================
# SIH 26170
# MODULE B: MULTIVARIATE TIME-SERIES DRIFT PREDICTOR
#
# PURPOSE
# ------------------------------------------------------------
# Predict future 168h IDDQ behavior using early burn-in
# measurements available at 0h and 24h.
#
# INPUT FEATURES
# ------------------------------------------------------------
# 1. IDDQ @ 0h
# 2. IDDQ @ 24h
# 3. Temperature
# 4. Voltage
# 5. Component Type
#
# TARGET
# ------------------------------------------------------------
# IDDQ @ 168h
#
#
# CUMULATIVE PROCESSING
# ------------------------------------------------------------
#
# File 1                -> 2,000 components
# File 1 + File 2       -> 4,000 components
# File 1 + File 2 + 3   -> 6,000 components
# File 1 + ... + File 4 -> 8,000 components
# File 1 + ... + File 5 -> 10,000 components
#
#
# IMPORTANT
# ------------------------------------------------------------
# Actual 168h measurements are NEVER used as prediction
# INPUT FEATURES.
#
# Actual 168h is used only as:
# - supervised learning target
# - evaluation
# - validation
# - drift reference
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
import warnings

import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split

from sklearn.linear_model import LinearRegression

from sklearn.ensemble import (
    RandomForestRegressor,
    HistGradientBoostingRegressor
)

from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score
)

warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================

# ------------------------------------------------------------
# IMPORTANT:
# CHANGE THESE FIVE PATHS TO YOUR ACTUAL CSV FILES.
# ------------------------------------------------------------

CSV_FILES = [

    "data/batch_1.csv",

    "data/batch_2.csv",

    "data/batch_3.csv",

    "data/batch_4.csv",

    "data/batch_5.csv"

]


# ------------------------------------------------------------
# Output directory
# ------------------------------------------------------------

OUTPUT_DIR = "data/module_B"

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# ------------------------------------------------------------
# Final combined output
# ------------------------------------------------------------

FINAL_OUTPUT_PATH = os.path.join(

    OUTPUT_DIR,

    "module_B_drift_predictions.csv"

)


# ------------------------------------------------------------
# Model path
# ------------------------------------------------------------

MODEL_PATH = os.path.join(

    OUTPUT_DIR,

    "module_B_model.pkl"

)


# ------------------------------------------------------------
# Cumulative stage output
#
# These files allow you to demonstrate:
#
# 2000
# 4000
# 6000
# 8000
# 10000
#
# ------------------------------------------------------------

STAGE_OUTPUT_TEMPLATE = os.path.join(

    OUTPUT_DIR,

    "module_B_stage_{stage}_{count}.csv"

)


# ============================================================
# GENERAL CONFIGURATION
# ============================================================

RANDOM_STATE = 42

TEST_SIZE = 0.20

CALIBRATION_FRACTION = 0.25


# ------------------------------------------------------------
# Prediction horizon
# ------------------------------------------------------------
#
# DO NOT scatter 168 throughout the code.
#
# This makes the system configurable later.
#
# ------------------------------------------------------------

INPUT_HOURS = (

    0,

    24

)


TARGET_HOUR = 168


# ------------------------------------------------------------
# Safety configuration
# ------------------------------------------------------------

SAFETY_PERCENTILE = 95


PREDICTION_INTERVAL_CONFIDENCE = 0.90


# ------------------------------------------------------------
# Reference population
# ------------------------------------------------------------

REFERENCE_CLASSES = [

    "Normal",

    "High_Stable"

]


# ------------------------------------------------------------
# Abnormal classes
# ------------------------------------------------------------

ABNORMAL_CLASSES = [

    "High_Stable",

    "Latent_Defect",

    "Absolute_Failure",

    "Sudden_Anomaly"

]


# ============================================================
# POSSIBLE COLUMN NAMES
# ============================================================
#
# Since the exact temperature/voltage/component-type column
# names were not included in the code you sent, this module
# tries several common names automatically.
#
# If your columns use different names, add them here.
#
# ============================================================


COLUMN_ALIASES = {

    "component_id": [

        "component_id",

        "component",

        "componentID",

        "Component_ID",

        "ComponentID"

    ],


    "lot_id": [

        "lot_id",

        "lot",

        "Lot_ID",

        "LotID"

    ],


    "ground_truth": [

        "ground_truth",

        "Ground_Truth",

        "groundTruth",

        "label",

        "class"

    ],


    "component_type": [

        "component_type",

        "Component_Type",

        "componentType",

        "type",

        "Type",

        "device_type",

        "deviceType"

    ],


    "temperature": [

        "temperature",

        "Temperature",

        "temp",

        "Temp",

        "temperature_C",

        "temperature_c",

        "temp_C",

        "temp_c"

    ],


    "voltage": [

        "voltage",

        "Voltage",

        "voltage_V",

        "voltage_v",

        "VDD",

        "vdd",

        "supply_voltage"

    ],


    "absolute_limit_uA": [

        "absolute_limit_uA",

        "absolute_limit",

        "Absolute_Limit",

        "limit_uA",

        "iddq_limit_uA",

        "IDDQ_limit_uA"

    ],


    "iddq_0h_uA": [

        "iddq_0h_uA",

        "IDDQ_0h_uA",

        "iddq_0h",

        "IDDQ_0h"

    ],


    "iddq_24h_uA": [

        "iddq_24h_uA",

        "IDDQ_24h_uA",

        "iddq_24h",

        "IDDQ_24h"

    ],


    "iddq_168h_uA": [

        "iddq_168h_uA",

        "IDDQ_168h_uA",

        "iddq_168h",

        "IDDQ_168h"

    ]

}


# ============================================================
# HELPER: FIND COLUMN
# ============================================================

def find_column(
    df,
    logical_name,
    required=True
):

    # --------------------------------------------------------
    # First try aliases
    # --------------------------------------------------------

    aliases = COLUMN_ALIASES.get(

        logical_name,

        []

    )


    # Exact matching

    for column in aliases:

        if column in df.columns:

            return column


    # --------------------------------------------------------
    # Case-insensitive matching
    # --------------------------------------------------------

    lower_columns = {

        str(column).lower():
        column

        for column in df.columns

    }


    for alias in aliases:

        alias_lower = alias.lower()

        if alias_lower in lower_columns:

            return lower_columns[
                alias_lower
            ]


    # --------------------------------------------------------
    # Not found
    # --------------------------------------------------------

    if required:

        raise ValueError(

            f"\nCould not find column for '{logical_name}'.\n"

            f"Expected one of:\n"
            f"{aliases}\n\n"

            f"Available columns:\n"
            f"{list(df.columns)}"

        )


    return None


# ============================================================
# HEADER
# ============================================================

print("=" * 80)

print(
    "SIH 26170"
)

print(
    "MODULE B: MULTIVARIATE TIME-SERIES DRIFT PREDICTOR"
)

print("=" * 80)

print()

print(
    f"Prediction horizon: {TARGET_HOUR} hours"
)

print(
    f"Early observations: {INPUT_HOURS}"
)


# ============================================================
# STEP 1: LOAD ALL CSV FILES
# ============================================================

print("\n" + "=" * 80)

print(
    "LOADING CSV FILES"
)

print("=" * 80)


for index, file_path in enumerate(
    CSV_FILES,
    start=1
):

    if not os.path.exists(file_path):

        raise FileNotFoundError(

            f"\nCSV file not found:\n"
            f"{file_path}\n\n"
            f"Update CSV_FILES at the top of Module B."

        )

    print(

        f"File {index}: "
        f"{file_path}"

    )


# ============================================================
# STEP 2: READ FIRST FILE TO IDENTIFY COLUMNS
# ============================================================

first_df = pd.read_csv(

    CSV_FILES[0]

)


print("\nFirst CSV loaded.")

print(

    f"Rows: {len(first_df)}"

)

print(

    f"Columns: {len(first_df.columns)}"

)


# ============================================================
# STEP 3: RESOLVE COLUMN NAMES
# ============================================================

component_id_col = find_column(

    first_df,

    "component_id"

)


lot_id_col = find_column(

    first_df,

    "lot_id"

)


ground_truth_col = find_column(

    first_df,

    "ground_truth"

)


component_type_col = find_column(

    first_df,

    "component_type"

)


temperature_col = find_column(

    first_df,

    "temperature"

)


voltage_col = find_column(

    first_df,

    "voltage"

)


absolute_limit_col = find_column(

    first_df,

    "absolute_limit_uA"

)


iddq_0h_col = find_column(

    first_df,

    "iddq_0h_uA"

)


iddq_24h_col = find_column(

    first_df,

    "iddq_24h_uA"

)


iddq_168h_col = find_column(

    first_df,

    "iddq_168h_uA"

)


print("\n" + "=" * 80)

print(
    "COLUMN MAPPING"
)

print("=" * 80)


print(
    f"\nComponent ID     : {component_id_col}"
)

print(
    f"Lot ID           : {lot_id_col}"
)

print(
    f"Ground Truth     : {ground_truth_col}"
)

print(
    f"Component Type   : {component_type_col}"
)

print(
    f"Temperature      : {temperature_col}"
)

print(
    f"Voltage          : {voltage_col}"
)

print(
    f"Absolute Limit   : {absolute_limit_col}"
)

print(
    f"IDDQ 0h          : {iddq_0h_col}"
)

print(
    f"IDDQ 24h         : {iddq_24h_col}"
)

print(
    f"IDDQ 168h        : {iddq_168h_col}"
)


# ============================================================
# STEP 4: STANDARDIZE COLUMN NAMES
# ============================================================
#
# This lets the rest of the code use stable internal names.
#
# ============================================================

COLUMN_RENAME_MAP = {

    component_id_col:
        "component_id",

    lot_id_col:
        "lot_id",

    ground_truth_col:
        "ground_truth",

    component_type_col:
        "component_type",

    temperature_col:
        "temperature",

    voltage_col:
        "voltage",

    absolute_limit_col:
        "absolute_limit_uA",

    iddq_0h_col:
        "iddq_0h_uA",

    iddq_24h_col:
        "iddq_24h_uA",

    iddq_168h_col:
        "iddq_168h_uA"

}


# ============================================================
# STEP 5: FUNCTION TO LOAD AND STANDARDIZE A CSV
# ============================================================

def load_and_standardize_csv(
    file_path
):

    data = pd.read_csv(

        file_path

    )


    # --------------------------------------------------------
    # Resolve columns independently for each file
    # --------------------------------------------------------

    mapping = {

        find_column(
            data,
            logical_name
        ):
        logical_name

        for logical_name in [

            "component_id",

            "lot_id",

            "ground_truth",

            "component_type",

            "temperature",

            "voltage",

            "absolute_limit_uA",

            "iddq_0h_uA",

            "iddq_24h_uA",

            "iddq_168h_uA"

        ]

    }


    data = data.rename(

        columns=mapping

    )


    return data


# ============================================================
# STEP 6: PREPARE DATA FOR DRIFT PREDICTION
# ============================================================

def prepare_drift_data(
    data
):

    df_local = data.copy()


    # --------------------------------------------------------
    # Required model input columns
    # --------------------------------------------------------

    required = [

        "component_id",

        "component_type",

        "temperature",

        "voltage",

        "iddq_0h_uA",

        "iddq_24h_uA"

    ]


    # --------------------------------------------------------
    # 168h is required for supervised training/evaluation.
    #
    # Components without 168h can still conceptually be
    # predicted, but cannot be used to train this supervised
    # model.
    # --------------------------------------------------------

    for column in required:

        if column not in df_local.columns:

            raise ValueError(

                f"Required column missing: {column}"

            )


    # --------------------------------------------------------
    # Convert numerical fields
    # --------------------------------------------------------

    numerical_columns = [

        "temperature",

        "voltage",

        "iddq_0h_uA",

        "iddq_24h_uA",

        "iddq_168h_uA",

        "absolute_limit_uA"

    ]


    for column in numerical_columns:

        if column in df_local.columns:

            df_local[column] = pd.to_numeric(

                df_local[column],

                errors="coerce"

            )


    # --------------------------------------------------------
    # Replace infinity
    # --------------------------------------------------------

    df_local = df_local.replace(

        [np.inf, -np.inf],

        np.nan

    )


    # --------------------------------------------------------
    # Remove rows missing prediction inputs
    # --------------------------------------------------------

    prediction_required = [

        "component_id",

        "component_type",

        "temperature",

        "voltage",

        "iddq_0h_uA",

        "iddq_24h_uA"

    ]


    valid_prediction_rows = (

        df_local[
            prediction_required
        ]
        .notnull()
        .all(axis=1)

    )


    df_local = df_local.loc[

        valid_prediction_rows

    ].copy()


    # --------------------------------------------------------
    # actual_abnormal
    # --------------------------------------------------------

    df_local["actual_abnormal"] = (

        df_local[
            "ground_truth"
        ].isin(
            ABNORMAL_CLASSES
        )

    )


    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Keep only one row per component if duplicate component
    # records exist.
    #
    # If your five CSVs contain different observations for the
    # SAME component, this section must be changed to merge
    # time observations instead.
    #
    # Your stated architecture indicates each file contains
    # another batch of components, so duplicates are treated
    # as duplicates here.
    # --------------------------------------------------------

    duplicate_count = (

        df_local[
            "component_id"
        ].duplicated()
        .sum()

    )


    if duplicate_count > 0:

        print(

            f"\nWARNING: {duplicate_count} "
            f"duplicate component IDs detected."

        )


        df_local = (

            df_local
            .drop_duplicates(
                subset=["component_id"],
                keep="last"
            )
            .copy()

        )


    # --------------------------------------------------------
    # Reset index
    # --------------------------------------------------------

    df_local = df_local.reset_index(

        drop=True

    )


    return df_local


# ============================================================
# STEP 7: BUILD MODEL PIPELINE
# ============================================================

NUMERICAL_FEATURES = [

    "iddq_0h_uA",

    "iddq_24h_uA",

    "temperature",

    "voltage"

]


CATEGORICAL_FEATURES = [

    "component_type"

]


MODEL_FEATURES = (

    NUMERICAL_FEATURES

    +

    CATEGORICAL_FEATURES

)


TARGET = "iddq_168h_uA"


# ------------------------------------------------------------
# OneHotEncoder compatibility between sklearn versions
# ------------------------------------------------------------

try:

    encoder = OneHotEncoder(

        handle_unknown="ignore",

        sparse_output=False

    )

except TypeError:

    encoder = OneHotEncoder(

        handle_unknown="ignore",

        sparse=False

    )


preprocessor = ColumnTransformer(

    transformers=[

        (

            "numerical",

            "passthrough",

            NUMERICAL_FEATURES

        ),

        (

            "categorical",

            encoder,

            CATEGORICAL_FEATURES

        )

    ]

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
# STEP 9: RUN ONE CUMULATIVE STAGE
# ============================================================

def run_cumulative_stage(

    cumulative_df,

    stage_number

):

    print("\n")

    print("#" * 80)

    print(

        f"CUMULATIVE STAGE {stage_number}"

    )

    print("#" * 80)


    print(

        f"\nTotal cumulative components: "
        f"{len(cumulative_df)}"

    )


    # --------------------------------------------------------
    # Prepare data
    # --------------------------------------------------------

    df_stage = prepare_drift_data(

        cumulative_df

    )


    print(

        f"Prediction-eligible components: "
        f"{len(df_stage)}"

    )


    # --------------------------------------------------------
    # Supervised training requires actual 168h target.
    # --------------------------------------------------------

    training_valid = (

        df_stage[
            TARGET
        ].notnull()

    )


    model_df = df_stage.loc[

        training_valid

    ].copy()


    model_df = model_df.reset_index(

        drop=True

    )


    print(

        f"Components with 168h target: "
        f"{len(model_df)}"

    )


    if len(model_df) < 10:

        print(

            "\nNot enough samples for this stage."

        )

        return None


    # ========================================================
    # INPUT / TARGET
    # ========================================================

    X = model_df[
        MODEL_FEATURES
    ].copy()


    y = model_df[
        TARGET
    ].copy()


    # ========================================================
    # DATA SPLIT
    # ========================================================

    indices = np.arange(

        len(model_df)

    )


    labels = model_df[
        "ground_truth"
    ]


    # --------------------------------------------------------
    # Try stratified split.
    #
    # If a class has too few samples, fall back to random
    # split rather than crashing.
    # --------------------------------------------------------

    try:

        development_indices, test_indices = train_test_split(

            indices,

            test_size=TEST_SIZE,

            random_state=RANDOM_STATE,

            stratify=labels

        )

    except ValueError:

        print(

            "\nWARNING: Stratified test split could not "
            "be created. Using random split."

        )


        development_indices, test_indices = train_test_split(

            indices,

            test_size=TEST_SIZE,

            random_state=RANDOM_STATE

        )


    development_labels = (

        model_df.iloc[
            development_indices
        ][
            "ground_truth"
        ]

    )


    try:

        train_indices, calibration_indices = train_test_split(

            development_indices,

            test_size=CALIBRATION_FRACTION,

            random_state=RANDOM_STATE,

            stratify=development_labels

        )

    except ValueError:

        print(

            "\nWARNING: Stratified calibration split "
            "could not be created. Using random split."

        )


        train_indices, calibration_indices = train_test_split(

            development_indices,

            test_size=CALIBRATION_FRACTION,

            random_state=RANDOM_STATE

        )


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


    print("\nData split:")

    print(

        f"Training    : {len(X_train)}"

    )

    print(

        f"Calibration : {len(X_calibration)}"

    )

    print(

        f"Testing     : {len(X_test)}"

    )


    # ========================================================
    # TRAIN MODELS
    # ========================================================

    results = []

    trained_models = {}

    calibration_predictions = {}


    print("\n" + "-" * 80)

    print("MODEL COMPARISON")

    print("-" * 80)


    for name, model in models.items():

        print(

            f"\nTraining: {name}"

        )


        # ----------------------------------------------------
        # Complete preprocessing + model pipeline
        # ----------------------------------------------------

        pipeline = Pipeline(

            steps=[

                (

                    "preprocessor",

                    preprocessor

                ),

                (

                    "model",

                    model

                )

            ]

        )


        # ----------------------------------------------------
        # Train
        # ----------------------------------------------------

        pipeline.fit(

            X_train,

            y_train

        )


        # ----------------------------------------------------
        # Calibration prediction
        # ----------------------------------------------------

        calibration_prediction = (

            pipeline.predict(

                X_calibration

            )

        )


        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

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
        ] = pipeline


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


    # ========================================================
    # MODEL COMPARISON
    # ========================================================

    results_df = pd.DataFrame(

        results

    )


    results_df = results_df.sort_values(

        "Calibration_MAE"

    )


    print("\n" + "-" * 80)

    print("MODEL PERFORMANCE")

    print("-" * 80)


    print(

        results_df.to_string(
            index=False
        )

    )


    # ========================================================
    # BEST MODEL
    # ========================================================

    best_model_name = (

        results_df.iloc[0]["Model"]

    )


    best_model = (

        trained_models[
            best_model_name
        ]

    )


    print(

        f"\nBest model: {best_model_name}"

    )


    # ========================================================
    # UNCERTAINTY CALIBRATION
    # ========================================================

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


    # ========================================================
    # DYNAMIC SAFETY SLOPE
    # ========================================================

    training_reference_df = (

        model_df.iloc[
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


    if len(training_reference_df) == 0:

        print(

            "\nWARNING: No reference population found."

        )


        # Conservative fallback based on training drift

        training_reference_df = (

            model_df.iloc[
                train_indices
            ].copy()

        )


    training_reference_drift_rate = (

        training_reference_df[
            TARGET
        ]

        -

        training_reference_df[
            "iddq_0h_uA"
        ]

    ) / TARGET_HOUR


    safety_slope = np.percentile(

        training_reference_drift_rate,

        SAFETY_PERCENTILE

    )


    # ========================================================
    # PREDICT FOR ALL ELIGIBLE COMPONENTS
    # ========================================================

    prediction_df = df_stage.copy()


    prediction_X = prediction_df[
        MODEL_FEATURES
    ].copy()


    prediction_df[
        "predicted_168h_uA"
    ] = best_model.predict(

        prediction_X

    )


    # ========================================================
    # PREDICTION INTERVAL
    # ========================================================

    prediction_df[
        "prediction_lower_uA"
    ] = (

        prediction_df[
            "predicted_168h_uA"
        ]

        -

        prediction_interval_radius

    )


    prediction_df[
        "prediction_upper_uA"
    ] = (

        prediction_df[
            "predicted_168h_uA"
        ]

        +

        prediction_interval_radius

    )


    # ========================================================
    # PREDICTION ERROR
    # ========================================================

    prediction_df[
        "prediction_error_uA"
    ] = np.where(

        prediction_df[
            TARGET
        ].notnull(),

        prediction_df[
            "predicted_168h_uA"
        ]

        -

        prediction_df[
            TARGET
        ],

        np.nan

    )


    prediction_df[
        "absolute_prediction_error_uA"
    ] = (

        prediction_df[
            "prediction_error_uA"
        ].abs()

    )


    # ========================================================
    # PREDICTED DRIFT
    # ========================================================

    prediction_df[
        "predicted_drift_uA"
    ] = (

        prediction_df[
            "predicted_168h_uA"
        ]

        -

        prediction_df[
            "iddq_0h_uA"
        ]

    )


    prediction_df[
        "predicted_drift_rate"
    ] = (

        prediction_df[
            "predicted_drift_uA"
        ]

        /

        TARGET_HOUR

    )


    # ========================================================
    # RELATIVE DRIFT
    # ========================================================

    prediction_df[
        "predicted_relative_drift"
    ] = np.where(

        prediction_df[
            "iddq_0h_uA"
        ] != 0,

        (

            prediction_df[
                "predicted_168h_uA"
            ]

            -

            prediction_df[
                "iddq_0h_uA"
            ]

        )

        /

        prediction_df[
            "iddq_0h_uA"
        ],

        0

    )


    # ========================================================
    # ACTUAL DRIFT
    # ========================================================

    prediction_df[
        "actual_drift_uA"
    ] = np.where(

        prediction_df[
            TARGET
        ].notnull(),

        prediction_df[
            TARGET
        ]

        -

        prediction_df[
            "iddq_0h_uA"
        ],

        np.nan

    )


    prediction_df[
        "actual_drift_rate"
    ] = (

        prediction_df[
            "actual_drift_uA"
        ]

        /

        TARGET_HOUR

    )


    # ========================================================
    # SAFETY SLOPE
    # ========================================================

    prediction_df[
        "safety_slope"
    ] = float(

        safety_slope

    )


    prediction_df[
        "drift_slope_excess"
    ] = (

        prediction_df[
            "predicted_drift_rate"
        ]

        -

        prediction_df[
            "safety_slope"
        ]

    )


    # ========================================================
    # EARLY DRIFT FLAG
    # ========================================================

    prediction_df[
        "early_drift_flag"
    ] = (

        prediction_df[
            "predicted_drift_rate"
        ]

        >

        prediction_df[
            "safety_slope"
        ]

    )


    # ========================================================
    # STATIC LIMIT
    # ========================================================

    prediction_df[
        "predicted_limit_exceeded"
    ] = (

        prediction_df[
            "predicted_168h_uA"
        ]

        >

        prediction_df[
            "absolute_limit_uA"
        ]

    )


    # ========================================================
    # UNCERTAINTY-ADJUSTED FAILURE
    # ========================================================

    prediction_df[
        "uncertainty_adjusted_failure"
    ] = (

        prediction_df[
            "prediction_upper_uA"
        ]

        >

        prediction_df[
            "absolute_limit_uA"
        ]

    )


    # ========================================================
    # LIMIT MARGINS
    # ========================================================

    prediction_df[
        "limit_margin_uA"
    ] = (

        prediction_df[
            "absolute_limit_uA"
        ]

        -

        prediction_df[
            "predicted_168h_uA"
        ]

    )


    prediction_df[
        "upper_bound_limit_margin_uA"
    ] = (

        prediction_df[
            "absolute_limit_uA"
        ]

        -

        prediction_df[
            "prediction_upper_uA"
        ]

    )


    # ========================================================
    # FUTURE DRIFT RISK
    # ========================================================

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


        return "LOW"


    prediction_df[
        "future_drift_risk"
    ] = prediction_df.apply(

        calculate_drift_risk,

        axis=1

    )


    # ========================================================
    # MODULE B DECISION
    # ========================================================

    def module_b_decision(row):

        if row[
            "uncertainty_adjusted_failure"
        ]:

            return "PREDICTED_FAILURE"


        elif row[
            "predicted_limit_exceeded"
        ]:

            return "PREDICTED_FAILURE"


        elif row[
            "early_drift_flag"
        ]:

            return "EARLY_DRIFT_RISK"


        return "NORMAL"


    prediction_df[
        "module_b_status"
    ] = prediction_df.apply(

        module_b_decision,

        axis=1

    )


    # ========================================================
    # EXPLANATION
    # ========================================================

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


    prediction_df[
        "module_b_explanation"
    ] = prediction_df.apply(

        module_b_explanation,

        axis=1

    )


    # ========================================================
    # MODEL TEST PERFORMANCE
    # ========================================================

    test_prediction = best_model.predict(

        X_test

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


    # ========================================================
    # TEST EVALUATION
    # ========================================================

    test_evaluation_df = (

        prediction_df.iloc[
            test_indices
        ].copy()

    )


    test_actual_binary = (

        test_evaluation_df[
            "actual_abnormal"
        ].astype(int)

    )


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


    # ========================================================
    # PRINT STAGE RESULTS
    # ========================================================

    print("\n" + "=" * 80)

    print(

        f"STAGE {stage_number} RESULTS"

    )

    print("=" * 80)


    print(

        f"\nCumulative components:"
        f" {len(prediction_df)}"

    )


    print(

        f"Best model:"
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

        f"Safety slope:"
        f" {safety_slope:.6f} µA/hour"

    )


    print(

        f"Prediction interval:"
        f" ±{prediction_interval_radius:.4f} µA"

    )


    print("\nModule B status:")


    print(

        prediction_df[
            "module_b_status"
        ].value_counts()

    )


    print("\nFuture drift risk:")


    print(

        prediction_df[
            "future_drift_risk"
        ].value_counts()

    )


    print("\nTest classification:")


    print(

        f"Precision: "
        f"{classification_precision:.4f}"

    )


    print(

        f"Recall: "
        f"{classification_recall:.4f}"

    )


    print(

        f"F1: "
        f"{classification_f1:.4f}"

    )


    print("\nConfusion Matrix:")


    print(cm)


    # ========================================================
    # SAVE STAGE RESULT
    # ========================================================

    stage_count = len(

        prediction_df

    )


    stage_output_path = STAGE_OUTPUT_TEMPLATE.format(

        stage=stage_number,

        count=stage_count

    )


    prediction_df.to_csv(

        stage_output_path,

        index=False

    )


    print(

        f"\nStage output saved:"
        f"\n{stage_output_path}"

    )


    # ========================================================
    # RETURN EVERYTHING NEEDED
    # ========================================================

    return {

        "data":
            prediction_df,

        "model":
            best_model,

        "model_name":
            best_model_name,

        "safety_slope":
            float(safety_slope),

        "prediction_interval_radius":
            float(
                prediction_interval_radius
            ),

        "test_mae":
            float(test_mae),

        "test_rmse":
            float(test_rmse),

        "test_r2":
            float(test_r2),

        "precision":
            float(
                classification_precision
            ),

        "recall":
            float(
                classification_recall
            ),

        "f1":
            float(
                classification_f1
            )

    }


# ============================================================
# STEP 10: CUMULATIVE PROCESSING
# ============================================================

print("\n" + "=" * 80)

print(
    "STARTING CUMULATIVE PROCESSING"
)

print("=" * 80)


cumulative_df = pd.DataFrame()

stage_results = []


for stage_number, file_path in enumerate(

    CSV_FILES,

    start=1

):

    print("\n")

    print("#" * 80)

    print(

        f"READING BATCH {stage_number}"

    )

    print("#" * 80)


    # --------------------------------------------------------
    # Load current batch
    # --------------------------------------------------------

    batch_df = load_and_standardize_csv(

        file_path

    )


    print(

        f"\nBatch {stage_number} rows:"
        f" {len(batch_df)}"

    )


    # --------------------------------------------------------
    # Add current batch to cumulative dataset
    # --------------------------------------------------------

    cumulative_df = pd.concat(

        [

            cumulative_df,

            batch_df

        ],

        ignore_index=True

    )


    # --------------------------------------------------------
    # IMPORTANT:
    #
    # The prediction receives cumulative_df,
    # NOT batch_df.
    #
    # --------------------------------------------------------

    result = run_cumulative_stage(

        cumulative_df,

        stage_number

    )


    if result is not None:

        stage_results.append(

            result

        )


# ============================================================
# STEP 11: FINAL RESULT
# ============================================================

if len(stage_results) == 0:

    raise RuntimeError(

        "No valid Module B stage was completed."

    )


final_result = stage_results[-1]


final_df = final_result[
    "data"
]


# ============================================================
# STEP 12: SAVE FINAL RESULTS
# ============================================================

final_df.to_csv(

    FINAL_OUTPUT_PATH,

    index=False

)


# ============================================================
# STEP 13: SAVE FINAL MODEL PACKAGE
# ============================================================

model_package = {

    "model":
        final_result[
            "model"
        ],

    "model_name":
        final_result[
            "model_name"
        ],

    "input_features":
        MODEL_FEATURES,

    "numerical_features":
        NUMERICAL_FEATURES,

    "categorical_features":
        CATEGORICAL_FEATURES,

    "input_hours":
        INPUT_HOURS,

    "target_hour":
        TARGET_HOUR,

    "target":
        TARGET,

    "safety_slope":
        final_result[
            "safety_slope"
        ],

    "safety_percentile":
        SAFETY_PERCENTILE,

    "prediction_interval_confidence":
        PREDICTION_INTERVAL_CONFIDENCE,

    "prediction_interval_radius_uA":
        final_result[
            "prediction_interval_radius"
        ],

    "reference_classes":
        REFERENCE_CLASSES,

    "abnormal_classes":
        ABNORMAL_CLASSES,

    "random_state":
        RANDOM_STATE

}


joblib.dump(

    model_package,

    MODEL_PATH

)


# ============================================================
# STEP 14: FINAL SUMMARY
# ============================================================

print("\n")

print("=" * 80)

print(
    "MODULE B COMPLETED SUCCESSFULLY"
)

print("=" * 80)


print(

    "\nCUMULATIVE PROCESSING:"
)

print(

    "  Batch 1              → 2,000"

)

print(

    "  Batch 1 + 2          → 4,000"

)

print(

    "  Batch 1 + 2 + 3      → 6,000"

)

print(

    "  Batch 1 + ... + 4    → 8,000"

)

print(

    "  All 5 batches        → 10,000"

)


print("\nMODEL INPUTS:")


for feature in MODEL_FEATURES:

    print(

        f"  ✓ {feature}"

    )


print("\nPREDICTION:")


print(

    f"  {TARGET} "
    f"← early 0h + 24h observations"

)


print("\nFINAL MODEL:")


print(

    f"  {final_result['model_name']}"

)


print("\nFINAL TEST PERFORMANCE:")


print(

    f"  MAE  : "
    f"{final_result['test_mae']:.4f} µA"

)


print(

    f"  RMSE : "
    f"{final_result['test_rmse']:.4f} µA"

)


print(

    f"  R²   : "
    f"{final_result['test_r2']:.4f}"

)


print("\nFINAL OUTPUT:")


print(

    f"  {FINAL_OUTPUT_PATH}"

)


print("\nMODEL:")


print(

    f"  {MODEL_PATH}"

)


print("\n" + "=" * 80)










































# # ============================================================
# # SIH 26170
# # MODULE B: MULTIVARIATE TIME-SERIES / DRIFT PREDICTOR
# #
# # Pleione - AI-Driven Component Burn-In Anomaly Detection
# #
# # CUMULATIVE PROCESSING
# # ------------------------------------------------------------
# # Batch 1                  -> 2,000 components
# # Batch 1 + Batch 2        -> 4,000 components
# # Batch 1 + Batch 2 + 3    -> 6,000 components
# # Batch 1 + ... + Batch 4  -> 8,000 components
# # Batch 1 + ... + Batch 5  -> 10,000 components
# #
# # PREDICTION
# # ------------------------------------------------------------
# # Early observations:
# #   0h + 24h
# #
# # Features:
# #   component_type
# #   temperature_C
# #   voltage_V
# #   IDDQ 0h
# #   IDDQ 24h
# #   Leakage 0h
# #   Leakage 24h
# #
# # Target:
# #   IDDQ at configurable future horizon
# #
# # Default:
# #   168h
# #
# # IMPORTANT:
# #   168h actual value is NEVER used as an INPUT feature.
# #   It is used only as supervised training target / evaluation
# #   reference when available.
# # ============================================================

# import os
# import warnings
# import joblib
# import numpy as np
# import pandas as pd

# from sklearn.compose import ColumnTransformer
# from sklearn.ensemble import (
#     RandomForestRegressor,
#     HistGradientBoostingRegressor
# )
# from sklearn.impute import SimpleImputer
# from sklearn.linear_model import LinearRegression
# from sklearn.metrics import mean_absolute_error, mean_squared_error
# from sklearn.pipeline import Pipeline
# from sklearn.preprocessing import OneHotEncoder

# warnings.filterwarnings("ignore")


# # ============================================================
# # CONFIGURATION
# # ============================================================

# # Five cumulative input files
# CSV_FILES = [
#     "data/batch_1.csv",
#     "data/batch_2.csv",
#     "data/batch_3.csv",
#     "data/batch_4.csv",
#     "data/batch_5.csv",
# ]

# # Output directory
# OUTPUT_DIR = "data/module_B"

# # Final combined output
# FINAL_OUTPUT_PATH = os.path.join(
#     OUTPUT_DIR,
#     "module_B_drift_predictions.csv"
# )

# # Model package
# MODEL_PATH = os.path.join(
#     OUTPUT_DIR,
#     "module_B_model.pkl"
# )

# # ------------------------------------------------------------
# # Configurable prediction horizon
# # ------------------------------------------------------------
# #
# # Current requirement:
# #   168h
# #
# # Future possibilities:
# #   24h
# #   48h
# #   96h
# #   168h
# #
# TARGET_HOUR = 168


# # ============================================================
# # DATASET COLUMN DEFINITIONS
# # ============================================================

# COMPONENT_ID_COL = "component_id"
# LOT_ID_COL = "lot_id"
# COMPONENT_TYPE_COL = "component_type"

# TEMPERATURE_COL = "temperature_C"
# VOLTAGE_COL = "voltage_V"

# GROUND_TRUTH_COL = "ground_truth"
# LIMIT_COL = "absolute_limit_uA"


# # ------------------------------------------------------------
# # Early observations
# # ------------------------------------------------------------

# EARLY_FEATURES = [
#     "temperature_C",
#     "voltage_V",
#     "iddq_0h_uA",
#     "iddq_24h_uA",
#     "leakage_0h_uA",
#     "leakage_24h_uA",
#     "component_type",
# ]


# # ============================================================
# # TARGET COLUMN
# # ============================================================

# TARGET_COLUMNS = {
#     24: "iddq_24h_uA",
#     48: "iddq_48h_uA",
#     96: "iddq_96h_uA",
#     168: "iddq_168h_uA",
# }


# # ============================================================
# # CONSTANTS
# # ============================================================

# RANDOM_STATE = 42

# TRAIN_FRACTION = 0.60
# CALIBRATION_FRACTION = 0.20
# TEST_FRACTION = 0.20

# ABNORMAL_CLASSES = [
#     "High_Stable",
#     "Latent_Defect",
#     "Absolute_Failure",
#     "Sudden_Anomaly",
# ]

# SAFETY_REFERENCE_CLASSES = [
#     "Normal",
#     "High_Stable",
# ]


# # ============================================================
# # HELPER FUNCTIONS
# # ============================================================

# def print_section(title):
#     print("\n" + "=" * 70)
#     print(title)
#     print("=" * 70)


# def safe_numeric(df, columns):
#     """
#     Convert selected columns to numeric.
#     Invalid values become NaN.
#     """
#     for col in columns:
#         if col in df.columns:
#             df[col] = pd.to_numeric(df[col], errors="coerce")

#     return df


# def calculate_rmse(y_true, y_pred):
#     return np.sqrt(mean_squared_error(y_true, y_pred))


# # ============================================================
# # LOAD ONE CSV
# # ============================================================

# def load_csv(file_path):
#     """
#     Load and validate one burn-in CSV.
#     """

#     if not os.path.exists(file_path):
#         raise FileNotFoundError(
#             f"\nCSV file not found:\n{file_path}\n"
#             f"Please verify the file path."
#         )

#     print(f"\nLoading: {file_path}")

#     df = pd.read_csv(file_path)

#     print(f"Rows loaded: {len(df):,}")

#     required_columns = [
#         COMPONENT_ID_COL,
#         LOT_ID_COL,
#         COMPONENT_TYPE_COL,
#         TEMPERATURE_COL,
#         VOLTAGE_COL,
#         "iddq_0h_uA",
#         "iddq_24h_uA",
#         "iddq_96h_uA",
#         "iddq_168h_uA",
#         "leakage_0h_uA",
#         "leakage_24h_uA",
#         "leakage_96h_uA",
#         "leakage_168h_uA",
#         GROUND_TRUTH_COL,
#         LIMIT_COL,
#     ]

#     missing_columns = [
#         col for col in required_columns
#         if col not in df.columns
#     ]

#     if missing_columns:
#         raise ValueError(
#             "\nMissing required columns:\n"
#             + "\n".join(f"  - {col}" for col in missing_columns)
#         )

#     # Convert numeric fields
#     numeric_columns = [
#         TEMPERATURE_COL,
#         VOLTAGE_COL,
#         "iddq_0h_uA",
#         "iddq_24h_uA",
#         "iddq_96h_uA",
#         "iddq_168h_uA",
#         "leakage_0h_uA",
#         "leakage_24h_uA",
#         "leakage_96h_uA",
#         "leakage_168h_uA",
#         LIMIT_COL,
#     ]

#     df = safe_numeric(df, numeric_columns)

#     # Remove completely duplicated rows
#     df = df.drop_duplicates().reset_index(drop=True)

#     return df


# # ============================================================
# # PREPARE DATA
# # ============================================================

# def prepare_data(df):
#     """
#     Prepare cumulative dataset.

#     Important:
#     - No 168h feature is included.
#     - 168h is only target/reference.
#     """

#     df = df.copy()

#     # Make sure component IDs are strings
#     df[COMPONENT_ID_COL] = (
#         df[COMPONENT_ID_COL]
#         .astype(str)
#     )

#     df[LOT_ID_COL] = (
#         df[LOT_ID_COL]
#         .astype(str)
#     )

#     df[COMPONENT_TYPE_COL] = (
#         df[COMPONENT_TYPE_COL]
#         .astype(str)
#     )

#     # Keep one row per component
#     # because this dataset is wide-format:
#     # one row contains multiple burn-in observations.
#     df = df.drop_duplicates(
#         subset=[COMPONENT_ID_COL],
#         keep="first"
#     ).reset_index(drop=True)

#     return df


# # ============================================================
# # CREATE PREPROCESSOR
# # ============================================================

# def create_preprocessor():
#     """
#     Preprocessing pipeline:
#     - numeric missing values -> median
#     - categorical missing values -> most frequent
#     - component_type -> one-hot encoding
#     """

#     numeric_features = [
#         TEMPERATURE_COL,
#         VOLTAGE_COL,
#         "iddq_0h_uA",
#         "iddq_24h_uA",
#         "leakage_0h_uA",
#         "leakage_24h_uA",
#     ]

#     categorical_features = [
#         COMPONENT_TYPE_COL
#     ]

#     numeric_transformer = Pipeline(
#         steps=[
#             (
#                 "imputer",
#                 SimpleImputer(strategy="median")
#             )
#         ]
#     )

#     categorical_transformer = Pipeline(
#         steps=[
#             (
#                 "imputer",
#                 SimpleImputer(strategy="most_frequent")
#             ),
#             (
#                 "onehot",
#                 OneHotEncoder(
#                     handle_unknown="ignore",
#                     sparse_output=False
#                 )
#             )
#         ]
#     )

#     preprocessor = ColumnTransformer(
#         transformers=[
#             (
#                 "numeric",
#                 numeric_transformer,
#                 numeric_features
#             ),
#             (
#                 "categorical",
#                 categorical_transformer,
#                 categorical_features
#             ),
#         ],
#         remainder="drop"
#     )

#     return preprocessor


# # ============================================================
# # CREATE MODELS
# # ============================================================

# def create_models(preprocessor):
#     """
#     Create three candidate regression models.
#     """

#     models = {

#         "LinearRegression": Pipeline(
#             steps=[
#                 ("preprocessor", preprocessor),
#                 (
#                     "model",
#                     LinearRegression()
#                 ),
#             ]
#         ),

#         "RandomForest": Pipeline(
#             steps=[
#                 ("preprocessor", preprocessor),
#                 (
#                     "model",
#                     RandomForestRegressor(
#                         n_estimators=400,
#                         max_depth=12,
#                         min_samples_leaf=3,
#                         random_state=RANDOM_STATE,
#                         n_jobs=-1
#                     )
#                 ),
#             ]
#         ),

#         "HistGradientBoosting": Pipeline(
#             steps=[
#                 ("preprocessor", preprocessor),
#                 (
#                     "model",
#                     HistGradientBoostingRegressor(
#                         max_iter=300,
#                         learning_rate=0.05,
#                         max_leaf_nodes=15,
#                         random_state=RANDOM_STATE
#                     )
#                 ),
#             ]
#         ),
#     }

#     return models


# # ============================================================
# # DATA SPLIT
# # ============================================================

# def split_data(df):
#     """
#     Deterministic shuffled split.

#     60% -> training
#     20% -> calibration
#     20% -> final test
#     """

#     df = df.sample(
#         frac=1,
#         random_state=RANDOM_STATE
#     ).reset_index(drop=True)

#     n = len(df)

#     train_end = int(
#         n * TRAIN_FRACTION
#     )

#     calibration_end = int(
#         n * (TRAIN_FRACTION + CALIBRATION_FRACTION)
#     )

#     train_df = df.iloc[
#         :train_end
#     ].copy()

#     calibration_df = df.iloc[
#         train_end:calibration_end
#     ].copy()

#     test_df = df.iloc[
#         calibration_end:
#     ].copy()

#     return train_df, calibration_df, test_df


# # ============================================================
# # SAFETY SLOPE
# # ============================================================

# def calculate_safety_slope(train_df):
#     """
#     Calculate a dynamic reference drift slope from
#     Normal / High_Stable components.

#     Uses early IDDQ:
#         drift = IDDQ_24h - IDDQ_0h

#     95th percentile becomes the safety slope.
#     """

#     reference_df = train_df[
#         train_df[GROUND_TRUTH_COL]
#         .isin(SAFETY_REFERENCE_CLASSES)
#     ].copy()

#     if len(reference_df) < 5:
#         reference_df = train_df.copy()

#     reference_df["early_drift"] = (
#         reference_df["iddq_24h_uA"]
#         - reference_df["iddq_0h_uA"]
#     )

#     reference_df["early_drift"] = (
#         reference_df["early_drift"]
#         .replace([np.inf, -np.inf], np.nan)
#         .dropna()
#     )

#     if len(reference_df) == 0:
#         return 0.0

#     safety_slope = float(
#         np.percentile(
#             np.abs(
#                 reference_df["early_drift"]
#             ),
#             95
#         )
#     )

#     return safety_slope


# # ============================================================
# # CALIBRATION INTERVAL
# # ============================================================

# def calculate_prediction_interval(
#     model,
#     calibration_df,
#     feature_columns,
#     target_column
# ):
#     """
#     Conformal-style prediction interval.

#     Uses absolute calibration errors.
#     """

#     valid_calibration = calibration_df.dropna(
#         subset=[target_column]
#     ).copy()

#     if len(valid_calibration) == 0:
#         return 0.0

#     X_cal = valid_calibration[
#         feature_columns
#     ]

#     y_cal = valid_calibration[
#         target_column
#     ]

#     predictions = model.predict(X_cal)

#     absolute_errors = np.abs(
#         y_cal.values - predictions
#     )

#     if len(absolute_errors) == 0:
#         return 0.0

#     interval = float(
#         np.quantile(
#             absolute_errors,
#             0.95
#         )
#     )

#     return interval


# # ============================================================
# # MODEL TRAINING
# # ============================================================

# def train_best_model(train_df, calibration_df):
#     """
#     Train three candidate models and select the one with
#     lowest calibration MAE.
#     """

#     target_column = TARGET_COLUMNS.get(
#         TARGET_HOUR
#     )

#     if target_column is None:
#         raise ValueError(
#             f"Unsupported target horizon: {TARGET_HOUR}h"
#         )

#     feature_columns = EARLY_FEATURES.copy()

#     # --------------------------------------------------------
#     # Training requires actual target values.
#     # Missing 168h values are excluded from training.
#     # --------------------------------------------------------

#     train_valid = train_df.dropna(
#         subset=[target_column]
#     ).copy()

#     calibration_valid = calibration_df.dropna(
#         subset=[target_column]
#     ).copy()

#     if len(train_valid) < 10:
#         raise ValueError(
#             "Not enough training samples with "
#             f"{target_column} available."
#         )

#     print(
#         f"\nTraining samples with target: "
#         f"{len(train_valid):,}"
#     )

#     print(
#         f"Calibration samples with target: "
#         f"{len(calibration_valid):,}"
#     )

#     X_train = train_valid[
#         feature_columns
#     ]

#     y_train = train_valid[
#         target_column
#     ]

#     models = create_models(
#         create_preprocessor()
#     )

#     best_model = None
#     best_name = None
#     best_mae = np.inf

#     model_scores = {}

#     # --------------------------------------------------------
#     # Train candidate models
#     # --------------------------------------------------------

#     for name, model in models.items():

#         print(f"\nTraining {name}...")

#         model.fit(
#             X_train,
#             y_train
#         )

#         if len(calibration_valid) > 0:

#             X_cal = calibration_valid[
#                 feature_columns
#             ]

#             y_cal = calibration_valid[
#                 target_column
#             ]

#             cal_predictions = model.predict(
#                 X_cal
#             )

#             mae = mean_absolute_error(
#                 y_cal,
#                 cal_predictions
#             )

#             rmse = calculate_rmse(
#                 y_cal,
#                 cal_predictions
#             )

#         else:

#             mae = np.nan
#             rmse = np.nan

#         model_scores[name] = {
#             "calibration_mae": float(mae)
#             if not np.isnan(mae)
#             else None,

#             "calibration_rmse": float(rmse)
#             if not np.isnan(rmse)
#             else None,
#         }

#         print(
#             f"{name}: "
#             f"Calibration MAE = {mae:.6f}"
#             if not np.isnan(mae)
#             else f"{name}: No calibration target available"
#         )

#         if (
#             not np.isnan(mae)
#             and mae < best_mae
#         ):
#             best_mae = mae
#             best_model = model
#             best_name = name

#     # --------------------------------------------------------
#     # Fallback
#     # --------------------------------------------------------

#     if best_model is None:

#         best_name = "RandomForest"

#         best_model = models[
#             "RandomForest"
#         ]

#         best_model.fit(
#             X_train,
#             y_train
#         )

#     # --------------------------------------------------------
#     # Prediction interval
#     # --------------------------------------------------------

#     if len(calibration_valid) > 0:

#         prediction_interval = (
#             calculate_prediction_interval(
#                 best_model,
#                 calibration_valid,
#                 feature_columns,
#                 target_column
#             )
#         )

#     else:

#         prediction_interval = 0.0

#     print(
#         f"\nSelected model: {best_name}"
#     )

#     print(
#         f"Calibration MAE: "
#         f"{best_mae:.6f}"
#         if best_mae != np.inf
#         else "\nCalibration MAE: unavailable"
#     )

#     print(
#         f"95% prediction interval: "
#         f"±{prediction_interval:.6f}"
#     )

#     package = {
#         "model": best_model,
#         "model_name": best_name,
#         "feature_columns": feature_columns,
#         "target_column": target_column,
#         "target_hour": TARGET_HOUR,
#         "prediction_interval": prediction_interval,
#         "model_scores": model_scores,
#     }

#     return package


# # ============================================================
# # FINAL TEST EVALUATION
# # ============================================================

# def evaluate_model(
#     model_package,
#     test_df
# ):
#     """
#     Evaluate model only where actual target exists.
#     """

#     model = model_package["model"]
#     feature_columns = model_package["feature_columns"]
#     target_column = model_package["target_column"]

#     valid_test = test_df.dropna(
#         subset=[target_column]
#     ).copy()

#     if len(valid_test) == 0:

#         return {
#             "test_samples": 0,
#             "test_mae": None,
#             "test_rmse": None,
#         }

#     X_test = valid_test[
#         feature_columns
#     ]

#     y_test = valid_test[
#         target_column
#     ]

#     predictions = model.predict(
#         X_test
#     )

#     mae = mean_absolute_error(
#         y_test,
#         predictions
#     )

#     rmse = calculate_rmse(
#         y_test,
#         predictions
#     )

#     print_section(
#         "FINAL TEST PERFORMANCE"
#     )

#     print(
#         f"Test samples : {len(valid_test):,}"
#     )

#     print(
#         f"MAE          : {mae:.6f}"
#     )

#     print(
#         f"RMSE         : {rmse:.6f}"
#     )

#     return {
#         "test_samples": int(len(valid_test)),
#         "test_mae": float(mae),
#         "test_rmse": float(rmse),
#     }


# # ============================================================
# # PREDICT CUMULATIVE DATA
# # ============================================================

# def generate_predictions(
#     model_package,
#     cumulative_df
# ):
#     """
#     Generate predictions for all components having usable
#     early observations.

#     Actual 168h is NEVER an input.
#     """

#     model = model_package["model"]
#     feature_columns = model_package["feature_columns"]
#     prediction_interval = model_package[
#         "prediction_interval"
#     ]

#     target_column = model_package[
#         "target_column"
#     ]

#     result = cumulative_df.copy()

#     # --------------------------------------------------------
#     # Prediction
#     # --------------------------------------------------------

#     X_all = result[
#         feature_columns
#     ]

#     result[
#         "predicted_168h_uA"
#     ] = model.predict(
#         X_all
#     )

#     # --------------------------------------------------------
#     # Prediction interval
#     # --------------------------------------------------------

#     result[
#         "prediction_interval_lower_uA"
#     ] = (
#         result["predicted_168h_uA"]
#         - prediction_interval
#     )

#     result[
#         "prediction_interval_upper_uA"
#     ] = (
#         result["predicted_168h_uA"]
#         + prediction_interval
#     )

#     # --------------------------------------------------------
#     # Actual target
#     # --------------------------------------------------------

#     result[
#         "prediction_error"
#     ] = (
#         result[target_column]
#         - result["predicted_168h_uA"]
#     )

#     result[
#         "absolute_prediction_error"
#     ] = np.abs(
#         result["prediction_error"]
#     )

#     # ========================================================
#     # DRIFT CALCULATIONS
#     # ========================================================

#     # Early drift
#     result[
#         "early_drift_uA"
#     ] = (
#         result["iddq_24h_uA"]
#         - result["iddq_0h_uA"]
#     )

#     # Predicted drift from 0h -> target
#     result[
#         "predicted_drift_uA"
#     ] = (
#         result["predicted_168h_uA"]
#         - result["iddq_0h_uA"]
#     )

#     # Prediction drift rate
#     result[
#         "predicted_drift_rate_uA_per_hour"
#     ] = (
#         result["predicted_drift_uA"]
#         / TARGET_HOUR
#     )

#     # Relative drift
#     result[
#         "predicted_relative_drift_percent"
#     ] = np.where(
#         result["iddq_0h_uA"] != 0,
#         (
#             result["predicted_drift_uA"]
#             / result["iddq_0h_uA"]
#         ) * 100,
#         np.nan
#     )

#     # --------------------------------------------------------
#     # Actual drift
#     # --------------------------------------------------------

#     result[
#         "actual_drift_uA"
#     ] = (
#         result[target_column]
#         - result["iddq_0h_uA"]
#     )

#     result[
#         "actual_drift_rate_uA_per_hour"
#     ] = (
#         result["actual_drift_uA"]
#         / TARGET_HOUR
#     )

#     # ========================================================
#     # 96h INTERMEDIATE INFORMATION
#     # ========================================================

#     if "iddq_96h_uA" in result.columns:

#         result[
#             "observed_96h_drift_uA"
#         ] = (
#             result["iddq_96h_uA"]
#             - result["iddq_0h_uA"]
#         )

#         result[
#             "observed_96h_to_168h_drift_uA"
#         ] = (
#             result[target_column]
#             - result["iddq_96h_uA"]
#         )

#     # ========================================================
#     # SAFETY SLOPE
#     # ========================================================

#     # We will calculate this outside and assign later.
#     result[
#         "safety_slope_uA_per_hour"
#     ] = np.nan

#     result[
#         "drift_slope_excess"
#     ] = np.nan

#     # ========================================================
#     # FLAGS
#     # ========================================================

#     result[
#         "early_drift_flag"
#     ] = False

#     result[
#         "predicted_limit_exceeded"
#     ] = False

#     result[
#         "uncertainty_adjusted_failure"
#     ] = False

#     result[
#         "future_drift_risk"
#     ] = "LOW"

#     return result


# # ============================================================
# # APPLY RISK LOGIC
# # ============================================================

# def apply_risk_logic(
#     result,
#     safety_slope
# ):
#     """
#     Apply existing Module B-style risk logic.
#     """

#     result = result.copy()

#     # --------------------------------------------------------
#     # Safety slope
#     # --------------------------------------------------------

#     result[
#         "safety_slope_uA_per_hour"
#     ] = safety_slope

#     # --------------------------------------------------------
#     # Drift slope excess
#     # --------------------------------------------------------

#     result[
#         "drift_slope_excess"
#     ] = (
#         result["predicted_drift_rate_uA_per_hour"]
#         - safety_slope
#     )

#     # --------------------------------------------------------
#     # Early drift
#     # --------------------------------------------------------

#     result[
#         "early_drift_flag"
#     ] = (
#         result["early_drift_uA"]
#         > safety_slope * 24
#     )

#     # --------------------------------------------------------
#     # Limit checks
#     # --------------------------------------------------------

#     result[
#         "predicted_limit_exceeded"
#     ] = (
#         result["predicted_168h_uA"]
#         > result[LIMIT_COL]
#     )

#     # --------------------------------------------------------
#     # Uncertainty adjusted failure
#     # --------------------------------------------------------

#     result[
#         "uncertainty_adjusted_failure"
#     ] = (
#         result["prediction_interval_upper_uA"]
#         > result[LIMIT_COL]
#     )

#     # ========================================================
#     # RISK LEVEL
#     # ========================================================

#     conditions = [
#         (
#             result["uncertainty_adjusted_failure"]
#             |
#             result["predicted_limit_exceeded"]
#         ),

#         (
#             result[
#                 "predicted_drift_rate_uA_per_hour"
#             ]
#             > safety_slope
#         ),

#         (
#             result[
#                 "predicted_drift_rate_uA_per_hour"
#             ]
#             > safety_slope * 0.8
#         ),
#     ]

#     choices = [
#         "HIGH",
#         "MEDIUM",
#         "WATCH",
#     ]

#     result[
#         "future_drift_risk"
#     ] = np.select(
#         conditions,
#         choices,
#         default="LOW"
#     )

#     # ========================================================
#     # MODULE B STATUS
#     # ========================================================

#     result[
#         "module_b_status"
#     ] = np.select(

#         [
#             result[
#                 "predicted_limit_exceeded"
#             ],

#             result[
#                 "uncertainty_adjusted_failure"
#             ],

#             (
#                 result["future_drift_risk"]
#                 .isin(["HIGH", "MEDIUM"])
#             ),

#             result[
#                 "early_drift_flag"
#             ],
#         ],

#         [
#             "PREDICTED_FAILURE",
#             "PREDICTED_FAILURE",
#             "EARLY_DRIFT_RISK",
#             "EARLY_DRIFT_RISK",
#         ],

#         default="NORMAL"
#     )

#     # ========================================================
#     # EXPLANATION
#     # ========================================================

#     explanations = []

#     for _, row in result.iterrows():

#         reasons = []

#         if row[
#             "predicted_limit_exceeded"
#         ]:
#             reasons.append(
#                 "Predicted IDDQ exceeds absolute safety limit"
#             )

#         elif row[
#             "uncertainty_adjusted_failure"
#         ]:
#             reasons.append(
#                 "Upper prediction interval crosses safety limit"
#             )

#         if row[
#             "early_drift_flag"
#         ]:
#             reasons.append(
#                 "Early 0h-to-24h drift exceeds reference slope"
#             )

#         if row[
#             "future_drift_risk"
#         ] in ["HIGH", "MEDIUM"]:
#             reasons.append(
#                 "Predicted future drift rate is elevated"
#             )

#         if row[
#             "future_drift_risk"
#         ] == "WATCH":
#             reasons.append(
#                 "Predicted drift is approaching reference slope"
#             )

#         if not reasons:
#             reasons.append(
#                 "Predicted future drift remains within reference limits"
#             )

#         explanations.append(
#             "; ".join(reasons)
#         )

#     result[
#         "module_b_explanation"
#     ] = explanations

#     return result


# # ============================================================
# # CUMULATIVE STAGE
# # ============================================================

# def run_cumulative_stage(
#     cumulative_df,
#     stage_number
# ):
#     """
#     Run Module B for one cumulative stage.
#     """

#     component_count = len(
#         cumulative_df
#     )

#     print_section(
#         f"MODULE B - STAGE {stage_number}"
#     )

#     print(
#         f"Cumulative components: "
#         f"{component_count:,}"
#     )

#     print(
#         f"Prediction target: "
#         f"IDDQ {TARGET_HOUR}h"
#     )

#     # --------------------------------------------------------
#     # Prepare
#     # --------------------------------------------------------

#     data = prepare_data(
#         cumulative_df
#     )

#     # --------------------------------------------------------
#     # Split
#     # --------------------------------------------------------

#     train_df, calibration_df, test_df = (
#         split_data(data)
#     )

#     print(
#         f"\nTrain       : {len(train_df):,}"
#     )

#     print(
#         f"Calibration : {len(calibration_df):,}"
#     )

#     print(
#         f"Test        : {len(test_df):,}"
#     )

#     # --------------------------------------------------------
#     # Safety slope
#     # --------------------------------------------------------

#     safety_slope = calculate_safety_slope(
#         train_df
#     )

#     print(
#         f"\nDynamic safety slope: "
#         f"{safety_slope:.8f} uA/hour"
#     )

#     # --------------------------------------------------------
#     # Train model
#     # --------------------------------------------------------

#     model_package = train_best_model(
#         train_df,
#         calibration_df
#     )

#     # --------------------------------------------------------
#     # Evaluate
#     # --------------------------------------------------------

#     test_metrics = evaluate_model(
#         model_package,
#         test_df
#     )

#     # --------------------------------------------------------
#     # Predict entire cumulative dataset
#     # --------------------------------------------------------

#     result = generate_predictions(
#         model_package,
#         data
#     )

#     # --------------------------------------------------------
#     # Apply risk logic
#     # --------------------------------------------------------

#     result = apply_risk_logic(
#         result,
#         safety_slope
#     )

#     # --------------------------------------------------------
#     # Stage information
#     # --------------------------------------------------------

#     result[
#         "module_B_stage"
#     ] = stage_number

#     result[
#         "cumulative_component_count"
#     ] = component_count

#     result[
#         "prediction_horizon_hours"
#     ] = TARGET_HOUR

#     # --------------------------------------------------------
#     # Reorder useful columns first
#     # --------------------------------------------------------

#     priority_columns = [
#         COMPONENT_ID_COL,
#         LOT_ID_COL,
#         COMPONENT_TYPE_COL,
#         TEMPERATURE_COL,
#         VOLTAGE_COL,

#         "iddq_0h_uA",
#         "iddq_24h_uA",
#         "iddq_96h_uA",
#         "iddq_168h_uA",

#         "leakage_0h_uA",
#         "leakage_24h_uA",
#         "leakage_96h_uA",
#         "leakage_168h_uA",

#         GROUND_TRUTH_COL,
#         LIMIT_COL,

#         "predicted_168h_uA",
#         "prediction_interval_lower_uA",
#         "prediction_interval_upper_uA",

#         "prediction_error",
#         "absolute_prediction_error",

#         "early_drift_uA",
#         "predicted_drift_uA",
#         "predicted_drift_rate_uA_per_hour",
#         "predicted_relative_drift_percent",

#         "actual_drift_uA",
#         "actual_drift_rate_uA_per_hour",

#         "observed_96h_drift_uA",
#         "observed_96h_to_168h_drift_uA",

#         "safety_slope_uA_per_hour",
#         "drift_slope_excess",

#         "early_drift_flag",
#         "predicted_limit_exceeded",
#         "uncertainty_adjusted_failure",

#         "future_drift_risk",
#         "module_b_status",
#         "module_b_explanation",

#         "module_B_stage",
#         "cumulative_component_count",
#         "prediction_horizon_hours",
#     ]

#     existing_priority_columns = [
#         col
#         for col in priority_columns
#         if col in result.columns
#     ]

#     remaining_columns = [
#         col
#         for col in result.columns
#         if col not in existing_priority_columns
#     ]

#     result = result[
#         existing_priority_columns
#         + remaining_columns
#     ]

#     # --------------------------------------------------------
#     # Save stage
#     # --------------------------------------------------------

#     stage_output = os.path.join(
#         OUTPUT_DIR,
#         f"module_B_stage_{stage_number}_{component_count}.csv"
#     )

#     result.to_csv(
#         stage_output,
#         index=False
#     )

#     print(
#         f"\nStage output saved:"
#     )

#     print(stage_output)

#     # --------------------------------------------------------
#     # Save model package
#     # --------------------------------------------------------

#     stage_model_path = os.path.join(
#         OUTPUT_DIR,
#         f"module_B_model_stage_{stage_number}.pkl"
#     )

#     model_package_to_save = {
#         **model_package,
#         "stage_number": stage_number,
#         "component_count": component_count,
#         "safety_slope": safety_slope,
#         "test_metrics": test_metrics,
#     }

#     joblib.dump(
#         model_package_to_save,
#         stage_model_path
#     )

#     print(
#         f"Stage model saved:"
#     )

#     print(stage_model_path)

#     # --------------------------------------------------------
#     # Summary
#     # --------------------------------------------------------

#     print_section(
#         f"STAGE {stage_number} SUMMARY"
#     )

#     print(
#         f"Components              : {component_count:,}"
#     )

#     print(
#         f"Selected model          : "
#         f"{model_package['model_name']}"
#     )

#     print(
#         f"Prediction horizon      : "
#         f"{TARGET_HOUR}h"
#     )

#     print(
#         f"Safety slope            : "
#         f"{safety_slope:.8f} uA/hour"
#     )

#     print(
#         "\nRisk distribution:"
#     )

#     print(
#         result["future_drift_risk"]
#         .value_counts()
#         .to_string()
#     )

#     print(
#         "\nModule B status:"
#     )

#     print(
#         result["module_b_status"]
#         .value_counts()
#         .to_string()
#     )

#     return result, model_package_to_save


# # ============================================================
# # MAIN
# # ============================================================

# def main():

#     print_section(
#         "SIH 26170 - MODULE B"
#     )

#     print(
#         "MULTIVARIATE TIME-SERIES / DRIFT PREDICTION"
#     )

#     print(
#         f"\nPrediction horizon: {TARGET_HOUR} hours"
#     )

#     print(
#         "\nEarly input features:"
#     )

#     for feature in EARLY_FEATURES:
#         print(
#             f"  - {feature}"
#         )

#     print(
#         "\nIMPORTANT:"
#     )

#     print(
#         "168h actual IDDQ is NOT used as a model input."
#     )

#     # --------------------------------------------------------
#     # Create output directory
#     # --------------------------------------------------------

#     os.makedirs(
#         OUTPUT_DIR,
#         exist_ok=True
#     )

#     # --------------------------------------------------------
#     # Check all files
#     # --------------------------------------------------------

#     print_section(
#         "CHECKING INPUT FILES"
#     )

#     for file_path in CSV_FILES:

#         if not os.path.exists(file_path):

#             raise FileNotFoundError(
#                 f"\nMissing input file:\n"
#                 f"{file_path}"
#             )

#         print(
#             f"[OK] {file_path}"
#         )

#     # --------------------------------------------------------
#     # Cumulative processing
#     # --------------------------------------------------------

#     cumulative_df = pd.DataFrame()

#     all_stage_results = []

#     final_model_package = None

#     for stage_number, file_path in enumerate(
#         CSV_FILES,
#         start=1
#     ):

#         # ----------------------------------------------------
#         # Load batch
#         # ----------------------------------------------------

#         batch_df = load_csv(
#             file_path
#         )

#         # ----------------------------------------------------
#         # Add to cumulative data
#         # ----------------------------------------------------

#         cumulative_df = pd.concat(
#             [
#                 cumulative_df,
#                 batch_df
#             ],
#             ignore_index=True
#         )

#         # ----------------------------------------------------
#         # Remove duplicate components
#         # ----------------------------------------------------

#         cumulative_df = cumulative_df.drop_duplicates(
#             subset=[COMPONENT_ID_COL],
#             keep="first"
#         ).reset_index(drop=True)

#         print(
#             f"\nAfter adding {file_path}:"
#         )

#         print(
#             f"Cumulative components: "
#             f"{len(cumulative_df):,}"
#         )

#         # ----------------------------------------------------
#         # Run Module B
#         # ----------------------------------------------------

#         stage_result, model_package = (
#             run_cumulative_stage(
#                 cumulative_df,
#                 stage_number
#             )
#         )

#         all_stage_results.append(
#             stage_result
#         )

#         final_model_package = model_package

#     # ========================================================
#     # FINAL OUTPUT
#     # ========================================================

#     print_section(
#         "CREATING FINAL 10,000-COMPONENT OUTPUT"
#     )

#     final_result = all_stage_results[-1]

#     final_result.to_csv(
#         FINAL_OUTPUT_PATH,
#         index=False
#     )

#     print(
#         f"Final output saved:"
#     )

#     print(
#         FINAL_OUTPUT_PATH
#     )

#     # --------------------------------------------------------
#     # Save final model
#     # --------------------------------------------------------

#     if final_model_package is not None:

#         joblib.dump(
#             final_model_package,
#             MODEL_PATH
#         )

#         print(
#             f"\nFinal model saved:"
#         )

#         print(
#             MODEL_PATH
#         )

#     # ========================================================
#     # FINAL SUMMARY
#     # ========================================================

#     print_section(
#         "MODULE B COMPLETE"
#     )

#     print(
#         f"Total components processed: "
#         f"{len(final_result):,}"
#     )

#     print(
#         f"Prediction horizon: "
#         f"{TARGET_HOUR}h"
#     )

#     print(
#         "\nGenerated stage files:"
#     )

#     for stage_number, stage_result in enumerate(
#         all_stage_results,
#         start=1
#     ):

#         print(
#             f"  Stage {stage_number}: "
#             f"{len(stage_result):,} components"
#         )

#     print(
#         "\nFinal risk distribution:"
#     )

#     print(
#         final_result[
#             "future_drift_risk"
#         ]
#         .value_counts()
#         .to_string()
#     )

#     print(
#         "\nFinal Module B status:"
#     )

#     print(
#         final_result[
#             "module_b_status"
#         ]
#         .value_counts()
#         .to_string()
#     )

#     print(
#         "\nOutput:"
#     )

#     print(
#         FINAL_OUTPUT_PATH
#     )

#     print(
#         "\nModule B finished successfully."
#     )


# # ============================================================
# # ENTRY POINT
# # ============================================================

# if __name__ == "__main__":
#     main()