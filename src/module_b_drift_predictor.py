# # ============================================================
# # SIH 26170
# # MODULE B: MULTIVARIATE TIME-SERIES DRIFT PREDICTOR
# #
# # PURPOSE
# # ------------------------------------------------------------
# # Predict future 168h IDDQ behavior using early burn-in
# # measurements available at 0h and 24h.
# #
# # INPUT FEATURES
# # ------------------------------------------------------------
# # 1. IDDQ @ 0h
# # 2. IDDQ @ 24h
# # 3. Temperature
# # 4. Voltage
# # 5. Component Type
# #
# # TARGET
# # ------------------------------------------------------------
# # IDDQ @ 168h
# #
# #
# # CUMULATIVE PROCESSING
# # ------------------------------------------------------------
# #
# # File 1                -> 2,000 components
# # File 1 + File 2       -> 4,000 components
# # File 1 + File 2 + 3   -> 6,000 components
# # File 1 + ... + File 4 -> 8,000 components
# # File 1 + ... + File 5 -> 10,000 components
# #
# #
# # IMPORTANT
# # ------------------------------------------------------------
# # Actual 168h measurements are NEVER used as prediction
# # INPUT FEATURES.
# #
# # Actual 168h is used only as:
# # - supervised learning target
# # - evaluation
# # - validation
# # - drift reference
# #
# #
# # SAFETY NOTE
# # ------------------------------------------------------------
# # Dynamic safety slope is a PROTOTYPE statistical boundary.
# # It is NOT an ISRO-qualified aerospace engineering limit.
# # ============================================================


# # ============================================================
# # IMPORTS
# # ============================================================

# import os
# import joblib
# import warnings

# import pandas as pd
# import numpy as np

# from sklearn.model_selection import train_test_split

# from sklearn.linear_model import LinearRegression

# from sklearn.ensemble import (
#     RandomForestRegressor,
#     HistGradientBoostingRegressor
# )

# from sklearn.preprocessing import OneHotEncoder
# from sklearn.compose import ColumnTransformer
# from sklearn.pipeline import Pipeline

# from sklearn.metrics import (
#     mean_absolute_error,
#     mean_squared_error,
#     r2_score,
#     confusion_matrix,
#     precision_score,
#     recall_score,
#     f1_score
# )

# warnings.filterwarnings("ignore")


# # ============================================================
# # CONFIGURATION
# # ============================================================

# # ------------------------------------------------------------
# # IMPORTANT:
# # CHANGE THESE FIVE PATHS TO YOUR ACTUAL CSV FILES.
# # ------------------------------------------------------------

# CSV_FILES = [

#     "data/batch_1.csv",

#     "data/batch_2.csv",

#     "data/batch_3.csv",

#     "data/batch_4.csv",

#     "data/batch_5.csv"

# ]


# # ------------------------------------------------------------
# # Output directory
# # ------------------------------------------------------------

# OUTPUT_DIR = "data/module_B"

# os.makedirs(
#     OUTPUT_DIR,
#     exist_ok=True
# )


# # ------------------------------------------------------------
# # Final combined output
# # ------------------------------------------------------------

# FINAL_OUTPUT_PATH = os.path.join(

#     OUTPUT_DIR,

#     "module_B_drift_predictions.csv"

# )


# # ------------------------------------------------------------
# # Model path
# # ------------------------------------------------------------

# MODEL_PATH = os.path.join(

#     OUTPUT_DIR,

#     "module_B_model.pkl"

# )


# # ------------------------------------------------------------
# # Cumulative stage output
# #
# # These files allow you to demonstrate:
# #
# # 2000
# # 4000
# # 6000
# # 8000
# # 10000
# #
# # ------------------------------------------------------------

# STAGE_OUTPUT_TEMPLATE = os.path.join(

#     OUTPUT_DIR,

#     "module_B_stage_{stage}_{count}.csv"

# )


# # ============================================================
# # GENERAL CONFIGURATION
# # ============================================================

# RANDOM_STATE = 42

# TEST_SIZE = 0.20

# CALIBRATION_FRACTION = 0.25


# # ------------------------------------------------------------
# # Prediction horizon
# # ------------------------------------------------------------
# #
# # DO NOT scatter 168 throughout the code.
# #
# # This makes the system configurable later.
# #
# # ------------------------------------------------------------

# INPUT_HOURS = (

#     0,

#     24

# )


# TARGET_HOUR = 168


# # ------------------------------------------------------------
# # Safety configuration
# # ------------------------------------------------------------

# SAFETY_PERCENTILE = 95


# PREDICTION_INTERVAL_CONFIDENCE = 0.90


# # ------------------------------------------------------------
# # Reference population
# # ------------------------------------------------------------

# REFERENCE_CLASSES = [

#     "Normal",

#     "High_Stable"

# ]


# # ------------------------------------------------------------
# # Abnormal classes
# # ------------------------------------------------------------

# ABNORMAL_CLASSES = [

#     "High_Stable",

#     "Latent_Defect",

#     "Absolute_Failure",

#     "Sudden_Anomaly"

# ]


# # ============================================================
# # POSSIBLE COLUMN NAMES
# # ============================================================
# #
# # Since the exact temperature/voltage/component-type column
# # names were not included in the code you sent, this module
# # tries several common names automatically.
# #
# # If your columns use different names, add them here.
# #
# # ============================================================


# COLUMN_ALIASES = {

#     "component_id": [

#         "component_id",

#         "component",

#         "componentID",

#         "Component_ID",

#         "ComponentID"

#     ],


#     "lot_id": [

#         "lot_id",

#         "lot",

#         "Lot_ID",

#         "LotID"

#     ],


#     "ground_truth": [

#         "ground_truth",

#         "Ground_Truth",

#         "groundTruth",

#         "label",

#         "class"

#     ],


#     "component_type": [

#         "component_type",

#         "Component_Type",

#         "componentType",

#         "type",

#         "Type",

#         "device_type",

#         "deviceType"

#     ],


#     "temperature": [

#         "temperature",

#         "Temperature",

#         "temp",

#         "Temp",

#         "temperature_C",

#         "temperature_c",

#         "temp_C",

#         "temp_c"

#     ],


#     "voltage": [

#         "voltage",

#         "Voltage",

#         "voltage_V",

#         "voltage_v",

#         "VDD",

#         "vdd",

#         "supply_voltage"

#     ],


#     "absolute_limit_uA": [

#         "absolute_limit_uA",

#         "absolute_limit",

#         "Absolute_Limit",

#         "limit_uA",

#         "iddq_limit_uA",

#         "IDDQ_limit_uA"

#     ],


#     "iddq_0h_uA": [

#         "iddq_0h_uA",

#         "IDDQ_0h_uA",

#         "iddq_0h",

#         "IDDQ_0h"

#     ],


#     "iddq_24h_uA": [

#         "iddq_24h_uA",

#         "IDDQ_24h_uA",

#         "iddq_24h",

#         "IDDQ_24h"

#     ],


#     "iddq_168h_uA": [

#         "iddq_168h_uA",

#         "IDDQ_168h_uA",

#         "iddq_168h",

#         "IDDQ_168h"

#     ]

# }


# # ============================================================
# # HELPER: FIND COLUMN
# # ============================================================

# def find_column(
#     df,
#     logical_name,
#     required=True
# ):

#     # --------------------------------------------------------
#     # First try aliases
#     # --------------------------------------------------------

#     aliases = COLUMN_ALIASES.get(

#         logical_name,

#         []

#     )


#     # Exact matching

#     for column in aliases:

#         if column in df.columns:

#             return column


#     # --------------------------------------------------------
#     # Case-insensitive matching
#     # --------------------------------------------------------

#     lower_columns = {

#         str(column).lower():
#         column

#         for column in df.columns

#     }


#     for alias in aliases:

#         alias_lower = alias.lower()

#         if alias_lower in lower_columns:

#             return lower_columns[
#                 alias_lower
#             ]


#     # --------------------------------------------------------
#     # Not found
#     # --------------------------------------------------------

#     if required:

#         raise ValueError(

#             f"\nCould not find column for '{logical_name}'.\n"

#             f"Expected one of:\n"
#             f"{aliases}\n\n"

#             f"Available columns:\n"
#             f"{list(df.columns)}"

#         )


#     return None


# # ============================================================
# # HEADER
# # ============================================================

# print("=" * 80)

# print(
#     "SIH 26170"
# )

# print(
#     "MODULE B: MULTIVARIATE TIME-SERIES DRIFT PREDICTOR"
# )

# print("=" * 80)

# print()

# print(
#     f"Prediction horizon: {TARGET_HOUR} hours"
# )

# print(
#     f"Early observations: {INPUT_HOURS}"
# )


# # ============================================================
# # STEP 1: LOAD ALL CSV FILES
# # ============================================================

# print("\n" + "=" * 80)

# print(
#     "LOADING CSV FILES"
# )

# print("=" * 80)


# for index, file_path in enumerate(
#     CSV_FILES,
#     start=1
# ):

#     if not os.path.exists(file_path):

#         raise FileNotFoundError(

#             f"\nCSV file not found:\n"
#             f"{file_path}\n\n"
#             f"Update CSV_FILES at the top of Module B."

#         )

#     print(

#         f"File {index}: "
#         f"{file_path}"

#     )


# # ============================================================
# # STEP 2: READ FIRST FILE TO IDENTIFY COLUMNS
# # ============================================================

# first_df = pd.read_csv(

#     CSV_FILES[0]

# )


# print("\nFirst CSV loaded.")

# print(

#     f"Rows: {len(first_df)}"

# )

# print(

#     f"Columns: {len(first_df.columns)}"

# )


# # ============================================================
# # STEP 3: RESOLVE COLUMN NAMES
# # ============================================================

# component_id_col = find_column(

#     first_df,

#     "component_id"

# )


# lot_id_col = find_column(

#     first_df,

#     "lot_id"

# )


# ground_truth_col = find_column(

#     first_df,

#     "ground_truth"

# )


# component_type_col = find_column(

#     first_df,

#     "component_type"

# )


