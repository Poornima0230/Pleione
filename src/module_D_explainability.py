"""
MODULE D - Explainable AI & Decision Explanation

Consumes the CURRENT Risk Fusion output and produces:
1. data/module_D_explanations.csv
2. data/priority_screening_list.csv
3. data/component_reports/

Design:
- Does NOT recalculate anomaly detection
- Does NOT recalculate drift prediction
- Does NOT recalculate risk score
- Uses evidence already produced by Modules A, B and Risk Fusion
- Handles OBSERVED / PREDICTED / UNAVAILABLE states
- Avoids hard-coded QA explanations
- Uses SHAP information if it is already available
"""

from pathlib import Path
import json
import math
import re
import shutil

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

INPUT_PATH = Path("data/risk/overall_risk_results.csv")

OUTPUT_PATH = Path("data/module_D_explanations.csv")
PRIORITY_PATH = Path("data/priority_screening_list.csv")
REPORT_DIR = Path("data/component_reports")


# ============================================================
# GENERAL HELPERS
# ============================================================

def is_missing(value):
    if value is None:
        return True

    if isinstance(value, str):
        value = value.strip().lower()
        return value in {
            "",
            "nan",
            "none",
            "null",
            "na",
            "n/a",
            "not available",
            "unavailable",
        }

    try:
        return bool(pd.isna(value))
    except Exception:
        return False


def safe_float(value):
    if is_missing(value):
        return None

    try:
        value = float(value)

        if not np.isfinite(value):
            return None

        return value

    except (TypeError, ValueError):
        return None


def safe_bool(value):
    if is_missing(value):
        return False

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    text = str(value).strip().lower()

    return text in {
        "true",
        "1",
        "yes",
        "y",
        "flagged",
        "anomaly",
        "failed",
        "failure",
        "violation",
        "critical",
        "high",
    }


def first_existing(row, columns, default=None):
    for column in columns:
        if column in row.index:
            value = row[column]

            if not is_missing(value):
                return value

    return default


def format_value(value, decimals=4):
    value = safe_float(value)

    if value is None:
        return "unavailable"

    return f"{value:.{decimals}f}"


def normalize_text(value):
    if is_missing(value):
        return None

    return str(value).strip()


# ============================================================
# COLUMN DISCOVERY
# ============================================================

def detect_parameter_columns(df):
    """
    Finds measurement columns without assuming only one parameter.

    Examples:
        iddq_0h_uA
        iddq_24h_uA
        leakage_0h_uA
        propagation_delay_24h_ns
    """

    ignored_patterns = [
        "score",
        "risk",
        "factor",
        "flag",
        "limit",
        "margin",
        "drift",
        "predicted",
        "actual",
        "error",
        "slope",
        "hour",
        "stage",
        "temperature",
        "voltage",
    ]

    candidates = []

    for column in df.columns:

        column_lower = column.lower()

        if not any(
            token in column_lower
            for token in ["_0h", "_24h", "_48h", "_72h", "_96h", "_120h", "_144h", "_168h"]
        ):
            continue

        if any(pattern in column_lower for pattern in ignored_patterns):
            continue

        if not pd.api.types.is_numeric_dtype(df[column]):
            continue

        candidates.append(column)

    return candidates


def extract_parameter_name(column):
    """
    Converts:

        iddq_0h_uA -> iddq
        leakage_current_24h_uA -> leakage_current
        propagation_delay_96h_ns -> propagation_delay
    """

    if not column:
        return None

    name = re.sub(
        r"_(0|24|48|72|96|120|144|168)h",
        "",
        column,
        flags=re.IGNORECASE,
    )

    # Remove common unit suffixes
    name = re.sub(
        r"_(ua|ma|a|mv|v|ns|us|ms|ohm|kohm|mhz|hz|db)$",
        "",
        name,
        flags=re.IGNORECASE,
    )

    return name


def extract_hour(column):
    if not column:
        return None

    match = re.search(r"_(\d+)h", column.lower())

    if match:
        return int(match.group(1))

    return None


def discover_observed_measurements(row):
    measurements = []

    for column in row.index:

        hour = extract_hour(column)

        if hour is None:
            continue

        if not pd.api.types.is_number(row[column]):
            continue

        value = safe_float(row[column])

        if value is None:
            continue

        parameter = extract_parameter_name(column)

        if parameter is None:
            continue

        measurements.append(
            {
                "column": column,
                "parameter": parameter,
                "hour": hour,
                "value": value,
            }
        )

    measurements.sort(key=lambda x: x["hour"])

    return measurements


