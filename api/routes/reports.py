from fastapi import APIRouter, HTTPException
from pathlib import Path

import pandas as pd
import numpy as np


router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"]
)


BASE_DIR = Path(__file__).resolve().parents[2]


DATA_FILE = (
    BASE_DIR
    / "data"
    / "sih_26170_burn_in_synthetic_dataset.csv"
)

ANOMALY_FILE = (
    BASE_DIR
    / "data"
    / "module_A_anomaly_results.csv"
)

PREDICTION_FILE = (
    BASE_DIR
    / "data"
    / "module_B_drift_predictions.csv"
)

EXPLANATION_FILE = (
    BASE_DIR
    / "data"
    / "module_D_explanations.csv"
)


def clean_value(value):

    if value is None:
        return None

    if isinstance(value, np.bool_):
        return bool(value)

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):

        if np.isnan(value):
            return None

        return float(value)

    if isinstance(value, float):

        if pd.isna(value):
            return None

        return value

    try:

        if pd.isna(value):
            return None

    except (TypeError, ValueError):
        pass

    return value


def clean_record(record):

    cleaned = {}

    for key, value in record.items():

        cleaned[str(key)] = clean_value(
            value
        )

    return cleaned


def read_csv_file(
    path: Path,
    required: bool = False
):

    if not path.exists():

        if required:
            raise HTTPException(
                status_code=404,
                detail=f"Required file not found: {path.name}"
            )

        return None

    try:

        return pd.read_csv(path)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to read {path.name}: "
                f"{str(e)}"
            )
        )


def normalize_bool_series(
    series
):

    return (
        series
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(
            [
                "true",
                "1",
                "yes",
                "y",
                "anomaly",
            ]
        )
    )


def normalize_text(
    series
):

    return (
        series
        .astype(str)
        .str.strip()
        .str.upper()
    )


def count_text(
    df,
    column,
    value
):

    if column not in df.columns:
        return 0

    return int(
        (
            normalize_text(
                df[column]
            )
            == str(value).upper()
        ).sum()
    )


def percentage(
    numerator,
    denominator
):

    if denominator == 0:
        return 0.0

    return round(
        (numerator / denominator) * 100,
        2
    )


def build_lot_findings(
    anomaly_df,
    prediction_df
):

    if anomaly_df is None:
        return []

    if "lot_id" not in anomaly_df.columns:
        return []

    lot_groups = anomaly_df.groupby(
        "lot_id",
        dropna=False
    )

    prediction_lookup = {}

    if (
        prediction_df is not None
        and "lot_id" in prediction_df.columns
    ):

        for lot_id, group in prediction_df.groupby(
            "lot_id",
            dropna=False
        ):

            if "risk_score" in group.columns:

                risk_values = pd.to_numeric(
                    group["risk_score"],
                    errors="coerce"
                ).dropna()

                average_risk = (
                    float(risk_values.mean())
                    if not risk_values.empty
                    else 0.0
                )

            else:

                average_risk = 0.0

            prediction_lookup[
                str(lot_id)
            ] = average_risk

    findings = []

    for lot_id, group in lot_groups:

        lot_id = str(lot_id)

        components = len(group)

        anomaly_count = 0
        latent_count = 0
        critical_count = 0
        high_count = 0

        if "combined_anomaly" in group.columns:

            anomaly_count = int(
                normalize_bool_series(
                    group[
                        "combined_anomaly"
                    ]
                ).sum()
            )

        if "latent_risk_flag" in group.columns:

            latent_count = int(
                normalize_bool_series(
                    group[
                        "latent_risk_flag"
                    ]
                ).sum()
            )

        if "anomaly_severity" in group.columns:

            severity = normalize_text(
                group[
                    "anomaly_severity"
                ]
            )

            critical_count = int(
                (severity == "CRITICAL").sum()
            )

            high_count = int(
                (severity == "HIGH").sum()
            )

        anomaly_rate = percentage(
            anomaly_count,
            components
        )

        average_risk = prediction_lookup.get(
            lot_id,
            0.0
        )

        if critical_count > 0:

            finding = (
                "Critical anomaly concentration "
                "requires immediate engineering review."
            )

        elif latent_count > 0:

            finding = (
                "Latent-risk components detected; "
                "review temporal behavior before release."
            )

        elif anomaly_count > 0:

            finding = (
                "Anomaly signals are present; "
                "inspect affected components."
            )

        else:

            finding = (
                "No active anomaly concentration "
                "identified in this lot."
            )

        findings.append(
            {
                "lot_id": lot_id,
                "components": components,
                "anomaly_count": anomaly_count,
                "anomaly_rate": round(
                    anomaly_rate,
                    2
                ),
                "latent_risk_count": latent_count,
                "critical_count": critical_count,
                "high_count": high_count,
                "average_risk": round(
                    average_risk,
                    2
                ),
                "finding": finding,
            }
        )

    findings.sort(
        key=lambda item: (
            item["average_risk"],
            item["critical_count"],
            item["anomaly_count"],
        ),
        reverse=True
    )

    return findings