# temperature_col = find_column(

#     first_df,

#     "temperature"

# )


# voltage_col = find_column(

#     first_df,

#     "voltage"

# )


# absolute_limit_col = find_column(

#     first_df,

#     "absolute_limit_uA"

# )


# iddq_0h_col = find_column(

#     first_df,

#     "iddq_0h_uA"

# )


# iddq_24h_col = find_column(

#     first_df,

#     "iddq_24h_uA"

# )


# iddq_168h_col = find_column(

#     first_df,

#     "iddq_168h_uA"

# )


# print("\n" + "=" * 80)

# print(
#     "COLUMN MAPPING"
# )

# print("=" * 80)


# print(
#     f"\nComponent ID     : {component_id_col}"
# )

# print(
#     f"Lot ID           : {lot_id_col}"
# )

# print(
#     f"Ground Truth     : {ground_truth_col}"
# )

# print(
#     f"Component Type   : {component_type_col}"
# )

# print(
#     f"Temperature      : {temperature_col}"
# )

# print(
#     f"Voltage          : {voltage_col}"
# )

# print(
#     f"Absolute Limit   : {absolute_limit_col}"
# )

# print(
#     f"IDDQ 0h          : {iddq_0h_col}"
# )

# print(
#     f"IDDQ 24h         : {iddq_24h_col}"
# )

# print(
#     f"IDDQ 168h        : {iddq_168h_col}"
# )


# # ============================================================
# # STEP 4: STANDARDIZE COLUMN NAMES
# # ============================================================
# #
# # This lets the rest of the code use stable internal names.
# #
# # ============================================================

# COLUMN_RENAME_MAP = {

#     component_id_col:
#         "component_id",

#     lot_id_col:
#         "lot_id",

#     ground_truth_col:
#         "ground_truth",

#     component_type_col:
#         "component_type",

#     temperature_col:
#         "temperature",

#     voltage_col:
#         "voltage",

#     absolute_limit_col:
#         "absolute_limit_uA",

#     iddq_0h_col:
#         "iddq_0h_uA",

#     iddq_24h_col:
#         "iddq_24h_uA",

#     iddq_168h_col:
#         "iddq_168h_uA"

# }


# # ============================================================
# # STEP 5: FUNCTION TO LOAD AND STANDARDIZE A CSV
# # ============================================================

# def load_and_standardize_csv(
#     file_path
# ):

#     data = pd.read_csv(

#         file_path

#     )


#     # --------------------------------------------------------
#     # Resolve columns independently for each file
#     # --------------------------------------------------------

#     mapping = {

#         find_column(
#             data,
#             logical_name
#         ):
#         logical_name

#         for logical_name in [

#             "component_id",

#             "lot_id",

#             "ground_truth",

#             "component_type",

#             "temperature",

#             "voltage",

#             "absolute_limit_uA",

#             "iddq_0h_uA",

#             "iddq_24h_uA",

#             "iddq_168h_uA"

#         ]

#     }


#     data = data.rename(

#         columns=mapping

#     )


#     return data


# # ============================================================
# # STEP 6: PREPARE DATA FOR DRIFT PREDICTION
# # ============================================================

# def prepare_drift_data(
#     data
# ):

#     df_local = data.copy()


#     # --------------------------------------------------------
#     # Required model input columns
#     # --------------------------------------------------------

#     required = [

#         "component_id",

#         "component_type",

#         "temperature",

#         "voltage",

#         "iddq_0h_uA",

#         "iddq_24h_uA"

#     ]


#     # --------------------------------------------------------
#     # 168h is required for supervised training/evaluation.
#     #
#     # Components without 168h can still conceptually be
#     # predicted, but cannot be used to train this supervised
#     # model.
#     # --------------------------------------------------------

#     for column in required:

#         if column not in df_local.columns:

#             raise ValueError(

#                 f"Required column missing: {column}"

#             )


#     # --------------------------------------------------------
#     # Convert numerical fields
#     # --------------------------------------------------------

#     numerical_columns = [

#         "temperature",

#         "voltage",

#         "iddq_0h_uA",

#         "iddq_24h_uA",

#         "iddq_168h_uA",

#         "absolute_limit_uA"

#     ]


#     for column in numerical_columns:

#         if column in df_local.columns:

#             df_local[column] = pd.to_numeric(

#                 df_local[column],

#                 errors="coerce"

#             )


#     # --------------------------------------------------------
#     # Replace infinity
#     # --------------------------------------------------------

#     df_local = df_local.replace(

#         [np.inf, -np.inf],

#         np.nan

#     )


#     # --------------------------------------------------------
#     # Remove rows missing prediction inputs
#     # --------------------------------------------------------

#     prediction_required = [

#         "component_id",

#         "component_type",

#         "temperature",

#         "voltage",

#         "iddq_0h_uA",

#         "iddq_24h_uA"

#     ]


#     valid_prediction_rows = (

#         df_local[
#             prediction_required
#         ]
#         .notnull()
#         .all(axis=1)

#     )


#     df_local = df_local.loc[

#         valid_prediction_rows

#     ].copy()


#     # --------------------------------------------------------
#     # actual_abnormal
#     # --------------------------------------------------------

#     df_local["actual_abnormal"] = (

#         df_local[
#             "ground_truth"
#         ].isin(
#             ABNORMAL_CLASSES
#         )

#     )


#     # --------------------------------------------------------
#     # IMPORTANT:
#     #
#     # Keep only one row per component if duplicate component
#     # records exist.
#     #
#     # If your five CSVs contain different observations for the
#     # SAME component, this section must be changed to merge
#     # time observations instead.
#     #
#     # Your stated architecture indicates each file contains
#     # another batch of components, so duplicates are treated
#     # as duplicates here.
#     # --------------------------------------------------------

#     duplicate_count = (

#         df_local[
#             "component_id"
#         ].duplicated()
#         .sum()

#     )


#     if duplicate_count > 0:

#         print(

#             f"\nWARNING: {duplicate_count} "
#             f"duplicate component IDs detected."

#         )


#         df_local = (

#             df_local
#             .drop_duplicates(
#                 subset=["component_id"],
#                 keep="last"
#             )
#             .copy()

#         )


#     # --------------------------------------------------------
#     # Reset index
#     # --------------------------------------------------------

#     df_local = df_local.reset_index(

#         drop=True

#     )


#     return df_local


# # ============================================================
# # STEP 7: BUILD MODEL PIPELINE
# # ============================================================

# NUMERICAL_FEATURES = [

#     "iddq_0h_uA",

#     "iddq_24h_uA",

#     "temperature",

#     "voltage"

# ]


# CATEGORICAL_FEATURES = [

#     "component_type"

# ]


# MODEL_FEATURES = (

#     NUMERICAL_FEATURES

#     +

#     CATEGORICAL_FEATURES

# )


# TARGET = "iddq_168h_uA"


# # ------------------------------------------------------------
# # OneHotEncoder compatibility between sklearn versions
# # ------------------------------------------------------------

# try:

#     encoder = OneHotEncoder(

#         handle_unknown="ignore",

#         sparse_output=False

#     )

# except TypeError:

#     encoder = OneHotEncoder(

#         handle_unknown="ignore",

#         sparse=False

#     )


# preprocessor = ColumnTransformer(

#     transformers=[

#         (

#             "numerical",

#             "passthrough",

#             NUMERICAL_FEATURES

#         ),

#         (

#             "categorical",

#             encoder,

#             CATEGORICAL_FEATURES

#         )

#     ]

# )


# # ============================================================
# # STEP 8: DEFINE MODELS
# # ============================================================

# models = {

#     "Linear Regression":

#         LinearRegression(),


#     "Random Forest":

#         RandomForestRegressor(

#             n_estimators=400,

#             max_depth=12,

#             min_samples_leaf=3,

#             random_state=RANDOM_STATE,

#             n_jobs=-1

#         ),


#     "Gradient Boosting":

#         HistGradientBoostingRegressor(

#             max_iter=300,

#             learning_rate=0.05,

#             max_leaf_nodes=15,

#             random_state=RANDOM_STATE

#         )

# }


# # ============================================================
# # STEP 9: RUN ONE CUMULATIVE STAGE
# # ============================================================

# def run_cumulative_stage(

#     cumulative_df,

#     stage_number

# ):

#     print("\n")

#     print("#" * 80)

#     print(

#         f"CUMULATIVE STAGE {stage_number}"

#     )

#     print("#" * 80)


#     print(

#         f"\nTotal cumulative components: "
#         f"{len(cumulative_df)}"

#     )


#     # --------------------------------------------------------
#     # Prepare data
#     # --------------------------------------------------------

#     df_stage = prepare_drift_data(

#         cumulative_df

#     )


#     print(

#         f"Prediction-eligible components: "
#         f"{len(df_stage)}"

#     )


#     # --------------------------------------------------------
#     # Supervised training requires actual 168h target.
#     # --------------------------------------------------------

#     training_valid = (

#         df_stage[
#             TARGET
#         ].notnull()

#     )


#     model_df = df_stage.loc[

#         training_valid

#     ].copy()


#     model_df = model_df.reset_index(

#         drop=True

#     )


#     print(

#         f"Components with 168h target: "
#         f"{len(model_df)}"

#     )


#     if len(model_df) < 10:

#         print(

#             "\nNot enough samples for this stage."

#         )

#         return None


#     # ========================================================
#     # INPUT / TARGET
#     # ========================================================

#     X = model_df[
#         MODEL_FEATURES
#     ].copy()


#     y = model_df[
#         TARGET
#     ].copy()


#     # ========================================================
#     # DATA SPLIT
#     # ========================================================

#     indices = np.arange(

#         len(model_df)

#     )


#     labels = model_df[
#         "ground_truth"
#     ]


#     # --------------------------------------------------------
#     # Try stratified split.
#     #
#     # If a class has too few samples, fall back to random
#     # split rather than crashing.
#     # --------------------------------------------------------

#     try:

#         development_indices, test_indices = train_test_split(

#             indices,

#             test_size=TEST_SIZE,

#             random_state=RANDOM_STATE,

