"""
PLEIONE - MODULE C
Risk Fusion & Early Screening

SIH 26170
AI-Driven Anomaly Detection in Component Burn-In & Screening

Module C combines:
    Module A -> observed anomaly evidence
    Module B -> predicted drift / future risk
    Specification -> current and predicted limit evidence

Important:
    ground_truth is evaluation-only.
    It is NEVER used to calculate risk, score, or screening decision.
"""

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

RISK_DIR = BASE_DIR / "data" / "risk"
RISK_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = BASE_DIR / "risk_config.json"


# ============================================================
# DEFAULT CONFIGURATION
# ============================================================

DEFAULT_CONFIG = {
    "weights": {
        "anomaly": 0.30,
        "drift": 0.25,
        "future": 0.30,
        "specification": 0.15,
    },
    "thresholds": {
        "medium": 30.0,
        "high": 60.0,
        "critical": 80.0,
    },
}


# ============================================================
# CONFIGURATION
# ============================================================

def load_config():
    """
    Load risk configuration.

    If risk_config.json does not exist or contains invalid data,
    the default configuration is used.
    """

    config = DEFAULT_CONFIG.copy()

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_config = json.load(f)

            if "weights" in user_config:
                config["weights"].update(user_config["weights"])

            if "thresholds" in user_config:
                config["thresholds"].update(user_config["thresholds"])

        except Exception as exc:
            warnings.warn(
                f"Could not load {CONFIG_FILE}: {exc}. "
                "Using default configuration."
            )

    # Normalize weights so accidental config errors do not
    # change the intended relative contribution.
    weights = config["weights"]

    total_weight = sum(float(v) for v in weights.values())

    if total_weight <= 0:
        config["weights"] = DEFAULT_CONFIG["weights"].copy()
    else:
        for key in weights:
            weights[key] = float(weights[key]) / total_weight

    return config


CONFIG = load_config()

WEIGHTS = CONFIG["weights"]
THRESHOLDS = CONFIG["thresholds"]


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clip01(value):
    """
    Clamp a scalar to [0, 1].
    """

    if value is None:
        return 0.0

    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0

    if not np.isfinite(value):
        return 0.0

    return float(np.clip(value, 0.0, 1.0))


def safe_float(value, default=0.0):
    """
    Convert a value safely to float.
    """

    try:
        value = float(value)

        if not np.isfinite(value):
            return default

        return value

    except (TypeError, ValueError):
        return default


def normalize_flag(value):
    """
    Safely convert common boolean representations to bool.
    """

    if isinstance(value, bool):
        return value

    if pd.isna(value):
        return False

    if isinstance(value, (int, float)):
        return bool(value)

    value = str(value).strip().lower()

    return value in {
        "true",
        "1",
        "yes",
        "y",
        "anomaly",
        "flagged",
    }


def percentile_position(value, median, q95):
    """
    Distribution-based calibration.

    median -> 0
    q95    -> 1

    Values between them are scaled smoothly.

    This is preferable to arbitrary hard-coded thresholds because
    Module B's output distribution is learned from the actual data.
    """

    value = safe_float(value)

    median = safe_float(median)
    q95 = safe_float(q95)

    if q95 <= median:
        return 1.0 if value > median else 0.0

    if value <= median:
        return 0.0

    if value >= q95:
        return 1.0

    return clip01((value - median) / (q95 - median))


def risk_level_from_score(score):
    """
    Convert numerical risk score to risk level.
    """

    score = safe_float(score)

    if score >= THRESHOLDS["critical"]:
        return "CRITICAL"

    if score >= THRESHOLDS["high"]:
        return "HIGH"

    if score >= THRESHOLDS["medium"]:
        return "MEDIUM"

    return "LOW"


# ============================================================
# MODULE A VALIDATION
# ============================================================