# ============================================================
# PREDICTION DISCOVERY
# ============================================================

def discover_prediction(row):
    """
    Finds prediction information from Module B / Risk Fusion.

    Does not assume the prediction target is always 168h.
    """

    prediction_candidates = []

    for column in row.index:

        lower = column.lower()

        if "predicted" not in lower:
            continue

        if not lower.endswith(("_ua", "_ma", "_a", "_v", "_mv", "_ns", "_us")):
            continue

        value = safe_float(row[column])

        if value is None:
            continue

        prediction_candidates.append(column)

    if not prediction_candidates:
        return {
            "available": False,
            "column": None,
            "value": None,
            "horizon": None,
        }

    # Prefer the main prediction column
    preferred = [
        column
        for column in prediction_candidates
        if "predicted_168h" in column.lower()
    ]

    if preferred:
        prediction_column = preferred[0]
    else:
        prediction_column = prediction_candidates[0]

    value = safe_float(row[prediction_column])

    horizon = extract_hour(prediction_column)

    return {
        "available": value is not None,
        "column": prediction_column,
        "value": value,
        "horizon": horizon,
    }


# ============================================================
# SPECIFICATION ANALYSIS
# ============================================================

def determine_spec_status(row):
    limit_violation = first_existing(
        row,
        [
            "limit_violation",
            "specification_violation",
            "spec_violation",
        ],
    )

    if not is_missing(limit_violation):
        if safe_bool(limit_violation):
            return "VIOLATED"

    explicit_status = first_existing(
        row,
        [
            "spec_status",
            "specification_status",
        ],
    )

    if explicit_status:
        return str(explicit_status).upper()

    excess = safe_float(
        first_existing(
            row,
            [
                "limit_excess_uA",
                "limit_excess",
            ],
        )
    )

    if excess is not None and excess > 0:
        return "VIOLATED"

    return "WITHIN_LIMIT"


# ============================================================
# ANOMALY ANALYSIS
# ============================================================

def determine_anomaly_status(row):

    anomaly_flag = first_existing(
        row,
        [
            "anomaly_flag",
            "statistical_anomaly_flag",
            "temporal_anomaly_flag",
            "isolation_forest_flag",
        ],
    )

    if safe_bool(anomaly_flag):
        return "ANOMALOUS"

    combined_score = safe_float(
        first_existing(
            row,
            [
                "combined_anomaly_score",
                "anomaly_score",
            ],
        )
    )

    if combined_score is not None and combined_score > 0:
        return "ANOMALY_SCORE_PRESENT"

    return "NO_ANOMALY_FLAG"


def anomaly_reason(row):

    reasons = []

    if safe_bool(row.get("statistical_anomaly_flag")):
        reasons.append("statistical detector")

    if safe_bool(row.get("temporal_anomaly_flag")):
        reasons.append("temporal detector")

    if safe_bool(row.get("isolation_forest_flag")):
        reasons.append("Isolation Forest")

    evidence_count = safe_float(row.get("statistical_evidence_count"))

    if evidence_count is not None and evidence_count > 0:
        reasons.append(
            f"{int(evidence_count)} statistical evidence signal(s)"
        )

    if safe_bool(row.get("limit_violation")):
        reasons.append("specification violation")

    if reasons:
        return "; ".join(reasons)

    return "No anomaly evidence was flagged by the available detectors."


# ============================================================
# DRIFT ANALYSIS
# ============================================================

def determine_drift_status(row):

    early_drift = safe_bool(row.get("early_drift_flag"))

    drift_excess = safe_float(
        first_existing(
            row,
            [
                "drift_slope_excess",
                "predicted_drift_slope_excess",
            ],
        )
    )

    future_drift_risk = normalize_text(
        first_existing(
            row,
            [
                "future_drift_risk",
            ],
        )
    )

    if early_drift:
        return "DRIFT_FLAGGED"

    if drift_excess is not None and drift_excess > 0:
        return "DRIFT_BOUNDARY_EXCEEDED"

    if future_drift_risk:
        if future_drift_risk.upper() not in {
            "LOW",
            "NONE",
            "NO",
            "FALSE",
        }:
            return "FUTURE_DRIFT_RISK"

    predicted_drift = safe_float(
        first_existing(
            row,
            [
                "predicted_drift_uA",
                "predicted_drift",
            ],
        )
    )

    if predicted_drift is not None:
        return "DRIFT_ANALYZED"

    return "NOT_AVAILABLE"