#             stratify=labels

#         )

#     except ValueError:

#         print(

#             "\nWARNING: Stratified test split could not "
#             "be created. Using random split."

#         )


#         development_indices, test_indices = train_test_split(

#             indices,

#             test_size=TEST_SIZE,

#             random_state=RANDOM_STATE

#         )


#     development_labels = (

#         model_df.iloc[
#             development_indices
#         ][
#             "ground_truth"
#         ]

#     )


#     try:

#         train_indices, calibration_indices = train_test_split(

#             development_indices,

#             test_size=CALIBRATION_FRACTION,

#             random_state=RANDOM_STATE,

#             stratify=development_labels

#         )

#     except ValueError:

#         print(

#             "\nWARNING: Stratified calibration split "
#             "could not be created. Using random split."

#         )


#         train_indices, calibration_indices = train_test_split(

#             development_indices,

#             test_size=CALIBRATION_FRACTION,

#             random_state=RANDOM_STATE

#         )


#     X_train = X.iloc[
#         train_indices
#     ].copy()


#     y_train = y.iloc[
#         train_indices
#     ].copy()


#     X_calibration = X.iloc[
#         calibration_indices
#     ].copy()


#     y_calibration = y.iloc[
#         calibration_indices
#     ].copy()


#     X_test = X.iloc[
#         test_indices
#     ].copy()


#     y_test = y.iloc[
#         test_indices
#     ].copy()


#     print("\nData split:")

#     print(

#         f"Training    : {len(X_train)}"

#     )

#     print(

#         f"Calibration : {len(X_calibration)}"

#     )

#     print(

#         f"Testing     : {len(X_test)}"

#     )


#     # ========================================================
#     # TRAIN MODELS
#     # ========================================================

#     results = []

#     trained_models = {}

#     calibration_predictions = {}


#     print("\n" + "-" * 80)

#     print("MODEL COMPARISON")

#     print("-" * 80)


#     for name, model in models.items():

#         print(

#             f"\nTraining: {name}"

#         )


#         # ----------------------------------------------------
#         # Complete preprocessing + model pipeline
#         # ----------------------------------------------------

#         pipeline = Pipeline(

#             steps=[

#                 (

#                     "preprocessor",

#                     preprocessor

#                 ),

#                 (

#                     "model",

#                     model

#                 )

#             ]

#         )


#         # ----------------------------------------------------
#         # Train
#         # ----------------------------------------------------

#         pipeline.fit(

#             X_train,

#             y_train

#         )


#         # ----------------------------------------------------
#         # Calibration prediction
#         # ----------------------------------------------------

#         calibration_prediction = (

#             pipeline.predict(

#                 X_calibration

#             )

#         )


#         # ----------------------------------------------------
#         # Metrics
#         # ----------------------------------------------------

#         calibration_mae = mean_absolute_error(

#             y_calibration,

#             calibration_prediction

#         )


#         calibration_rmse = np.sqrt(

#             mean_squared_error(

#                 y_calibration,

#                 calibration_prediction

#             )

#         )


#         calibration_r2 = r2_score(

#             y_calibration,

#             calibration_prediction

#         )


#         results.append({

#             "Model":
#                 name,

#             "Calibration_MAE":
#                 calibration_mae,

#             "Calibration_RMSE":
#                 calibration_rmse,

#             "Calibration_R2":
#                 calibration_r2

#         })


#         trained_models[
#             name
#         ] = pipeline


#         calibration_predictions[
#             name
#         ] = calibration_prediction


#         print(

#             f"MAE : {calibration_mae:.4f} µA"

#         )

#         print(

#             f"RMSE: {calibration_rmse:.4f} µA"

#         )

#         print(

#             f"R²  : {calibration_r2:.4f}"

#         )


#     # ========================================================
#     # MODEL COMPARISON
#     # ========================================================

#     results_df = pd.DataFrame(

#         results

#     )


#     results_df = results_df.sort_values(

#         "Calibration_MAE"

#     )


#     print("\n" + "-" * 80)

#     print("MODEL PERFORMANCE")

#     print("-" * 80)


#     print(

#         results_df.to_string(
#             index=False
#         )

#     )


#     # ========================================================
#     # BEST MODEL
#     # ========================================================

#     best_model_name = (

#         results_df.iloc[0]["Model"]

#     )


#     best_model = (

#         trained_models[
#             best_model_name
#         ]

#     )


#     print(

#         f"\nBest model: {best_model_name}"

#     )


#     # ========================================================
#     # UNCERTAINTY CALIBRATION
#     # ========================================================

#     best_calibration_prediction = (

#         calibration_predictions[
#             best_model_name
#         ]

#     )


#     calibration_absolute_errors = np.abs(

#         y_calibration.to_numpy()

#         -

#         best_calibration_prediction

#     )


#     alpha = (

#         1

#         -

#         PREDICTION_INTERVAL_CONFIDENCE

#     )


#     n_calibration = len(

#         calibration_absolute_errors

#     )


#     conformal_quantile_level = min(

#         1.0,

#         np.ceil(

#             (n_calibration + 1)

#             *

#             (1 - alpha)

#         )

#         /

#         n_calibration

#     )


#     prediction_interval_radius = np.quantile(

#         calibration_absolute_errors,

#         conformal_quantile_level

#     )


#     # ========================================================
#     # DYNAMIC SAFETY SLOPE
#     # ========================================================

#     training_reference_df = (

#         model_df.iloc[
#             train_indices
#         ].copy()

#     )


#     training_reference_df = (

#         training_reference_df[

#             training_reference_df[
#                 "ground_truth"
#             ].isin(
#                 REFERENCE_CLASSES
#             )

#         ].copy()

#     )


#     if len(training_reference_df) == 0:

#         print(

#             "\nWARNING: No reference population found."

#         )


#         # Conservative fallback based on training drift

#         training_reference_df = (

#             model_df.iloc[
#                 train_indices
#             ].copy()

#         )


#     training_reference_drift_rate = (

#         training_reference_df[
#             TARGET
#         ]

#         -

#         training_reference_df[
#             "iddq_0h_uA"
#         ]

#     ) / TARGET_HOUR


#     safety_slope = np.percentile(

#         training_reference_drift_rate,

#         SAFETY_PERCENTILE

#     )


#     # ========================================================
#     # PREDICT FOR ALL ELIGIBLE COMPONENTS
#     # ========================================================

#     prediction_df = df_stage.copy()


#     prediction_X = prediction_df[
#         MODEL_FEATURES
#     ].copy()


#     prediction_df[
#         "predicted_168h_uA"
#     ] = best_model.predict(

#         prediction_X

#     )


#     # ========================================================
#     # PREDICTION INTERVAL
#     # ========================================================

#     prediction_df[
#         "prediction_lower_uA"
#     ] = (

#         prediction_df[
#             "predicted_168h_uA"
#         ]

#         -

#         prediction_interval_radius

#     )


#     prediction_df[
#         "prediction_upper_uA"
#     ] = (

#         prediction_df[
#             "predicted_168h_uA"
#         ]

#         +

#         prediction_interval_radius

#     )


#     # ========================================================
#     # PREDICTION ERROR
#     # ========================================================

#     prediction_df[
#         "prediction_error_uA"
#     ] = np.where(

#         prediction_df[
#             TARGET
#         ].notnull(),

#         prediction_df[
#             "predicted_168h_uA"
#         ]

#         -

#         prediction_df[
#             TARGET
#         ],

#         np.nan

#     )


#     prediction_df[
#         "absolute_prediction_error_uA"
#     ] = (

#         prediction_df[
#             "prediction_error_uA"
#         ].abs()

#     )


#     # ========================================================
#     # PREDICTED DRIFT
#     # ========================================================

#     prediction_df[
#         "predicted_drift_uA"
#     ] = (

#         prediction_df[
#             "predicted_168h_uA"
#         ]

#         -

#         prediction_df[
#             "iddq_0h_uA"
#         ]

#     )


#     prediction_df[
#         "predicted_drift_rate"
#     ] = (

#         prediction_df[
#             "predicted_drift_uA"
#         ]

#         /

#         TARGET_HOUR

#     )


#     # ========================================================
#     # RELATIVE DRIFT
#     # ========================================================

#     prediction_df[
#         "predicted_relative_drift"
#     ] = np.where(

#         prediction_df[
#             "iddq_0h_uA"
#         ] != 0,

#         (

#             prediction_df[
#                 "predicted_168h_uA"
#             ]

#             -

#             prediction_df[
#                 "iddq_0h_uA"
#             ]

#         )

#         /

#         prediction_df[
#             "iddq_0h_uA"
#         ],

#         0

#     )


#     # ========================================================
#     # ACTUAL DRIFT
#     # ========================================================

#     prediction_df[
#         "actual_drift_uA"
#     ] = np.where(

#         prediction_df[
#             TARGET
#         ].notnull(),

#         prediction_df[
#             TARGET
#         ]

#         -

#         prediction_df[
#             "iddq_0h_uA"
#         ],

#         np.nan

#     )


#     prediction_df[
#         "actual_drift_rate"
#     ] = (

#         prediction_df[
#             "actual_drift_uA"
#         ]

#         /

#         TARGET_HOUR

#     )


#     # ========================================================
#     # SAFETY SLOPE
#     # ========================================================

#     prediction_df[
#         "safety_slope"
#     ] = float(

#         safety_slope

#     )


#     prediction_df[
#         "drift_slope_excess"
#     ] = (

#         prediction_df[
#             "predicted_drift_rate"
#         ]

#         -

#         prediction_df[
#             "safety_slope"
#         ]

#     )


#     # ========================================================
#     # EARLY DRIFT FLAG
#     # ========================================================

#     prediction_df[
#         "early_drift_flag"
#     ] = (

#         prediction_df[
#             "predicted_drift_rate"
#         ]

#         >

#         prediction_df[
#             "safety_slope"
#         ]

#     )


#     # ========================================================
#     # STATIC LIMIT
#     # ========================================================

#     prediction_df[
#         "predicted_limit_exceeded"
#     ] = (

