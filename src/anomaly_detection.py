"""
SIH 26170
MODULE A - 0h Anomaly Detection

Purpose
-------
Detect abnormal component behavior using ONLY information
available at 0h.

Cumulative batch architecture
-----------------------------
Batch 1 : 2,000 components
Batch 2 : 4,000 cumulative components
Batch 3 : 6,000 cumulative components
Batch 4 : 8,000 cumulative components
Batch 5 : 10,000 cumulative components

Module A information boundary
------------------------------
Allowed:
    - component_id
    - lot_id
    - component_type
    - temperature_C
    - voltage_V
    - iddq_0h_uA
    - current specification limit
    - peer statistics calculated from 0h data

NOT allowed:
    - iddq_24h_uA
    - iddq_96h_uA
    - iddq_168h_uA
    - drift_0_24_uA_per_h
    - drift_24_96_uA_per_h
    - drift_96_168_uA_per_h
    - overall_drift_uA_per_h
    - iddq_24h_zscore
    - iddq_96h_zscore
    - iddq_168h_zscore
    - static_pass_168h
    - ground_truth for prediction

Module A answers:
    "Is this component abnormal at 0h?"

Module B will later answer:
    "Using 0h + 24h, is this component likely to
     become problematic by 168h?"

Module C will later combine:
    Module A + Module B + specifications
    into the final screening decision.

Important
---------
A Module A REVIEW is NOT a final component rejection.
The final PASS / REVIEW / REJECT decision belongs to Module C.
"""


# ============================================================
# IMPORTS
# ============================================================

from pathlib import Path
import json
import warnings

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
)

warnings.filterwarnings("ignore")


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

# Expected batch location:
#
# data/
#   batch_1.csv
#   batch_2.csv
#   batch_3.csv
#   batch_4.csv
#   batch_5.csv
#
BATCH_DIR = DATA_DIR

# Also support:
#
# data/
#   batches/
#       batch_1.csv
#       ...
#
ALTERNATIVE_BATCH_DIR = DATA_DIR / "batches"

# Stage outputs
STAGE_OUTPUT_DIR = DATA_DIR / "module_A_stages"

# Final Module A result
FINAL_OUTPUT = DATA_DIR / "module_A_anomaly_results.csv"

# Final trained model
MODEL_OUTPUT = MODEL_DIR / "module_A_0h_isolation_forest.joblib"

# Configuration used by the model
CONFIG_OUTPUT = MODEL_DIR / "module_A_0h_config.json"


# ============================================================
# DATASET ARCHITECTURE
# ============================================================

TOTAL_BATCHES = 5

COMPONENTS_PER_BATCH = 2000

TOTAL_COMPONENTS = (
    TOTAL_BATCHES * COMPONENTS_PER_BATCH
)

EXPECTED_CUMULATIVE_COUNTS = [
    2000,
    4000,
    6000,
    8000,
    10000,
]


# ============================================================
# REQUIRED MODULE A COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "component_id",
    "lot_id",
    "component_type",
    "temperature_C",
    "voltage_V",
    "iddq_0h_uA",
]


# ============================================================
# FUTURE COLUMNS
# ============================================================
#
# These columns may exist in the dataset.
# They are deliberately NOT used by Module A.
#

FUTURE_COLUMNS = [
    "iddq_24h_uA",
    "iddq_96h_uA",
    "iddq_168h_uA",
    "drift_0_24_uA_per_h",
    "drift_24_96_uA_per_h",
    "drift_96_168_uA_per_h",
    "overall_drift_uA_per_h",
    "iddq_24h_zscore",
    "iddq_96h_zscore",
    "iddq_168h_zscore",
    "static_pass_168h",
]


# ============================================================
# MODEL CONFIGURATION
# ============================================================

RANDOM_STATE = 42

ISOLATION_FOREST_ESTIMATORS = 300

ISOLATION_FOREST_CONTAMINATION = 0.10

# Temperature peer-group bin
TEMPERATURE_BIN_SIZE = 1.0

# Voltage peer-group bin
VOLTAGE_BIN_SIZE = 0.05

# Robust statistical anomaly threshold
ROBUST_Z_THRESHOLD = 3.5

# Final Module A anomaly threshold
ANOMALY_SCORE_THRESHOLD = 0.60


# ============================================================
# DISPLAY HELPERS
# ============================================================

def print_section(title: str) -> None:
    """
    Print a clean terminal section.
    """

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