def drift_reason(row):

    reasons = []

    drift_rate = safe_float(row.get("predicted_drift_rate"))

    relative_drift = safe_float(row.get("predicted_relative_drift"))

    slope_excess = safe_float(row.get("drift_slope_excess"))

    if safe_bool(row.get("early_drift_flag")):
        reasons.append("early drift flag")

    if drift_rate is not None:
        reasons.append(
            f"predicted drift rate={format_value(drift_rate)}"
        )

    if relative_drift is not None:
        reasons.append(
            f"predicted relative drift={format_value(relative_drift)}"
        )

    if slope_excess is not None:
        reasons.append(
            f"safety-slope excess={format_value(slope_excess)}"
        )

    if not reasons:
        return "No drift evidence is available."

    return "; ".join(reasons)


# ============================================================
# RISK FACTORS
# ============================================================

def get_risk_factors(row):

    factor_columns = [
        "anomaly_factor",
        "drift_factor",
        "future_factor",
        "specification_factor",
    ]

    factors = {}

    for column in factor_columns:

        if column not in row.index:
            continue

        value = safe_float(row[column])

        if value is not None:
            factors[column] = round(value, 6)

    if not factors:
        return {}

    return factors


def strongest_risk_factor(row):

    factors = get_risk_factors(row)

    if not factors:
        return None

    return max(
        factors,
        key=lambda key: abs(factors[key])
    )


# ============================================================
# SHAP SUPPORT
# ============================================================

def get_shap_information(row):

    shap_features = []

    for column in row.index:

        lower = column.lower()

        if "shap" not in lower:
            continue

        value = row[column]

        if is_missing(value):
            continue

        shap_features.append(
            {
                "feature": column,
                "value": str(value),
            }
        )

    return shap_features


# ============================================================
# QA REASON
# ============================================================

def generate_qa_reason(
    row,
    spec_status,
    anomaly_status,
    drift_status,
    prediction,
    strongest_factor,
):

    classification = normalize_text(
        first_existing(
            row,
            [
                "qa_classification",
                "final_risk_level",
                "risk_level",
                "final_decision",
            ],
            "UNCLASSIFIED",
        )
    )

    reasons = []

    if spec_status == "VIOLATED":
        reasons.append("the applicable specification was violated")

    if anomaly_status == "ANOMALOUS":
        reasons.append("anomaly detection produced abnormal evidence")

    if drift_status in {
        "DRIFT_FLAGGED",
        "DRIFT_BOUNDARY_EXCEEDED",
        "FUTURE_DRIFT_RISK",
    }:
        reasons.append("drift analysis identified future or early drift risk")

    if prediction["available"]:

        predicted_limit_exceeded = safe_bool(
            row.get("predicted_limit_exceeded")
        )

        uncertainty_failure = safe_bool(
            row.get("uncertainty_adjusted_failure")
        )

        if predicted_limit_exceeded:
            reasons.append("the predicted future value exceeds the applicable boundary")

        if uncertainty_failure:
            reasons.append(
                "the prediction interval indicates potential future specification failure"
            )

    if strongest_factor:
        factor_label = strongest_factor.replace("_", " ")
        reasons.append(
            f"{factor_label} is the strongest available risk factor"
        )

    if not reasons:
        reasons.append(
            "no abnormal condition was identified from the available evidence"
        )

    return (
        f"QA classification: {classification}. "
        + ". ".join(reasons)
        + "."
    )


# ============================================================
# SUMMARY
# ============================================================

def generate_summary(
    row,
    parameter,
    observed,
    prediction,
    spec_status,
    anomaly_status,
    drift_status,
    strongest_factor,
):

    component_id = normalize_text(
        first_existing(
            row,
            ["component_id", "component", "id"],
            "Unknown component",
        )
    )

    parts = [
        f"Component {component_id} was analyzed for {parameter or 'the available electrical parameter(s)'}."
    ]

    if observed:

        latest = observed[-1]

        parts.append(
            f"The latest observed value is {format_value(latest['value'])} "
            f"at {latest['hour']}h."
        )

    else:
        parts.append(
            "No directly observed measurement was available in the Risk Fusion output."
        )

    parts.append(
        f"Specification status: {spec_status}."
    )

    parts.append(
        f"Anomaly status: {anomaly_status}."
    )

    parts.append(
        f"Drift status: {drift_status}."
    )

    if prediction["available"]:

        horizon_text = (
            f"{prediction['horizon']}h"
            if prediction["horizon"] is not None
            else "the configured prediction horizon"
        )

        parts.append(
            f"A predicted value of {format_value(prediction['value'])} "
            f"is available for {horizon_text}."
        )

    else:
        parts.append(
            "No future prediction is available."
        )

    if strongest_factor:

        parts.append(
            f"The strongest risk factor reported by the Risk Engine is "
            f"{strongest_factor.replace('_', ' ')}."
        )

    return " ".join(parts)


