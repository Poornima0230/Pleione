# ============================================================
# SIH 26170
# MODULE A: DYNAMIC AND COMPONENT-AWARE ANOMALY DETECTION
#
# FLOW
# ------------------------------------------------------------
# Batch 1                    -> 2,000 components
# Batch 1 + Batch 2          -> 4,000
# Batch 1 + Batch 2 + Batch3 -> 6,000
# ...
# All 10 batches             -> 20,000
#
# For every cumulative stage:
#
#   Data
#      ↓
#   Grouping
#      ↓
#   Group Statistics
#      ↓
#   Statistical Anomaly Score
#      +
#   Isolation Forest Score
#      ↓
#   Combined Anomaly Score
#      ↓
#   Risk Score
#      ↓
#   Screening
#      ↓
#   Ground Truth Evaluation
#      ↓
#   Explanation
#
# Ground truth is used ONLY for evaluation.
# It is NOT used as a detection feature.
# ============================================================

import os
import glob
import time
import warnings

import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

from config_loader import load_config


# ============================================================
# 1. LOAD CONFIGURATION
# ============================================================

CONFIG = load_config()

INPUT_CONFIG = CONFIG["input"]
GROUP_COLUMNS = CONFIG["grouping"]["columns"]

IDDQ_COLUMNS = CONFIG["measurements"]["iddq"]
LEAKAGE_COLUMNS = CONFIG["measurements"]["leakage"]

COLUMN_CONFIG = CONFIG["columns"]

COMPONENT_ID_COLUMN = COLUMN_CONFIG["component_id"]
LOT_ID_COLUMN = COLUMN_CONFIG["lot_id"]
COMPONENT_TYPE_COLUMN = COLUMN_CONFIG["component_type"]
TEMPERATURE_COLUMN = COLUMN_CONFIG["temperature"]
VOLTAGE_COLUMN = COLUMN_CONFIG["voltage"]
GROUND_TRUTH_COLUMN = COLUMN_CONFIG["ground_truth"]
ABSOLUTE_LIMIT_COLUMN = COLUMN_CONFIG["absolute_limit"]

IF_CONFIG = CONFIG["isolation_forest"]

STAT_WEIGHT = CONFIG["anomaly_score"]["statistical_weight"]
IF_WEIGHT = CONFIG["anomaly_score"]["isolation_forest_weight"]

ANOMALY_THRESHOLD = CONFIG["anomaly"]["threshold"]

PASS_THRESHOLD = CONFIG["screening"]["pass_threshold"]
REVIEW_THRESHOLD = CONFIG["screening"]["review_threshold"]
OUTPUT_FOLDER = CONFIG["output"]["folder"]
STAGE_PREFIX = CONFIG["output"]["stage_prefix"]
FINAL_FILE = CONFIG["output"]["final_file"]


# ============================================================
# 2. CONSTANTS
# ============================================================

ALL_MEASUREMENT_COLUMNS = IDDQ_COLUMNS + LEAKAGE_COLUMNS

EPSILON = 1e-9

# Minimum number of components required for
# reliable primary group statistics.
MIN_GROUP_SIZE = 5
TEMPERATURE_BIN_SIZE = 1.0
VOLTAGE_BIN_SIZE = 0.05
warnings.filterwarnings("ignore")


# ============================================================
# 3. BASIC VALIDATION
# ============================================================

def validate_config():
    """Validate important configuration settings."""

    if abs(STAT_WEIGHT + IF_WEIGHT - 1.0) > 1e-6:
        raise ValueError(
            "Statistical weight + Isolation Forest weight must equal 1.0"
        )

    if not (0 <= ANOMALY_THRESHOLD <= 1):
        raise ValueError(
            "Anomaly threshold must be between 0 and 1"
        )

    if not (0 <= PASS_THRESHOLD < REVIEW_THRESHOLD <= 1):
        raise ValueError(
            "Screening thresholds must satisfy "
            "0 <= pass < review <= 1"
        )


def validate_dataframe(df):
    """Validate that required columns exist."""

    required_columns = [
        COMPONENT_ID_COLUMN,
        LOT_ID_COLUMN,
        COMPONENT_TYPE_COLUMN,
        TEMPERATURE_COLUMN,
        VOLTAGE_COLUMN,
        GROUND_TRUTH_COLUMN,
        ABSOLUTE_LIMIT_COLUMN
    ]

    required_columns.extend(ALL_MEASUREMENT_COLUMNS)

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )


# ============================================================
# 4. FIND BATCH FILES
# ============================================================