# ============================================================
# BATCH FILE DISCOVERY
# ============================================================

def locate_batch_file(batch_number: int) -> Path:
    """
    Locate one batch CSV.

    Supported:

        data/batch_1.csv

    or:

        data/batches/batch_1.csv
    """

    possible_paths = [
        BATCH_DIR / f"batch_{batch_number}.csv",
        ALTERNATIVE_BATCH_DIR / f"batch_{batch_number}.csv",
    ]

    for path in possible_paths:

        if path.exists():
            return path

    searched_paths = "\n".join(
        str(path)
        for path in possible_paths
    )

    raise FileNotFoundError(
        "\n"
        f"Batch {batch_number} was not found.\n\n"
        "Expected one of:\n"
        f"{searched_paths}\n"
    )


# ============================================================
# LOAD ALL FIVE BATCHES
# ============================================================

def load_all_batches() -> list[pd.DataFrame]:
    """
    Load the five independent 2,000-component batches.

    Expected:
        5 batches
        2,000 components each
        10,000 total components
    """

    print_section(
        "LOADING 5 COMPONENT BATCHES"
    )

    batches = []

    for batch_number in range(
        1,
        TOTAL_BATCHES + 1,
    ):

        path = locate_batch_file(
            batch_number
        )

        print()
        print(
            f"Batch {batch_number}"
        )

        print(
            f"File : {path}"
        )

        df = pd.read_csv(
            path
        )

        print(
            f"Rows : {len(df):,}"
        )

        print(
            f"Cols : {len(df.columns)}"
        )

        # ----------------------------------------------------
        # Validate batch size
        # ----------------------------------------------------

        if len(df) != COMPONENTS_PER_BATCH:

            raise ValueError(
                f"\nBatch {batch_number} contains "
                f"{len(df):,} rows.\n"
                f"Expected exactly "
                f"{COMPONENTS_PER_BATCH:,} rows."
            )

        # ----------------------------------------------------
        # Validate required columns
        # ----------------------------------------------------

        missing_columns = [
            column
            for column in REQUIRED_COLUMNS
            if column not in df.columns
        ]

        if missing_columns:

            raise ValueError(
                f"\nBatch {batch_number} is missing "
                f"required Module A columns:\n"
                f"{missing_columns}"
            )

        # ----------------------------------------------------
        # Validate component IDs inside the batch
        # ----------------------------------------------------

        duplicate_count = (
            df["component_id"]
            .duplicated()
            .sum()
        )

        if duplicate_count > 0:

            raise ValueError(
                f"\nBatch {batch_number} contains "
                f"{duplicate_count} duplicate "
                f"component IDs."
            )

        batches.append(
            df
        )

    # --------------------------------------------------------
    # Validate component IDs across all batches
    # --------------------------------------------------------

    all_component_ids = pd.concat(
        [
            batch["component_id"]
            for batch in batches
        ],
        ignore_index=True,
    )

    duplicate_count = (
        all_component_ids
        .duplicated()
        .sum()
    )

    if duplicate_count > 0:

        raise ValueError(
            "\nDuplicate component IDs were found "
            "across different batches.\n"
            f"Duplicate count: {duplicate_count}"
        )

    # --------------------------------------------------------
    # Validate final population
    # --------------------------------------------------------

    total_rows = len(
        all_component_ids
    )

    if total_rows != TOTAL_COMPONENTS:

        raise ValueError(
            f"\nExpected "
            f"{TOTAL_COMPONENTS:,} total components "
            f"but found {total_rows:,}."
        )

    print()
    print(
        "All five batches loaded successfully."
    )

    print(
        f"Total components available: "
        f"{total_rows:,}"
    )

    return batches


# ============================================================
# MODULE A COLUMN VALIDATION
# ============================================================

def validate_module_a_information_boundary(
    df: pd.DataFrame,
) -> None:
    """
    Display and validate the Module A information boundary.

    This function does not delete future columns.
    It simply makes sure Module A never uses them.
    """

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "Required Module A columns are missing:\n"
            f"{missing}"
        )

    print()
    print(
        "Module A 0h input columns:"
    )

    for column in REQUIRED_COLUMNS:

        print(
            f"  {column}"
        )

    print()
    print(
        "Module A explicitly ignores future columns:"
    )

    for column in FUTURE_COLUMNS:

        if column in df.columns:

            print(
                f"  {column}"
            )


# ============================================================
# DATA PREPARATION
# ============================================================

