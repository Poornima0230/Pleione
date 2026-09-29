from pathlib import Path
import json
import warnings

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

MODULE_A_DIR = BASE_DIR / "data" / "module_A_results"
MODULE_B_FILE = BASE_DIR / "data" / "module_B" / "module_B_drift_predictions.csv"

CONFIG_FILE = BASE_DIR / "risk_config.json"

OUTPUT_DIR = BASE_DIR / "data" / "risk"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FINAL_OUTPUT = OUTPUT_DIR / "overall_risk_results.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "risk_stage_summary.csv"


# ============================================================
# DEFAULT CONFIGURATION
# ============================================================

DEFAULT_CONFIG = {
    "weights": {
        "anomaly": 0.35,
        "drift": 0.20,
        "future": 0.30,
        "specification": 0.15,
    },

    "risk_thresholds": {
        "critical": 80,
        "high": 60,
        "medium": 30,
    },

    "module_a_thresholds": {
        "review": 0.50,
        "high": 0.70,
    },

    "module_b_thresholds": {
        "review": 0.50,
        "high": 0.75,
    },

    "specification_thresholds": {
        "near": 0.90,
        "high_utilization": 0.95,
    },
}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clamp(value, low=0.0, high=1.0):
    """Clamp a numeric value to [low, high]."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return low

    if not np.isfinite(value):
        return low

    return max(low, min(high, value))


def safe_float(value, default=0.0):
    """Convert a value safely to float."""
    try:
        value = float(value)
        if np.isfinite(value):
            return value
    except (TypeError, ValueError):
        pass

    return default


def safe_bool(value):
    """Convert common dataframe values to bool safely."""
    if isinstance(value, bool):
        return value

    if pd.isna(value):
        return False

    if isinstance(value, str):
        return value.strip().lower() in {
            "true",
            "1",
            "yes",
            "y",
            "t",
        }

    try:
        return bool(value)
    except Exception:
        return False


def normalize_text(value):
    """Normalize categorical values."""
    if pd.isna(value):
        return ""

    return str(value).strip().upper()


def load_config():
    """Load risk configuration while preserving safe defaults."""
    config = DEFAULT_CONFIG.copy()

    if not CONFIG_FILE.exists():
        print(f"[INFO] {CONFIG_FILE} not found. Using default configuration.")
        return config

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        for section in config:
            if section in loaded and isinstance(loaded[section], dict):
                config[section].update(loaded[section])

        print(f"[INFO] Loaded configuration from: {CONFIG_FILE}")

    except Exception as exc:
        warnings.warn(
            f"Could not load risk configuration: {exc}. "
            "Using default configuration."
        )

    return config


def validate_required_columns(df, required_columns, source_name):
    """Validate required columns exist."""
    missing = [col for col in required_columns if col not in df.columns]

    if missing:
        raise ValueError(
            f"{source_name} is missing required columns:\n"
            f"{missing}"
        )


# ============================================================
# DATA LOADING
# ============================================================

def load_module_a(stage):
    """Load Module A stage output."""
    file_path = MODULE_A_DIR / f"stage_{stage:02d}.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            f"Module A stage file not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    required = [
        "component_id",
        "iddq_0h_uA",
        "absolute_limit_uA",
    ]

    validate_required_columns(
        df,
        required,
        f"Module A stage {stage}"
    )

    return df


def load_module_b():
    """Load Module B prediction output."""
    if not MODULE_B_FILE.exists():
        raise FileNotFoundError(
            f"Module B file not found: {MODULE_B_FILE}"
        )

    df = pd.read_csv(MODULE_B_FILE)

    required = [
        "component_id",
        "predicted_drift_uA",
        "predicted_drift_rate",
        "predicted_relative_drift",
        "drift_slope_excess",
        "early_drift_flag",
        "predicted_168h_uA",
        "prediction_lower_uA",
        "prediction_upper_uA",
        "future_drift_risk",
        "module_b_status",
        "predicted_limit_exceeded",
        "uncertainty_adjusted_failure",
    ]

    validate_required_columns(
        df,
        required,
        "Module B"
    )

    return df


# ============================================================
# DRIFT CALIBRATION
# ============================================================

def build_drift_calibration(module_b_df):
    """
    Build unsupervised calibration statistics from Module B predictions.

    IMPORTANT:
    This uses only Module B prediction outputs.

    It does NOT use:
      - actual 96h measurements
      - actual 168h measurements
      - actual drift
      - ground truth

    Each continuous signal is calibrated between its median and
    95th percentile.

    This prevents the previous problem where thresholds such as
    0.03 drift rate caused thousands of components to immediately
    saturate at drift_factor = 1.0.
    """

    calibration = {}

    columns = [
        "predicted_drift_rate",
        "predicted_relative_drift",
        "drift_slope_excess",
    ]

    for column in columns:
        values = pd.to_numeric(
            module_b_df[column],
            errors="coerce"
        )

        values = values.replace(
            [np.inf, -np.inf],
            np.nan
        ).dropna()

        values = values[values >= 0]

        if values.empty:
            calibration[column] = {
                "median": 0.0,
                "q95": 1.0,
            }
            continue

        median = float(values.quantile(0.50))
        q95 = float(values.quantile(0.95))
        maximum = float(values.max())

        if q95 <= median:
            q95 = maximum

        if q95 <= median:
            q95 = median + 1e-9

        calibration[column] = {
            "median": median,
            "q95": q95,
        }

    return calibration


def percentile_signal_score(
    value,
    median,
    q95,
):
    """
    Convert a continuous prediction into a 0-1 risk signal.

    <= median       -> 0
    median          -> 0
    q95             -> 1
    >= q95          -> 1
    """

    value = max(0.0, safe_float(value))

    median = safe_float(median)
    q95 = safe_float(q95)

    if q95 <= median:
        return 0.0

    return clamp(
        (value - median) / (q95 - median)
    )


def calculate_drift_components(row, calibration):
    """
    Calculate individual continuous drift evidence.

    Continuous signals are primary.
    early_drift_flag is only a small supporting signal.
    """

    drift_rate_score = percentile_signal_score(
        row.get("predicted_drift_rate", 0),
        calibration["predicted_drift_rate"]["median"],
        calibration["predicted_drift_rate"]["q95"],
    )

    relative_drift_score = percentile_signal_score(
        row.get("predicted_relative_drift", 0),
        calibration["predicted_relative_drift"]["median"],
        calibration["predicted_relative_drift"]["q95"],
    )

    slope_score = percentile_signal_score(
        row.get("drift_slope_excess", 0),
        calibration["drift_slope_excess"]["median"],
        calibration["drift_slope_excess"]["q95"],
    )

    early_flag = safe_bool(
        row.get("early_drift_flag", False)
    )

    early_score = 0.05 if early_flag else 0.0

    # Continuous signals dominate.
    factor = (
        0.40 * drift_rate_score
        + 0.35 * relative_drift_score
        + 0.20 * slope_score
        + early_score
    )

    return {
        "drift_rate_factor": clamp(drift_rate_score),
        "relative_drift_factor": clamp(relative_drift_score),
        "slope_excess_factor": clamp(slope_score),
        "early_drift_support": early_score,
        "drift_factor": clamp(factor),
    }


def calculate_drift_factor(row, calibration):
    """Calculate final drift factor."""
    components = calculate_drift_components(
        row,
        calibration
    )

    return components["drift_factor"]


# ============================================================
# MODULE A — ANOMALY FACTOR
# ============================================================

def calculate_anomaly_factor(row, config):
    """
    Convert Module A anomaly evidence into a 0-1 factor.

    Module A signals:
      - combined anomaly score
      - statistical anomaly score
      - isolation anomaly score
      - anomaly flag
    """

    combined = clamp(
        safe_float(
            row.get("combined_anomaly_score", 0)
        )
    )

    statistical = clamp(
        safe_float(
            row.get("statistical_anomaly_score", 0)
        )
    )

    isolation = clamp(
        safe_float(
            row.get("isolation_anomaly_score", 0)
        )
    )

    anomaly_flag = safe_bool(
        row.get("anomaly_flag", False)
    )

    avg_model_score = (
        statistical + isolation
    ) / 2.0

    flag_agreement = (
        1.0 if anomaly_flag else 0.0
    )

    factor = (
        0.65 * combined
        + 0.20 * avg_model_score
        + 0.15 * flag_agreement
    )

    # A flag alone should provide evidence,
    # but not create an automatic rejection.
    if anomaly_flag:
        factor = max(
            factor,
            0.60
        )

    return clamp(factor)


# ============================================================
# FUTURE RISK FACTOR
# ============================================================

def calculate_future_factor(row):
    """
    Calculate future-risk evidence.

    Continuous prediction values are primary.

    Categorical future_drift_risk is deliberately given
    lower influence because Module B's categorical labels
    are broad and can contain false positives.

    Direct predicted specification exceedance remains strong.
    """

    predicted = safe_float(
        row.get("predicted_168h_uA", 0)
    )

    upper = safe_float(
        row.get("prediction_upper_uA", 0)
    )

    limit = safe_float(
        row.get("absolute_limit_uA", 0)
    )

    if limit <= 0:
        return 0.0

    point_ratio = predicted / limit
    upper_ratio = upper / limit

    # Point prediction:
    # 80% of limit -> 0
    # 100% of limit -> 1
    point_factor = clamp(
        (point_ratio - 0.80) / 0.20
    )

    # Upper prediction:
    # 95% of limit -> small evidence
    # 110% of limit -> strong evidence
    upper_factor = clamp(
        (upper_ratio - 0.95) / 0.15
    )

    future_risk = normalize_text(
        row.get("future_drift_risk", "")
    )

    categorical_map = {
        "LOW": 0.05,
        "WATCH": 0.15,
        "MEDIUM": 0.30,
        "HIGH": 0.50,
        "CRITICAL": 0.70,
    }

    categorical_factor = categorical_map.get(
        future_risk,
        0.0
    )

    direct_exceedance = safe_bool(
        row.get("predicted_limit_exceeded", False)
    )

    direct_factor = (
        1.0 if direct_exceedance else 0.0
    )

    uncertainty_failure = safe_bool(
        row.get("uncertainty_adjusted_failure", False)
    )

    # Uncertainty is evidence, not a hard failure.
    uncertainty_factor = (
        0.40 if uncertainty_failure else 0.0
    )

    factor = (
        0.35 * point_factor
        + 0.25 * upper_factor
        + 0.10 * categorical_factor
        + 0.20 * direct_factor
        + 0.10 * uncertainty_factor
    )

    return clamp(factor)


# ============================================================
# SPECIFICATION FACTOR
# ============================================================

def calculate_specification(row, config):
    """
    Evaluate current 0h specification compliance.

    Current measured violation remains a hard reject.
    """

    current = safe_float(
        row.get("iddq_0h_uA", 0)
    )

    limit = safe_float(
        row.get("absolute_limit_uA", 0)
    )

    if limit <= 0:
        return {
            "specification_factor": 0.0,
            "current_limit_violation": False,
            "current_utilization": 0.0,
        }

    utilization = current / limit

    violation = (
        current > limit
    )

    if violation:
        factor = 1.0

    else:
        near_threshold = safe_float(
            config["specification_thresholds"].get(
                "near",
                0.90
            ),
            0.90
        )

        if utilization <= near_threshold:
            factor = 0.0

        else:
            factor = clamp(
                (utilization - near_threshold)
                / (1.0 - near_threshold)
            )

    return {
        "specification_factor": clamp(factor),
        "current_limit_violation": violation,
        "current_utilization": utilization,
    }


# ============================================================
# FUTURE SPECIFICATION STATUS
# ============================================================

def future_specification_status(row):
    """Determine whether future point prediction exceeds the limit."""

    predicted = safe_float(
        row.get("predicted_168h_uA", 0)
    )

    limit = safe_float(
        row.get("absolute_limit_uA", 0)
    )

    explicit_flag = safe_bool(
        row.get("predicted_limit_exceeded", False)
    )

    direct_exceedance = (
        limit > 0
        and predicted > limit
    )

    return (
        direct_exceedance
        or explicit_flag
    )


# ============================================================
# OVERALL RISK SCORE
# ============================================================

def calculate_overall_risk(
    anomaly_factor,
    drift_factor,
    future_factor,
    specification_factor,
    config,
):
    """
    Weighted overall risk score from 0-100.
    """

    weights = config["weights"]

    total_weight = (
        safe_float(weights.get("anomaly", 0.35))
        + safe_float(weights.get("drift", 0.20))
        + safe_float(weights.get("future", 0.30))
        + safe_float(weights.get("specification", 0.15))
    )

    if total_weight <= 0:
        total_weight = 1.0

    score = (
        safe_float(weights.get("anomaly", 0.35))
        * anomaly_factor

        + safe_float(weights.get("drift", 0.20))
        * drift_factor

        + safe_float(weights.get("future", 0.30))
        * future_factor

        + safe_float(weights.get("specification", 0.15))
        * specification_factor
    )

    score = (
        score / total_weight
    ) * 100.0

    return clamp(
        score / 100.0
    ) * 100.0


# ============================================================
# RISK LEVEL
# ============================================================

def determine_risk_level(
    risk_score,
    decision,
    config,
):
    """
    Map risk score to LOW/MEDIUM/HIGH/CRITICAL.

    REJECT is always CRITICAL.
    """

    if decision == "REJECT":
        return "CRITICAL"

    thresholds = config["risk_thresholds"]

    critical = safe_float(
        thresholds.get("critical", 80),
        80
    )

    high = safe_float(
        thresholds.get("high", 60),
        60
    )

    medium = safe_float(
        thresholds.get("medium", 30),
        30
    )

    if risk_score >= critical:
        return "CRITICAL"

    if risk_score >= high:
        return "HIGH"

    if risk_score >= medium:
        return "MEDIUM"

    return "LOW"


# ============================================================
# DECISION EVIDENCE
# ============================================================

def calculate_decision_evidence(
    row,
    anomaly_factor,
    drift_factor,
    future_factor,
    specification_factor,
    risk_score,
):
    """
    Convert the factors into an explainable screening decision.

    Decision philosophy:

    REJECT:
      1. Current measured specification violation
      2. Direct future point prediction exceeds limit
      3. Strong converging current/future evidence

    REVIEW:
      Significant but not sufficiently definitive evidence.

    PASS:
      No meaningful evidence requiring intervention.
    """

    combined_score = clamp(
        safe_float(
            row.get("combined_anomaly_score", 0)
        )
    )

    statistical_score = clamp(
        safe_float(
            row.get("statistical_anomaly_score", 0)
        )
    )

    isolation_score = clamp(
        safe_float(
            row.get("isolation_anomaly_score", 0)
        )
    )

    anomaly_flag = safe_bool(
        row.get("anomaly_flag", False)
    )

    statistical_flag = safe_bool(
        row.get("statistical_anomaly_flag", False)
    )

    isolation_flag = safe_bool(
        row.get("isolation_anomaly_flag", False)
    )

    anomaly_signal_count = sum(
        [
            anomaly_flag,
            statistical_flag,
            isolation_flag,
            combined_score >= 0.70,
            statistical_score >= 0.70,
            isolation_score >= 0.70,
        ]
    )

    strong_current_anomaly = (
        anomaly_signal_count >= 2
        or combined_score >= 0.70
        or anomaly_factor >= 0.75
    )

    moderate_current_anomaly = (
        anomaly_signal_count >= 1
        or combined_score >= 0.50
        or anomaly_factor >= 0.50
    )

    # --------------------------------------------------------
    # Drift evidence
    # --------------------------------------------------------

    drift_components = calculate_drift_components(
        row,
        GLOBAL_DRIFT_CALIBRATION
    )

    drift_rate_factor = drift_components[
        "drift_rate_factor"
    ]

    relative_drift_factor = drift_components[
        "relative_drift_factor"
    ]

    slope_factor = drift_components[
        "slope_excess_factor"
    ]

    early_drift_flag = safe_bool(
        row.get("early_drift_flag", False)
    )

    strong_drift = (
        drift_factor >= 0.75
        or (
            drift_rate_factor >= 0.80
            and relative_drift_factor >= 0.80
        )
        or (
            relative_drift_factor >= 0.85
            and slope_factor >= 0.80
        )
    )

    moderate_drift = (
        drift_factor >= 0.40
        or early_drift_flag
    )

    # --------------------------------------------------------
    # Future evidence
    # --------------------------------------------------------

    predicted = safe_float(
        row.get("predicted_168h_uA", 0)
    )

    upper = safe_float(
        row.get("prediction_upper_uA", 0)
    )

    limit = safe_float(
        row.get("absolute_limit_uA", 0)
    )

    point_ratio = (
        predicted / limit
        if limit > 0
        else 0.0
    )

    upper_ratio = (
        upper / limit
        if limit > 0
        else 0.0
    )

    predicted_limit_exceeded = safe_bool(
        row.get("predicted_limit_exceeded", False)
    )

    direct_future_exceedance = (
        limit > 0
        and predicted > limit
    )

    direct_future_exceedance = (
        direct_future_exceedance
        or predicted_limit_exceeded
    )

    uncertainty_failure = safe_bool(
        row.get("uncertainty_adjusted_failure", False)
    )

    future_risk = normalize_text(
        row.get("future_drift_risk", "")
    )

    # IMPORTANT:
    # Do NOT treat future_drift_risk == HIGH by itself
    # as strong future evidence.
    #
    # Strong future evidence requires continuous evidence
    # approaching/exceeding the specification boundary.

    strong_future = (
        direct_future_exceedance
        or (
            future_factor >= 0.75
            and (
                point_ratio >= 0.90
                or upper_ratio >= 1.10
            )
        )
    )

    moderate_future = (
        future_factor >= 0.40
        or future_risk in {
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        }
        or uncertainty_failure
        or direct_future_exceedance
    )

    # --------------------------------------------------------
    # Hard specification evidence
    # --------------------------------------------------------

    specification_result = calculate_specification(
        row,
        CURRENT_CONFIG
    )

    current_limit_violation = specification_result[
        "current_limit_violation"
    ]

    # --------------------------------------------------------
    # HARD REJECT
    # --------------------------------------------------------

    if current_limit_violation:
        return {
            "decision": "REJECT",
            "driver": "CURRENT_SPECIFICATION_LIMIT",
            "reason_code": "CURRENT_LIMIT_VIOLATION",
            "strong_current_anomaly": strong_current_anomaly,
            "moderate_current_anomaly": moderate_current_anomaly,
            "strong_drift": strong_drift,
            "moderate_drift": moderate_drift,
            "strong_future": strong_future,
            "moderate_future": moderate_future,
            "anomaly_signal_count": anomaly_signal_count,
        }

    if direct_future_exceedance:
        return {
            "decision": "REJECT",
            "driver": "PREDICTED_SPECIFICATION_LIMIT",
            "reason_code": "PREDICTED_LIMIT_EXCEEDED",
            "strong_current_anomaly": strong_current_anomaly,
            "moderate_current_anomaly": moderate_current_anomaly,
            "strong_drift": strong_drift,
            "moderate_drift": moderate_drift,
            "strong_future": strong_future,
            "moderate_future": moderate_future,
            "anomaly_signal_count": anomaly_signal_count,
        }

    # --------------------------------------------------------
    # CONVERGING EVIDENCE REJECT
    # --------------------------------------------------------

    converging_evidence = (
        strong_future
        and (
            strong_current_anomaly
            or strong_drift
        )
        and risk_score >= 70
    )

    if converging_evidence:
        return {
            "decision": "REJECT",
            "driver": "CONVERGING_FUTURE_RISK",
            "reason_code": "CONVERGING_EVIDENCE",
            "strong_current_anomaly": strong_current_anomaly,
            "moderate_current_anomaly": moderate_current_anomaly,
            "strong_drift": strong_drift,
            "moderate_drift": moderate_drift,
            "strong_future": strong_future,
            "moderate_future": moderate_future,
            "anomaly_signal_count": anomaly_signal_count,
        }

    # --------------------------------------------------------
    # REVIEW
    # --------------------------------------------------------

    if (
        strong_current_anomaly
        or strong_drift
        or strong_future
        or moderate_current_anomaly
        or moderate_drift
        or moderate_future
        or risk_score >= 30
    ):

        if strong_current_anomaly:
            driver = "CURRENT_ANOMALY_EVIDENCE"

        elif strong_drift:
            driver = "PREDICTED_DRIFT_RISK"

        elif strong_future:
            driver = "FUTURE_SPECIFICATION_RISK"

        elif uncertainty_failure:
            driver = "UNCERTAINTY_ADJUSTED_FUTURE_RISK"

        elif moderate_future:
            driver = "FUTURE_DRIFT_EVIDENCE"

        elif moderate_drift:
            driver = "EARLY_DRIFT_EVIDENCE"

        elif moderate_current_anomaly:
            driver = "CURRENT_ANOMALY_EVIDENCE"

        else:
            driver = "OVERALL_RISK_SCORE"

        return {
            "decision": "REVIEW",
            "driver": driver,
            "reason_code": "REVIEW_REQUIRED",
            "strong_current_anomaly": strong_current_anomaly,
            "moderate_current_anomaly": moderate_current_anomaly,
            "strong_drift": strong_drift,
            "moderate_drift": moderate_drift,
            "strong_future": strong_future,
            "moderate_future": moderate_future,
            "anomaly_signal_count": anomaly_signal_count,
        }

    # --------------------------------------------------------
    # PASS
    # --------------------------------------------------------

    return {
        "decision": "PASS",
        "driver": "NO_SIGNIFICANT_RISK",
        "reason_code": "NO_SIGNIFICANT_EVIDENCE",
        "strong_current_anomaly": strong_current_anomaly,
        "moderate_current_anomaly": moderate_current_anomaly,
        "strong_drift": strong_drift,
        "moderate_drift": moderate_drift,
        "strong_future": strong_future,
        "moderate_future": moderate_future,
        "anomaly_signal_count": anomaly_signal_count,
    }


# ============================================================
# EXPLANATION BUILDER
# ============================================================

def build_explanation(row):
    """Build a concise QA-readable explanation."""

    decision = normalize_text(
        row.get("screening_decision", "")
    )

    driver = str(
        row.get(
            "decision_driver",
            "NO_SIGNIFICANT_RISK"
        )
    )

    current = safe_float(
        row.get("iddq_0h_uA", 0)
    )

    limit = safe_float(
        row.get("absolute_limit_uA", 0)
    )

    predicted = safe_float(
        row.get("predicted_168h_uA", 0)
    )

    upper = safe_float(
        row.get("prediction_upper_uA", 0)
    )

    risk_score = safe_float(
        row.get("overall_risk_score", 0)
    )

    future_risk = str(
        row.get("future_drift_risk", "UNKNOWN")
    )

    current_utilization = (
        current / limit
        if limit > 0
        else 0.0
    )

    predicted_utilization = (
        predicted / limit
        if limit > 0
        else 0.0
    )

    upper_utilization = (
        upper / limit
        if limit > 0
        else 0.0
    )

    if decision == "REJECT":

        if driver == "CURRENT_SPECIFICATION_LIMIT":
            return (
                f"Current 0h Iddq ({current:.2f} µA) exceeds "
                f"the absolute specification limit "
                f"({limit:.2f} µA). Direct specification "
                f"violation requires rejection."
            )

        if driver == "PREDICTED_SPECIFICATION_LIMIT":
            return (
                f"Predicted 168h Iddq ({predicted:.2f} µA) "
                f"exceeds the absolute specification limit "
                f"({limit:.2f} µA). Future specification "
                f"violation requires rejection."
            )

        if driver == "CONVERGING_FUTURE_RISK":
            return (
                f"Multiple independent risk signals converge: "
                f"future prediction ({predicted:.2f} µA), "
                f"prediction upper bound ({upper:.2f} µA), "
                f"and current/drift evidence. "
                f"Overall risk score is {risk_score:.1f}/100."
            )

    if decision == "REVIEW":

        if driver == "CURRENT_ANOMALY_EVIDENCE":
            return (
                f"Current screening contains anomaly evidence. "
                f"Current Iddq is {current:.2f} µA "
                f"({current_utilization * 100:.1f}% of limit). "
                f"Further investigation is recommended."
            )

        if driver == "PREDICTED_DRIFT_RISK":
            return (
                f"Predicted drift shows elevated risk. "
                f"Predicted 168h Iddq is {predicted:.2f} µA "
                f"({predicted_utilization * 100:.1f}% of limit). "
                f"Investigation is recommended before final screening."
            )

        if driver == "FUTURE_SPECIFICATION_RISK":
            return (
                f"Future prediction approaches the specification "
                f"boundary. Predicted 168h Iddq is "
                f"{predicted:.2f} µA and the upper prediction "
                f"bound is {upper:.2f} µA."
            )

        if driver == "UNCERTAINTY_ADJUSTED_FUTURE_RISK":
            return (
                f"Prediction uncertainty reaches the specification "
                f"region. Point prediction is {predicted:.2f} µA "
                f"while the upper prediction bound is "
                f"{upper:.2f} µA. This is treated as review evidence, "
                f"not an automatic failure."
            )

        if driver == "FUTURE_DRIFT_EVIDENCE":
            return (
                f"Future drift indicators show elevated risk "
                f"({future_risk}). Predicted 168h Iddq is "
                f"{predicted:.2f} µA and the upper bound is "
                f"{upper:.2f} µA."
            )

        if driver == "EARLY_DRIFT_EVIDENCE":
            return (
                f"Early drift indicators were detected. "
                f"Predicted future behavior requires investigation "
                f"before final screening."
            )

        return (
            f"Overall risk score is {risk_score:.1f}/100. "
            f"No direct specification violation was detected, "
            f"but the available evidence warrants review."
        )

    return (
        f"No strong anomaly, drift, or future specification "
        f"evidence was detected. Current Iddq is "
        f"{current:.2f} µA and predicted 168h Iddq is "
        f"{predicted:.2f} µA. "
        f"Overall risk score is {risk_score:.1f}/100."
    )


# ============================================================
# PROCESS ONE STAGE
# ============================================================

def process_stage(
    stage,
    module_b,
    config,
    drift_calibration,
):
    """Process one Module A stage against Module B predictions."""

    print()
    print("=" * 70)
    print(f"PROCESSING STAGE {stage}")
    print("=" * 70)

    module_a = load_module_a(stage)

    print(
        f"[INFO] Module A rows: {len(module_a):,}"
    )

    print(
        f"[INFO] Module B rows: {len(module_b):,}"
    )

    # --------------------------------------------------------
    # Prevent duplicate Module B component records
    # --------------------------------------------------------

    if module_b["component_id"].duplicated().any():

        duplicate_count = int(
            module_b["component_id"].duplicated().sum()
        )

        print(
            f"[WARNING] Module B contains "
            f"{duplicate_count:,} duplicate component IDs."
        )

        module_b = (
            module_b
            .drop_duplicates(
                subset=["component_id"],
                keep="last"
            )
            .copy()
        )

    # --------------------------------------------------------
    # Merge Module A + Module B
    # --------------------------------------------------------

    df = module_a.merge(
        module_b,
        on="component_id",
        how="left",
        suffixes=("", "_module_b"),
    )

    print(
        f"[INFO] Merged rows: {len(df):,}"
    )

    # --------------------------------------------------------
    # Numeric conversion
    # --------------------------------------------------------

    numeric_columns = [
        "iddq_0h_uA",
        "absolute_limit_uA",

        "combined_anomaly_score",
        "statistical_anomaly_score",
        "isolation_anomaly_score",

        "predicted_drift_uA",
        "predicted_drift_rate",
        "predicted_relative_drift",
        "drift_slope_excess",

        "predicted_168h_uA",
        "prediction_lower_uA",
        "prediction_upper_uA",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    # --------------------------------------------------------
    # Boolean conversion
    # --------------------------------------------------------

    boolean_columns = [
        "anomaly_flag",
        "statistical_anomaly_flag",
        "isolation_anomaly_flag",
        "early_drift_flag",
        "predicted_limit_exceeded",
        "uncertainty_adjusted_failure",
    ]

    for column in boolean_columns:
        if column in df.columns:
            df[column] = df[column].apply(
                safe_bool
            )

    # --------------------------------------------------------
    # Missing Module B protection
    # --------------------------------------------------------

    missing_module_b = (
        df["predicted_drift_uA"].isna()
        if "predicted_drift_uA" in df.columns
        else pd.Series(
            True,
            index=df.index
        )
    )

    if missing_module_b.any():

        count = int(
            missing_module_b.sum()
        )

        print(
            f"[WARNING] {count:,} components "
            f"have no Module B prediction."
        )

        # Safe defaults.
        for column in [
            "predicted_drift_uA",
            "predicted_drift_rate",
            "predicted_relative_drift",
            "drift_slope_excess",
            "predicted_168h_uA",
            "prediction_lower_uA",
            "prediction_upper_uA",
        ]:
            if column in df.columns:
                df.loc[
                    missing_module_b,
                    column
                ] = 0.0

        for column in [
            "early_drift_flag",
            "predicted_limit_exceeded",
            "uncertainty_adjusted_failure",
        ]:
            if column in df.columns:
                df.loc[
                    missing_module_b,
                    column
                ] = False

        if "future_drift_risk" in df.columns:
            df.loc[
                missing_module_b,
                "future_drift_risk"
            ] = "WATCH"

        if "module_b_status" in df.columns:
            df.loc[
                missing_module_b,
                "module_b_status"
            ] = "NO_PREDICTION"

    # --------------------------------------------------------
    # Calculate factors row by row
    # --------------------------------------------------------

    anomaly_factors = []
    drift_factors = []
    future_factors = []
    specification_factors = []

    drift_rate_factors = []
    relative_drift_factors = []
    slope_factors = []
    early_drift_support = []

    current_limit_violations = []
    current_utilizations = []

    future_limit_exceeded = []

    overall_scores = []
    decisions = []
    risk_levels = []
    drivers = []
    reason_codes = []

    strong_current_values = []
    moderate_current_values = []
    strong_drift_values = []
    moderate_drift_values = []
    strong_future_values = []
    moderate_future_values = []
    anomaly_signal_counts = []

    # --------------------------------------------------------
    # Main risk calculation
    # --------------------------------------------------------

    for _, row in df.iterrows():

        anomaly_factor = calculate_anomaly_factor(
            row,
            config
        )

        drift_components = calculate_drift_components(
            row,
            drift_calibration
        )

        drift_factor = drift_components[
            "drift_factor"
        ]

        future_factor = calculate_future_factor(
            row
        )

        specification_result = calculate_specification(
            row,
            config
        )

        specification_factor = specification_result[
            "specification_factor"
        ]

        risk_score = calculate_overall_risk(
            anomaly_factor,
            drift_factor,
            future_factor,
            specification_factor,
            config,
        )

        evidence = calculate_decision_evidence(
            row,
            anomaly_factor,
            drift_factor,
            future_factor,
            specification_factor,
            risk_score,
        )

        decision = evidence[
            "decision"
        ]

        risk_level = determine_risk_level(
            risk_score,
            decision,
            config,
        )

        anomaly_factors.append(
            anomaly_factor
        )

        drift_factors.append(
            drift_factor
        )

        future_factors.append(
            future_factor
        )

        specification_factors.append(
            specification_factor
        )

        drift_rate_factors.append(
            drift_components["drift_rate_factor"]
        )

        relative_drift_factors.append(
            drift_components["relative_drift_factor"]
        )

        slope_factors.append(
            drift_components["slope_excess_factor"]
        )

        early_drift_support.append(
            drift_components["early_drift_support"]
        )

        current_limit_violations.append(
            specification_result[
                "current_limit_violation"
            ]
        )

        current_utilizations.append(
            specification_result[
                "current_utilization"
            ]
        )

        future_limit_exceeded.append(
            future_specification_status(row)
        )

        overall_scores.append(
            risk_score
        )

        decisions.append(
            decision
        )

        risk_levels.append(
            risk_level
        )

        drivers.append(
            evidence["driver"]
        )

        reason_codes.append(
            evidence["reason_code"]
        )

        strong_current_values.append(
            evidence["strong_current_anomaly"]
        )

        moderate_current_values.append(
            evidence["moderate_current_anomaly"]
        )

        strong_drift_values.append(
            evidence["strong_drift"]
        )

        moderate_drift_values.append(
            evidence["moderate_drift"]
        )

        strong_future_values.append(
            evidence["strong_future"]
        )

        moderate_future_values.append(
            evidence["moderate_future"]
        )

        anomaly_signal_counts.append(
            evidence["anomaly_signal_count"]
        )

    # --------------------------------------------------------
    # Attach factors
    # --------------------------------------------------------

    df["anomaly_factor"] = anomaly_factors

    df["drift_factor"] = drift_factors

    df["future_factor"] = future_factors

    df["specification_factor"] = (
        specification_factors
    )

    # Individual drift evidence.
    df["drift_rate_factor"] = (
        drift_rate_factors
    )

    df["relative_drift_factor"] = (
        relative_drift_factors
    )

    df["slope_excess_factor"] = (
        slope_factors
    )

    df["early_drift_support"] = (
        early_drift_support
    )

    # Specification evidence.
    df["current_limit_violation"] = (
        current_limit_violations
    )

    df["current_utilization"] = (
        current_utilizations
    )

    df["future_limit_exceeded"] = (
        future_limit_exceeded
    )

    # Risk.
    df["overall_risk_score"] = (
        overall_scores
    )

    df["screening_decision"] = (
        decisions
    )

    df["risk_level"] = (
        risk_levels
    )

    df["decision_driver"] = (
        drivers
    )

    df["decision_reason_code"] = (
        reason_codes
    )

    # Evidence columns.
    df["strong_current_anomaly"] = (
        strong_current_values
    )

    df["moderate_current_anomaly"] = (
        moderate_current_values
    )

    df["strong_drift_evidence"] = (
        strong_drift_values
    )

    df["moderate_drift_evidence"] = (
        moderate_drift_values
    )

    df["strong_future_evidence"] = (
        strong_future_values
    )

    df["moderate_future_evidence"] = (
        moderate_future_values
    )

    df["anomaly_signal_count"] = (
        anomaly_signal_counts
    )

    # --------------------------------------------------------
    # Future ratios for UI / investigation
    # --------------------------------------------------------

    df["future_point_ratio"] = (
        df["predicted_168h_uA"]
        / df["absolute_limit_uA"].replace(
            0,
            np.nan
        )
    )

    df["future_upper_ratio"] = (
        df["prediction_upper_uA"]
        / df["absolute_limit_uA"].replace(
            0,
            np.nan
        )
    )

    df["upper_prediction_limit_crossed"] = (
        df["future_upper_ratio"] > 1.0
    )

    # --------------------------------------------------------
    # Explanation
    # --------------------------------------------------------

    df["risk_explanation"] = df.apply(
        build_explanation,
        axis=1
    )

    # --------------------------------------------------------
    # Stage metadata
    # --------------------------------------------------------

    df["risk_stage"] = stage

    # --------------------------------------------------------
    # Sorting
    # --------------------------------------------------------

    decision_order = {
        "REJECT": 0,
        "REVIEW": 1,
        "PASS": 2,
    }

    df["_decision_order"] = (
        df["screening_decision"]
        .map(decision_order)
        .fillna(99)
    )

    df = (
        df
        .sort_values(
            by=[
                "_decision_order",
                "overall_risk_score",
            ],
            ascending=[
                True,
                False,
            ],
        )
        .drop(
            columns=["_decision_order"]
        )
        .reset_index(
            drop=True
        )
    )

    return df


# ============================================================
# STAGE SUMMARY
# ============================================================

def create_stage_summary(df):
    """Create compact stage-level summary."""

    total = len(df)

    decision_counts = (
        df["screening_decision"]
        .value_counts()
        .to_dict()
    )

    risk_counts = (
        df["risk_level"]
        .value_counts()
        .to_dict()
    )

    return {
        "stage": int(
            df["risk_stage"].iloc[0]
        ) if total else None,

        "total_components": total,

        "pass_count": int(
            decision_counts.get(
                "PASS",
                0
            )
        ),

        "review_count": int(
            decision_counts.get(
                "REVIEW",
                0
            )
        ),

        "reject_count": int(
            decision_counts.get(
                "REJECT",
                0
            )
        ),

        "low_risk_count": int(
            risk_counts.get(
                "LOW",
                0
            )
        ),

        "medium_risk_count": int(
            risk_counts.get(
                "MEDIUM",
                0
            )
        ),

        "high_risk_count": int(
            risk_counts.get(
                "HIGH",
                0
            )
        ),

        "critical_risk_count": int(
            risk_counts.get(
                "CRITICAL",
                0
            )
        ),

        "current_limit_violations": int(
            df["current_limit_violation"]
            .sum()
        ),

        "predicted_limit_exceedances": int(
            df["future_limit_exceeded"]
            .sum()
        ),

        "uncertainty_adjusted_failures": int(
            df["uncertainty_adjusted_failure"]
            .sum()
        ),

        "strong_future_evidence_count": int(
            df["strong_future_evidence"]
            .sum()
        ),

        "strong_drift_evidence_count": int(
            df["strong_drift_evidence"]
            .sum()
        ),

        "mean_risk_score": round(
            float(
                df["overall_risk_score"].mean()
            ),
            3
        ),

        "max_risk_score": round(
            float(
                df["overall_risk_score"].max()
            ),
            3
        ),
    }


# ============================================================
# VALIDATION
# ============================================================

def validate_final_result(df):
    """Validate final risk output."""

    print()
    print("=" * 70)
    print("VALIDATING FINAL RISK OUTPUT")
    print("=" * 70)

    required_columns = [
        "component_id",
        "anomaly_factor",
        "drift_factor",
        "future_factor",
        "specification_factor",
        "overall_risk_score",
        "screening_decision",
        "risk_level",
        "decision_driver",
        "risk_explanation",
    ]

    validate_required_columns(
        df,
        required_columns,
        "Final risk output"
    )

    allowed_decisions = {
        "PASS",
        "REVIEW",
        "REJECT",
    }

    invalid_decisions = set(
        df["screening_decision"].dropna()
    ) - allowed_decisions

    if invalid_decisions:
        raise ValueError(
            f"Invalid screening decisions: "
            f"{invalid_decisions}"
        )

    allowed_levels = {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }

    invalid_levels = set(
        df["risk_level"].dropna()
    ) - allowed_levels

    if invalid_levels:
        raise ValueError(
            f"Invalid risk levels: "
            f"{invalid_levels}"
        )

    duplicate_ids = (
        df["component_id"]
        .duplicated()
        .sum()
    )

    if duplicate_ids:
        raise ValueError(
            f"Final output contains "
            f"{duplicate_ids} duplicate component IDs."
        )

    # Every REJECT must be CRITICAL.
    invalid_reject_levels = df[
        (
            df["screening_decision"]
            == "REJECT"
        )
        & (
            df["risk_level"]
            != "CRITICAL"
        )
    ]

    if not invalid_reject_levels.empty:
        raise ValueError(
            "REJECT components must always be CRITICAL."
        )

    # Current measured violation must reject.
    invalid_current_rejects = df[
        df["current_limit_violation"]
        & (
            df["screening_decision"]
            != "REJECT"
        )
    ]

    if not invalid_current_rejects.empty:
        raise ValueError(
            "Current specification violations "
            "must be REJECT."
        )

    # Direct future exceedance must reject.
    invalid_future_rejects = df[
        df["future_limit_exceeded"]
        & (
            df["screening_decision"]
            != "REJECT"
        )
    ]

    if not invalid_future_rejects.empty:
        raise ValueError(
            "Direct future specification exceedances "
            "must be REJECT."
        )

    # Scores should remain between 0 and 100.
    invalid_scores = df[
        (
            df["overall_risk_score"] < 0
        )
        | (
            df["overall_risk_score"] > 100
        )
    ]

    if not invalid_scores.empty:
        raise ValueError(
            "Overall risk score outside [0, 100]."
        )

    # Factors should remain 0-1.
    factor_columns = [
        "anomaly_factor",
        "drift_factor",
        "future_factor",
        "specification_factor",
    ]

    for column in factor_columns:

        invalid = df[
            (
                df[column] < 0
            )
            | (
                df[column] > 1
            )
        ]

        if not invalid.empty:
            raise ValueError(
                f"{column} contains values "
                "outside [0, 1]."
            )

    print("[PASS] Required columns present")
    print("[PASS] Screening decisions valid")
    print("[PASS] Risk levels valid")
    print("[PASS] Component IDs unique")
    print("[PASS] REJECT -> CRITICAL validation passed")
    print("[PASS] Current violation validation passed")
    print("[PASS] Future exceedance validation passed")
    print("[PASS] Risk score range validation passed")
    print("[PASS] Risk factor range validation passed")

    print()
    print("Final output validation successful.")


# ============================================================
# REPORTING
# ============================================================

def print_decision_summary(df):
    """Print final decision distribution."""

    print()
    print("=" * 70)
    print("FINAL SCREENING DECISIONS")
    print("=" * 70)

    counts = (
        df["screening_decision"]
        .value_counts()
    )

    total = len(df)

    for decision in [
        "PASS",
        "REVIEW",
        "REJECT",
    ]:
        count = int(
            counts.get(
                decision,
                0
            )
        )

        percentage = (
            count / total * 100
            if total
            else 0
        )

        print(
            f"{decision:<8} "
            f"{count:>7,} "
            f"({percentage:>6.2f}%)"
        )


def print_risk_summary(df):
    """Print final risk distribution."""

    print()
    print("=" * 70)
    print("FINAL RISK LEVELS")
    print("=" * 70)

    counts = (
        df["risk_level"]
        .value_counts()
    )

    total = len(df)

    for level in [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ]:
        count = int(
            counts.get(
                level,
                0
            )
        )

        percentage = (
            count / total * 100
            if total
            else 0
        )

        print(
            f"{level:<8} "
            f"{count:>7,} "
            f"({percentage:>6.2f}%)"
        )


def print_specification_evidence(df):
    """Print specification/future evidence."""

    print()
    print("=" * 70)
    print("SPECIFICATION / FUTURE EVIDENCE")
    print("=" * 70)

    current_violations = int(
        df["current_limit_violation"]
        .sum()
    )

    future_exceedances = int(
        df["future_limit_exceeded"]
        .sum()
    )

    uncertainty_failures = int(
        df["uncertainty_adjusted_failure"]
        .sum()
    )

    rejects = int(
        (
            df["screening_decision"]
            == "REJECT"
        ).sum()
    )

    print(
        f"Current 0h limit violations: "
        f"{current_violations:,}"
    )

    print(
        f"Predicted 168h limit exceedances: "
        f"{future_exceedances:,}"
    )

    print(
        f"Uncertainty-adjusted failures: "
        f"{uncertainty_failures:,}"
    )

    print(
        f"Final REJECT decisions: "
        f"{rejects:,}"
    )

    print(
        f"Strong future evidence: "
        f"{int(df['strong_future_evidence'].sum()):,}"
    )

    print(
        f"Strong drift evidence: "
        f"{int(df['strong_drift_evidence'].sum()):,}"
    )


def print_reject_evidence(df):
    """Print reject evidence breakdown."""

    print()
    print("=" * 70)
    print("REJECT EVIDENCE")
    print("=" * 70)

    reject_df = df[
        df["screening_decision"]
        == "REJECT"
    ]

    if reject_df.empty:
        print("No REJECT decisions.")
        return

    current_rejects = int(
        (
            reject_df["decision_driver"]
            == "CURRENT_SPECIFICATION_LIMIT"
        ).sum()
    )

    predicted_rejects = int(
        (
            reject_df["decision_driver"]
            == "PREDICTED_SPECIFICATION_LIMIT"
        ).sum()
    )

    convergence_rejects = int(
        (
            reject_df["decision_driver"]
            == "CONVERGING_FUTURE_RISK"
        ).sum()
    )

    print(
        f"Direct current specification rejects: "
        f"{current_rejects:,}"
    )

    print(
        f"Direct predicted specification rejects: "
        f"{predicted_rejects:,}"
    )

    print(
        f"Converging-evidence rejects: "
        f"{convergence_rejects:,}"
    )


def print_top_risk_components(df, n=10):
    """Print highest-risk components."""

    print()
    print("=" * 70)
    print(f"TOP {n} HIGHEST-RISK COMPONENTS")
    print("=" * 70)

    columns = [
        "component_id",
        "screening_decision",
        "risk_level",
        "overall_risk_score",
        "anomaly_factor",
        "drift_factor",
        "future_factor",
        "specification_factor",
        "decision_driver",
        "predicted_168h_uA",
        "prediction_upper_uA",
        "absolute_limit_uA",
    ]

    available = [
        column
        for column in columns
        if column in df.columns
    ]

    top = (
        df
        .sort_values(
            "overall_risk_score",
            ascending=False
        )
        .head(n)
    )

    print(
        top[available]
        .to_string(
            index=False
        )
    )


def print_drift_calibration(calibration):
    """Print the calibration values used by Module C."""

    print()
    print("=" * 70)
    print("MODULE B DRIFT CALIBRATION")
    print("=" * 70)

    for column, values in calibration.items():

        print(
            f"{column:<30} "
            f"median={values['median']:.6f}  "
            f"q95={values['q95']:.6f}"
        )


# ============================================================
# GLOBALS
# ============================================================

GLOBAL_DRIFT_CALIBRATION = {}
CURRENT_CONFIG = {}


# ============================================================
# MAIN
# ============================================================

def main():

    global GLOBAL_DRIFT_CALIBRATION
    global CURRENT_CONFIG

    print()
    print("=" * 70)
    print("PLEIONE MODULE C — RISK ENGINE")
    print("=" * 70)

    print(
        "Purpose: combine Module A anomaly evidence, "
        "Module B predicted drift, future specification evidence, "
        "and current specification compliance."
    )

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    config = load_config()
    CURRENT_CONFIG = config

    # --------------------------------------------------------
    # Load Module B
    # --------------------------------------------------------

    print()
    print("[INFO] Loading Module B predictions...")

    module_b = load_module_b()

    print(
        f"[INFO] Module B components: "
        f"{len(module_b):,}"
    )

    # --------------------------------------------------------
    # Build calibration
    # --------------------------------------------------------

    GLOBAL_DRIFT_CALIBRATION = (
        build_drift_calibration(
            module_b
        )
    )

    print_drift_calibration(
        GLOBAL_DRIFT_CALIBRATION
    )

    # --------------------------------------------------------
    # Process stages
    # --------------------------------------------------------

    all_stage_results = []
    stage_summaries = []

    for stage in range(1, 6):

        stage_result = process_stage(
            stage=stage,
            module_b=module_b,
            config=config,
            drift_calibration=GLOBAL_DRIFT_CALIBRATION,
        )

        stage_output = (
            OUTPUT_DIR
            / f"risk_stage_{stage:02d}.csv"
        )

        stage_result.to_csv(
            stage_output,
            index=False
        )

        print(
            f"[SAVED] {stage_output}"
        )

        summary = create_stage_summary(
            stage_result
        )

        stage_summaries.append(
            summary
        )

        all_stage_results.append(
            stage_result
        )

    # --------------------------------------------------------
    # Combine stages
    # --------------------------------------------------------

    final_df = pd.concat(
        all_stage_results,
        ignore_index=True
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # If each stage contains the same component IDs,
    # keep the latest stage for the final screening result.
    # --------------------------------------------------------

    if final_df["component_id"].duplicated().any():

        duplicate_count = int(
            final_df["component_id"]
            .duplicated()
            .sum()
        )

        print()
        print(
            f"[INFO] Combined stage outputs contain "
            f"{duplicate_count:,} repeated component-stage records."
        )

        print(
            "[INFO] Final component-level result will use "
            "the latest available stage."
        )

        final_df = (
            final_df
            .sort_values(
                [
                    "component_id",
                    "risk_stage",
                ]
            )
            .drop_duplicates(
                subset=["component_id"],
                keep="last"
            )
            .reset_index(
                drop=True
            )
        )

    # --------------------------------------------------------
    # Recalculate explanations after final selection
    # --------------------------------------------------------

    final_df["risk_explanation"] = (
        final_df.apply(
            build_explanation,
            axis=1
        )
    )

    # --------------------------------------------------------
    # Final validation
    # --------------------------------------------------------

    validate_final_result(
        final_df
    )

    # --------------------------------------------------------
    # Save final result
    # --------------------------------------------------------

    final_df.to_csv(
        FINAL_OUTPUT,
        index=False
    )

    print()
    print(
        f"[SAVED] Final risk output: "
        f"{FINAL_OUTPUT}"
    )

    # --------------------------------------------------------
    # Stage summary
    # --------------------------------------------------------

    summary_df = pd.DataFrame(
        stage_summaries
    )

    summary_df.to_csv(
        SUMMARY_OUTPUT,
        index=False
    )

    print(
        f"[SAVED] Stage summary: "
        f"{SUMMARY_OUTPUT}"
    )

    # --------------------------------------------------------
    # Final reports
    # --------------------------------------------------------

    print_decision_summary(
        final_df
    )

    print_risk_summary(
        final_df
    )

    print_specification_evidence(
        final_df
    )

    print_reject_evidence(
        final_df
    )

    print_top_risk_components(
        final_df,
        n=10
    )

    # --------------------------------------------------------
    # Completion
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("MODULE C RISK ENGINE COMPLETED")
    print("=" * 70)

    print(
        f"Final components: "
        f"{len(final_df):,}"
    )

    print(
        f"Final output: "
        f"{FINAL_OUTPUT}"
    )

    print()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()