def get_batch_files():
    """
    Find batch CSV files and sort them numerically.

    Important:
    Normal alphabetical sorting would give:
        batch_1
        batch_10
        batch_2

    We explicitly sort by the batch number.
    """

    folder = INPUT_CONFIG["folder"]
    pattern = INPUT_CONFIG["file_pattern"]

    search_pattern = os.path.join(folder, pattern)

    files = glob.glob(search_pattern)

    if not files:
        raise FileNotFoundError(
            f"No batch files found using: {search_pattern}"
        )

    def batch_number(path):
        filename = os.path.basename(path)

        try:
            number = int(
                filename.lower()
                .replace("batch_", "")
                .replace(".csv", "")
            )
            return number
        except ValueError:
            return 999999

    files = sorted(files, key=batch_number)

    expected_batches = INPUT_CONFIG.get("expected_batches")

    if expected_batches is not None:
        if len(files) < expected_batches:
            raise ValueError(
                f"Expected at least {expected_batches} batches "
                f"but found only {len(files)}."
            )

        files = files[:expected_batches]

    return files

# ============================================================
# 5. LOAD ONE BATCH
# ============================================================

def load_batch(file_path):
    """Load and clean one batch."""

    df = pd.read_csv(file_path)

    validate_dataframe(df)

    # Convert measurements to numeric
    numeric_columns = (
        IDDQ_COLUMNS
        + LEAKAGE_COLUMNS
        + [
            TEMPERATURE_COLUMN,
            VOLTAGE_COLUMN,
            ABSOLUTE_LIMIT_COLUMN
        ]
    )

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # Remove rows without component ID
    df = df.dropna(
        subset=[COMPONENT_ID_COLUMN]
    ).copy()

    # Fill numeric missing measurements using
    # interpolation followed by median.
    for column in ALL_MEASUREMENT_COLUMNS:

        if df[column].isna().any():

            df[column] = (
                df[column]
                .interpolate(limit_direction="both")
            )

            df[column] = df[column].fillna(
                df[column].median()
            )

    return df


# ============================================================
# 6. ROBUST Z-SCORE
# ============================================================

def calculate_robust_z(values, median, mad):
    """
    Calculate robust z-score using MAD.

    Robust z-score is less affected by extreme values
    than ordinary z-score.
    """

    if pd.isna(mad) or mad < EPSILON:
        return 0.0

    return abs(
        0.6745 * (values - median) / mad
    )


# ============================================================
# 7. NORMALIZE VALUE
# ============================================================

def minmax_series(series):
    """Normalize a pandas Series to 0-1."""

    series = pd.to_numeric(
        series,
        errors="coerce"
    ).fillna(0)

    minimum = series.min()
    maximum = series.max()

    if pd.isna(minimum) or pd.isna(maximum):
        return pd.Series(
            0.0,
            index=series.index
        )

    if maximum - minimum < EPSILON:
        return pd.Series(
            0.0,
            index=series.index
        )

    return (
        (series - minimum)
        / (maximum - minimum)
    ).clip(0, 1)