# ============================================================
# STRUCTURED EXPLANATION
# ============================================================

def build_explanation(row):

    component_id = normalize_text(
        first_existing(
            row,
            ["component_id", "component", "id"],
            "UNKNOWN",
        )
    )

    component_type = normalize_text(
        first_existing(
            row,
            ["component_type", "component_category", "type"],
            "UNKNOWN",
        )
    )

    lot_id = normalize_text(
        first_existing(
            row,
            ["lot_id", "lot", "batch_id"],
            "UNKNOWN",
        )
    )

    observed = discover_observed_measurements(row)

    if observed:
        parameter = observed[-1]["parameter"]
    else:
        parameter = None

    prediction = discover_prediction(row)

    spec_status = determine_spec_status(row)

    anomaly_status = determine_anomaly_status(row)

    drift_status = determine_drift_status(row)

    risk_factors = get_risk_factors(row)

    strongest_factor = strongest_risk_factor(row)

    shap_features = get_shap_information(row)

    risk_score = safe_float(
        first_existing(
            row,
            [
                "risk_score",
                "risk_score_100",
            ],
        )
    )

    qa_classification = normalize_text(
        first_existing(
            row,
            [
                "qa_classification",
                "final_risk_level",
                "risk_level",
                "final_decision",
            ],
            "UNCLASSIFIED",
        )
    )

    spec_limit = safe_float(
        first_existing(
            row,
            [
                "absolute_limit_uA",
                "spec_upper",
                "upper_limit",
            ],
        )
    )

    predicted_limit_exceeded = safe_bool(
        row.get("predicted_limit_exceeded")
    )

    uncertainty_adjusted_failure = safe_bool(
        row.get("uncertainty_adjusted_failure")
    )

    qa_reason = generate_qa_reason(
        row,
        spec_status,
        anomaly_status,
        drift_status,
        prediction,
        strongest_factor,
    )

    summary = generate_summary(
        row,
        parameter,
        observed,
        prediction,
        spec_status,
        anomaly_status,
        drift_status,
        strongest_factor,
    )

    explanation = {
        "component": {
            "component_id": component_id,
            "component_type": component_type,
            "lot_id": lot_id,
        },

        "parameter_analysis": {
            "parameter": parameter,
            "observed_measurements": observed,
            "latest_observed_value": (
                observed[-1]["value"]
                if observed
                else None
            ),
            "latest_observed_time_hours": (
                observed[-1]["hour"]
                if observed
                else None
            ),
        },

        "specification": {
            "status": spec_status,
            "applicable_limit": spec_limit,
            "limit_violation": safe_bool(
                row.get("limit_violation")
            ),
            "limit_excess": safe_float(
                first_existing(
                    row,
                    [
                        "limit_excess_uA",
                        "limit_excess",
                    ],
                )
            ),
        },

        "anomaly": {
            "status": anomaly_status,
            "reason": anomaly_reason(row),
            "combined_anomaly_score": safe_float(
                row.get("combined_anomaly_score")
            ),
            "statistical_score": safe_float(
                row.get("statistical_score")
            ),
            "temporal_anomaly_score": safe_float(
                row.get("temporal_anomaly_score")
            ),
            "isolation_forest_score": safe_float(
                row.get("isolation_forest_score")
            ),
            "statistical_evidence_count": safe_float(
                row.get("statistical_evidence_count")
            ),
        },

        "drift": {
            "status": drift_status,
            "reason": drift_reason(row),
            "predicted_drift": safe_float(
                first_existing(
                    row,
                    [
                        "predicted_drift_uA",
                        "predicted_drift",
                    ],
                )
            ),
            "predicted_drift_rate": safe_float(
                row.get("predicted_drift_rate")
            ),
            "predicted_relative_drift": safe_float(
                row.get("predicted_relative_drift")
            ),
            "safety_slope": safe_float(
                row.get("safety_slope")
            ),
            "drift_slope_excess": safe_float(
                row.get("drift_slope_excess")
            ),
            "early_drift_flag": safe_bool(
                row.get("early_drift_flag")
            ),
            "future_drift_risk": normalize_text(
                row.get("future_drift_risk")
            ),
        },

        "prediction": {
            "available": prediction["available"],
            "prediction_column": prediction["column"],
            "prediction_horizon_hours": prediction["horizon"],
            "predicted_value": prediction["value"],
            "prediction_lower": safe_float(
                first_existing(
                    row,
                    [
                        "prediction_lower_uA",
                        "prediction_lower",
                    ],
                )
            ),
            "prediction_upper": safe_float(
                first_existing(
                    row,
                    [
                        "prediction_upper_uA",
                        "prediction_upper",
                    ],
                )
            ),
            "predicted_limit_exceeded": predicted_limit_exceeded,
            "uncertainty_adjusted_failure": uncertainty_adjusted_failure,
        },

        "risk": {
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "strongest_factor": strongest_factor,
        },

        "qa_decision": {
            "classification": qa_classification,
            "reason": qa_reason,
        },

        "shap": {
            "available": bool(shap_features),
            "features": shap_features,
        },

        "summary": summary,
    }

    return explanation


