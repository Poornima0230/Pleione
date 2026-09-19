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