def build_priority_components(
    anomaly_df,
    prediction_df,
    explanation_df
):

    if anomaly_df is None:
        return []

    if "component_id" not in anomaly_df.columns:
        return []

    merged = anomaly_df.copy()

    if (
        prediction_df is not None
        and "component_id"
        in prediction_df.columns
    ):

        prediction_columns = [
            "component_id",
            "risk_score",
            "final_risk_level",
            "final_decision",
            "predicted_168h_uA",
            "absolute_limit_uA",
            "predicted_limit_utilization_percent",
            "upper_limit_utilization_percent",
            "future_drift_risk",
            "primary_risk_driver",
            "evidence_summary",
            "detailed_explanation",
        ]

        available = [
            column
            for column in prediction_columns
            if column in prediction_df.columns
        ]

        prediction_subset = (
            prediction_df[
                available
            ]
            .drop_duplicates(
                subset=["component_id"]
            )
        )

        merged = merged.merge(
            prediction_subset,
            on="component_id",
            how="left",
            suffixes=(
                "",
                "_prediction"
            )
        )

    if (
        explanation_df is not None
        and "component_id"
        in explanation_df.columns
    ):

        explanation_columns = [
            "component_id",
            "detailed_explanation",
            "evidence_summary",
            "explanation",
            "reason",
        ]

        available = [
            column
            for column in explanation_columns
            if column in explanation_df.columns
        ]

        explanation_subset = (
            explanation_df[
                available
            ]
            .drop_duplicates(
                subset=["component_id"]
            )
        )

        merged = merged.merge(
            explanation_subset,
            on="component_id",
            how="left",
            suffixes=(
                "",
                "_explanation"
            )
        )

    if "risk_score" in merged.columns:

        merged["_risk_sort"] = pd.to_numeric(
            merged["risk_score"],
            errors="coerce"
        ).fillna(0)

    else:

        merged["_risk_sort"] = 0

    if "anomaly_severity" in merged.columns:

        severity_rank = {
            "CRITICAL": 4,
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1,
            "NORMAL": 0,
        }

        merged["_severity_sort"] = (
            normalize_text(
                merged[
                    "anomaly_severity"
                ]
            )
            .map(severity_rank)
            .fillna(0)
        )

    else:

        merged["_severity_sort"] = 0

    merged = merged.sort_values(
        by=[
            "_risk_sort",
            "_severity_sort",
        ],
        ascending=False
    )

    priority = []

    for _, row in merged.head(20).iterrows():

        component_id = str(
            row.get(
                "component_id",
                ""
            )
        )

        risk_score = clean_value(
            row.get(
                "risk_score"
            )
        )

        final_risk = clean_value(
            row.get(
                "final_risk_level"
            )
        )

        severity = clean_value(
            row.get(
                "anomaly_severity"
            )
        )

        screening_status = clean_value(
            row.get(
                "screening_status"
            )
        )

        driver = clean_value(
            row.get(
                "primary_risk_driver"
            )
        )

        evidence = clean_value(
            row.get(
                "evidence_summary"
            )
        )

        explanation = clean_value(
            row.get(
                "detailed_explanation"
            )
        )

        if evidence is None:
            evidence = clean_value(
                row.get(
                    "evidence_summary_explanation"
                )
            )

        if explanation is None:
            explanation = clean_value(
                row.get(
                    "detailed_explanation_explanation"
                )
            )

        if (
            driver is None
            or str(driver).strip() == ""
        ):

            driver = "Temporal / anomaly signal"

        if (
            evidence is None
            or str(evidence).strip() == ""
        ):

            evidence = (
                "Review component trajectory "
                "and anomaly indicators."
            )

        priority.append(
            {
                "component_id": component_id,
                "lot_id": clean_value(
                    row.get("lot_id")
                ),
                "severity": severity,
                "current_anomaly_level": clean_value(
                    row.get(
                        "current_anomaly_level"
                    )
                ),
                "latent_risk": clean_value(
                    row.get(
                        "latent_risk_flag"
                    )
                ),
                "screening_status": screening_status,
                "risk_score": risk_score,
                "final_risk_level": final_risk,
                "final_decision": clean_value(
                    row.get(
                        "final_decision"
                    )
                ),
                "predicted_168h_uA": clean_value(
                    row.get(
                        "predicted_168h_uA"
                    )
                ),
                "absolute_limit_uA": clean_value(
                    row.get(
                        "absolute_limit_uA"
                    )
                ),
                "predicted_limit_utilization_percent": clean_value(
                    row.get(
                        "predicted_limit_utilization_percent"
                    )
                ),
                "upper_limit_utilization_percent": clean_value(
                    row.get(
                        "upper_limit_utilization_percent"
                    )
                ),
                "future_drift_risk": clean_value(
                    row.get(
                        "future_drift_risk"
                    )
                ),
                "primary_risk_driver": driver,
                "evidence_summary": evidence,
                "explanation": explanation,
            }
        )

    return priority