def prepare_numeric_columns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert the 0h numerical inputs into numeric values.

    No future column is used here.
    """

    result = df.copy()

    numeric_columns = [
        "temperature_C",
        "voltage_V",
        "iddq_0h_uA",
    ]

    for column in numeric_columns:

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    result = result.dropna(
        subset=REQUIRED_COLUMNS
    ).copy()

    return result


# ============================================================
# PEER GROUP CREATION
# ============================================================

def create_peer_groups(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create comparable 0h peer groups.

    Peer group definition:

        component_type
        +
        temperature bin
        +
        voltage bin

    Example:

        MCU | T=125 | V=3.3
    """

    result = df.copy()

    # --------------------------------------------------------
    # Temperature bin
    # --------------------------------------------------------

    result["temperature_bin"] = (
        np.round(
            result["temperature_C"]
            / TEMPERATURE_BIN_SIZE
        )
        * TEMPERATURE_BIN_SIZE
    )

    # --------------------------------------------------------
    # Voltage bin
    # --------------------------------------------------------

    result["voltage_bin"] = (
        np.round(
            result["voltage_V"]
            / VOLTAGE_BIN_SIZE
        )
        * VOLTAGE_BIN_SIZE
    )

    # --------------------------------------------------------
    # Peer group identifier
    # --------------------------------------------------------

    result["peer_group"] = (
        result["component_type"]
        .astype(str)
        + "|T="
        + result["temperature_bin"]
        .round(2)
        .astype(str)
        + "|V="
        + result["voltage_bin"]
        .round(3)
        .astype(str)
    )

    return result


# ============================================================
# PEER STATISTICS
# ============================================================