#         prediction_df[
#             "predicted_168h_uA"
#         ]

#         >

#         prediction_df[
#             "absolute_limit_uA"
#         ]

#     )


#     # ========================================================
#     # UNCERTAINTY-ADJUSTED FAILURE
#     # ========================================================

#     prediction_df[
#         "uncertainty_adjusted_failure"
#     ] = (

#         prediction_df[
#             "prediction_upper_uA"
#         ]

#         >

#         prediction_df[
#             "absolute_limit_uA"
#         ]

#     )


#     # ========================================================
#     # LIMIT MARGINS
#     # ========================================================

#     prediction_df[
#         "limit_margin_uA"
#     ] = (

#         prediction_df[
#             "absolute_limit_uA"
#         ]

#         -

#         prediction_df[
#             "predicted_168h_uA"
#         ]

#     )


#     prediction_df[
#         "upper_bound_limit_margin_uA"
#     ] = (

#         prediction_df[
#             "absolute_limit_uA"
#         ]

#         -

#         prediction_df[
#             "prediction_upper_uA"
#         ]

#     )


#     # ========================================================
#     # FUTURE DRIFT RISK
#     # ========================================================

#     def calculate_drift_risk(row):

#         slope = row[
#             "predicted_drift_rate"
#         ]


#         if (

#             row[
#                 "uncertainty_adjusted_failure"
#             ]

#             or

#             row[
#                 "predicted_limit_exceeded"
#             ]

#         ):

#             return "HIGH"


#         elif (

#             slope

#             >

#             row[
#                 "safety_slope"
#             ]

#         ):

#             return "MEDIUM"


#         elif (

#             slope

#             >

#             row[
#                 "safety_slope"
#             ] * 0.80

#         ):

#             return "WATCH"


#         return "LOW"


#     prediction_df[
#         "future_drift_risk"
#     ] = prediction_df.apply(

#         calculate_drift_risk,

#         axis=1

#     )


#     # ========================================================
#     # MODULE B DECISION
#     # ========================================================

#     def module_b_decision(row):

#         if row[
#             "uncertainty_adjusted_failure"
#         ]:

#             return "PREDICTED_FAILURE"


#         elif row[
#             "predicted_limit_exceeded"
#         ]:

#             return "PREDICTED_FAILURE"


#         elif row[
#             "early_drift_flag"
#         ]:

#             return "EARLY_DRIFT_RISK"


#         return "NORMAL"


#     prediction_df[
#         "module_b_status"
#     ] = prediction_df.apply(

#         module_b_decision,

#         axis=1

#     )


#     # ========================================================
#     # EXPLANATION
#     # ========================================================

#     def module_b_explanation(row):

#         reasons = []


#         if row[
#             "predicted_limit_exceeded"
#         ]:

#             reasons.append(

#                 "Point prediction exceeds absolute "
#                 "specification limit"

#             )


#         if row[
#             "uncertainty_adjusted_failure"
#         ]:

#             reasons.append(

#                 "Prediction uncertainty interval "
#                 "reaches or exceeds absolute limit"

#             )


#         if row[
#             "early_drift_flag"
#         ]:

#             reasons.append(

#                 "Predicted future drift exceeds "
#                 "dynamic safety boundary"

#             )


#         if (

#             row[
#                 "early_drift_flag"
#             ]

#             and

#             not row[
#                 "predicted_limit_exceeded"
#             ]

#         ):

#             reasons.append(

#                 "Component is below static limit "
#                 "but shows abnormal future drift"

#             )


#         if len(reasons) == 0:

#             return (

#                 "Predicted 168h behavior remains "
#                 "within the dynamic safety boundary."

#             )


#         return "; ".join(

#             reasons

#         )


#     prediction_df[
#         "module_b_explanation"
#     ] = prediction_df.apply(

#         module_b_explanation,

#         axis=1

#     )


#     # ========================================================
#     # MODEL TEST PERFORMANCE
#     # ========================================================

#     test_prediction = best_model.predict(

#         X_test

#     )


#     test_mae = mean_absolute_error(

#         y_test,

#         test_prediction

#     )


#     test_rmse = np.sqrt(

#         mean_squared_error(

#             y_test,

#             test_prediction

#         )

#     )


#     test_r2 = r2_score(

#         y_test,

#         test_prediction

#     )


#     # ========================================================
#     # TEST EVALUATION
#     # ========================================================

#     test_evaluation_df = (

#         prediction_df.iloc[
#             test_indices
#         ].copy()

#     )


#     test_actual_binary = (

#         test_evaluation_df[
#             "actual_abnormal"
#         ].astype(int)

#     )


#     test_evaluation_df[
#         "module_b_predicted_risk"
#     ] = (

#         test_evaluation_df[
#             "module_b_status"
#         ]

#         !=

#         "NORMAL"

#     )


#     test_predicted_binary = (

#         test_evaluation_df[
#             "module_b_predicted_risk"
#         ].astype(int)

#     )


#     classification_precision = precision_score(

#         test_actual_binary,

#         test_predicted_binary,

#         zero_division=0

#     )


#     classification_recall = recall_score(

#         test_actual_binary,

#         test_predicted_binary,

#         zero_division=0

#     )


#     classification_f1 = f1_score(

#         test_actual_binary,

#         test_predicted_binary,

#         zero_division=0

#     )


#     cm = confusion_matrix(

#         test_actual_binary,

#         test_predicted_binary

#     )


#     # ========================================================
#     # PRINT STAGE RESULTS
#     # ========================================================

#     print("\n" + "=" * 80)

#     print(

#         f"STAGE {stage_number} RESULTS"

#     )

#     print("=" * 80)


#     print(

#         f"\nCumulative components:"
#         f" {len(prediction_df)}"

#     )


#     print(

#         f"Best model:"
#         f" {best_model_name}"

#     )


#     print(

#         f"Test MAE:"
#         f" {test_mae:.4f} µA"

#     )


#     print(

#         f"Test RMSE:"
#         f" {test_rmse:.4f} µA"

#     )


#     print(

#         f"Test R²:"
#         f" {test_r2:.4f}"

#     )


#     print(

#         f"Safety slope:"
#         f" {safety_slope:.6f} µA/hour"

#     )


#     print(

#         f"Prediction interval:"
#         f" ±{prediction_interval_radius:.4f} µA"

#     )


#     print("\nModule B status:")


#     print(

#         prediction_df[
#             "module_b_status"
#         ].value_counts()

#     )


#     print("\nFuture drift risk:")


#     print(

#         prediction_df[
#             "future_drift_risk"
#         ].value_counts()

#     )


#     print("\nTest classification:")


#     print(

#         f"Precision: "
#         f"{classification_precision:.4f}"

#     )


#     print(

#         f"Recall: "
#         f"{classification_recall:.4f}"

#     )


#     print(

#         f"F1: "
#         f"{classification_f1:.4f}"

#     )


#     print("\nConfusion Matrix:")


#     print(cm)


#     # ========================================================
#     # SAVE STAGE RESULT
#     # ========================================================

#     stage_count = len(

#         prediction_df

#     )


#     stage_output_path = STAGE_OUTPUT_TEMPLATE.format(

#         stage=stage_number,

#         count=stage_count

#     )


#     prediction_df.to_csv(

#         stage_output_path,

#         index=False

#     )


#     print(

#         f"\nStage output saved:"
#         f"\n{stage_output_path}"

#     )


#     # ========================================================
#     # RETURN EVERYTHING NEEDED
#     # ========================================================

#     return {

#         "data":
#             prediction_df,

#         "model":
#             best_model,

#         "model_name":
#             best_model_name,

#         "safety_slope":
#             float(safety_slope),

#         "prediction_interval_radius":
#             float(
#                 prediction_interval_radius
#             ),

#         "test_mae":
#             float(test_mae),

#         "test_rmse":
#             float(test_rmse),

#         "test_r2":
#             float(test_r2),

#         "precision":
#             float(
#                 classification_precision
#             ),

#         "recall":
#             float(
#                 classification_recall
#             ),

#         "f1":
#             float(
#                 classification_f1
#             )

#     }


# # ============================================================
# # STEP 10: CUMULATIVE PROCESSING
# # ============================================================

# print("\n" + "=" * 80)

# print(
#     "STARTING CUMULATIVE PROCESSING"
# )

# print("=" * 80)


# cumulative_df = pd.DataFrame()

# stage_results = []


# for stage_number, file_path in enumerate(

#     CSV_FILES,

#     start=1

# ):

#     print("\n")

#     print("#" * 80)

#     print(

#         f"READING BATCH {stage_number}"

#     )

#     print("#" * 80)


#     # --------------------------------------------------------
#     # Load current batch
#     # --------------------------------------------------------

#     batch_df = load_and_standardize_csv(

#         file_path

#     )


#     print(

#         f"\nBatch {stage_number} rows:"
#         f" {len(batch_df)}"

#     )


#     # --------------------------------------------------------
#     # Add current batch to cumulative dataset
#     # --------------------------------------------------------

#     cumulative_df = pd.concat(

#         [

#             cumulative_df,

#             batch_df

#         ],

#         ignore_index=True

#     )


#     # --------------------------------------------------------
#     # IMPORTANT:
#     #
#     # The prediction receives cumulative_df,
#     # NOT batch_df.
#     #
#     # --------------------------------------------------------

#     result = run_cumulative_stage(

#         cumulative_df,

#         stage_number

#     )


#     if result is not None:

#         stage_results.append(

#             result

#         )


# # ============================================================
# # STEP 11: FINAL RESULT
# # ============================================================

# if len(stage_results) == 0:

#     raise RuntimeError(

#         "No valid Module B stage was completed."

#     )


# final_result = stage_results[-1]


# final_df = final_result[
#     "data"
# ]


# # ============================================================
# # STEP 12: SAVE FINAL RESULTS
# # ============================================================

# final_df.to_csv(

#     FINAL_OUTPUT_PATH,

#     index=False

# )


# # ============================================================
# # STEP 13: SAVE FINAL MODEL PACKAGE
# # ============================================================

# model_package = {

#     "model":
#         final_result[
#             "model"
#         ],

