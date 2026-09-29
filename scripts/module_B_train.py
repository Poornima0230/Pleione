"""
MODULE B
0h + 24h -> 168h Future Prediction + Early Failure Risk

Purpose:
    1. Predict the continuous 168h IDDQ value.
    2. Produce a conformal prediction interval.
    3. Predict whether the component is likely to violate the
       absolute specification limit by 168h.

INFORMATION BOUNDARY
--------------------
Deployment-time model inputs:
    0h + 24h measurements only.

NOT used as model inputs:
    - 96h measurements
    - 168h measurements
    - ground_truth
    - component_id
    - lot_id
    - absolute_limit_uA

Historical 168h measurements are used ONLY as supervised targets.

MODEL SPLIT
-----------
Training:
    Batch 1 + Batch 2 + Batch 3

Conformal calibration:
    Batch 4

Unseen evaluation:
    Batch 5

IMPORTANT
---------
After training, the frozen models are applied to ALL 10,000
components for dashboard / deployment-style prediction.

Outputs:
    data/module_B/module_B_predictions.csv
        -> ALL 10,000 predictions

    data/module_B/module_B_batch5_results.csv
        -> Batch 5 evaluation only

    data/module_B/module_B_feature_importance.csv

    data/module_B/module_B_ground_truth_diagnostics.csv

Models:
    RandomForestRegressor
    RandomForestClassifier
"""

from pathlib import Path
import json
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import OneHotEncoder

warnings.filterwarnings("ignore")


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
MODULE_B_DIR = DATA_DIR / "module_B"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODULE_B_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

TRAIN_BATCHES = [
    "batch_1.csv",
    "batch_2.csv",
    "batch_3.csv",
]

CALIBRATION_BATCH = "batch_4.csv"
TEST_BATCH = "batch_5.csv"

ALL_BATCHES = [
    "batch_1.csv",
    "batch_2.csv",
    "batch_3.csv",
    "batch_4.csv",
    "batch_5.csv",
]

LIMIT_COLUMN = "absolute_limit_uA"
TARGET_COLUMN = "iddq_168h_uA"


# ============================================================
# DEPLOYMENT-TIME FEATURES
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

FEATURE_COLUMNS = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURES
)

RANDOM_STATE = 42


# ============================================================
# LOAD DATA
# ============================================================

def load_batch(filename: str) -> pd.DataFrame:

    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found:\n{path}"
        )

    df = pd.read_csv(path)

    # Derive early change using only 0h and 24h.
    df["delta_0_24"] = (
        df["iddq_24h_uA"]
        - df["iddq_0h_uA"]
    )

    df["batch"] = filename.replace(
        ".csv",
        "",
    )

    return df


def load_all_batches() -> pd.DataFrame:

    frames = []

    for filename in ALL_BATCHES:
        frames.append(
            load_batch(filename)
        )

    return pd.concat(
        frames,
        ignore_index=True,
    )


# ============================================================
# PREPARE FEATURES
# ============================================================

def prepare_features(
    df: pd.DataFrame,
) -> pd.DataFrame:

    missing = [
        column
        for column in FEATURE_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required features: {missing}"
        )

    return df[
        FEATURE_COLUMNS
    ].copy()


# ============================================================
# INFORMATION BOUNDARY
# ============================================================

FORBIDDEN_FEATURES = [
    "iddq_96h_uA",
    "iddq_168h_uA",
    "leakage_96h_uA",
    "leakage_168h_uA",
    "ground_truth",
    "absolute_limit_uA",
    "lot_id",
    "component_id",
]


def validate_information_boundary():

    for forbidden in FORBIDDEN_FEATURES:

        if forbidden in FEATURE_COLUMNS:

            raise RuntimeError(
                "INFORMATION LEAKAGE: "
                f"{forbidden} is present in model features."
            )


# ============================================================
# RISK BANDS
# ============================================================

def classify_failure_risk(
    probability: float,
) -> str:

    if probability >= 0.75:
        return "HIGH"

    if probability >= 0.40:
        return "MEDIUM"

    if probability >= 0.15:
        return "LOW"

    return "VERY_LOW"


# ============================================================
# BINARY METRICS
# ============================================================