def build_report():

    data_df = read_csv_file(
        DATA_FILE,
        required=True
    )

    anomaly_df = read_csv_file(
        ANOMALY_FILE,
        required=True
    )

    prediction_df = read_csv_file(
        PREDICTION_FILE
    )

    explanation_df = read_csv_file(
        EXPLANATION_FILE
    )

    total_components = len(
        data_df
    )

    lots = 0

    if "lot_id" in data_df.columns:

        lots = int(
            data_df[
                "lot_id"
            ].nunique()
        )

    pass_count = 0
    review_count = 0
    reject_count = 0

    if "screening_status" in anomaly_df.columns:

        status = normalize_text(
            anomaly_df[
                "screening_status"
            ]
        )

        pass_count = int(
            status.str.contains(
                "PASS",
                na=False
            ).sum()
        )

        review_count = int(
            status.str.contains(
                "REVIEW",
                na=False
            ).sum()
        )

        reject_count = int(
            status.str.contains(
                "REJECT",
                na=False
            ).sum()
        )

    anomaly_count = 0
    latent_count = 0

    if "combined_anomaly" in anomaly_df.columns:

        anomaly_count = int(
            normalize_bool_series(
                anomaly_df[
                    "combined_anomaly"
                ]
            ).sum()
        )

    if "latent_risk_flag" in anomaly_df.columns:

        latent_count = int(
            normalize_bool_series(
                anomaly_df[
                    "latent_risk_flag"
                ]
            ).sum()
        )

    critical_count = 0
    high_count = 0
    medium_count = 0

    if "anomaly_severity" in anomaly_df.columns:

        severity = normalize_text(
            anomaly_df[
                "anomaly_severity"
            ]
        )

        critical_count = int(
            (severity == "CRITICAL").sum()
        )

        high_count = int(
            (severity == "HIGH").sum()
        )

        medium_count = int(
            (severity == "MEDIUM").sum()
        )

    risk_scores = []

    if (
        prediction_df is not None
        and "risk_score"
        in prediction_df.columns
    ):

        risk_scores = pd.to_numeric(
            prediction_df[
                "risk_score"
            ],
            errors="coerce"
        ).dropna().tolist()

    average_risk = (
        float(
            np.mean(risk_scores)
        )
        if risk_scores
        else 0.0
    )

    predicted_over_limit = 0

    if (
        prediction_df is not None
        and "predicted_limit_utilization_percent"
        in prediction_df.columns
    ):

        utilization = pd.to_numeric(
            prediction_df[
                "predicted_limit_utilization_percent"
            ],
            errors="coerce"
        )

        predicted_over_limit = int(
            (
                utilization >= 100
            ).sum()
        )

    upper_over_limit = 0

    if (
        prediction_df is not None
        and "upper_limit_utilization_percent"
        in prediction_df.columns
    ):

        utilization = pd.to_numeric(
            prediction_df[
                "upper_limit_utilization_percent"
            ],
            errors="coerce"
        )

        upper_over_limit = int(
            (
                utilization >= 100
            ).sum()
        )

    anomaly_rate = percentage(
        anomaly_count,
        total_components
    )

    pass_rate = percentage(
        pass_count,
        total_components
    )

    review_rate = percentage(
        review_count,
        total_components
    )

    reject_rate = percentage(
        reject_count,
        total_components
    )

    if critical_count > 0:

        overall_assessment = (
            "Critical reliability signals are "
            "present. Components carrying critical "
            "signals should be investigated before "
            "release."
        )

    elif latent_count > 0:

        overall_assessment = (
            "Latent-risk behavior has been detected. "
            "Components should be reviewed for abnormal "
            "temporal drift even when absolute limits "
            "are not exceeded."
        )

    elif anomaly_count > 0:

        overall_assessment = (
            "Anomaly signals are present within the "
            "screening population. Review affected "
            "components before final disposition."
        )

    else:

        overall_assessment = (
            "No significant anomaly concentration "
            "was identified by the current screening "
            "pipeline."
        )

    if predicted_over_limit > 0:

        forecast_assessment = (
            f"{predicted_over_limit} component(s) are "
            "projected to reach or exceed the absolute "
            "limit at 168H."
        )

    elif upper_over_limit > 0:

        forecast_assessment = (
            f"{upper_over_limit} component(s) have an "
            "upper prediction interval reaching or "
            "exceeding the absolute limit."
        )

    else:

        forecast_assessment = (
            "No component is currently projected to "
            "exceed the absolute limit at 168H."
        )

    if reject_count > 0:

        recommended_action = (
            "Hold rejected components from release "
            "and perform engineering investigation."
        )

    elif review_count > 0:

        recommended_action = (
            "Review flagged components and their "
            "temporal trajectories before disposition."
        )

    elif latent_count > 0:

        recommended_action = (
            "Investigate latent-risk trajectories "
            "before treating components as fully nominal."
        )

    else:

        recommended_action = (
            "Continue standard screening and "
            "reliability monitoring."
        )

    return {
        "report_id": "PLEIONE-PS26170-RPT-001",
        "run_id": "RUN-26170-01",
        "problem_statement": "PS 26170",
        "title": (
            "AI-Driven Component Burn-In "
            "Screening Report"
        ),
        "status": "COMPLETED",
        "duration": "168H",
        "generated_from": {
            "dataset": DATA_FILE.name,
            "anomaly_results": ANOMALY_FILE.name,
            "prediction_results": (
                PREDICTION_FILE.name
                if prediction_df is not None
                else None
            ),
            "explanation_results": (
                EXPLANATION_FILE.name
                if explanation_df is not None
                else None
            ),
        },
        "screening_summary": {
            "components": total_components,
            "lots": lots,
            "pass_count": pass_count,
            "review_count": review_count,
            "reject_count": reject_count,
            "pass_rate": pass_rate,
            "review_rate": review_rate,
            "reject_rate": reject_rate,
        },
        "reliability_summary": {
            "active_anomalies": anomaly_count,
            "anomaly_rate": anomaly_rate,
            "latent_risk": latent_count,
            "critical": critical_count,
            "high": high_count,
            "medium": medium_count,
            "average_risk": round(
                average_risk,
                2
            ),
        },
        "forecast_summary": {
            "predicted_over_limit": (
                predicted_over_limit
            ),
            "upper_interval_over_limit": (
                upper_over_limit
            ),
            "assessment": forecast_assessment,
        },
        "overall_assessment": overall_assessment,
        "recommended_action": recommended_action,
        "measurement_points": [
            "0H",
            "24H",
            "96H",
            "168H",
        ],
        "detection_engine": (
            "Statistical Deviation + "
            "Isolation Forest + "
            "Temporal Drift"
        ),
        "prediction_engine": (
            "Future Drift Prediction + "
            "Risk Assessment"
        ),
        "lot_findings": build_lot_findings(
            anomaly_df,
            prediction_df
        ),
        "priority_components": build_priority_components(
            anomaly_df,
            prediction_df,
            explanation_df
        ),
    }


@router.get("/")
def get_reports():

    report = build_report()

    return {
        "data": [report],
        "total": 1,
    }


@router.get("/summary")
def get_report_summary():

    return build_report()


@router.get("/{report_id}")
def get_report(
    report_id: str
):

    report = build_report()

    if report_id != report["report_id"]:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Report {report_id} "
                "not found"
            )
        )

    return report