#     "model_name":
#         final_result[
#             "model_name"
#         ],

#     "input_features":
#         MODEL_FEATURES,

#     "numerical_features":
#         NUMERICAL_FEATURES,

#     "categorical_features":
#         CATEGORICAL_FEATURES,

#     "input_hours":
#         INPUT_HOURS,

#     "target_hour":
#         TARGET_HOUR,

#     "target":
#         TARGET,

#     "safety_slope":
#         final_result[
#             "safety_slope"
#         ],

#     "safety_percentile":
#         SAFETY_PERCENTILE,

#     "prediction_interval_confidence":
#         PREDICTION_INTERVAL_CONFIDENCE,

#     "prediction_interval_radius_uA":
#         final_result[
#             "prediction_interval_radius"
#         ],

#     "reference_classes":
#         REFERENCE_CLASSES,

#     "abnormal_classes":
#         ABNORMAL_CLASSES,

#     "random_state":
#         RANDOM_STATE

# }


# joblib.dump(

#     model_package,

#     MODEL_PATH

# )


# # ============================================================
# # STEP 14: FINAL SUMMARY
# # ============================================================

# print("\n")

# print("=" * 80)

# print(
#     "MODULE B COMPLETED SUCCESSFULLY"
# )

# print("=" * 80)


# print(

#     "\nCUMULATIVE PROCESSING:"
# )

# print(

#     "  Batch 1              → 2,000"

# )

# print(

#     "  Batch 1 + 2          → 4,000"

# )

# print(

#     "  Batch 1 + 2 + 3      → 6,000"

# )

# print(

#     "  Batch 1 + ... + 4    → 8,000"

# )

# print(

#     "  All 5 batches        → 10,000"

# )


# print("\nMODEL INPUTS:")


# for feature in MODEL_FEATURES:

#     print(

#         f"  ✓ {feature}"

#     )


# print("\nPREDICTION:")


# print(

#     f"  {TARGET} "
#     f"← early 0h + 24h observations"

# )


# print("\nFINAL MODEL:")


# print(

#     f"  {final_result['model_name']}"

# )


# print("\nFINAL TEST PERFORMANCE:")


# print(

#     f"  MAE  : "
#     f"{final_result['test_mae']:.4f} µA"

# )


# print(

#     f"  RMSE : "
#     f"{final_result['test_rmse']:.4f} µA"

# )


# print(

#     f"  R²   : "
#     f"{final_result['test_r2']:.4f}"

# )


# print("\nFINAL OUTPUT:")


# print(

#     f"  {FINAL_OUTPUT_PATH}"

# )


# print("\nMODEL:")


# print(

#     f"  {MODEL_PATH}"

# )


# print("\n" + "=" * 80)











# ============================================================
# MODULE B
# Early-Life Trajectory Prediction + Prediction Intervals
#
# DATA SPLIT
#
#   Batch 1 + Batch 2 + Batch 3
#       6,000 components
#              ↓
#           TRAIN MODEL
#
#   Batch 4
#       2,000 components
#              ↓
#       CALIBRATE PREDICTION INTERVAL
#
#   Batch 5
#       2,000 components
#              ↓
#        FINAL UNSEEN TEST
#
#
# FINAL OUTPUT
#
#   Predictions are generated for ALL 10,000 components.
#
# IMPORTANT:
#
#   Model inputs are ONLY information available by 24h:
#
#       temperature_C
#       voltage_V
#       iddq_0h_uA
#       iddq_24h_uA
#       leakage_0h_uA
#       leakage_24h_uA
#       delta_0_24
#       component_type
#
#   NEVER used as model inputs:
#
#       iddq_96h_uA
#       iddq_168h_uA
#       leakage_96h_uA
#       leakage_168h_uA
#       ground_truth
#       component_id
#       lot_id
#       absolute_limit_uA
#
# ============================================================


from pathlib import Path
import json
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


warnings.filterwarnings("ignore")


# ============================================================
# 1. PROJECT PATHS
# ============================================================

BASE_DIR = Path(
    r"C:\Users\peris\Desktop\SIH2k26"
)

DATA_DIR = BASE_DIR / "data"

MODEL_DIR = BASE_DIR / "models"

MODULE_B_DIR = DATA_DIR / "module_B"

MODULE_B_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# 2. BATCH FILES
# ============================================================

BATCH_FILES = [
    DATA_DIR / "batch_1.csv",
    DATA_DIR / "batch_2.csv",
    DATA_DIR / "batch_3.csv",
    DATA_DIR / "batch_4.csv",
    DATA_DIR / "batch_5.csv",
]


# ============================================================
# 3. OUTPUT FILES
# ============================================================

FINAL_PREDICTION_FILE = (
    MODULE_B_DIR
    / "module_B_predictions.csv"
)

FINAL_MODEL_FILE = (
    MODEL_DIR
    / "module_B_0h_24h_to_168h.joblib"
)

CONFIG_FILE = (
    MODEL_DIR
    / "module_B_0h_24h_config.json"
)


# ============================================================
# 4. EXPECTED DATASET COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "component_id",
    "lot_id",
    "component_type",
    "temperature_C",
    "voltage_V",
    "iddq_0h_uA",
    "iddq_24h_uA",
    "iddq_96h_uA",
    "iddq_168h_uA",
    "leakage_0h_uA",
    "leakage_24h_uA",
    "leakage_96h_uA",
    "leakage_168h_uA",
    "ground_truth",
    "absolute_limit_uA",
]


# ============================================================
# 5. MODEL FEATURES
# ============================================================

NUMERIC_FEATURES = [
    "temperature_C",
    "voltage_V",
    "iddq_0h_uA",
    "iddq_24h_uA",
    "leakage_0h_uA",
    "leakage_24h_uA",
    "delta_0_24",
]


CATEGORICAL_FEATURES = [
    "component_type",
]


MODEL_FEATURES = (
    NUMERIC_FEATURES
    +
    CATEGORICAL_FEATURES
)


TARGET = "iddq_168h_uA"


# ============================================================
# 6. CONFORMAL SETTINGS
# ============================================================

# 90% prediction interval.
#
# Meaning:
#
# The calibration procedure attempts to construct
# intervals with approximately 90% marginal coverage
# for future exchangeable observations.
#
# This is NOT a guarantee that every individual
# component will be inside its interval.

CONFIDENCE_LEVEL = 0.90

ALPHA = 1.0 - CONFIDENCE_LEVEL


# ============================================================
# 7. LOAD ONE BATCH
# ============================================================

def load_batch(
    path: Path,
    batch_number: int,
) -> pd.DataFrame:

    if not path.exists():

        raise FileNotFoundError(
            f"\nBatch file not found:\n{path}"
        )

    df = pd.read_csv(path)

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"\nBatch {batch_number} is missing "
            f"the following columns:\n"
            f"{missing_columns}\n\n"
            f"Available columns:\n"
            f"{list(df.columns)}"
        )

    df = df.copy()

    # Keep track of where every component came from.
    df["batch_number"] = batch_number

    # --------------------------------------------------------
    # Derived early-life feature
    # --------------------------------------------------------

    df["delta_0_24"] = (
        df["iddq_24h_uA"]
        -
        df["iddq_0h_uA"]
    )

    return df


# ============================================================
# 8. LOAD ALL FIVE BATCHES
# ============================================================

def load_all_batches():

    print("\n")
    print("=" * 72)
    print("LOADING MODULE B DATA")
    print("=" * 72)

    batches = []

    for batch_number, path in enumerate(
        BATCH_FILES,
        start=1,
    ):

        df = load_batch(
            path,
            batch_number,
        )

        print(
            f"Batch {batch_number}: "
            f"{len(df):,} components"
        )

        batches.append(df)

    combined_df = pd.concat(
        batches,
        ignore_index=True,
    )

    print("-" * 72)

    print(
        f"Total components: "
        f"{len(combined_df):,}"
    )

    if len(combined_df) != 10000:

        raise ValueError(
            "Expected exactly 10,000 components "
            f"but found {len(combined_df):,}."
        )

    for batch_number, df in enumerate(
        batches,
        start=1,
    ):

        if len(df) != 2000:

            raise ValueError(
                f"Batch {batch_number} should contain "
                f"2,000 components but contains "
                f"{len(df):,}."
            )

    print(
        "Batch-size validation: PASS"
    )

    print(
        "Total-size validation: PASS"
    )

    return batches, combined_df


# ============================================================
# 9. VALIDATE DATA
# ============================================================

def validate_data(
    combined_df: pd.DataFrame,
):

    print("\n")
    print("=" * 72)
    print("VALIDATING DATA")
    print("=" * 72)

    # --------------------------------------------------------
    # Duplicate component IDs
    # --------------------------------------------------------

    duplicate_count = (
        combined_df[
            "component_id"
        ]
        .duplicated()
        .sum()
    )

    print(
        f"Duplicate component IDs: "
        f"{duplicate_count}"
    )

    if duplicate_count > 0:

        raise ValueError(
            "Duplicate component IDs detected."
        )

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    important_columns = (
        MODEL_FEATURES
        +
        [
            TARGET,
            "ground_truth",
            "absolute_limit_uA",
        ]
    )

    missing_counts = (
        combined_df[
            important_columns
        ]
        .isna()
        .sum()
    )

    missing_total = (
        missing_counts.sum()
    )

    print(
        f"Missing required values: "
        f"{missing_total}"
    )

    if missing_total > 0:

        print(
            missing_counts[
                missing_counts > 0
            ]
        )

        raise ValueError(
            "Missing values detected."
        )

    # --------------------------------------------------------
    # Specification
    # --------------------------------------------------------

    if (
        combined_df[
            "absolute_limit_uA"
        ]
        <= 0
    ).any():

        raise ValueError(
            "Invalid absolute specification limit."
        )

    # --------------------------------------------------------
    # Forbidden model inputs
    # --------------------------------------------------------

    forbidden_inputs = [
        "iddq_96h_uA",
        "iddq_168h_uA",
        "leakage_96h_uA",
        "leakage_168h_uA",
        "ground_truth",
        "component_id",
        "lot_id",
        "absolute_limit_uA",
    ]

    leakage = [
        feature
        for feature in MODEL_FEATURES
        if feature in forbidden_inputs
    ]

    if leakage:

        raise ValueError(
            "Forbidden feature leakage detected:\n"
            f"{leakage}"
        )

    print(
        "Duplicate check: PASS"
    )

    print(
        "Missing-value check: PASS"
    )

    print(
        "Future-data leakage check: PASS"
    )

    print(
        "Specification check: PASS"
    )