def calculate_peer_statistics(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate robust peer statistics using 0h IDDQ.

    Generated fields:

        iddq_peer_median
        iddq_peer_mad
        iddq_peer_iqr
        iddq_peer_deviation
        iddq_robust_z
        peer_group_size
    """

    result = df.copy()

    grouped = (
        result
        .groupby(
            "peer_group",
            observed=True,
        )["iddq_0h_uA"]
    )

    # --------------------------------------------------------
    # Peer median
    # --------------------------------------------------------

    peer_median = (
        grouped.transform("median")
    )

    # --------------------------------------------------------
    # IQR
    # --------------------------------------------------------

    q1 = grouped.transform(
        lambda values:
        values.quantile(0.25)
    )

    q3 = grouped.transform(
        lambda values:
        values.quantile(0.75)
    )

    iqr = q3 - q1

    # --------------------------------------------------------
    # MAD
    # --------------------------------------------------------

    absolute_deviation = (
        result["iddq_0h_uA"]
        - peer_median
    ).abs()

    mad = (
        absolute_deviation
        .groupby(
            result["peer_group"]
        )
        .transform("median")
    )

    # --------------------------------------------------------
    # Robust Z-score using MAD
    # --------------------------------------------------------

    mad_safe = mad.replace(
        0,
        np.nan,
    )

    robust_z = (
        0.6745
        * (
            result["iddq_0h_uA"]
            - peer_median
        )
        / mad_safe
    )

    # --------------------------------------------------------
    # IQR fallback
    # --------------------------------------------------------

    iqr_safe = iqr.replace(
        0,
        np.nan,
    )

    iqr_based_z = (
        result["iddq_0h_uA"]
        - peer_median
    ) / (
        iqr_safe / 1.349
    )

    robust_z = robust_z.fillna(
        iqr_based_z
    )

    robust_z = robust_z.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    robust_z = robust_z.fillna(
        0.0
    )

    # --------------------------------------------------------
    # Save statistics
    # --------------------------------------------------------

    result["iddq_peer_median"] = (
        peer_median
    )

    result["iddq_peer_mad"] = (
        mad
    )

    result["iddq_peer_iqr"] = (
        iqr
    )

    result["iddq_peer_deviation"] = (
        result["iddq_0h_uA"]
        - peer_median
    ).abs()

    result["iddq_robust_z"] = (
        robust_z
    )

    # --------------------------------------------------------
    # Peer group size
    # --------------------------------------------------------

    result["peer_group_size"] = (
        result
        .groupby(
            "peer_group",
            observed=True,
        )["component_id"]
        .transform("count")
    )

    return result


# ============================================================
# MODEL FEATURES
# ============================================================

def build_training_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build the exact features used by Module A.

    IMPORTANT:
    All features are available at 0h.
    """

    features = pd.DataFrame(
        index=df.index
    )

    features["iddq_0h_uA"] = (
        df["iddq_0h_uA"]
    )

    features["temperature_C"] = (
        df["temperature_C"]
    )

    features["voltage_V"] = (
        df["voltage_V"]
    )

    features["iddq_peer_deviation"] = (
        df["iddq_peer_deviation"]
    )

    features["iddq_robust_z"] = (
        df["iddq_robust_z"]
    )

    features = features.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    features = features.fillna(
        0.0
    )

    return features


# ============================================================
# ISOLATION FOREST
# ============================================================

def fit_isolation_forest(
    features: pd.DataFrame,
) -> IsolationForest:
    """
    Train Isolation Forest on the cumulative
    0h population.
    """

    model = IsolationForest(
        n_estimators=ISOLATION_FOREST_ESTIMATORS,
        contamination=ISOLATION_FOREST_CONTAMINATION,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    model.fit(
        features
    )

    return model


def calculate_isolation_scores(
    model: IsolationForest,
    features: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert Isolation Forest output into:

        isolation_forest_score
        isolation_forest_flag

    Score:
        0 = normal
        1 = highly anomalous
    """

    raw_score = (
        -model.decision_function(
            features
        )
    )

    # --------------------------------------------------------
    # Robust score scaling
    # --------------------------------------------------------

    lower_bound = np.percentile(
        raw_score,
        1,
    )

    upper_bound = np.percentile(
        raw_score,
        99,
    )

    if upper_bound <= lower_bound:

        normalized_score = np.zeros(
            len(raw_score)
        )

    else:

        normalized_score = (
            raw_score
            - lower_bound
        ) / (
            upper_bound
            - lower_bound
        )

    normalized_score = np.clip(
        normalized_score,
        0.0,
        1.0,
    )

    # --------------------------------------------------------
    # Isolation Forest binary flag
    # --------------------------------------------------------

    prediction = model.predict(
        features
    )

    isolation_flag = (
        prediction == -1
    )

    return (
        normalized_score,
        isolation_flag,
    )


# ============================================================
# SPECIFICATION CHECK
# ============================================================

def calculate_specification_evidence(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Check the 0h IDDQ against the current specification.

    A specification violation is evidence for Module A,
    but it is NOT automatically a final REJECT.
    """

    result = df.copy()

    if "absolute_limit_uA" in result.columns:

        result["absolute_limit_uA"] = (
            pd.to_numeric(
                result["absolute_limit_uA"],
                errors="coerce",
            )
        )

        result["current_limit_violation"] = (
            result["iddq_0h_uA"]
            > result["absolute_limit_uA"]
        )

    else:

        result["absolute_limit_uA"] = (
            np.nan
        )

        result["current_limit_violation"] = (
            False
        )

    return result


# ============================================================
# MODULE A SCORE
# ============================================================

def calculate_anomaly_scores(
    df: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    IsolationForest,
]:
    """
    Generate the final Module A anomaly evidence.

    Evidence sources:

        1. Robust peer statistics
        2. Isolation Forest
        3. Current specification violation
    """

    result = df.copy()

    # ========================================================
    # 1. ROBUST STATISTICAL SCORE
    # ========================================================

    absolute_robust_z = (
        result["iddq_robust_z"]
        .abs()
    )

    statistical_score = (
        absolute_robust_z
        / ROBUST_Z_THRESHOLD
    )

    statistical_score = np.clip(
        statistical_score,
        0.0,
        1.0,
    )

    result["statistical_score"] = (
        statistical_score
    )

    result["statistical_anomaly_flag"] = (
        absolute_robust_z
        >= ROBUST_Z_THRESHOLD
    )

    # ========================================================
    # 2. ISOLATION FOREST
    # ========================================================

    features = build_training_features(
        result
    )

    model = fit_isolation_forest(
        features
    )

    (
        isolation_score,
        isolation_flag,
    ) = calculate_isolation_scores(
        model,
        features,
    )

    result["isolation_forest_score"] = (
        isolation_score
    )

    result["isolation_forest_flag"] = (
        isolation_flag
    )

    # ========================================================
    # 3. SPECIFICATION EVIDENCE
    # ========================================================

    result = calculate_specification_evidence(
        result
    )

    # ========================================================
    # 4. COMBINED ANOMALY SCORE
    # ========================================================

    result["combined_anomaly_score"] = (
        0.50
        * result["statistical_score"]
        +
        0.50
        * result["isolation_forest_score"]
    )

    # --------------------------------------------------------
    # Direct current specification violation
    #
    # Give strong anomaly evidence, but still keep the
    # final Module C decision separate.
    # --------------------------------------------------------

    violation_mask = (
        result["current_limit_violation"]
    )

    result.loc[
        violation_mask,
        "combined_anomaly_score",
    ] = np.maximum(
        result.loc[
            violation_mask,
            "combined_anomaly_score",
        ],
        0.85,
    )

    # ========================================================
    # 5. FINAL MODULE A ANOMALY FLAG
    # ========================================================

    result["anomaly_flag"] = (
        result["combined_anomaly_score"]
        >= ANOMALY_SCORE_THRESHOLD
    )

    # ========================================================
    # 6. EVIDENCE COUNT
    # ========================================================

    result["evidence_count"] = (
        result["statistical_anomaly_flag"]
        .astype(int)
        +
        result["isolation_forest_flag"]
        .astype(int)
        +
        result["current_limit_violation"]
        .astype(int)
    )

    # ========================================================
    # 7. SEVERITY
    # ========================================================

    result["severity"] = (
        "LOW"
    )

    result.loc[
        result["combined_anomaly_score"]
        >= 0.60,
        "severity",
    ] = "MEDIUM"

    result.loc[
        result["combined_anomaly_score"]
        >= 0.80,
        "severity",
    ] = "HIGH"

    result.loc[
        (
            result["combined_anomaly_score"]
            >= 0.90
        )
        |
        (
            result["current_limit_violation"]
        ),
        "severity",
    ] = "CRITICAL"

    # ========================================================
    # 8. MODULE A DECISION
    # ========================================================
    #
    # Module A does NOT issue final REJECT.
    #
    # It only says:
    #
    #   PASS   -> no strong 0h anomaly evidence
    #   REVIEW -> 0h anomaly evidence exists
    #
    # Module C will later determine:
    #
    #   PASS / REVIEW / REJECT
    #

    result["module_A_decision"] = np.where(
        result["anomaly_flag"],
        "REVIEW",
        "PASS",
    )

    return (
        result,
        model,
    )


# ============================================================
# OFFLINE EVALUATION
# ============================================================

def evaluate_against_ground_truth(
    df: pd.DataFrame,
) -> None:
    """
    Evaluate Module A against ground_truth when available.

    IMPORTANT:
        ground_truth is NEVER used as a model input.
        It is only used after prediction for evaluation.
    """

    if "ground_truth" not in df.columns:

        print()
        print(
            "No ground_truth column available."
        )

        print(
            "Skipping offline evaluation."
        )

        return

    truth = (
        df["ground_truth"]
        .astype(str)
    )

    # --------------------------------------------------------
    # Define abnormal ground truth
    # --------------------------------------------------------

    actual_abnormal = (
        truth != "Normal"
    )

    predicted_abnormal = (
        df["anomaly_flag"]
        .astype(bool)
    )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    precision = precision_score(
        actual_abnormal,
        predicted_abnormal,
        zero_division=0,
    )

    recall = recall_score(
        actual_abnormal,
        predicted_abnormal,
        zero_division=0,
    )

    f1 = f1_score(
        actual_abnormal,
        predicted_abnormal,
        zero_division=0,
    )

    matrix = confusion_matrix(
        actual_abnormal,
        predicted_abnormal,
    )

    print()
    print(
        "MODULE A OFFLINE EVALUATION"
    )

    print(
        "-" * 45
    )

    print(
        f"Precision : {precision:.4f}"
    )

    print(
        f"Recall    : {recall:.4f}"
    )

    print(
        f"F1 Score  : {f1:.4f}"
    )

    # --------------------------------------------------------
    # Confusion matrix
    # --------------------------------------------------------

    print()
    print(
        "Confusion Matrix"
    )

    print(
        "                "
        "Pred Normal   "
        "Pred Anomaly"
    )

    if matrix.shape == (2, 2):

        print(
            f"Actual Normal     "
            f"{matrix[0, 0]:8d}       "
            f"{matrix[0, 1]:8d}"
        )

        print(
            f"Actual Abnormal   "
            f"{matrix[1, 0]:8d}       "
            f"{matrix[1, 1]:8d}"
        )

    # --------------------------------------------------------
    # Class-level breakdown
    # --------------------------------------------------------

    breakdown = (
        df.assign(
            actual_abnormal=
            actual_abnormal
        )
        .groupby(
            "ground_truth"
        )
        .agg(
            components=(
                "component_id",
                "count",
            ),

            anomaly_rate=(
                "anomaly_flag",
                "mean",
            ),

            mean_score=(
                "combined_anomaly_score",
                "mean",
            ),

            median_score=(
                "combined_anomaly_score",
                "median",
            ),
        )
        .sort_values(
            "components",
            ascending=False,
        )
    )

    print()
    print(
        "Ground-truth breakdown:"
    )

    print(
        breakdown.to_string(
            float_format=
            lambda value:
            f"{value:.4f}"
        )
    )


# ============================================================
# PROCESS ONE CUMULATIVE STAGE
# ============================================================

def process_cumulative_stage(
    cumulative_df: pd.DataFrame,
    stage_number: int,
    expected_total: int,
) -> tuple[
    pd.DataFrame,
    IsolationForest,
]:
    """
    Process one cumulative stage.

    Stage 1:
        2,000

    Stage 2:
        4,000

    Stage 3:
        6,000

    Stage 4:
        8,000

    Stage 5:
        10,000
    """

    print_section(
        f"MODULE A - STAGE {stage_number} "
        f"({expected_total:,} CUMULATIVE COMPONENTS)"
    )

    print(
        f"Cumulative components: "
        f"{len(cumulative_df):,}"
    )

    # ========================================================
    # VALIDATE STAGE SIZE
    # ========================================================

    if len(cumulative_df) != expected_total:

        raise ValueError(
            f"Stage {stage_number} expected "
            f"{expected_total:,} components "
            f"but received "
            f"{len(cumulative_df):,}."
        )

    # ========================================================
    # PREPARE DATA
    # ========================================================

    df = prepare_numeric_columns(
        cumulative_df
    )

    print(
        f"Valid Module A rows: "
        f"{len(df):,}"
    )

    if len(df) != expected_total:

        raise ValueError(
            f"Stage {stage_number} lost data "
            f"during 0h validation.\n"
            f"Expected {expected_total:,} rows.\n"
            f"Valid {len(df):,} rows."
        )

    # ========================================================
    # CREATE PEER GROUPS
    # ========================================================

    df = create_peer_groups(
        df
    )

    print(
        f"Peer groups: "
        f"{df['peer_group'].nunique():,}"
    )

    # ========================================================
    # CALCULATE PEER STATISTICS
    # ========================================================
    #
    # IMPORTANT:
    #
    # peer_group_size is created here.
    #
    # This must happen BEFORE checking peer_group_size.
    #

    df = calculate_peer_statistics(
        df
    )

    # ========================================================
    # CHECK SMALL PEER GROUPS
    # ========================================================

    small_group_components = (
        df["peer_group_size"]
        < 5
    ).sum()

    print(
        f"Components in small peer groups: "
        f"{small_group_components:,}"
    )

    # ========================================================
    # RUN MODULE A
    # ========================================================

    df, model = calculate_anomaly_scores(
        df
    )

    # ========================================================
    # STAGE STATISTICS
    # ========================================================

    anomaly_count = int(
        df["anomaly_flag"]
        .sum()
    )

    pass_count = int(
        (
            df["module_A_decision"]
            == "PASS"
        ).sum()
    )

    review_count = int(
        (
            df["module_A_decision"]
            == "REVIEW"
        ).sum()
    )

    low_count = int(
        (
            df["severity"]
            == "LOW"
        ).sum()
    )

    medium_count = int(
        (
            df["severity"]
            == "MEDIUM"
        ).sum()
    )

    high_count = int(
        (
            df["severity"]
            == "HIGH"
        ).sum()
    )

    critical_count = int(
        (
            df["severity"]
            == "CRITICAL"
        ).sum()
    )

    specification_violations = int(
        df[
            "current_limit_violation"
        ].sum()
    )

    # ========================================================
    # PRINT STAGE RESULT
    # ========================================================

    print()
    print(
        "STAGE RESULT"
    )

    print(
        "-" * 45
    )

    print(
        f"Components processed : "
        f"{len(df):,}"
    )

    print(
        f"0h anomalies         : "
        f"{anomaly_count:,}"
    )

    print(
        f"0h anomaly rate      : "
        f"{(
            anomaly_count
            / len(df)
            * 100
        ):.2f}%"
    )

    print(
        f"Module A PASS        : "
        f"{pass_count:,}"
    )

    print(
        f"Module A REVIEW      : "
        f"{review_count:,}"
    )

    print(
        f"LOW severity         : "
        f"{low_count:,}"
    )

    print(
        f"MEDIUM severity      : "
        f"{medium_count:,}"
    )

    print(
        f"HIGH severity        : "
        f"{high_count:,}"
    )

    print(
        f"CRITICAL severity    : "
        f"{critical_count:,}"
    )

    print(
        f"Current limit violations: "
        f"{specification_violations:,}"
    )

    # ========================================================
    # ADD CUMULATIVE STAGE INFORMATION
    # ========================================================

    df["module_A_stage"] = (
        stage_number
    )

    df["cumulative_component_count"] = (
        expected_total
    )

    # ========================================================
    # SAVE STAGE RESULT
    # ========================================================

    STAGE_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    stage_path = (
        STAGE_OUTPUT_DIR
        /
        f"stage_{stage_number:02d}_"
        f"{expected_total}.csv"
    )

    df.to_csv(
        stage_path,
        index=False,
    )

    print()
    print(
        "Stage output saved:"
    )

    print(
        stage_path
    )

    return (
        df,
        model,
    )


# ============================================================
# SAVE MODEL CONFIGURATION
# ============================================================

def save_model_configuration() -> None:
    """
    Save Module A configuration and information boundary.
    """

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    configuration = {

        "project":
            "SIH 26170",

        "module":
            "Module A",

        "purpose":
            "0h anomaly detection",

        "dataset_architecture": {

            "batch_count":
                TOTAL_BATCHES,

            "components_per_batch":
                COMPONENTS_PER_BATCH,

            "total_components":
                TOTAL_COMPONENTS,

            "cumulative_stages":
                EXPECTED_CUMULATIVE_COUNTS,
        },

        "module_A_inputs": [

            "component_type",

            "temperature_C",

            "voltage_V",

            "iddq_0h_uA",
        ],

        "derived_features": [

            "iddq_peer_median",

            "iddq_peer_mad",

            "iddq_peer_iqr",

            "iddq_peer_deviation",

            "iddq_robust_z",

            "peer_group_size",
        ],

        "future_columns_not_used":
            FUTURE_COLUMNS,

        "peer_group_configuration": {

            "temperature_bin_C":
                TEMPERATURE_BIN_SIZE,

            "voltage_bin_V":
                VOLTAGE_BIN_SIZE,
        },

        "isolation_forest": {

            "n_estimators":
                ISOLATION_FOREST_ESTIMATORS,

            "contamination":
                ISOLATION_FOREST_CONTAMINATION,

            "random_state":
                RANDOM_STATE,
        },

        "decision_configuration": {

            "robust_z_threshold":
                ROBUST_Z_THRESHOLD,

            "anomaly_score_threshold":
                ANOMALY_SCORE_THRESHOLD,
        },

        "deployment_information_boundary":
            (
                "Module A uses only information "
                "available at 0h."
            ),

        "module_A_decision_meaning":
            (
                "PASS means no strong 0h anomaly "
                "evidence was detected. REVIEW means "
                "0h anomaly evidence exists. Module A "
                "does not issue the final REJECT decision."
            ),
    }

    with open(
        CONFIG_OUTPUT,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            configuration,
            file,
            indent=4,
        )

    print()
    print(
        "Configuration saved:"
    )

    print(
        CONFIG_OUTPUT
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)

    print(
        "SIH 26170 - MODULE A"
    )

    print(
        "0h-ONLY CUMULATIVE ANOMALY DETECTION"
    )

    print("=" * 70)

    # ========================================================
    # ARCHITECTURE
    # ========================================================

    print()
    print(
        "Architecture:"
    )

    print(
        "  Batch 1 -> 2,000 components"
    )

    print(
        "  Batch 2 -> 4,000 cumulative"
    )

    print(
        "  Batch 3 -> 6,000 cumulative"
    )

    print(
        "  Batch 4 -> 8,000 cumulative"
    )

    print(
        "  Batch 5 -> 10,000 cumulative"
    )

    print()
    print(
        "Module A information boundary:"
    )

    print(
        "  0h measurements ONLY"
    )

    print(
        "  Future 24h/96h/168h values are NOT used"
    )

    # ========================================================
    # CREATE DIRECTORIES
    # ========================================================

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    STAGE_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # LOAD ALL BATCHES
    # ========================================================

    batches = load_all_batches()

    # ========================================================
    # VALIDATE INFORMATION BOUNDARY
    # ========================================================

    validate_module_a_information_boundary(
        batches[0]
    )

    # ========================================================
    # PROCESS CUMULATIVE STAGES
    # ========================================================

    cumulative_batches = []

    final_result = None

    final_model = None

    for stage_index in range(
        TOTAL_BATCHES
    ):

        # ----------------------------------------------------
        # Add the next 2,000-component batch
        # ----------------------------------------------------

        cumulative_batches.append(
            batches[stage_index]
        )

        # ----------------------------------------------------
        # Build cumulative dataset
        # ----------------------------------------------------

        cumulative_df = pd.concat(
            cumulative_batches,
            ignore_index=True,
        )

        stage_number = (
            stage_index + 1
        )

        expected_total = (
            EXPECTED_CUMULATIVE_COUNTS[
                stage_index
            ]
        )

        # ----------------------------------------------------
        # Process cumulative stage
        # ----------------------------------------------------

        (
            stage_result,
            stage_model,
        ) = process_cumulative_stage(
            cumulative_df=
                cumulative_df,

            stage_number=
                stage_number,

            expected_total=
                expected_total,
        )

        # ----------------------------------------------------
        # Stage 5 becomes final result
        # ----------------------------------------------------

        if stage_number == 5:

            final_result = (
                stage_result
            )

            final_model = (
                stage_model
            )

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    print_section(
        "FINAL MODULE A RESULT - 10,000 COMPONENTS"
    )

    if final_result is None:

        raise RuntimeError(
            "Stage 5 did not produce "
            "a final Module A result."
        )

    if len(final_result) != TOTAL_COMPONENTS:

        raise RuntimeError(
            f"Final result contains "
            f"{len(final_result):,} rows "
            f"instead of "
            f"{TOTAL_COMPONENTS:,}."
        )

    duplicate_ids = (
        final_result[
            "component_id"
        ]
        .duplicated()
        .sum()
    )

    if duplicate_ids > 0:

        raise RuntimeError(
            f"Final result contains "
            f"{duplicate_ids} duplicate "
            f"component IDs."
        )

    # ========================================================
    # SAVE FINAL RESULT
    # ========================================================

    final_result.to_csv(
        FINAL_OUTPUT,
        index=False,
    )

    print()
    print(
        "Final Module A result saved:"
    )

    print(
        FINAL_OUTPUT
    )

    # ========================================================
    # SAVE FINAL MODEL
    # ========================================================

    joblib.dump(
        final_model,
        MODEL_OUTPUT,
    )

    print()
    print(
        "Final Isolation Forest saved:"
    )

    print(
        MODEL_OUTPUT
    )

    # ========================================================
    # SAVE CONFIGURATION
    # ========================================================

    save_model_configuration()

    # ========================================================
    # OFFLINE EVALUATION
    # ========================================================

    evaluate_against_ground_truth(
        final_result
    )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print_section(
        "FINAL 10,000-COMPONENT SUMMARY"
    )

    total_components = len(
        final_result
    )

    total_anomalies = int(
        final_result[
            "anomaly_flag"
        ].sum()
    )

    total_pass = int(
        (
            final_result[
                "module_A_decision"
            ]
            == "PASS"
        ).sum()
    )

    total_review = int(
        (
            final_result[
                "module_A_decision"
            ]
            == "REVIEW"
        ).sum()
    )

    print(
        f"Total components : "
        f"{total_components:,}"
    )

    print(
        f"Module A PASS    : "
        f"{total_pass:,}"
    )

    print(
        f"Module A REVIEW  : "
        f"{total_review:,}"
    )

    print(
        f"0h anomalies     : "
        f"{total_anomalies:,}"
    )

    print()
    print(
        "Cumulative stages completed:"
    )

    for stage_number, count in enumerate(
        EXPECTED_CUMULATIVE_COUNTS,
        start=1,
    ):

        print(
            f"  Stage {stage_number}: "
            f"{count:,} components"
        )

    # ========================================================
    # FINAL MESSAGE
    # ========================================================

    print()
    print(
        "Module A pipeline completed successfully."
    )

    print()
    print(
        "Information boundary confirmed:"
    )

    print(
        "  Module A = 0h anomaly detection"
    )

    print(
        "  Module B = 0h + 24h future-risk prediction"
    )

    print(
        "  Module C = final screening decision"
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()