def validate_module_a(df, path):
    """
    Validate the ACTUAL Module A schema.

    Current Module A provides:

        component_id
        component_type
        combined_anomaly_score
        anomaly_flag
        statistical_score
        statistical_anomaly_flag
        isolation_forest_score
        isolation_forest_flag
        absolute_limit_uA
        iddq_0h_uA

    Module A does NOT currently provide:

        temporal_anomaly_score
        temporal_anomaly_flag
        statistical_evidence_count
        limit_violation
        limit_excess_uA

    Therefore those values are derived inside Module C.
    """

    required_columns = [
        "component_id",
        "component_type",
        "combined_anomaly_score",
        "anomaly_flag",
        "statistical_score",
        "statistical_anomaly_flag",
        "isolation_forest_score",
        "isolation_forest_flag",
        "absolute_limit_uA",
        "iddq_0h_uA",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Module A file {path} is missing required columns:\n"
            + "\n".join(f" - {column}" for column in missing)
        )

    numeric_columns = [
        "combined_anomaly_score",
        "statistical_score",
        "isolation_forest_score",
        "absolute_limit_uA",
        "iddq_0h_uA",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    invalid_numeric = [
        column
        for column in numeric_columns
        if df[column].isna().any()
    ]

    if invalid_numeric:
        raise ValueError(
            f"Module A file {path} contains invalid numeric values:\n"
            + "\n".join(f" - {column}" for column in invalid_numeric)
        )

    boolean_columns = [
        "anomaly_flag",
        "statistical_anomaly_flag",
        "isolation_forest_flag",
    ]

    for column in boolean_columns:
        df[column] = df[column].apply(normalize_flag)

    return df


# ============================================================
# MODULE B VALIDATION
# ============================================================

def validate_module_b(df):
    """
    Validate Module B prediction data.
    """

    required_columns = [
        "component_id",
        "predicted_drift_rate",
        "predicted_relative_drift",
        "drift_slope_excess",
        "predicted_168h_uA",
        "prediction_lower_uA",
        "prediction_upper_uA",
        "early_drift_flag",
        "uncertainty_adjusted_failure",
        "predicted_limit_exceeded",
        "future_drift_risk",
        "module_b_status",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Module B is missing required columns:\n"
            + "\n".join(f" - {column}" for column in missing)
        )

    numeric_columns = [
        "predicted_drift_rate",
        "predicted_relative_drift",
        "drift_slope_excess",
        "predicted_168h_uA",
        "prediction_lower_uA",
        "prediction_upper_uA",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    for column in [
        "early_drift_flag",
        "uncertainty_adjusted_failure",
        "predicted_limit_exceeded",
    ]:
        df[column] = df[column].apply(normalize_flag)

    return df


# ============================================================
# MODULE B CALIBRATION
# ============================================================

def calculate_module_b_calibration(module_b):
    """
    Learn drift reference points from Module B itself.

    We use:
        median -> normal/reference region
        q95    -> strong drift region

    This avoids arbitrary universal thresholds.
    """

    calibration = {}

    columns = [
        "predicted_drift_rate",
        "predicted_relative_drift",
        "drift_slope_excess",
    ]

    print("\nModule B drift calibration:")

    for column in columns:
        values = pd.to_numeric(
            module_b[column],
            errors="coerce",
        ).dropna()

        if len(values) == 0:
            median = 0.0
            q95 = 1.0
        else:
            median = float(values.median())
            q95 = float(values.quantile(0.95))

        calibration[column] = {
            "median": median,
            "q95": q95,
        }

        print(
            f"  {column}: "
            f"median={median:.6f}, "
            f"q95={q95:.6f}"
        )

    return calibration


# ============================================================
# MODULE A ANOMALY FACTOR
# ============================================================

def calculate_anomaly_factor(row):
    """
    Calculate Module A anomaly evidence.

    Current available evidence:

        1. combined anomaly score
        2. statistical detector
        3. isolation forest detector
        4. detector agreement

    There is intentionally NO artificial anomaly floor.

    A component is not automatically considered risky merely because
    anomaly_flag is True. The actual evidence strength matters.
    """

    combined_score = clip01(
        row.get("combined_anomaly_score", 0.0)
    )

    statistical_score = clip01(
        row.get("statistical_score", 0.0)
    )

    isolation_score = clip01(
        row.get("isolation_forest_score", 0.0)
    )

    statistical_flag = normalize_flag(
        row.get("statistical_anomaly_flag", False)
    )

    isolation_flag = normalize_flag(
        row.get("isolation_forest_flag", False)
    )

    anomaly_flag = normalize_flag(
        row.get("anomaly_flag", False)
    )

    detector_average = (
        statistical_score + isolation_score
    ) / 2.0

    evidence_count = (
        int(statistical_flag)
        + int(isolation_flag)
    )

    if evidence_count == 2:
        agreement_factor = 1.0
    elif evidence_count == 1:
        agreement_factor = 0.50
    else:
        agreement_factor = 0.0

    factor = (
        0.60 * combined_score
        + 0.25 * detector_average
        + 0.15 * agreement_factor
    )

    # The anomaly flag is used as supporting evidence only.
    # It does not force the score upward.
    if anomaly_flag:
        factor = max(factor, combined_score * 0.90)

    return clip01(factor), evidence_count


# ============================================================
# MODULE B DRIFT FACTOR
# ============================================================

def calculate_drift_factor(row, calibration):
    """
    Calculate current drift evidence from Module B.

    Components:

        predicted_drift_rate
        predicted_relative_drift
        drift_slope_excess
        early_drift_flag

    Negative drift values do not create positive risk.
    """

    drift_rate = max(
        0.0,
        safe_float(row.get("predicted_drift_rate", 0.0)),
    )

    relative_drift = max(
        0.0,
        safe_float(row.get("predicted_relative_drift", 0.0)),
    )

    slope_excess = max(
        0.0,
        safe_float(row.get("drift_slope_excess", 0.0)),
    )

    early_flag = normalize_flag(
        row.get("early_drift_flag", False)
    )

    rate_factor = percentile_position(
        drift_rate,
        calibration["predicted_drift_rate"]["median"],
        calibration["predicted_drift_rate"]["q95"],
    )

    relative_factor = percentile_position(
        relative_drift,
        calibration["predicted_relative_drift"]["median"],
        calibration["predicted_relative_drift"]["q95"],
    )

    slope_factor = percentile_position(
        slope_excess,
        calibration["drift_slope_excess"]["median"],
        calibration["drift_slope_excess"]["q95"],
    )

    # Early flag is supporting evidence, not a full risk score.
    early_support = 0.35 if early_flag else 0.0

    drift_factor = (
        0.40 * rate_factor
        + 0.35 * relative_factor
        + 0.20 * slope_factor
        + 0.05 * early_support
    )

    return (
        clip01(drift_factor),
        rate_factor,
        relative_factor,
        slope_factor,
        early_support,
    )


# ============================================================
# FUTURE RISK FACTOR
# ============================================================

def calculate_future_factor(row, limit):
    """
    Calculate future risk using Module B predictions.

    Evidence:

        - predicted 168h current-to-limit ratio
        - upper prediction bound vs limit
        - categorical future risk
        - direct predicted limit exceedance
        - uncertainty-adjusted failure

    Important:
        A categorical HIGH label alone does NOT create an automatic
        reject or strong-future condition.
    """

    predicted = safe_float(
        row.get("predicted_168h_uA", 0.0)
    )

    upper = safe_float(
        row.get("prediction_upper_uA", 0.0)
    )

    direct_exceedance = normalize_flag(
        row.get("predicted_limit_exceeded", False)
    )

    uncertainty_failure = normalize_flag(
        row.get("uncertainty_adjusted_failure", False)
    )

    future_risk = str(
        row.get("future_drift_risk", "LOW")
    ).upper()

    if limit <= 0:
        point_ratio = 0.0
        upper_ratio = 0.0
    else:
        point_ratio = predicted / limit
        upper_ratio = upper / limit

    # Point prediction:
    # <80% of limit -> low
    # 80-100% -> progressively increasing
    # >=100% -> maximum
    point_factor = clip01(
        (point_ratio - 0.80) / 0.20
    )

    # Upper prediction:
    # <80% -> low
    # 80-110% -> progressively increasing
    # >=110% -> maximum
    upper_factor = clip01(
        (upper_ratio - 0.80) / 0.30
    )

    categorical_factor = {
        "LOW": 0.00,
        "WATCH": 0.15,
        "MEDIUM": 0.35,
        "HIGH": 0.55,
        "CRITICAL": 0.75,
    }.get(
        future_risk,
        0.0,
    )

    direct_factor = 1.0 if direct_exceedance else 0.0

    uncertainty_factor = (
        0.55 if uncertainty_failure else 0.0
    )

    future_factor = (
        0.35 * point_factor
        + 0.25 * upper_factor
        + 0.10 * categorical_factor
        + 0.20 * direct_factor
        + 0.10 * uncertainty_factor
    )

    upper_limit_crossed = upper_ratio >= 1.0

    return (
        clip01(future_factor),
        point_ratio,
        upper_ratio,
        upper_limit_crossed,
    )


# ============================================================
# SPECIFICATION FACTOR
# ============================================================

def calculate_specification_factor(
    current_value,
    limit,
):
    """
    Calculate current specification utilization.

    <80% of limit:
        low specification pressure

    80-100%:
        increasing pressure

    >=100%:
        current specification violation
    """

    current_value = max(
        0.0,
        safe_float(current_value),
    )

    limit = safe_float(limit)

    if limit <= 0:
        return 0.0, False, 0.0

    ratio = current_value / limit

    factor = clip01(
        (ratio - 0.80) / 0.20
    )

    violation = ratio > 1.0

    excess = max(
        0.0,
        current_value - limit,
    )

    return (
        factor,
        violation,
        excess,
    )


# ============================================================
# DECISION EVIDENCE
# ============================================================

def calculate_decision_evidence(
    row,
    calibration,
):
    """
    Calculate all evidence and final screening decision
    for one component.

    Decision philosophy:

        REJECT
            only for direct specification violation,
            direct predicted limit exceedance, or a strong
            convergence of independent evidence.

        REVIEW
            when meaningful anomaly/drift/future evidence exists.

        PASS
            when available evidence does not justify review.

    Ground truth is never used.
    """

    # --------------------------------------------------------
    # MODULE A
    # --------------------------------------------------------

    anomaly_factor, evidence_count = calculate_anomaly_factor(
        row
    )

    # --------------------------------------------------------
    # MODULE B DRIFT
    # --------------------------------------------------------

    (
        drift_factor,
        drift_rate_factor,
        relative_drift_factor,
        slope_excess_factor,
        early_drift_support,
    ) = calculate_drift_factor(
        row,
        calibration,
    )

    # --------------------------------------------------------
    # SPECIFICATION
    # --------------------------------------------------------

    current_value = safe_float(
        row.get("iddq_0h_uA", 0.0)
    )

    limit = safe_float(
        row.get("absolute_limit_uA", 0.0)
    )

    (
        specification_factor,
        current_limit_violation,
        current_limit_excess,
    ) = calculate_specification_factor(
        current_value,
        limit,
    )

    # --------------------------------------------------------
    # FUTURE
    # --------------------------------------------------------

    (
        future_factor,
        future_point_ratio,
        future_upper_ratio,
        upper_prediction_limit_crossed,
    ) = calculate_future_factor(
        row,
        limit,
    )

    direct_future_exceedance = normalize_flag(
        row.get("predicted_limit_exceeded", False)
    )

    uncertainty_failure = normalize_flag(
        row.get("uncertainty_adjusted_failure", False)
    )

    # --------------------------------------------------------
    # EVIDENCE STRENGTH
    # --------------------------------------------------------

    strong_current_anomaly = (
        anomaly_factor >= 0.75
        and evidence_count >= 1
    )

    medium_current_anomaly = (
        anomaly_factor >= 0.45
    )

    strong_drift = (
        drift_factor >= 0.75
        or (
            drift_rate_factor >= 0.80
            and relative_drift_factor >= 0.80
        )
        or (
            relative_drift_factor >= 0.80
            and slope_excess_factor >= 0.80
        )
    )

    moderate_drift = (
        drift_factor >= 0.45
    )

    strong_future = (
        direct_future_exceedance
        or (
            future_factor >= 0.75
            and (
                future_point_ratio >= 0.90
                or future_upper_ratio >= 1.10
            )
        )
    )

    moderate_future = (
        future_factor >= 0.45
        or future_point_ratio >= 0.90
        or future_upper_ratio >= 1.00
    )

    # --------------------------------------------------------
    # RISK SCORE
    # --------------------------------------------------------

    risk_score = (
        WEIGHTS["anomaly"] * anomaly_factor
        + WEIGHTS["drift"] * drift_factor
        + WEIGHTS["future"] * future_factor
        + WEIGHTS["specification"] * specification_factor
    ) * 100.0

    risk_score = float(
        np.clip(risk_score, 0.0, 100.0)
    )

    risk_level = risk_level_from_score(
        risk_score
    )

    # --------------------------------------------------------
    # REJECT LOGIC
    # --------------------------------------------------------

    # Direct current specification violation.
    hard_current_reject = current_limit_violation

    # Direct predicted future limit violation.
    hard_future_reject = direct_future_exceedance

    # Strong independent evidence converging toward future
    # failure. This is intentionally much stricter than simply
    # having an early_drift_flag.
    converging_reject = (
        strong_future
        and (
            strong_current_anomaly
            or strong_drift
        )
        and risk_score >= 70.0
    )

    hard_reject = (
        hard_current_reject
        or hard_future_reject
        or converging_reject
    )

    # --------------------------------------------------------
    # REVIEW LOGIC
    # --------------------------------------------------------

    # Current anomaly alone can trigger review when evidence
    # is genuinely strong.
    review_current = (
        strong_current_anomaly
        or medium_current_anomaly
    )

    # Drift alone can trigger review only when the continuous
    # evidence is meaningful. early_drift_flag by itself does
    # NOT automatically mean REVIEW.
    review_drift = moderate_drift

    # Future evidence can trigger review when prediction
    # approaches the specification limit.
    review_future = moderate_future

    # Risk score is a secondary aggregate signal.
    review_score = risk_score >= THRESHOLDS["medium"]

    if hard_reject:
        decision = "REJECT"

    elif (
        review_current
        or review_drift
        or review_future
        or review_score
    ):
        decision = "REVIEW"

    else:
        decision = "PASS"

    # --------------------------------------------------------
    # DRIVER
    # --------------------------------------------------------

    drivers = []

    if current_limit_violation:
        drivers.append("CURRENT_LIMIT_VIOLATION")

    if direct_future_exceedance:
        drivers.append("PREDICTED_LIMIT_EXCEEDANCE")

    if strong_current_anomaly:
        drivers.append("STRONG_ANOMALY_EVIDENCE")
    elif medium_current_anomaly:
        drivers.append("ANOMALY_EVIDENCE")

    if strong_drift:
        drivers.append("STRONG_DRIFT_EVIDENCE")
    elif moderate_drift:
        drivers.append("DRIFT_EVIDENCE")

    if strong_future:
        drivers.append("STRONG_FUTURE_RISK")
    elif moderate_future:
        drivers.append("FUTURE_RISK")

    if uncertainty_failure:
        drivers.append("UNCERTAINTY_ADJUSTED_RISK")

    if not drivers:
        drivers.append("NO_STRONG_RISK_SIGNAL")

    primary_driver = drivers[0]

    # --------------------------------------------------------
    # EXPLANATION
    # --------------------------------------------------------

    if decision == "REJECT":

        if current_limit_violation:
            explanation = (
                f"Current 0h Iddq exceeds the absolute specification "
                f"limit by {current_limit_excess:.2f} µA."
            )

        elif direct_future_exceedance:
            explanation = (
                "Module B predicts the component will exceed the "
                "absolute specification limit by 168h."
            )

        elif converging_reject:
            explanation = (
                "Multiple independent signals converge on elevated "
                "future risk: strong anomaly/drift evidence together "
                "with strong future prediction evidence."
            )

        else:
            explanation = (
                "The component has sufficient evidence to require "
                "rejection."
            )

    elif decision == "REVIEW":

        explanation_parts = []

        if medium_current_anomaly:
            explanation_parts.append(
                "Module A detected anomaly evidence"
            )

        if moderate_drift:
            explanation_parts.append(
                "Module B indicates meaningful drift"
            )

        if moderate_future:
            explanation_parts.append(
                "future prediction approaches elevated risk"
            )

        if uncertainty_failure:
            explanation_parts.append(
                "uncertainty-adjusted future risk is elevated"
            )

        if explanation_parts:
            explanation = (
                "; ".join(explanation_parts)
                + ". Further investigation is recommended."
            )
        else:
            explanation = (
                "Aggregate risk evidence exceeds the review threshold."
            )

    else:
        explanation = (
            "No sufficiently strong anomaly, drift, future-risk, "
            "or specification signal was detected."
        )

    # --------------------------------------------------------
    # RETURN EVIDENCE
    # --------------------------------------------------------

    return {
        "anomaly_factor": anomaly_factor,

        "drift_factor": drift_factor,
        "drift_rate_factor": drift_rate_factor,
        "relative_drift_factor": relative_drift_factor,
        "slope_excess_factor": slope_excess_factor,
        "early_drift_support": early_drift_support,

        "future_factor": future_factor,
        "future_point_ratio": future_point_ratio,
        "future_upper_ratio": future_upper_ratio,
        "upper_prediction_limit_crossed": upper_prediction_limit_crossed,

        "specification_factor": specification_factor,

        "statistical_evidence_count": evidence_count,

        "current_limit_violation": current_limit_violation,
        "current_limit_excess_uA": current_limit_excess,

        "direct_future_exceedance": direct_future_exceedance,
        "uncertainty_adjusted_failure": uncertainty_failure,

        "strong_current_anomaly": strong_current_anomaly,
        "moderate_current_anomaly": medium_current_anomaly,

        "strong_drift": strong_drift,
        "moderate_drift": moderate_drift,

        "strong_future": strong_future,
        "moderate_future": moderate_future,

        "risk_score": risk_score,
        "risk_level": risk_level,

        "hard_current_reject": hard_current_reject,
        "hard_future_reject": hard_future_reject,
        "converging_reject": converging_reject,

        "decision": decision,
        "primary_driver": primary_driver,
        "risk_drivers": " | ".join(drivers),
        "explanation": explanation,
    }


# ============================================================
# PROCESS ONE STAGE
# ============================================================

def process_stage(
    stage_number,
    module_b,
    calibration,
):
    """
    Process one cumulative Module A stage.
    """

    stage_file = (
        MODULE_A_DIR
        / f"stage_{stage_number:02d}.csv"
    )

    if not stage_file.exists():
        raise FileNotFoundError(
            f"Module A stage file not found: {stage_file}"
        )

    print("=" * 70)
    print(
        f"PROCESSING CUMULATIVE STAGE {stage_number}"
    )
    print("=" * 70)

    print(f"Module A: {stage_file}")

    module_a = pd.read_csv(stage_file)

    module_a = validate_module_a(
        module_a,
        stage_file,
    )

    print(
        f"Module A components: {len(module_a)}"
    )

    # --------------------------------------------------------
    # MERGE MODULE B
    # --------------------------------------------------------

    module_b_subset = module_b.copy()

    duplicate_ids = (
        module_b_subset["component_id"]
        .duplicated()
        .sum()
    )

    if duplicate_ids:
        print(
            f"Warning: Module B contains {duplicate_ids} "
            "duplicate component IDs. Keeping first occurrence."
        )

        module_b_subset = (
            module_b_subset
            .drop_duplicates(
                subset=["component_id"],
                keep="first",
            )
        )

    merged = module_a.merge(
        module_b_subset,
        on="component_id",
        how="left",
        suffixes=("", "_module_b"),
        validate="one_to_one",
    )

    missing_module_b = (
        merged["predicted_drift_rate"]
        .isna()
        .sum()
    )

    if missing_module_b:
        raise ValueError(
            f"Stage {stage_number}: "
            f"{missing_module_b} Module A components have no "
            "matching Module B prediction."
        )

    # --------------------------------------------------------
    # CALCULATE DECISIONS
    # --------------------------------------------------------

    evidence_rows = []

    for _, row in merged.iterrows():

        evidence = calculate_decision_evidence(
            row,
            calibration,
        )

        evidence_rows.append(evidence)

    evidence_df = pd.DataFrame(
        evidence_rows,
        index=merged.index,
    )

    result = pd.concat(
        [
            merged.reset_index(drop=True),
            evidence_df.reset_index(drop=True),
        ],
        axis=1,
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    output_file = (
        RISK_DIR
        / f"risk_stage_{stage_number:02d}.csv"
    )

    result.to_csv(
        output_file,
        index=False,
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\nStage result:")

    decision_counts = (
        result["decision"]
        .value_counts()
        .to_dict()
    )

    risk_counts = (
        result["risk_level"]
        .value_counts()
        .to_dict()
    )

    print(
        f"  PASS   : {decision_counts.get('PASS', 0)}"
    )

    print(
        f"  REVIEW : {decision_counts.get('REVIEW', 0)}"
    )

    print(
        f"  REJECT : {decision_counts.get('REJECT', 0)}"
    )

    print("\nRisk levels:")

    print(
        f"  LOW      : {risk_counts.get('LOW', 0)}"
    )

    print(
        f"  MEDIUM   : {risk_counts.get('MEDIUM', 0)}"
    )

    print(
        f"  HIGH     : {risk_counts.get('HIGH', 0)}"
    )

    print(
        f"  CRITICAL : {risk_counts.get('CRITICAL', 0)}"
    )

    print(
        f"\nSaved: {output_file}"
    )

    return result


# ============================================================
# BUILD FINAL RESULTS
# ============================================================

def build_final_results(stage_results):
    """
    The final stage contains all 10,000 cumulative components.

    Save a clean final output.
    """

    if not stage_results:
        raise ValueError(
            "No stage results were generated."
        )

    final_result = stage_results[-1].copy()

    final_file = (
        RISK_DIR
        / "overall_risk_results.csv"
    )

    final_result.to_csv(
        final_file,
        index=False,
    )

    return final_result


# ============================================================
# BUILD STAGE SUMMARY
# ============================================================

def build_stage_summary(stage_results):
    """
    Create a compact summary across cumulative stages.
    """

    rows = []

    for stage_number, result in enumerate(
        stage_results,
        start=1,
    ):

        decision_counts = (
            result["decision"]
            .value_counts()
            .to_dict()
        )

        risk_counts = (
            result["risk_level"]
            .value_counts()
            .to_dict()
        )

        rows.append(
            {
                "stage": stage_number,
                "components": len(result),

                "pass": decision_counts.get(
                    "PASS",
                    0,
                ),

                "review": decision_counts.get(
                    "REVIEW",
                    0,
                ),

                "reject": decision_counts.get(
                    "REJECT",
                    0,
                ),

                "low_risk": risk_counts.get(
                    "LOW",
                    0,
                ),

                "medium_risk": risk_counts.get(
                    "MEDIUM",
                    0,
                ),

                "high_risk": risk_counts.get(
                    "HIGH",
                    0,
                ),

                "critical_risk": risk_counts.get(
                    "CRITICAL",
                    0,
                ),

                "mean_risk_score": result[
                    "risk_score"
                ].mean(),

                "max_risk_score": result[
                    "risk_score"
                ].max(),

                "current_limit_violations": result[
                    "current_limit_violation"
                ].sum(),

                "predicted_limit_exceedances": result[
                    "direct_future_exceedance"
                ].sum(),

                "strong_anomaly_evidence": result[
                    "strong_current_anomaly"
                ].sum(),

                "strong_drift_evidence": result[
                    "strong_drift"
                ].sum(),

                "strong_future_evidence": result[
                    "strong_future"
                ].sum(),
            }
        )

    summary = pd.DataFrame(rows)

    summary_file = (
        RISK_DIR
        / "risk_stage_summary.csv"
    )

    summary.to_csv(
        summary_file,
        index=False,
    )

    return summary


# ============================================================
# FINAL VALIDATION
# ============================================================

def validate_final_result(result):
    """
    Validate the final Module C result.
    """

    required_columns = [
        "component_id",
        "risk_score",
        "risk_level",
        "decision",
        "anomaly_factor",
        "drift_factor",
        "future_factor",
        "specification_factor",
        "current_limit_violation",
        "direct_future_exceedance",
        "explanation",
    ]

    missing = [
        column
        for column in required_columns
        if column not in result.columns
    ]

    if missing:
        raise ValueError(
            "Final Module C output is missing columns:\n"
            + "\n".join(f" - {column}" for column in missing)
        )

    if result["component_id"].duplicated().any():
        raise ValueError(
            "Final Module C output contains duplicate component IDs."
        )

    if result["risk_score"].isna().any():
        raise ValueError(
            "Final Module C output contains missing risk scores."
        )

    if (
        (result["risk_score"] < 0)
        | (result["risk_score"] > 100)
    ).any():
        raise ValueError(
            "Risk scores must remain between 0 and 100."
        )

    valid_risk_levels = {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }

    invalid_risk_levels = set(
        result["risk_level"].dropna().unique()
    ) - valid_risk_levels

    if invalid_risk_levels:
        raise ValueError(
            f"Invalid risk levels: {invalid_risk_levels}"
        )

    valid_decisions = {
        "PASS",
        "REVIEW",
        "REJECT",
    }

    invalid_decisions = set(
        result["decision"].dropna().unique()
    ) - valid_decisions

    if invalid_decisions:
        raise ValueError(
            f"Invalid decisions: {invalid_decisions}"
        )

    # Direct predicted limit exceedance must always result
    # in rejection.
    invalid_direct_future_decisions = result[
        result["direct_future_exceedance"]
        & (result["decision"] != "REJECT")
    ]

    if len(invalid_direct_future_decisions) > 0:
        raise ValueError(
            "Validation failed: direct predicted limit "
            "exceedance is not marked REJECT."
        )

    # Direct current limit violation must always result
    # in rejection.
    invalid_current_decisions = result[
        result["current_limit_violation"]
        & (result["decision"] != "REJECT")
    ]

    if len(invalid_current_decisions) > 0:
        raise ValueError(
            "Validation failed: current specification violation "
            "is not marked REJECT."
        )

    print("\nFinal validation: PASSED")


# ============================================================
# PRINT FINAL REPORT
# ============================================================

def print_final_report(result):
    """
    Print final Module C statistics.
    """

    print("\n")
    print("=" * 70)
    print("PLEIONE MODULE C FINAL REPORT")
    print("=" * 70)

    print(
        f"Total components : {len(result)}"
    )

    print("\nScreening decisions:")

    decisions = (
        result["decision"]
        .value_counts()
    )

    for decision in [
        "PASS",
        "REVIEW",
        "REJECT",
    ]:

        count = int(
            decisions.get(
                decision,
                0,
            )
        )

        percentage = (
            count / len(result) * 100
            if len(result)
            else 0
        )

        print(
            f"  {decision:<7}: "
            f"{count:>5} "
            f"({percentage:6.2f}%)"
        )

    print("\nRisk levels:")

    risks = (
        result["risk_level"]
        .value_counts()
    )

    for level in [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ]:

        count = int(
            risks.get(
                level,
                0,
            )
        )

        percentage = (
            count / len(result) * 100
            if len(result)
            else 0
        )

        print(
            f"  {level:<9}: "
            f"{count:>5} "
            f"({percentage:6.2f}%)"
        )

    print("\nEvidence:")

    print(
        f"  Current limit violations : "
        f"{int(result['current_limit_violation'].sum())}"
    )

    print(
        f"  Predicted limit exceeds  : "
        f"{int(result['direct_future_exceedance'].sum())}"
    )

    print(
        f"  Strong anomaly evidence  : "
        f"{int(result['strong_current_anomaly'].sum())}"
    )

    print(
        f"  Strong drift evidence    : "
        f"{int(result['strong_drift'].sum())}"
    )

    print(
        f"  Strong future evidence   : "
        f"{int(result['strong_future'].sum())}"
    )

    uncertainty_count = (
    result["uncertainty_adjusted_failure"]
    .loc[:, ~result["uncertainty_adjusted_failure"].columns.duplicated()]
    .iloc[:, 0]
    .sum()
    if isinstance(result["uncertainty_adjusted_failure"], pd.DataFrame)
    else result["uncertainty_adjusted_failure"].sum()
    )

    print(
    f"  Uncertainty-adjusted risk: "
    f"{int(uncertainty_count)}"
    )

    print("\nRisk score:")

    print(
        f"  Mean : {result['risk_score'].mean():.2f}"
    )

    print(
        f"  Max  : {result['risk_score'].max():.2f}"
    )

    print(
        f"  Min  : {result['risk_score'].min():.2f}"
    )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("PLEIONE")
    print("SIH 26170")
    print("MODULE C: RISK FUSION & EARLY SCREENING")
    print("=" * 70)

    print("\nRisk weights:")

    print(
        f"  anomaly        : "
        f"{WEIGHTS['anomaly']:.3f}"
    )

    print(
        f"  drift          : "
        f"{WEIGHTS['drift']:.3f}"
    )

    print(
        f"  future         : "
        f"{WEIGHTS['future']:.3f}"
    )

    print(
        f"  specification  : "
        f"{WEIGHTS['specification']:.3f}"
    )

    print("\nRisk thresholds:")

    print(
        f"  MEDIUM  >= "
        f"{THRESHOLDS['medium']:.1f}"
    )

    print(
        f"  HIGH    >= "
        f"{THRESHOLDS['high']:.1f}"
    )

    print(
        f"  CRITICAL>= "
        f"{THRESHOLDS['critical']:.1f}"
    )

    # --------------------------------------------------------
    # LOAD MODULE B
    # --------------------------------------------------------

    print("\nLoading Module B...")

    if not MODULE_B_FILE.exists():
        raise FileNotFoundError(
            f"Module B file not found: {MODULE_B_FILE}"
        )

    module_b = pd.read_csv(
        MODULE_B_FILE
    )

    module_b = validate_module_b(
        module_b
    )

    print(
        f"Module B components: {len(module_b)}"
    )

    calibration = (
        calculate_module_b_calibration(
            module_b
        )
    )

    # --------------------------------------------------------
    # PROCESS ALL CUMULATIVE STAGES
    # --------------------------------------------------------

    stage_results = []

    for stage_number in range(1, 6):

        result = process_stage(
            stage_number,
            module_b,
            calibration,
        )

        stage_results.append(
            result
        )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    final_result = build_final_results(
        stage_results
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    build_stage_summary(
        stage_results
    )

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    validate_final_result(
        final_result
    )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    print_final_report(
        final_result
    )

    print(
        "\nFinal output:"
    )

    print(
        f"  {RISK_DIR / 'overall_risk_results.csv'}"
    )

    print(
        f"  {RISK_DIR / 'risk_stage_summary.csv'}"
    )

    print(
        "\nModule C completed successfully."
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()