# ============================================================
# 10. CREATE RANDOM FOREST PIPELINE
# ============================================================

def create_model():

    # --------------------------------------------------------
    # Numeric preprocessing
    # --------------------------------------------------------

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                ),
            ),
        ]
    )

    # --------------------------------------------------------
    # Categorical preprocessing
    # --------------------------------------------------------

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                ),
            ),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
            ),
        ]
    )

    # --------------------------------------------------------
    # Column transformer
    # --------------------------------------------------------

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    # --------------------------------------------------------
    # Random Forest
    # --------------------------------------------------------

    random_forest = RandomForestRegressor(
        n_estimators=400,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1,
    )

    # --------------------------------------------------------
    # Complete pipeline
    # --------------------------------------------------------

    pipeline = Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "model",
                random_forest,
            ),
        ]
    )

    return pipeline


# ============================================================
# 11. BASELINE
# ============================================================

def calculate_baseline(
    df: pd.DataFrame,
):

    return (
        df["iddq_24h_uA"]
        +
        6.0
        *
        (
            df["iddq_24h_uA"]
            -
            df["iddq_0h_uA"]
        )
    )


# ============================================================
# 12. REGRESSION METRICS
# ============================================================

def calculate_regression_metrics(
    actual,
    predicted,
):

    mae = mean_absolute_error(
        actual,
        predicted,
    )

    rmse = np.sqrt(
        mean_squared_error(
            actual,
            predicted,
        )
    )

    r2 = r2_score(
        actual,
        predicted,
    )

    return {
        "MAE": float(mae),
        "RMSE": float(rmse),
        "R2": float(r2),
    }


# ============================================================
# 13. SPECIFICATION METRICS
# ============================================================

def calculate_specification_metrics(
    actual,
    predicted,
    limits,
):

    actual_violation = (
        actual >= limits
    )

    predicted_violation = (
        predicted >= limits
    )

    true_positive = int(
        np.sum(
            actual_violation
            &
            predicted_violation
        )
    )

    true_negative = int(
        np.sum(
            ~actual_violation
            &
            ~predicted_violation
        )
    )

    false_positive = int(
        np.sum(
            ~actual_violation
            &
            predicted_violation
        )
    )

    false_negative = int(
        np.sum(
            actual_violation
            &
            ~predicted_violation
        )
    )

    precision = (
        true_positive
        /
        (true_positive + false_positive)
        if (
            true_positive
            +
            false_positive
        ) > 0
        else 0.0
    )

    recall = (
        true_positive
        /
        (true_positive + false_negative)
        if (
            true_positive
            +
            false_negative
        ) > 0
        else 0.0
    )

    f1 = (
        2.0
        *
        precision
        *
        recall
        /
        (precision + recall)
        if (
            precision + recall
        ) > 0
        else 0.0
    )

    return {
        "actual_violations": int(
            actual_violation.sum()
        ),
        "predicted_violations": int(
            predicted_violation.sum()
        ),
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": float(
            precision
        ),
        "recall": float(
            recall
        ),
        "f1": float(f1),
    }


# ============================================================
# 14. ERROR BY GROUND TRUTH
# ============================================================

def error_by_ground_truth(
    df: pd.DataFrame,
    prediction_column: str,
):

    results = {}

    for label, group in df.groupby(
        "ground_truth"
    ):

        metrics = (
            calculate_regression_metrics(
                group[TARGET],
                group[prediction_column],
            )
        )

        results[str(label)] = metrics

    return results


# ============================================================
# 15. CONFORMAL CALIBRATION
# ============================================================
#
# We use Batch 4 only here.
#
# The model has already been trained on Batch 1-3.
#
# For every Batch-4 component:
#
#     residual = |actual_168h - predicted_168h|
#
# Then calculate the finite-sample conformal quantile.
#
# Prediction interval:
#
#     lower = prediction - q
#     upper = prediction + q
#
# ============================================================

def calibrate_prediction_interval(
    model,
    calibration_df: pd.DataFrame,
):

    print("\n")
    print("=" * 72)
    print("PREDICTION INTERVAL CALIBRATION")
    print("=" * 72)

    print(
        "\nCalibration data: Batch 4"
    )

    print(
        f"Calibration components: "
        f"{len(calibration_df):,}"
    )

    # --------------------------------------------------------
    # Predict Batch 4
    # --------------------------------------------------------

    calibration_predictions = (
        model.predict(
            calibration_df[
                MODEL_FEATURES
            ]
        )
    )

    actual_values = (
        calibration_df[
            TARGET
        ]
        .to_numpy()
    )

    # --------------------------------------------------------
    # Absolute nonconformity scores
    # --------------------------------------------------------

    absolute_residuals = np.abs(
        actual_values
        -
        calibration_predictions
    )

    n = len(
        absolute_residuals
    )

    # --------------------------------------------------------
    # Finite-sample conformal quantile
    #
    # For confidence 1-alpha:
    #
    # k = ceil((n + 1) * (1-alpha))
    #
    # q = k-th smallest residual
    #
    # This gives a conservative finite-sample
    # split-conformal interval.
    # --------------------------------------------------------

    k = int(
        np.ceil(
            (n + 1)
            *
            CONFIDENCE_LEVEL
        )
    )

    # Convert k to zero-based index.
    k_index = min(
        max(k - 1, 0),
        n - 1,
    )

    sorted_residuals = np.sort(
        absolute_residuals
    )

    conformal_q = float(
        sorted_residuals[
            k_index
        ]
    )

    # --------------------------------------------------------
    # Calibration intervals
    # --------------------------------------------------------

    lower = (
        calibration_predictions
        -
        conformal_q
    )

    upper = (
        calibration_predictions
        +
        conformal_q
    )

    coverage = np.mean(
        (
            actual_values >= lower
        )
        &
        (
            actual_values <= upper
        )
    )

    mean_width = np.mean(
        upper - lower
    )

    print(
        f"\nConfidence level: "
        f"{CONFIDENCE_LEVEL * 100:.1f}%"
    )

    print(
        f"Alpha: "
        f"{ALPHA:.4f}"
    )

    print(
        f"Calibration residual quantile: "
        f"{conformal_q:.6f} µA"
    )

    print(
        f"Calibration empirical coverage: "
        f"{coverage * 100:.2f}%"
    )

    print(
        f"Prediction interval width: "
        f"{mean_width:.6f} µA"
    )

    return {
        "conformal_q": conformal_q,
        "confidence_level": CONFIDENCE_LEVEL,
        "alpha": ALPHA,
        "calibration_rows": int(n),
        "calibration_coverage": float(
            coverage
        ),
        "mean_interval_width": float(
            mean_width
        ),
    }


# ============================================================
# 16. ADD PREDICTION INTERVAL
# ============================================================

def add_prediction_interval(
    predictions,
    conformal_q,
):

    lower = (
        predictions
        -
        conformal_q
    )

    upper = (
        predictions
        +
        conformal_q
    )

    return lower, upper


# ============================================================
# 17. FEATURE IMPORTANCE
# ============================================================