# ============================================================
# SCREENING PRIORITY
# ============================================================

def priority_rank(row):

    classification = str(
        first_existing(
            row,
            [
                "qa_classification",
                "final_risk_level",
                "risk_level",
            ],
            "",
        )
    ).upper()

    ranking = {
        "CRITICAL": 1,
        "HIGH": 2,
        "MEDIUM": 3,
        "WATCH": 4,
        "LOW": 5,
        "NORMAL": 5,
    }

    if classification in ranking:
        return ranking[classification]

    risk_score = safe_float(
        first_existing(
            row,
            [
                "risk_score",
                "risk_score_100",
            ],
            0,
        )
    )

    if risk_score is None:
        risk_score = 0

    if risk_score >= 80:
        return 1
    if risk_score >= 60:
        return 2
    if risk_score >= 40:
        return 3
    if risk_score >= 20:
        return 4

    return 5


def screening_recommendation(classification):

    classification = str(classification).upper()

    recommendations = {
        "CRITICAL": "Immediate engineering review and screening hold.",
        "HIGH": "Prioritize engineering review and additional screening.",
        "MEDIUM": "Review anomaly and drift evidence before release.",
        "WATCH": "Monitor and review according to QA policy.",
        "LOW": "No additional action indicated by the current risk assessment.",
        "NORMAL": "No additional action indicated by the current risk assessment.",
    }

    return recommendations.get(
        classification,
        "Follow the configured QA policy for this classification.",
    )


# ============================================================
# MAIN PROCESS
# ============================================================