# ============================================================
# 8. CALCULATE GROUP STATISTICS
# ============================================================
def calculate_group_statistics(df):
    """
    Calculate component-aware peer-group statistics.

    Components are grouped using:
        component_type
        lot_id
        temperature_bin
        voltage_bin

    Temperature and voltage are continuous values, so they
    are converted into operating-condition bins before grouping.

    If a primary group has fewer than MIN_GROUP_SIZE components,
    a broader group without lot_id is used.
    """

    result = df.copy()

    # --------------------------------------------------------
    # Create operating-condition bins
    # --------------------------------------------------------

    result["temperature_bin"] = (
        np.floor(result[TEMPERATURE_COLUMN] / TEMPERATURE_BIN_SIZE)
        * TEMPERATURE_BIN_SIZE
    )

    result["voltage_bin"] = (
        np.floor(result[VOLTAGE_COLUMN] / VOLTAGE_BIN_SIZE)
        * VOLTAGE_BIN_SIZE
    )

    # --------------------------------------------------------
    # Primary peer group
    # --------------------------------------------------------

    primary_columns = [
        COMPONENT_TYPE_COLUMN,
        LOT_ID_COLUMN,
        "temperature_bin",
        "voltage_bin"
    ]

    primary_group = result.groupby(
        primary_columns,
        dropna=False
    )

    # --------------------------------------------------------
    # Fallback peer group
    # --------------------------------------------------------

    fallback_columns = [
        COMPONENT_TYPE_COLUMN,
        "temperature_bin",
        "voltage_bin"
    ]

    fallback_group = result.groupby(
        fallback_columns,
        dropna=False
    )

    # --------------------------------------------------------
    # Calculate statistics
    # --------------------------------------------------------

    for measurement in ALL_MEASUREMENT_COLUMNS:

        # ====================================================
        # PRIMARY GROUP
        # ====================================================

        primary_count = primary_group[measurement].transform("count")
        primary_mean = primary_group[measurement].transform("mean")
        primary_median = primary_group[measurement].transform("median")
        primary_std = primary_group[measurement].transform("std")
        primary_min = primary_group[measurement].transform("min")
        primary_max = primary_group[measurement].transform("max")

        primary_q1 = primary_group[measurement].transform(
            lambda x: x.quantile(0.25)
        )

        primary_q3 = primary_group[measurement].transform(
            lambda x: x.quantile(0.75)
        )

        primary_mad = primary_group[measurement].transform(
            lambda x: np.median(
                np.abs(x - np.median(x))
            )
        )

        # ====================================================
        # FALLBACK GROUP
        # ====================================================

        fallback_count = fallback_group[measurement].transform("count")
        fallback_mean = fallback_group[measurement].transform("mean")
        fallback_median = fallback_group[measurement].transform("median")
        fallback_std = fallback_group[measurement].transform("std")
        fallback_min = fallback_group[measurement].transform("min")
        fallback_max = fallback_group[measurement].transform("max")

        fallback_q1 = fallback_group[measurement].transform(
            lambda x: x.quantile(0.25)
        )

        fallback_q3 = fallback_group[measurement].transform(
            lambda x: x.quantile(0.75)
        )

        fallback_mad = fallback_group[measurement].transform(
            lambda x: np.median(
                np.abs(x - np.median(x))
            )
        )

        # ====================================================
        # SELECT PRIMARY OR FALLBACK
        # ====================================================

        use_primary = primary_count >= MIN_GROUP_SIZE

        result[
            f"{measurement}_group_count"
        ] = np.where(
            use_primary,
            primary_count,
            fallback_count
        )

        result[
            f"{measurement}_group_mean"
        ] = np.where(
            use_primary,
            primary_mean,
            fallback_mean
        )

        result[
            f"{measurement}_group_median"
        ] = np.where(
            use_primary,
            primary_median,
            fallback_median
        )

        result[
            f"{measurement}_group_std"
        ] = np.where(
            use_primary,
            primary_std,
            fallback_std
        )

        result[
            f"{measurement}_group_min"
        ] = np.where(
            use_primary,
            primary_min,
            fallback_min
        )

        result[
            f"{measurement}_group_max"
        ] = np.where(
            use_primary,
            primary_max,
            fallback_max
        )

        result[
            f"{measurement}_group_q1"
        ] = np.where(
            use_primary,
            primary_q1,
            fallback_q1
        )

        result[
            f"{measurement}_group_q3"
        ] = np.where(
            use_primary,
            primary_q3,
            fallback_q3
        )

        result[
            f"{measurement}_group_iqr"
        ] = (
            result[f"{measurement}_group_q3"]
            -
            result[f"{measurement}_group_q1"]
        )

        result[
            f"{measurement}_group_mad"
        ] = np.where(
            use_primary,
            primary_mad,
            fallback_mad
        )

    return result