def get_feature_importance(
    model,
):

    preprocessor = model[
        "preprocessor"
    ]

    forest = model[
        "model"
    ]

    feature_names = (
        preprocessor
        .get_feature_names_out()
    )

    importances = (
        forest.feature_importances_
    )

    importance_df = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": importances,
        }
    )

    importance_df = (
        importance_df
        .sort_values(
            "importance",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    return importance_df


# ============================================================
# 18. STAGE 1
#     TRAIN ON 6,000
# ============================================================

def train_on_first_three_batches(
    batches,
):

    print("\n")
    print("=" * 72)
    print("STAGE 1 - MODEL TRAINING")
    print("=" * 72)

    train_df = pd.concat(
        batches[:3],
        ignore_index=True,
    )

    print(
        "\nTraining batches:"
        "\n  Batch 1"
        "\n  Batch 2"
        "\n  Batch 3"
    )

    print(
        f"\nTraining components: "
        f"{len(train_df):,}"
    )

    if len(train_df) != 6000:

        raise ValueError(
            "Training set should contain "
            f"6,000 rows, found {len(train_df):,}."
        )

    model = create_model()

    print(
        "\nTraining Random Forest..."
    )

    model.fit(
        train_df[
            MODEL_FEATURES
        ],
        train_df[TARGET],
    )

    print(
        "Training complete."
    )

    return (
        model,
        train_df,
    )


# ============================================================
# 19. STAGE 2
#     BATCH 4 CALIBRATION
# ============================================================

def run_calibration(
    model,
    batch_4,
):

    calibration_results = (
        calibrate_prediction_interval(
            model,
            batch_4,
        )
    )

    return calibration_results


# ============================================================
# 20. STAGE 3
#     BATCH 5 INDEPENDENT TEST
# ============================================================

def run_unseen_test(
    model,
    batch_5,
    conformal_q,
):

    print("\n")
    print("=" * 72)
    print("STAGE 3 - FINAL UNSEEN TEST")
    print("=" * 72)

    print(
        "\nBatch 5 was NOT used for:"
        "\n  - model training"
        "\n  - interval calibration"
    )

    print(
        "\nTherefore Batch 5 is the "
        "independent unseen test set."
    )

    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    predictions = model.predict(
        batch_5[
            MODEL_FEATURES
        ]
    )

    actual = (
        batch_5[
            TARGET
        ]
        .to_numpy()
    )

    # --------------------------------------------------------
    # Intervals
    # --------------------------------------------------------

    lower, upper = (
        add_prediction_interval(
            predictions,
            conformal_q,
        )
    )

    # --------------------------------------------------------
    # Regression metrics
    # --------------------------------------------------------

    model_metrics = (
        calculate_regression_metrics(
            actual,
            predictions,
        )
    )

    # --------------------------------------------------------
    # Baseline
    # --------------------------------------------------------

    baseline = (
        calculate_baseline(
            batch_5
        )
        .to_numpy()
    )

    baseline_metrics = (
        calculate_regression_metrics(
            actual,
            baseline,
        )
    )

    # --------------------------------------------------------
    # Specification metrics
    # --------------------------------------------------------

    specification_metrics = (
        calculate_specification_metrics(
            actual,
            predictions,
            batch_5[
                "absolute_limit_uA"
            ].to_numpy(),
        )
    )

    # --------------------------------------------------------
    # Prediction interval coverage
    # --------------------------------------------------------

    interval_coverage = np.mean(
        (
            actual >= lower
        )
        &
        (
            actual <= upper
        )
    )

    interval_width = np.mean(
        upper - lower
    )

    # --------------------------------------------------------
    # Error by ground truth
    # --------------------------------------------------------

    evaluation_df = (
        batch_5.copy()
    )

    evaluation_df[
        "predicted_168h"
    ] = predictions

    evaluation_df[
        "prediction_interval_lower"
    ] = lower

    evaluation_df[
        "prediction_interval_upper"
    ] = upper

    evaluation_df[
        "absolute_prediction_error"
    ] = np.abs(
        actual
        -
        predictions
    )

    ground_truth_metrics = (
        error_by_ground_truth(
            evaluation_df,
            "predicted_168h",
        )
    )

    # --------------------------------------------------------
    # Print
    # --------------------------------------------------------

    print("\n")
    print("-" * 72)
    print("BATCH 5 REGRESSION PERFORMANCE")
    print("-" * 72)

    print(
        f"MAE  : "
        f"{model_metrics['MAE']:.4f}"
    )

    print(
        f"RMSE : "
        f"{model_metrics['RMSE']:.4f}"
    )

    print(
        f"R²   : "
        f"{model_metrics['R2']:.4f}"
    )

    print("\n")
    print("-" * 72)
    print("BASELINE PERFORMANCE")
    print("-" * 72)

    print(
        f"MAE  : "
        f"{baseline_metrics['MAE']:.4f}"
    )

    print(
        f"RMSE : "
        f"{baseline_metrics['RMSE']:.4f}"
    )

    print(
        f"R²   : "
        f"{baseline_metrics['R2']:.4f}"
    )

    print("\n")
    print("-" * 72)
    print("BATCH 5 SPECIFICATION PERFORMANCE")
    print("-" * 72)

    print(
        f"Actual violations    : "
        f"{specification_metrics['actual_violations']}"
    )

    print(
        f"Predicted violations : "
        f"{specification_metrics['predicted_violations']}"
    )

    print(
        f"True positives       : "
        f"{specification_metrics['true_positive']}"
    )

    print(
        f"False positives      : "
        f"{specification_metrics['false_positive']}"
    )

    print(
        f"False negatives      : "
        f"{specification_metrics['false_negative']}"
    )

    print(
        f"Precision            : "
        f"{specification_metrics['precision']:.4f}"
    )

    print(
        f"Recall               : "
        f"{specification_metrics['recall']:.4f}"
    )

    print(
        f"F1                   : "
        f"{specification_metrics['f1']:.4f}"
    )

    print("\n")
    print("-" * 72)
    print("BATCH 5 PREDICTION INTERVAL PERFORMANCE")
    print("-" * 72)

    print(
        f"Target confidence   : "
        f"{CONFIDENCE_LEVEL * 100:.1f}%"
    )

    print(
        f"Observed coverage   : "
        f"{interval_coverage * 100:.2f}%"
    )

    print(
        f"Mean interval width : "
        f"{interval_width:.4f} µA"
    )

    print("\n")
    print("-" * 72)
    print("ERROR BY GROUND TRUTH")
    print("-" * 72)

    for label, metrics in (
        ground_truth_metrics.items()
    ):

        print(
            f"{label:20s} "
            f"MAE={metrics['MAE']:.4f} "
            f"RMSE={metrics['RMSE']:.4f} "
            f"R2={metrics['R2']:.4f}"
        )

    return {
        "model_metrics": model_metrics,
        "baseline_metrics": baseline_metrics,
        "specification_metrics": specification_metrics,
        "prediction_interval": {
            "confidence_level": (
                CONFIDENCE_LEVEL
            ),
            "observed_test_coverage": float(
                interval_coverage
            ),
            "mean_interval_width": float(
                interval_width
            ),
            "conformal_q": float(
                conformal_q
            ),
        },
        "error_by_ground_truth": (
            ground_truth_metrics
        ),
    }


# ============================================================
# 21. GENERATE PREDICTIONS FOR ALL 10,000
# ============================================================
#
# IMPORTANT:
#
# We DO NOT retrain the model here.
#
# The evaluated model remains the model trained
# exclusively on Batch 1-3.
#
# Therefore:
#
#   Batch 1-3 = in-sample predictions
#   Batch 4   = calibration predictions
#   Batch 5   = genuine unseen predictions
#
# This preserves the integrity of the evaluation.
#
# ============================================================

def generate_all_10000_predictions(
    model,
    combined_df,
    conformal_q,
):

    print("\n")
    print("=" * 72)
    print("GENERATING PREDICTIONS FOR ALL 10,000")
    print("=" * 72)

    print(
        "\nIMPORTANT:"
    )

    print(
        "The model is still the model trained "
        "only on Batch 1-3."
    )

    print(
        "No Batch 4 or Batch 5 data is used "
        "to retrain the model."
    )

    # --------------------------------------------------------
    # Predict all 10,000
    # --------------------------------------------------------

    predictions = model.predict(
        combined_df[
            MODEL_FEATURES
        ]
    )

    if len(predictions) != 10000:

        raise ValueError(
            "Expected 10,000 predictions "
            f"but received {len(predictions):,}."
        )

    # --------------------------------------------------------
    # Prediction intervals
    # --------------------------------------------------------

    lower, upper = (
        add_prediction_interval(
            predictions,
            conformal_q,
        )
    )

    # --------------------------------------------------------
    # Create output
    # --------------------------------------------------------

    output = combined_df[
        [
            "component_id",
            "lot_id",
            "component_type",
            "temperature_C",
            "voltage_V",
            "iddq_0h_uA",
            "iddq_24h_uA",
            "leakage_0h_uA",
            "leakage_24h_uA",
            "absolute_limit_uA",
            "batch_number",
        ]
    ].copy()

    # --------------------------------------------------------
    # Derived early-life feature
    # --------------------------------------------------------

    output["delta_0_24"] = (
        output["iddq_24h_uA"]
        -
        output["iddq_0h_uA"]
    )

    # --------------------------------------------------------
    # ML prediction
    # --------------------------------------------------------

    output[
        "predicted_168h"
    ] = predictions

    # --------------------------------------------------------
    # Prediction interval
    # --------------------------------------------------------

    output[
        "prediction_interval_lower"
    ] = lower

    output[
        "prediction_interval_upper"
    ] = upper

    output[
        "prediction_interval_width"
    ] = (
        upper
        -
        lower
    )

    # --------------------------------------------------------
    # Limit utilization
    # --------------------------------------------------------

    output[
        "predicted_limit_utilization_pct"
    ] = (
        output[
            "predicted_168h"
        ]
        /
        output[
            "absolute_limit_uA"
        ]
        *
        100.0
    )

    # --------------------------------------------------------
    # Future risk
    #
    # This is NOT the final Module C decision.
    # --------------------------------------------------------

    def future_risk(
        utilization
    ):

        if utilization >= 100:

            return "CRITICAL"

        if utilization >= 80:

            return "HIGH"

        if utilization >= 60:

            return "MEDIUM"

        return "LOW"

    output[
        "future_risk"
    ] = (
        output[
            "predicted_limit_utilization_pct"
        ]
        .apply(future_risk)
    )

    # --------------------------------------------------------
    # Prediction provenance
    # --------------------------------------------------------

    def prediction_type(
        batch_number
    ):

        if batch_number <= 3:

            return "IN_SAMPLE_TRAINING"

        if batch_number == 4:

            return "CALIBRATION"

        return "UNSEEN_TEST"

    output[
        "prediction_type"
    ] = (
        output[
            "batch_number"
        ]
        .apply(prediction_type)
    )

    # --------------------------------------------------------
    # Actual 168h
    #
    # OFFLINE REFERENCE ONLY.
    #
    # It is NOT used by the model.
    # --------------------------------------------------------

    output[
        "actual_168h"
    ] = combined_df[
        "iddq_168h_uA"
    ].to_numpy()

    # --------------------------------------------------------
    # Offline prediction error
    # --------------------------------------------------------

    output[
        "absolute_prediction_error"
    ] = np.abs(
        output[
            "actual_168h"
        ]
        -
        output[
            "predicted_168h"
        ]
    )

    # --------------------------------------------------------
    # Ground truth
    #
    # OFFLINE REFERENCE ONLY.
    # --------------------------------------------------------

    output[
        "ground_truth"
    ] = combined_df[
        "ground_truth"
    ].to_numpy()

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output.to_csv(
        FINAL_PREDICTION_FILE,
        index=False,
    )

    print(
        f"\nSaved:"
        f"\n{FINAL_PREDICTION_FILE}"
    )

    print(
        f"Rows: "
        f"{len(output):,}"
    )

    return output


# ============================================================
# 22. SAVE FINAL MODEL
# ============================================================

def save_model(
    model,
):

    joblib.dump(
        model,
        FINAL_MODEL_FILE,
    )

    print(
        f"\nSaved model:"
        f"\n{FINAL_MODEL_FILE}"
    )


# ============================================================
# 23. FEATURE IMPORTANCE
# ============================================================

def print_feature_importance(
    model,
):

    print("\n")
    print("=" * 72)
    print("FEATURE IMPORTANCE")
    print("=" * 72)

    importance_df = (
        get_feature_importance(
            model
        )
    )

    for _, row in (
        importance_df.head(15)
        .iterrows()
    ):

        print(
            f"{row['feature']:40s}"
            f"{row['importance']:.6f}"
        )

    return importance_df


# ============================================================
# 24. FINAL OUTPUT SUMMARY
# ============================================================

def print_final_summary(
    output,
):

    print("\n")
    print("=" * 72)
    print("FINAL 10,000-COMPONENT OUTPUT")
    print("=" * 72)

    print(
        f"\nTotal predictions: "
        f"{len(output):,}"
    )

    # --------------------------------------------------------
    # Prediction types
    # --------------------------------------------------------

    print(
        "\nPrediction provenance:"
    )

    type_counts = (
        output[
            "prediction_type"
        ]
        .value_counts()
    )

    for prediction_type, count in (
        type_counts.items()
    ):

        print(
            f"  {prediction_type:22s}: "
            f"{count:,}"
        )

    # --------------------------------------------------------
    # Risk distribution
    # --------------------------------------------------------

    print(
        "\nFuture-risk distribution:"
    )

    risk_order = [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ]

    risk_counts = (
        output[
            "future_risk"
        ]
        .value_counts()
        .reindex(
            risk_order,
            fill_value=0,
        )
    )

    for risk, count in (
        risk_counts.items()
    ):

        percentage = (
            count
            /
            len(output)
            *
            100.0
        )

        print(
            f"  {risk:10s}: "
            f"{count:5,} "
            f"({percentage:6.2f}%)"
        )

    # --------------------------------------------------------
    # Prediction statistics
    # --------------------------------------------------------

    print(
        "\nPredicted 168h statistics:"
    )

    print(
        f"  Mean   : "
        f"{output['predicted_168h'].mean():.4f}"
    )

    print(
        f"  Median : "
        f"{output['predicted_168h'].median():.4f}"
    )

    print(
        f"  Minimum: "
        f"{output['predicted_168h'].min():.4f}"
    )

    print(
        f"  Maximum: "
        f"{output['predicted_168h'].max():.4f}"
    )

    # --------------------------------------------------------
    # Interval statistics
    # --------------------------------------------------------

    print(
        "\nPrediction interval:"
    )

    print(
        f"  Confidence level: "
        f"{CONFIDENCE_LEVEL * 100:.1f}%"
    )

    print(
        f"  Width: "
        f"{output['prediction_interval_width'].mean():.4f} µA"
    )

    # --------------------------------------------------------
    # Offline actual violation count
    # --------------------------------------------------------

    predicted_violations = (
        output[
            "predicted_168h"
        ]
        >=
        output[
            "absolute_limit_uA"
        ]
    ).sum()

    actual_violations = (
        output[
            "actual_168h"
        ]
        >=
        output[
            "absolute_limit_uA"
        ]
    ).sum()

    print(
        "\nOffline specification reference:"
    )

    print(
        f"  Predicted 168h violations: "
        f"{predicted_violations:,}"
    )

    print(
        f"  Actual 168h violations:    "
        f"{actual_violations:,}"
    )

    print(
        "\nIMPORTANT:"
    )

    print(
        "actual_168h and ground_truth are "
        "included only for offline evaluation."
    )

    print(
        "They are NOT model inputs."
    )


# ============================================================
# 25. SAVE CONFIGURATION
# ============================================================

def save_config(
    calibration_results,
    test_results,
    importance_df,
    output,
):

    config = {

        "module": "Module B",

        "description": (
            "Early-life trajectory prediction "
            "from 0h + 24h measurements to "
            "predicted 168h IDDQ with "
            "split-conformal prediction intervals."
        ),

        "target": TARGET,

        "model": {
            "type": "RandomForestRegressor",
            "n_estimators": 400,
            "max_features": "sqrt",
            "random_state": 42,
        },

        # ----------------------------------------------------
        # Data split
        # ----------------------------------------------------

        "data_split": {

            "training_batches": [
                1,
                2,
                3,
            ],

            "training_rows": 6000,

            "calibration_batch": 4,

            "calibration_rows": 2000,

            "test_batch": 5,

            "test_rows": 2000,

            "total_rows": 10000,
        },

        # ----------------------------------------------------
        # Features
        # ----------------------------------------------------

        "model_features": MODEL_FEATURES,

        "numeric_features": (
            NUMERIC_FEATURES
        ),

        "categorical_features": (
            CATEGORICAL_FEATURES
        ),

        # ----------------------------------------------------
        # Forbidden features
        # ----------------------------------------------------

        "forbidden_model_inputs": [
            "iddq_96h_uA",
            "iddq_168h_uA",
            "leakage_96h_uA",
            "leakage_168h_uA",
            "ground_truth",
            "component_id",
            "lot_id",
            "absolute_limit_uA",
        ],

        # ----------------------------------------------------
        # Prediction interval
        # ----------------------------------------------------

        "prediction_interval": {

            "method": (
                "split_conformal_prediction"
            ),

            "confidence_level": (
                CONFIDENCE_LEVEL
            ),

            "alpha": ALPHA,

            "calibration_batch": 4,

            "calibration_rows": 2000,

            "conformal_q": (
                calibration_results[
                    "conformal_q"
                ]
            ),

            "calibration_coverage": (
                calibration_results[
                    "calibration_coverage"
                ]
            ),
        },

        # ----------------------------------------------------
        # Independent test
        # ----------------------------------------------------

        "unseen_test": test_results,

        # ----------------------------------------------------
        # Feature importance
        # ----------------------------------------------------

        "feature_importance": (
            importance_df
            .to_dict(
                orient="records"
            )
        ),

        # ----------------------------------------------------
        # Final prediction file
        # ----------------------------------------------------

        "final_prediction_file": {
            "path": str(
                FINAL_PREDICTION_FILE
            ),
            "rows": int(
                len(output)
            ),
            "expected_rows": 10000,
            "prediction_model_training_rows": 6000,
        },

        # ----------------------------------------------------
        # Interpretation
        # ----------------------------------------------------

        "prediction_provenance": {

            "batch_1_to_3": (
                "IN_SAMPLE_TRAINING"
            ),

            "batch_4": (
                "CALIBRATION"
            ),

            "batch_5": (
                "UNSEEN_TEST"
            ),
        },

        "important_note": (
            "The final 10,000-row prediction file "
            "is generated by the model trained on "
            "Batch 1-3 only. Batch 4 is used only "
            "for conformal calibration and Batch 5 "
            "is kept as an independent unseen test. "
            "Predictions for Batch 1-3 are in-sample, "
            "Batch 4 predictions are calibration "
            "predictions, and Batch 5 predictions "
            "are genuine unseen predictions."
        ),
    }

    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            config,
            file,
            indent=4,
        )

    print(
        f"\nSaved configuration:"
        f"\n{CONFIG_FILE}"
    )


# ============================================================
# 26. MAIN
# ============================================================

def main():

    print("\n")
    print("=" * 72)
    print(
        "MODULE B - "
        "EARLY-LIFE TRAJECTORY PREDICTION"
    )
    print("=" * 72)

    print(
        "\nFINAL EXPERIMENT DESIGN:"
    )

    print(
        "\nBatch 1-3"
        "\n6,000 components"
        "\n       ↓"
        "\nTRAIN MODEL"
    )

    print(
        "\nBatch 4"
        "\n2,000 components"
        "\n       ↓"
        "\nCALIBRATE PREDICTION INTERVAL"
    )

    print(
        "\nBatch 5"
        "\n2,000 components"
        "\n       ↓"
        "\nINDEPENDENT UNSEEN TEST"
    )

    print(
        "\nAll 10,000"
        "\n       ↓"
        "\nGENERATE FINAL PREDICTION FILE"
    )

    # ========================================================
    # LOAD
    # ========================================================

    batches, combined_df = (
        load_all_batches()
    )

    # ========================================================
    # VALIDATE
    # ========================================================

    validate_data(
        combined_df
    )

    # ========================================================
    # TRAIN ON 6,000
    # ========================================================

    (
        model,
        train_df,
    ) = train_on_first_three_batches(
        batches
    )

    # ========================================================
    # CALIBRATE USING BATCH 4
    # ========================================================

    calibration_results = (
        run_calibration(
            model,
            batches[3],
        )
    )

    conformal_q = (
        calibration_results[
            "conformal_q"
        ]
    )

    # ========================================================
    # TEST USING BATCH 5
    # ========================================================

    test_results = (
        run_unseen_test(
            model,
            batches[4],
            conformal_q,
        )
    )

    # ========================================================
    # FEATURE IMPORTANCE
    # ========================================================

    importance_df = (
        print_feature_importance(
            model
        )
    )

    # ========================================================
    # PREDICT ALL 10,000
    # ========================================================

    final_output = (
        generate_all_10000_predictions(
            model,
            combined_df,
            conformal_q,
        )
    )

    # ========================================================
    # SAVE MODEL
    # ========================================================

    save_model(
        model
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print_final_summary(
        final_output
    )

    # ========================================================
    # SAVE CONFIG
    # ========================================================

    save_config(
        calibration_results,
        test_results,
        importance_df,
        final_output,
    )

    # ========================================================
    # COMPLETE
    # ========================================================

    print("\n")
    print("=" * 72)
    print("MODULE B COMPLETED")
    print("=" * 72)

    print(
        "\nTraining:       6,000"
    )

    print(
        "Calibration:    2,000"
    )

    print(
        "Independent test: 2,000"
    )

    print(
        "Final predictions: 10,000"
    )

    print(
        "\nPrediction file:"
    )

    print(
        FINAL_PREDICTION_FILE
    )

    print(
        "\nModel:"
    )

    print(
        FINAL_MODEL_FILE
    )

    print(
        "\nConfiguration:"
    )

    print(
        CONFIG_FILE
    )

    print(
        "\nThe Batch-5 predictions in the "
        "10,000-row file are genuine unseen "
        "predictions."
    )

    print(
        "\nModule B is ready for the next step."
    )


# ============================================================
# 27. RUN
# ============================================================

if __name__ == "__main__":
    main()