def main():

    print("=" * 70)
    print("MODULE D: EXPLAINABLE AI & DECISION EXPLANATION")
    print("=" * 70)

    if not INPUT_PATH.exists():

        raise FileNotFoundError(
            f"Risk Fusion output not found:\n{INPUT_PATH}\n\n"
            "Run Module C successfully before running Module D."
        )

    print(f"Loading Risk Fusion results: {INPUT_PATH}")

    df = pd.read_csv(INPUT_PATH)

    if df.empty:
        raise ValueError(
            "Risk Fusion output exists but contains no rows."
        )

    print(f"Components received: {len(df)}")
    print(f"Columns received: {len(df.columns)}")

    # --------------------------------------------------------
    # Create output directories
    # --------------------------------------------------------

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    explanations = []
    priority_rows = []

    # --------------------------------------------------------
    # Process each component
    # --------------------------------------------------------

    for _, row in df.iterrows():

        explanation = build_explanation(row)

        component_id = explanation["component"]["component_id"]

        classification = explanation["qa_decision"]["classification"]

        risk_score = explanation["risk"]["risk_score"]

        priority_rows.append(
            {
                "component_id": component_id,
                "component_type": explanation["component"]["component_type"],
                "lot_id": explanation["component"]["lot_id"],
                "risk_score": risk_score,
                "qa_classification": classification,
                "priority_rank": priority_rank(row),
                "screening_recommendation": screening_recommendation(
                    classification
                ),
                "strongest_risk_factor": explanation["risk"][
                    "strongest_factor"
                ],
                "explanation_summary": explanation["summary"],
            }
        )

        # ----------------------------------------------------
        # Flat output for CSV
        # ----------------------------------------------------

        explanations.append(
            {
                "component_id": component_id,

                "component_type": explanation["component"][
                    "component_type"
                ],

                "lot_id": explanation["component"]["lot_id"],

                "parameter": explanation["parameter_analysis"][
                    "parameter"
                ],

                "latest_observed_value": explanation[
                    "parameter_analysis"
                ]["latest_observed_value"],

                "latest_observed_time_hours": explanation[
                    "parameter_analysis"
                ]["latest_observed_time_hours"],

                "spec_status": explanation["specification"][
                    "status"
                ],

                "spec_limit": explanation["specification"][
                    "applicable_limit"
                ],

                "anomaly_status": explanation["anomaly"][
                    "status"
                ],

                "anomaly_reason": explanation["anomaly"][
                    "reason"
                ],

                "combined_anomaly_score": explanation["anomaly"][
                    "combined_anomaly_score"
                ],

                "drift_status": explanation["drift"][
                    "status"
                ],

                "drift_reason": explanation["drift"][
                    "reason"
                ],

                "prediction_available": explanation[
                    "prediction"
                ]["available"],

                "prediction_horizon_hours": explanation[
                    "prediction"
                ]["prediction_horizon_hours"],

                "predicted_value": explanation[
                    "prediction"
                ]["predicted_value"],

                "prediction_lower": explanation[
                    "prediction"
                ]["prediction_lower"],

                "prediction_upper": explanation[
                    "prediction"
                ]["prediction_upper"],

                "predicted_limit_exceeded": explanation[
                    "prediction"
                ]["predicted_limit_exceeded"],

                "uncertainty_adjusted_failure": explanation[
                    "prediction"
                ]["uncertainty_adjusted_failure"],

                "anomaly_factor": explanation["risk"][
                    "risk_factors"
                ].get("anomaly_factor"),

                "drift_factor": explanation["risk"][
                    "risk_factors"
                ].get("drift_factor"),

                "future_factor": explanation["risk"][
                    "risk_factors"
                ].get("future_factor"),

                "specification_factor": explanation["risk"][
                    "risk_factors"
                ].get("specification_factor"),

                "strongest_risk_factor": explanation["risk"][
                    "strongest_factor"
                ],

                "risk_score": explanation["risk"][
                    "risk_score"
                ],

                "qa_classification": explanation[
                    "qa_decision"
                ]["classification"],

                "qa_reason": explanation["qa_decision"][
                    "reason"
                ],

                "shap_available": explanation["shap"][
                    "available"
                ],

                "shap_top_features": json.dumps(
                    explanation["shap"]["features"],
                    ensure_ascii=False,
                ),

                "explanation_summary": explanation[
                    "summary"
                ],

                "explanation_json": json.dumps(
                    explanation,
                    ensure_ascii=False,
                ),
            }
        )

        # ----------------------------------------------------
        # Individual component report
        # ----------------------------------------------------

        safe_component_id = re.sub(
            r"[^A-Za-z0-9_.-]",
            "_",
            str(component_id),
        )

        report_path = REPORT_DIR / (
            f"{safe_component_id}_explanation.json"
        )

        with open(
            report_path,
            "w",
            encoding="utf-8",
        ) as report_file:

            json.dump(
                explanation,
                report_file,
                indent=2,
                ensure_ascii=False,
            )

    # ========================================================
    # SAVE EXPLANATIONS
    # ========================================================

    explanation_df = pd.DataFrame(explanations)

    explanation_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    # ========================================================
    # SAVE PRIORITY SCREENING LIST
    # ========================================================

    priority_df = pd.DataFrame(priority_rows)

    priority_df = priority_df.sort_values(
        by=[
            "priority_rank",
            "risk_score",
        ],
        ascending=[
            True,
            False,
        ],
        na_position="last",
    )

    priority_df.to_csv(
        PRIORITY_PATH,
        index=False,
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("MODULE D COMPLETED")
    print("-" * 70)

    print(f"Explanation file : {OUTPUT_PATH}")
    print(f"Priority file    : {PRIORITY_PATH}")
    print(f"Reports directory: {REPORT_DIR}")

    print()
    print(f"Components processed: {len(explanation_df)}")

    if "qa_classification" in explanation_df.columns:

        print()
        print("QA classification distribution:")

        print(
            explanation_df[
                "qa_classification"
            ].value_counts(
                dropna=False
            )
        )

    if "anomaly_status" in explanation_df.columns:

        print()
        print("Anomaly status distribution:")

        print(
            explanation_df[
                "anomaly_status"
            ].value_counts(
                dropna=False
            )
        )

    if "drift_status" in explanation_df.columns:

        print()
        print("Drift status distribution:")

        print(
            explanation_df[
                "drift_status"
            ].value_counts(
                dropna=False
            )
        )

    print()
    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()