# ============================================================
# 9. STATISTICAL ANOMALY FEATURES
# ============================================================
def calculate_statistical_features(df):
    """
    Calculate statistical and temporal anomaly evidence.

    Statistical evidence:
        - deviation from peer-group median
        - robust z-score
        - IQR anomaly

    Temporal evidence:
        - 0h -> 24h change
        - 24h -> 96h change
        - 96h -> 168h change

    Temporal changes are compared with the corresponding
    changes of components in the same peer group.
    """

    result = df.copy()

    robust_z_columns = []
    iqr_flag_columns = []

    # ========================================================
    # 1. EXISTING PEER-GROUP STATISTICAL EVIDENCE
    # ========================================================

    for measurement in ALL_MEASUREMENT_COLUMNS:

        median_column = f"{measurement}_group_median"
        mad_column = f"{measurement}_group_mad"
        q1_column = f"{measurement}_group_q1"
        q3_column = f"{measurement}_group_q3"
        iqr_column = f"{measurement}_group_iqr"

        # ----------------------------------------------------
        # Deviation from peer-group median
        # ----------------------------------------------------

        deviation_column = f"{measurement}_deviation"

        result[deviation_column] = abs(
            result[measurement] - result[median_column]
        )

        # ----------------------------------------------------
        # Robust Z-score
        # ----------------------------------------------------

        robust_z_column = f"{measurement}_robust_z"

        mad = result[mad_column]
        deviation = result[deviation_column]

        result[robust_z_column] = 0.0

        valid_mad = mad >= EPSILON

        result.loc[valid_mad, robust_z_column] = (
            0.6745
            * deviation[valid_mad]
            / mad[valid_mad]
        )

        zero_mad = ~valid_mad

        result.loc[
            zero_mad & (deviation > EPSILON),
            robust_z_column
        ] = 3.0

        result[robust_z_column] = (
            result[robust_z_column]
            .replace([np.inf, -np.inf], 0)
            .fillna(0)
        )

        robust_z_columns.append(robust_z_column)

        # ----------------------------------------------------
        # IQR anomaly
        # ----------------------------------------------------

        lower_bound = (
            result[q1_column]
            - 1.5 * result[iqr_column]
        )

        upper_bound = (
            result[q3_column]
            + 1.5 * result[iqr_column]
        )

        iqr_flag_column = f"{measurement}_iqr_anomaly"

        result[iqr_flag_column] = (
            (result[measurement] < lower_bound)
            |
            (result[measurement] > upper_bound)
        ).astype(int)

        iqr_flag_columns.append(iqr_flag_column)

    # ========================================================
    # 2. EXISTING STATISTICAL SCORE
    # ========================================================

    result["max_robust_z"] = result[
        robust_z_columns
    ].max(axis=1)

    result["statistical_evidence_count"] = result[
        iqr_flag_columns
    ].sum(axis=1)

    robust_component = (
        (result["max_robust_z"] - 2.0)
        / 4.0
    ).clip(0, 1)

    iqr_component = (
        result["statistical_evidence_count"]
        / max(len(ALL_MEASUREMENT_COLUMNS), 1)
    ).clip(0, 1)

    statistical_score = (
        0.70 * robust_component
        +
        0.30 * iqr_component
    ).clip(0, 1)

    # ========================================================
    # 3. TEMPORAL CHANGE FEATURES
    # ========================================================

    temporal_robust_z_columns = []

    measurement_pairs = [
        (
            "iddq",
            IDDQ_COLUMNS
        ),
        (
            "leakage",
            LEAKAGE_COLUMNS
        )
    ]

    for measurement_name, columns in measurement_pairs:

        for i in range(len(columns) - 1):

            current_column = columns[i]
            next_column = columns[i + 1]

            change_name = (
                f"{measurement_name}_change_"
                f"{current_column.split('_')[1]}_"
                f"{next_column.split('_')[1]}"
            )

            # ------------------------------------------------
            # Calculate change
            # ------------------------------------------------

            result[change_name] = (
                result[next_column]
                - result[current_column]
            )

            # ------------------------------------------------
            # Create change column for every peer component
            # ------------------------------------------------

            change_group = result.groupby(
                [
                    COMPONENT_TYPE_COLUMN,
                    LOT_ID_COLUMN,
                    "temperature_bin",
                    "voltage_bin"
                ],
                dropna=False
            )[change_name]

            change_median = change_group.transform("median")

            change_mad = change_group.transform(
                lambda x: np.median(
                    np.abs(x - np.median(x))
                )
            )

            # ------------------------------------------------
            # Robust Z-score for temporal change
            # ------------------------------------------------

            temporal_z_name = (
                f"{change_name}_robust_z"
            )

            temporal_deviation = abs(
                result[change_name]
                - change_median
            )

            result[temporal_z_name] = 0.0

            valid_change_mad = (
                change_mad >= EPSILON
            )

            result.loc[
                valid_change_mad,
                temporal_z_name
            ] = (
                0.6745
                * temporal_deviation[valid_change_mad]
                / change_mad[valid_change_mad]
            )

            zero_change_mad = ~valid_change_mad

            result.loc[
                zero_change_mad
                & (temporal_deviation > EPSILON),
                temporal_z_name
            ] = 3.0

            result[temporal_z_name] = (
                result[temporal_z_name]
                .replace([np.inf, -np.inf], 0)
                .fillna(0)
            )

            temporal_robust_z_columns.append(
                temporal_z_name
            )

    # ========================================================
    # 4. TEMPORAL ANOMALY SCORE
    # ========================================================

    result["max_temporal_robust_z"] = result[
        temporal_robust_z_columns
    ].max(axis=1)

    result["temporal_anomaly_score"] = (
        (
            result["max_temporal_robust_z"] - 2.0
        )
        / 4.0
    ).clip(0, 1)

    result["temporal_anomaly_flag"] = (
        result["temporal_anomaly_score"] >= 0.50
    ).astype(int)

    # ========================================================
    # 5. COMBINE STATISTICAL + TEMPORAL EVIDENCE
    # ========================================================

    result["statistical_score"] = (
        0.70 * statistical_score
        +
        0.30 * result["temporal_anomaly_score"]
    ).clip(0, 1)

    result["statistical_anomaly_flag"] = (
        result["statistical_score"] >= 0.50
    ).astype(int)

    return result