def binary_metrics(
    actual,
    predicted,
):

    precision = precision_score(
        actual,
        predicted,
        zero_division=0,
    )

    recall = recall_score(
        actual,
        predicted,
        zero_division=0,
    )

    f1 = f1_score(
        actual,
        predicted,
        zero_division=0,
    )

    tn, fp, fn, tp = confusion_matrix(
        actual,
        predicted,
        labels=[0, 1],
    ).ravel()

    return {
        "tp": int(tp),
        "fp": int(fp),
        "fn": int(fn),
        "tn": int(tn),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print(
        "MODULE B - 0h + 24h EARLY PREDICTION"
    )
    print("=" * 70)

    validate_information_boundary()

    # --------------------------------------------------------
    # Load datasets
    # --------------------------------------------------------

    train_parts = [
        load_batch(filename)
        for filename in TRAIN_BATCHES
    ]

    train_df = pd.concat(
        train_parts,
        ignore_index=True,
    )

    calibration_df = load_batch(
        CALIBRATION_BATCH
    )

    test_df = load_batch(
        TEST_BATCH
    )

    all_df = load_all_batches()

    print("\nDATA SPLIT")
    print("-" * 70)

    print(
        f"Training              : {len(train_df):,}"
    )

    print(
        f"Calibration           : {len(calibration_df):,}"
    )

    print(
        f"Unseen test           : {len(test_df):,}"
    )

    print(
        f"Complete dataset      : {len(all_df):,}"
    )

    # --------------------------------------------------------
    # Prepare features
    # --------------------------------------------------------

    X_train = prepare_features(
        train_df
    )

    X_calibration = prepare_features(
        calibration_df
    )

    X_test = prepare_features(
        test_df
    )

    X_all = prepare_features(
        all_df
    )

    # --------------------------------------------------------
    # Targets
    # --------------------------------------------------------

    y_train_reg = (
        train_df[TARGET_COLUMN]
        .astype(float)
    )

    y_calibration_reg = (
        calibration_df[TARGET_COLUMN]
        .astype(float)
    )

    y_test_reg = (
        test_df[TARGET_COLUMN]
        .astype(float)
    )

    # Future violation target.
    y_train_failure = (
        train_df[TARGET_COLUMN]
        > train_df[LIMIT_COLUMN]
    ).astype(int)

    y_calibration_failure = (
        calibration_df[TARGET_COLUMN]
        > calibration_df[LIMIT_COLUMN]
    ).astype(int)

    y_test_failure = (
        test_df[TARGET_COLUMN]
        > test_df[LIMIT_COLUMN]
    ).astype(int)

    print("\nTARGET DISTRIBUTION")
    print("-" * 70)

    print(
        "Training future violations: "
        f"{y_train_failure.sum()} / "
        f"{len(y_train_failure)}"
    )

    print(
        "Calibration future violations: "
        f"{y_calibration_failure.sum()} / "
        f"{len(y_calibration_failure)}"
    )

    print(
        "Batch 5 future violations: "
        f"{y_test_failure.sum()} / "
        f"{len(y_test_failure)}"
    )

    # ========================================================
    # PREPROCESSOR
    # ========================================================

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                "passthrough",
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    # Fit ONLY on training data.
    X_train_processed = (
        preprocessor.fit_transform(
            X_train
        )
    )

    X_calibration_processed = (
        preprocessor.transform(
            X_calibration
        )
    )

    X_test_processed = (
        preprocessor.transform(
            X_test
        )
    )

    X_all_processed = (
        preprocessor.transform(
            X_all
        )
    )

    # ========================================================
    # MODEL A — REGRESSION
    # ========================================================

    print("\n" + "=" * 70)
    print(
        "MODEL A - 168h REGRESSION"
    )
    print("=" * 70)

    regressor = RandomForestRegressor(
        n_estimators=400,
        max_features="sqrt",
        min_samples_leaf=2,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    print(
        "\nTraining regression model..."
    )

    regressor.fit(
        X_train_processed,
        y_train_reg,
    )

    print(
        "Regression model trained."
    )

    # --------------------------------------------------------
    # Batch 4 calibration prediction
    # --------------------------------------------------------

    calibration_predictions = (
        regressor.predict(
            X_calibration_processed
        )
    )

    # --------------------------------------------------------
    # Batch 5 test prediction
    # --------------------------------------------------------

    test_predictions = (
        regressor.predict(
            X_test_processed
        )
    )

    # --------------------------------------------------------
    # ALL 10,000 prediction
    # --------------------------------------------------------

    all_predictions = (
        regressor.predict(
            X_all_processed
        )
    )

    # ========================================================
    # CONFORMAL CALIBRATION
    # ========================================================

    print("\n" + "=" * 70)
    print(
        "CONFORMAL CALIBRATION"
    )
    print("=" * 70)

    calibration_residuals = np.abs(
        y_calibration_reg.to_numpy()
        - calibration_predictions
    )

    CONFORMAL_ALPHA = 0.10

    n_calibration = (
        len(calibration_residuals)
    )

    conformal_rank = int(
        np.ceil(
            (n_calibration + 1)
            * (1 - CONFORMAL_ALPHA)
        )
    )

    conformal_rank = min(
        conformal_rank,
        n_calibration,
    )

    conformal_q = np.sort(
        calibration_residuals
    )[conformal_rank - 1]

    print(
        f"Calibration residual count : "
        f"{n_calibration}"
    )

    print(
        f"Target coverage             : "
        f"{1 - CONFORMAL_ALPHA:.2%}"
    )

    print(
        f"Conformal q                 : "
        f"{conformal_q:.4f} µA"
    )

    # Batch 5 intervals.
    prediction_lower = (
        test_predictions
        - conformal_q
    )

    prediction_upper = (
        test_predictions
        + conformal_q
    )

    prediction_interval_width = (
        prediction_upper
        - prediction_lower
    )

    # All 10,000 intervals.
    all_prediction_lower = (
        all_predictions
        - conformal_q
    )

    all_prediction_upper = (
        all_predictions
        + conformal_q
    )

    all_prediction_interval_width = (
        all_prediction_upper
        - all_prediction_lower
    )

    # ========================================================
    # MODEL B — CLASSIFIER
    # ========================================================

    print("\n" + "=" * 70)
    print(
        "MODEL B - EARLY FUTURE-FAILURE CLASSIFIER"
    )
    print("=" * 70)

    classifier = RandomForestClassifier(
        n_estimators=500,
        max_features="sqrt",
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    print(
        "\nTraining classifier..."
    )

    classifier.fit(
        X_train_processed,
        y_train_failure,
    )

    print(
        "Classifier trained."
    )

    # --------------------------------------------------------
    # Batch 5 classifier
    # --------------------------------------------------------

    test_failure_probability = (
        classifier.predict_proba(
            X_test_processed
        )[:, 1]
    )

    test_failure_class = (
        test_failure_probability >= 0.50
    ).astype(int)

    # --------------------------------------------------------
    # ALL 10,000 classifier predictions
    # --------------------------------------------------------

    all_failure_probability = (
        classifier.predict_proba(
            X_all_processed
        )[:, 1]
    )

    all_failure_class = (
        all_failure_probability >= 0.50
    ).astype(int)

    all_failure_risk = [
        classify_failure_risk(
            probability
        )
        for probability
        in all_failure_probability
    ]

    test_failure_risk = [
        classify_failure_risk(
            probability
        )
        for probability
        in test_failure_probability
    ]

    # ========================================================
    # BATCH 5 EVALUATION
    # ========================================================

    point_prediction_violation = (
        test_predictions
        > test_df[LIMIT_COLUMN].to_numpy()
    )

    upper_prediction_violation = (
        prediction_upper
        > test_df[LIMIT_COLUMN].to_numpy()
    )

    point_metrics = binary_metrics(
        y_test_failure,
        point_prediction_violation,
    )

    upper_metrics = binary_metrics(
        y_test_failure,
        upper_prediction_violation,
    )

    classifier_metrics = binary_metrics(
        y_test_failure,
        test_failure_class,
    )

    classifier_accuracy = accuracy_score(
        y_test_failure,
        test_failure_class,
    )

    try:

        classifier_auc = roc_auc_score(
            y_test_failure,
            test_failure_probability,
        )

    except ValueError:

        classifier_auc = float("nan")

    # ========================================================
    # REGRESSION METRICS
    # ========================================================

    mae = mean_absolute_error(
        y_test_reg,
        test_predictions,
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test_reg,
            test_predictions,
        )
    )

    r2 = r2_score(
        y_test_reg,
        test_predictions,
    )

    # ========================================================
    # BASELINE
    # ========================================================

    baseline_value = (
        y_train_reg.median()
    )

    baseline_predictions = np.full(
        len(y_test_reg),
        baseline_value,
    )

    baseline_mae = mean_absolute_error(
        y_test_reg,
        baseline_predictions,
    )

    baseline_rmse = np.sqrt(
        mean_squared_error(
            y_test_reg,
            baseline_predictions,
        )
    )

    baseline_r2 = r2_score(
        y_test_reg,
        baseline_predictions,
    )

    # ========================================================
    # CALIBRATION COVERAGE
    # ========================================================

    calibration_lower = (
        calibration_predictions
        - conformal_q
    )

    calibration_upper = (
        calibration_predictions
        + conformal_q
    )

    calibration_coverage = np.mean(
        (
            y_calibration_reg.to_numpy()
            >= calibration_lower
        )
        &
        (
            y_calibration_reg.to_numpy()
            <= calibration_upper
        )
    )

    # ========================================================
    # FEATURE IMPORTANCE
    # ========================================================

    try:

        categorical_encoder = (
            preprocessor
            .named_transformers_["categorical"]
        )

        categorical_names = list(
            categorical_encoder
            .get_feature_names_out(
                CATEGORICAL_FEATURES
            )
        )

        processed_feature_names = (
            NUMERIC_FEATURES
            + categorical_names
        )

    except Exception:

        processed_feature_names = [
            f"feature_{i}"
            for i in range(
                len(
                    regressor
                    .feature_importances_
                )
            )
        ]

    regression_importance = pd.DataFrame(
        {
            "feature": (
                processed_feature_names
            ),
            "regression_importance": (
                regressor
                .feature_importances_
            ),
            "classifier_importance": (
                classifier
                .feature_importances_
            ),
        }
    )

    regression_importance = (
        regression_importance
        .sort_values(
            "regression_importance",
            ascending=False,
        )
    )

    # ========================================================
    # BUILD ALL 10,000 RESULTS
    # ========================================================

    all_results = all_df[
        [
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
            "batch",
        ]
    ].copy()

    all_results["delta_0_24"] = (
        all_results["iddq_24h_uA"]
        - all_results["iddq_0h_uA"]
    )

    all_results["predicted_168h_uA"] = (
        all_predictions
    )

    all_results["prediction_lower_uA"] = (
        all_prediction_lower
    )

    all_results["prediction_upper_uA"] = (
        all_prediction_upper
    )

    all_results[
        "prediction_interval_width_uA"
    ] = (
        all_prediction_interval_width
    )

    all_results[
        "predicted_violation"
    ] = (
        all_predictions
        > all_results[
            "absolute_limit_uA"
        ].to_numpy()
    )

    all_results[
        "upper_bound_violation"
    ] = (
        all_prediction_upper
        > all_results[
            "absolute_limit_uA"
        ].to_numpy()
    )

    all_results[
        "actual_violation"
    ] = (
        all_results[
            "iddq_168h_uA"
        ]
        > all_results[
            "absolute_limit_uA"
        ]
    )

    all_results[
        "prediction_error_uA"
    ] = (
        all_results[
            "iddq_168h_uA"
        ].to_numpy()
        - all_predictions
    )

    all_results[
        "absolute_prediction_error_uA"
    ] = np.abs(
        all_results[
            "prediction_error_uA"
        ]
    )

    all_results[
        "failure_probability"
    ] = all_failure_probability

    all_results[
        "predicted_future_violation"
    ] = (
        all_failure_class.astype(bool)
    )

    all_results[
        "failure_risk"
    ] = all_failure_risk

    all_results[
        "prediction_type"
    ] = np.where(
        all_results[
            "predicted_168h_uA"
        ]
        > all_results[
            "absolute_limit_uA"
        ],
        "POINT_ABOVE_LIMIT",
        "POINT_BELOW_LIMIT",
    )

    # ========================================================
    # BATCH 5 RESULTS
    # ========================================================

    batch5_results = all_results[
        all_results["batch"] == "batch_5"
    ].copy()

    # ========================================================
    # GROUND-TRUTH DIAGNOSTICS
    # ========================================================

    diagnostics = (
        batch5_results
        .groupby("ground_truth")
        .agg(
            count=(
                "component_id",
                "count",
            ),
            actual_168h_mean=(
                "iddq_168h_uA",
                "mean",
            ),
            predicted_168h_mean=(
                "predicted_168h_uA",
                "mean",
            ),
            mae=(
                "absolute_prediction_error_uA",
                "mean",
            ),
            failure_probability_mean=(
                "failure_probability",
                "mean",
            ),
            actual_violation_rate=(
                "actual_violation",
                "mean",
            ),
        )
        .reset_index()
    )

    # ========================================================
    # SAVE ALL PREDICTIONS
    # ========================================================

    all_predictions_path = (
        MODULE_B_DIR
        / "module_B_predictions.csv"
    )

    batch5_path = (
        MODULE_B_DIR
        / "module_B_batch5_results.csv"
    )

    importance_path = (
        MODULE_B_DIR
        / "module_B_feature_importance.csv"
    )

    diagnostics_path = (
        MODULE_B_DIR
        / "module_B_ground_truth_diagnostics.csv"
    )

    all_results.to_csv(
        all_predictions_path,
        index=False,
    )

    batch5_results.to_csv(
        batch5_path,
        index=False,
    )

    regression_importance.to_csv(
        importance_path,
        index=False,
    )

    diagnostics.to_csv(
        diagnostics_path,
        index=False,
    )

    # ========================================================
    # SAVE MODELS
    # ========================================================

    regression_model_path = (
        MODEL_DIR
        / "module_B_0h_24h_to_168h.joblib"
    )

    classifier_model_path = (
        MODEL_DIR
        / "module_B_early_failure_classifier.joblib"
    )

    regression_config_path = (
        MODEL_DIR
        / "module_B_0h_24h_config.json"
    )

    classifier_config_path = (
        MODEL_DIR
        / "module_B_early_failure_config.json"
    )

    joblib.dump(
        {
            "preprocessor": preprocessor,
            "model": regressor,
            "feature_columns": FEATURE_COLUMNS,
            "numeric_features": NUMERIC_FEATURES,
            "categorical_features": (
                CATEGORICAL_FEATURES
            ),
            "target": TARGET_COLUMN,
            "conformal_q": float(
                conformal_q
            ),
            "conformal_alpha": (
                CONFORMAL_ALPHA
            ),
        },
        regression_model_path,
    )

    joblib.dump(
        {
            "preprocessor": preprocessor,
            "model": classifier,
            "feature_columns": FEATURE_COLUMNS,
            "numeric_features": NUMERIC_FEATURES,
            "categorical_features": (
                CATEGORICAL_FEATURES
            ),
            "target": (
                "future_168h_violation"
            ),
            "probability_threshold": 0.50,
            "risk_thresholds": {
                "very_low": 0.15,
                "low": 0.40,
                "medium": 0.75,
                "high": 1.00,
            },
        },
        classifier_model_path,
    )

    regression_config = {
        "module": "B",
        "purpose": (
            "0h + 24h -> 168h prediction"
        ),
        "input_features": FEATURE_COLUMNS,
        "forbidden_features": (
            FORBIDDEN_FEATURES
        ),
        "training_batches": (
            TRAIN_BATCHES
        ),
        "calibration_batch": (
            CALIBRATION_BATCH
        ),
        "test_batch": TEST_BATCH,
        "all_prediction_batches": (
            ALL_BATCHES
        ),
        "target": TARGET_COLUMN,
        "model": "RandomForestRegressor",
        "n_estimators": 400,
        "max_features": "sqrt",
        "min_samples_leaf": 2,
        "random_state": RANDOM_STATE,
        "conformal_alpha": (
            CONFORMAL_ALPHA
        ),
        "conformal_q": float(
            conformal_q
        ),
        "calibration_coverage": float(
            calibration_coverage
        ),
    }

    classifier_config = {
        "module": "B",
        "purpose": (
            "Early prediction of future "
            "168h violation"
        ),
        "input_features": FEATURE_COLUMNS,
        "forbidden_features": (
            FORBIDDEN_FEATURES
        ),
        "training_batches": (
            TRAIN_BATCHES
        ),
        "test_batch": TEST_BATCH,
        "all_prediction_batches": (
            ALL_BATCHES
        ),
        "target": (
            "future_168h_violation"
        ),
        "target_definition": (
            "iddq_168h_uA > "
            "absolute_limit_uA"
        ),
        "model": "RandomForestClassifier",
        "n_estimators": 500,
        "max_features": "sqrt",
        "min_samples_leaf": 3,
        "class_weight": "balanced",
        "random_state": RANDOM_STATE,
        "probability_threshold": 0.50,
    }

    with open(
        regression_config_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            regression_config,
            file,
            indent=2,
        )

    with open(
        classifier_config_path,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            classifier_config,
            file,
            indent=2,
        )

    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print("\n" + "=" * 70)
    print(
        "DATASET PREDICTION COUNTS"
    )
    print("=" * 70)

    print(
        f"All predictions : "
        f"{len(all_results):,}"
    )

    print(
        f"Batch 5         : "
        f"{len(batch5_results):,}"
    )

    print("\nBY LOT")

    print(
        all_results[
            "lot_id"
        ].value_counts()
        .sort_index()
        .to_string()
    )

    print("\n" + "=" * 70)
    print(
        "REGRESSION RESULTS - BATCH 5"
    )
    print("=" * 70)

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
        f"Conformal q : "
        f"{conformal_q:.4f} µA"
    )

    print(
        f"Calibration coverage : "
        f"{calibration_coverage:.4f}"
    )

    print("\nPOINT PREDICTION > LIMIT")

    print(
        f"TP : {point_metrics['tp']}"
    )

    print(
        f"FP : {point_metrics['fp']}"
    )

    print(
        f"FN : {point_metrics['fn']}"
    )

    print(
        f"TN : {point_metrics['tn']}"
    )

    print(
        f"Precision : "
        f"{point_metrics['precision']:.4f}"
    )

    print(
        f"Recall : "
        f"{point_metrics['recall']:.4f}"
    )

    print(
        f"F1 : "
        f"{point_metrics['f1']:.4f}"
    )

    print("\n" + "=" * 70)
    print(
        "EARLY FAILURE CLASSIFIER - BATCH 5"
    )
    print("=" * 70)

    print(
        f"Accuracy : "
        f"{classifier_accuracy:.4f}"
    )

    print(
        f"ROC-AUC : "
        f"{classifier_auc:.4f}"
    )

    print(
        f"TP : {classifier_metrics['tp']}"
    )

    print(
        f"FP : {classifier_metrics['fp']}"
    )

    print(
        f"FN : {classifier_metrics['fn']}"
    )

    print(
        f"TN : {classifier_metrics['tn']}"
    )

    print(
        f"Precision : "
        f"{classifier_metrics['precision']:.4f}"
    )

    print(
        f"Recall : "
        f"{classifier_metrics['recall']:.4f}"
    )

    print(
        f"F1 : "
        f"{classifier_metrics['f1']:.4f}"
    )

    print("\n" + "=" * 70)
    print(
        "ALL 10,000 FAILURE RISK DISTRIBUTION"
    )
    print("=" * 70)

    print(
        pd.Series(
            all_failure_risk
        ).value_counts()
    )

    print("\n" + "=" * 70)
    print(
        "GROUND-TRUTH DIAGNOSTICS - BATCH 5"
    )
    print("=" * 70)

    print(
        diagnostics.to_string(
            index=False
        )
    )

    print("\n" + "=" * 70)
    print("FILES SAVED")
    print("=" * 70)

    print(
        all_predictions_path
    )

    print(
        batch5_path
    )

    print(
        importance_path
    )

    print(
        diagnostics_path
    )

    print(
        regression_model_path
    )

    print(
        classifier_model_path
    )

    print(
        regression_config_path
    )

    print(
        classifier_config_path
    )

    print("\n" + "=" * 70)
    print(
        "INFORMATION BOUNDARY CHECK"
    )
    print("=" * 70)

    print(
        "Deployment inputs = 0h + 24h ONLY"
    )

    print(
        "96h/168h measurements were NOT "
        "model inputs."
    )

    print(
        "ground_truth was NOT a model input."
    )

    print(
        "Batch 5 remains the unseen "
        "evaluation set."
    )

    print(
        "Frozen models were applied to "
        "all 10,000 components."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()