# ============================================================
# 10. CREATE ISOLATION FOREST FEATURES
# ============================================================

def create_isolation_forest_features(df):
    """
    Create numeric features for Isolation Forest.

    Ground truth is deliberately excluded.
    """

    features = pd.DataFrame(
        index=df.index
    )

    # --------------------------------------------------------
    # Raw measurements
    # --------------------------------------------------------

    for column in ALL_MEASUREMENT_COLUMNS:
        features[column] = df[column]

    # --------------------------------------------------------
    # Group-relative features
    # --------------------------------------------------------

    for measurement in ALL_MEASUREMENT_COLUMNS:

        features[
            f"{measurement}_robust_z"
        ] = df[
            f"{measurement}_robust_z"
        ]

    # --------------------------------------------------------
    # Environmental conditions
    # --------------------------------------------------------

    features[TEMPERATURE_COLUMN] = (
        df[TEMPERATURE_COLUMN]
    )

    features[VOLTAGE_COLUMN] = (
        df[VOLTAGE_COLUMN]
    )

    # --------------------------------------------------------
    # Drift features for Iddq
    # --------------------------------------------------------

    if len(IDDQ_COLUMNS) >= 2:

        for i in range(
            len(IDDQ_COLUMNS) - 1
        ):

            first = IDDQ_COLUMNS[i]
            second = IDDQ_COLUMNS[i + 1]

            feature_name = (
                f"drift_{first}_to_{second}"
            )

            features[feature_name] = (
                df[second]
                - df[first]
            )

    # --------------------------------------------------------
    # Drift features for leakage
    # --------------------------------------------------------

    if len(LEAKAGE_COLUMNS) >= 2:

        for i in range(
            len(LEAKAGE_COLUMNS) - 1
        ):

            first = LEAKAGE_COLUMNS[i]
            second = LEAKAGE_COLUMNS[i + 1]

            feature_name = (
                f"drift_{first}_to_{second}"
            )

            features[feature_name] = (
                df[second]
                - df[first]
            )

    # Clean values
    features = features.replace(
        [np.inf, -np.inf],
        np.nan
    )

    features = features.fillna(
        features.median(numeric_only=True)
    )

    features = features.fillna(0)

    return features


# ============================================================
# 11. ISOLATION FOREST
# ============================================================

def calculate_isolation_forest(df):
    """
    Run Isolation Forest on the cumulative dataset.

    sklearn IsolationForest does not provide partial_fit,
    so a fresh model is fitted for every cumulative stage.
    """

    result = df.copy()

    features = create_isolation_forest_features(
        result
    )

    model = IsolationForest(
        n_estimators=IF_CONFIG["n_estimators"],
        contamination=IF_CONFIG["contamination"],
        random_state=IF_CONFIG["random_state"],
        n_jobs=IF_CONFIG["n_jobs"]
    )

    model.fit(features)

    # sklearn:
    # -1 = anomaly
    # +1 = normal

    predictions = model.predict(features)

    raw_scores = -model.score_samples(features)

    # Normalize to 0-1
    minimum = raw_scores.min()
    maximum = raw_scores.max()

    if maximum - minimum < EPSILON:

        normalized_scores = np.zeros(
            len(raw_scores)
        )

    else:

        normalized_scores = (
            (raw_scores - minimum)
            / (maximum - minimum)
        )

    result["isolation_forest_score"] = (
        normalized_scores.clip(0, 1)
    )

    result["isolation_forest_flag"] = (
        predictions == -1
    ).astype(int)

    return result


# ============================================================
# 12. COMBINED ANOMALY SCORE
# ============================================================

def calculate_combined_anomaly_score(df):
    """
    Combine:

        Statistical anomaly score
        +
        Isolation Forest score

    according to config.yaml.
    """

    result = df.copy()

    result["combined_anomaly_score"] = (
        STAT_WEIGHT
        * result["statistical_score"]
        +
        IF_WEIGHT
        * result["isolation_forest_score"]
    ).clip(0, 1)

    # Combined anomaly flag
    result["anomaly_flag"] = (
        result["combined_anomaly_score"]
        >= ANOMALY_THRESHOLD
    ).astype(int)

    return result


# ============================================================
# 13. SPECIFICATION VIOLATION
# ============================================================

def calculate_specification_violation(df):
    """
    Check the final Iddq value against the absolute limit.

    This is separate from statistical anomaly detection.

    A component can therefore be:

        statistically abnormal but below limit

    OR

        within group statistics but above specification.
    """

    result = df.copy()

    final_iddq = IDDQ_COLUMNS[-1]

    result["limit_violation"] = (
        result[final_iddq]
        > result[ABSOLUTE_LIMIT_COLUMN]
    ).astype(int)

    result["limit_excess_uA"] = (
        result[final_iddq]
        - result[ABSOLUTE_LIMIT_COLUMN]
    )

    result["limit_excess_uA"] = (
        result["limit_excess_uA"]
        .clip(lower=0)
    )

    return result


# ============================================================
# 14. RISK SCORE
# ============================================================

def calculate_risk_score(df):
    """
    Calculate final risk score.

    Risk combines:

        1. Combined anomaly score
        2. Specification violation
        3. Statistical evidence

    The anomaly component itself already combines
    statistical detection + Isolation Forest.
    """

    result = df.copy()

    anomaly_component = (
        result["combined_anomaly_score"]
    )

    specification_component = (
        result["limit_violation"]
    )

    statistical_component = (
        result["statistical_score"]
    )

    result["risk_score"] = (
        0.65 * anomaly_component
        +
        0.25 * specification_component
        +
        0.10 * statistical_component
    )

    result["risk_score"] = (
        result["risk_score"]
        .clip(0, 1)
    )

    # Convert to 0-100
    result["risk_score_100"] = (
        result["risk_score"] * 100
    ).round(2)

    # --------------------------------------------------------
    # Risk level
    # --------------------------------------------------------

    result["risk_level"] = np.select(
        [
            result["risk_score"] >= 0.80,
            result["risk_score"] >= 0.60,
            result["risk_score"] >= 0.30
        ],
        [
            "CRITICAL",
            "HIGH",
            "MEDIUM"
        ],
        default="LOW"
    )

    return result


# ============================================================
# 15. SCREENING DECISION
# ============================================================

def calculate_screening(df):
    """
    Screening:

        PASS   -> Within specification and low risk
        REVIEW -> Within specification but elevated risk
        REJECT -> Specification limit violation
    """

    result = df.copy()

    result["screening_decision"] = np.select(
        [
            result["limit_violation"] == 1,
            result["risk_score"] >= PASS_THRESHOLD
        ],
        [
            "REJECT",
            "REVIEW"
        ],
        default="PASS"
    )

    return result

# ============================================================
# 16. EVIDENCE-BASED EXPLANATION
# ============================================================

def create_explanation(row):
    """
    Generate a human-readable explanation based on
    actual evidence for that component.
    """

    reasons = []

    # --------------------------------------------------------
    # Specification
    # --------------------------------------------------------

    if row["limit_violation"] == 1:

        reasons.append(
            "final Iddq exceeds the absolute specification limit"
        )

    # --------------------------------------------------------
    # Statistical evidence
    # --------------------------------------------------------

    if row["statistical_score"] >= 0.50:

        reasons.append(
            "measurement is statistically abnormal "
            "within its component/lot/condition group"
        )

    # --------------------------------------------------------
    # Isolation Forest
    # --------------------------------------------------------

    if row["isolation_forest_flag"] == 1:

        reasons.append(
            "Isolation Forest identified an unusual "
            "multivariate pattern"
        )

    # --------------------------------------------------------
    # Strong combined evidence
    # --------------------------------------------------------

    if (
        row["statistical_score"] >= 0.50
        and
        row["isolation_forest_flag"] == 1
    ):

        reasons.append(
            "statistical and machine-learning evidence agree"
        )

    # --------------------------------------------------------
    # No evidence
    # --------------------------------------------------------

    if not reasons:

        return (
            "No strong anomaly evidence detected; "
            "component follows its group pattern."
        )

    return "; ".join(reasons) + "."


def generate_explanations(df):
    """Generate explanation for every component."""

    result = df.copy()

    result["explanation"] = (
        result.apply(
            create_explanation,
            axis=1
        )
    )

    return result


# ============================================================
# 17. GROUND-TRUTH NORMALIZATION
# ============================================================

def convert_ground_truth_to_binary(series):
    """
    Convert ground truth values into:

        1 = defective/anomalous
        0 = normal

    Handles common textual labels.
    """

    values = (
        series
        .astype(str)
        .str.strip()
        .str.lower()
    )

    normal_values = {
        "normal",
        "good",
        "pass",
        "healthy",
        "0",
        "false"
    }

    return (
        ~values.isin(normal_values)
    ).astype(int)


# ============================================================
# 18. GROUND-TRUTH EVALUATION
# ============================================================

def evaluate_ground_truth(df):
    """
    Evaluate Module A against ground truth.

    IMPORTANT:
    Ground truth is NOT used for anomaly detection.
    It is only used here for evaluation.
    """

    y_true = convert_ground_truth_to_binary(
        df[GROUND_TRUTH_COLUMN]
    )

    y_pred = (
        df["screening_decision"]
        != "PASS"
    ).astype(int)

    accuracy = accuracy_score(
        y_true,
        y_pred
    )

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0
    )

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1]
    ).ravel()

    metrics = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "true_positive": tp
    }

    return metrics


# ============================================================
# 19. PROCESS ONE CUMULATIVE STAGE
# ============================================================

def process_stage(df, stage_number, batch_files):
    """
    Process one cumulative dataset.
    """

    print()
    print("=" * 70)
    print(
        f"STAGE {stage_number}: "
        f"{len(df):,} COMPONENTS"
    )
    print("=" * 70)

    start_time = time.time()

    # --------------------------------------------------------
    # Group statistics
    # --------------------------------------------------------

    print("1/8 Calculating group statistics...")

    result = calculate_group_statistics(
        df
    )

    # --------------------------------------------------------
    # Statistical anomaly detection
    # --------------------------------------------------------

    print("2/8 Calculating statistical anomaly features...")

    result = calculate_statistical_features(
        result
    )

    # --------------------------------------------------------
    # Isolation Forest
    # --------------------------------------------------------

    print("3/8 Running Isolation Forest...")

    result = calculate_isolation_forest(
        result
    )

    # --------------------------------------------------------
    # Combined anomaly score
    # --------------------------------------------------------

    print("4/8 Combining statistical + Isolation Forest scores...")

    result = calculate_combined_anomaly_score(
        result
    )

    # --------------------------------------------------------
    # Specification
    # --------------------------------------------------------

    print("5/8 Checking specification limits...")

    result = calculate_specification_violation(
        result
    )

    # --------------------------------------------------------
    # Risk
    # --------------------------------------------------------

    print("6/8 Calculating risk and screening...")

    result = calculate_risk_score(
        result
    )

    result = calculate_screening(
        result
    )

    # --------------------------------------------------------
    # Explanation
    # --------------------------------------------------------

    print("7/8 Generating explanations...")

    result = generate_explanations(
        result
    )

    # --------------------------------------------------------
    # Evaluation
    # --------------------------------------------------------

    print("8/8 Evaluating against ground truth...")

    metrics = evaluate_ground_truth(
        result
    )

    processing_time = (
        time.time()
        - start_time
    )

    # --------------------------------------------------------
    # Stage metadata
    # --------------------------------------------------------

    result["stage"] = stage_number

    result["cumulative_components"] = len(
        result
    )

    result["batches_processed"] = (
        stage_number
    )

    # --------------------------------------------------------
    # Save stage
    # --------------------------------------------------------

    os.makedirs(
        OUTPUT_FOLDER,
        exist_ok=True
    )

    stage_file = os.path.join(
        OUTPUT_FOLDER,
        f"{STAGE_PREFIX}{stage_number:02d}.csv"
    )

    result.to_csv(
        stage_file,
        index=False
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    anomalies = int(
        result["anomaly_flag"].sum()
    )

    high_risk = int(
        (
            result["risk_level"]
            .isin(["HIGH", "CRITICAL"])
        ).sum()
    )

    critical = int(
        (
            result["risk_level"]
            == "CRITICAL"
        ).sum()
    )

    pass_count = int(
        (
            result["screening_decision"]
            == "PASS"
        ).sum()
    )

    review_count = int(
        (
            result["screening_decision"]
            == "REVIEW"
        ).sum()
    )

    reject_count = int(
        (
            result["screening_decision"]
            == "REJECT"
        ).sum()
    )

    summary = {
        "stage": stage_number,
        "files_processed": stage_number,
        "components_processed": len(result),
        "anomalies_detected": anomalies,
        "high_risk": high_risk,
        "critical": critical,
        "pass": pass_count,
        "review": review_count,
        "reject": reject_count,
        "accuracy": metrics["accuracy"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "true_negative": metrics["true_negative"],
        "false_positive": metrics["false_positive"],
        "false_negative": metrics["false_negative"],
        "true_positive": metrics["true_positive"],
        "processing_time_seconds": round(
            processing_time,
            2
        ),
        "output_file": stage_file
    }

    print()
    print(
        f"Components: {len(result):,}"
    )

    print(
        f"Anomalies: {anomalies:,}"
    )

    print(
        f"PASS: {pass_count:,}"
    )

    print(
        f"REVIEW: {review_count:,}"
    )

    print(
        f"REJECT: {reject_count:,}"
    )

    print(
        f"Precision: {metrics['precision']:.4f}"
    )

    print(
        f"Recall: {metrics['recall']:.4f}"
    )

    print(
        f"F1: {metrics['f1']:.4f}"
    )

    print(
        f"Time: {processing_time:.2f} seconds"
    )

    print(
        f"Saved: {stage_file}"
    )

    return result, summary


# ============================================================
# 20. MAIN PIPELINE
# ============================================================

def main():

    print()
    print("=" * 70)
    print("SIH 26170 - MODULE A")
    print("DYNAMIC AND COMPONENT-AWARE ANOMALY DETECTION")
    print("=" * 70)

    validate_config()

    # --------------------------------------------------------
    # Find batches
    # --------------------------------------------------------

    batch_files = get_batch_files()

    print()
    print(
        f"Number of batches found: {len(batch_files)}"
    )

    print()

    for file_path in batch_files:

        print(
            f"  {os.path.basename(file_path)}"
        )

    # --------------------------------------------------------
    # Load batches
    # --------------------------------------------------------

    print()
    print("Loading batch files...")

    loaded_batches = []

    for file_path in batch_files:

        batch = load_batch(
            file_path
        )

        loaded_batches.append(
            batch
        )

        print(
            f"  {os.path.basename(file_path)}: "
            f"{len(batch):,} rows"
        )

    total_rows = sum(
        len(batch)
        for batch in loaded_batches
    )

    print()
    print(
        f"Total rows: {total_rows:,}"
    )

    # --------------------------------------------------------
    # Cumulative processing
    # --------------------------------------------------------

    cumulative_data = []

    stage_summaries = []

    final_result = None

    for stage_index, batch in enumerate(
        loaded_batches,
        start=1
    ):

        print()
        print(
            f"Adding batch {stage_index}..."
        )

        cumulative_data.append(
            batch
        )

        cumulative_df = pd.concat(
            cumulative_data,
            ignore_index=True
        )

        # ----------------------------------------------------
        # Remove duplicate component IDs
        # ----------------------------------------------------

        duplicate_count = (
            cumulative_df[
                COMPONENT_ID_COLUMN
            ].duplicated()
            .sum()
        )

        if duplicate_count > 0:

            print(
                f"WARNING: {duplicate_count} "
                "duplicate component IDs found."
            )

            cumulative_df = (
                cumulative_df
                .drop_duplicates(
                    subset=[
                        COMPONENT_ID_COLUMN
                    ],
                    keep="last"
                )
                .reset_index(drop=True)
            )

        # ----------------------------------------------------
        # Process cumulative stage
        # ----------------------------------------------------

        final_result, summary = process_stage(
            cumulative_df,
            stage_index,
            batch_files[:stage_index]
        )

        stage_summaries.append(
            summary
        )

    # ========================================================
    # SAVE STAGE SUMMARY
    # ========================================================

    summary_df = pd.DataFrame(
        stage_summaries
    )

    summary_file = os.path.join(
        OUTPUT_FOLDER,
        "stage_summary.csv"
    )

    summary_df.to_csv(
        summary_file,
        index=False
    )

    # ========================================================
    # SAVE FINAL MODULE A FILE
    # ========================================================

    final_file_path = os.path.join(
        "data",
        FINAL_FILE
    )

    final_result.to_csv(
        final_file_path,
        index=False
    )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("MODULE A COMPLETED")
    print("=" * 70)

    print()
    print(
        f"Total components processed: "
        f"{len(final_result):,}"
    )

    print(
        f"Final anomalies: "
        f"{int(final_result['anomaly_flag'].sum()):,}"
    )

    print(
        f"Final PASS: "
        f"{int((final_result['screening_decision'] == 'PASS').sum()):,}"
    )

    print(
        f"Final REVIEW: "
        f"{int((final_result['screening_decision'] == 'REVIEW').sum()):,}"
    )

    print(
        f"Final REJECT: "
        f"{int((final_result['screening_decision'] == 'REJECT').sum()):,}"
    )

    final_metrics = evaluate_ground_truth(
        final_result
    )

    print()
    print("FINAL GROUND-TRUTH EVALUATION")
    print("-" * 40)

    print(
        f"Accuracy : {final_metrics['accuracy']:.4f}"
    )

    print(
        f"Precision: {final_metrics['precision']:.4f}"
    )

    print(
        f"Recall   : {final_metrics['recall']:.4f}"
    )

    print(
        f"F1 Score : {final_metrics['f1']:.4f}"
    )

    print()
    print(
        f"Stage results saved to: "
        f"{OUTPUT_FOLDER}"
    )

    print(
        f"Stage summary saved to: "
        f"{summary_file}"
    )

    print(
        f"Final Module A file: "
        f"{final_file_path}"
    )

    print()
    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()