from fastapi import APIRouter, HTTPException
from pathlib import Path

import pandas as pd
import numpy as np


router = APIRouter(
    prefix="/api/screening-runs",
    tags=["Screening Runs"]
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


def safe_count(df, column, value):
    if column not in df.columns:
        return 0

    return int(
        (
            df[column]
            .astype(str)
            .str.upper()
            == str(value).upper()
        ).sum()
    )


def build_run():
    if not DATA_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Screening dataset not found"
        )

    try:
        df = pd.read_csv(DATA_FILE)

        anomaly_df = None

        if ANOMALY_FILE.exists():
            anomaly_df = pd.read_csv(
                ANOMALY_FILE
            )

        prediction_df = None

        if PREDICTION_FILE.exists():
            prediction_df = pd.read_csv(
                PREDICTION_FILE
            )

        total_components = len(df)

        lots = 0

        if "lot_id" in df.columns:
            lots = int(
                df["lot_id"]
                .nunique()
            )

        pass_count = 0
        review_count = 0
        reject_count = 0
        anomaly_count = 0
        latent_count = 0
        critical_count = 0
        high_count = 0
        medium_count = 0

        if anomaly_df is not None:

            if "screening_status" in anomaly_df.columns:
                status = (
                    anomaly_df[
                        "screening_status"
                    ]
                    .astype(str)
                    .str.upper()
                )

                pass_count = int(
                    status.str.contains(
                        "PASS"
                    ).sum()
                )

                review_count = int(
                    status.str.contains(
                        "REVIEW"
                    ).sum()
                )

                reject_count = int(
                    status.str.contains(
                        "REJECT"
                    ).sum()
                )

            if "combined_anomaly" in anomaly_df.columns:
                anomaly_values = (
                    anomaly_df[
                        "combined_anomaly"
                    ]
                    .astype(str)
                    .str.lower()
                )

                anomaly_count = int(
                    anomaly_values.isin(
                        [
                            "true",
                            "1",
                            "yes"
                        ]
                    ).sum()
                )

            if "latent_risk_flag" in anomaly_df.columns:
                latent_values = (
                    anomaly_df[
                        "latent_risk_flag"
                    ]
                    .astype(str)
                    .str.lower()
                )

                latent_count = int(
                    latent_values.isin(
                        [
                            "true",
                            "1",
                            "yes"
                        ]
                    ).sum()
                )

            if "anomaly_severity" in anomaly_df.columns:
                severity = (
                    anomaly_df[
                        "anomaly_severity"
                    ]
                    .astype(str)
                    .str.upper()
                )

                critical_count = int(
                    severity.str.contains(
                        "CRITICAL"
                    ).sum()
                )

                high_count = int(
                    severity.str.contains(
                        "HIGH"
                    ).sum()
                )

                medium_count = int(
                    severity.str.contains(
                        "MEDIUM"
                    ).sum()
                )

        risk_average = 0.0

        if prediction_df is not None:
            if "risk_score" in prediction_df.columns:

                risk_series = pd.to_numeric(
                    prediction_df[
                        "risk_score"
                    ],
                    errors="coerce"
                )

                if not risk_series.dropna().empty:
                    risk_average = float(
                        risk_series
                        .dropna()
                        .mean()
                    )

        anomaly_rate = 0.0

        if total_components > 0:
            anomaly_rate = (
                anomaly_count
                / total_components
            ) * 100

        return {
            "run_id": "RUN-26170-01",
            "problem_statement": "PS 26170",
            "title": "Burn-In Screening Run",
            "duration": "168H",
            "status": "COMPLETED",
            "components": total_components,
            "lots": lots,
            "pass_count": pass_count,
            "review_count": review_count,
            "reject_count": reject_count,
            "anomaly_count": anomaly_count,
            "latent_risk_count": latent_count,
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "anomaly_rate": round(
                anomaly_rate,
                2
            ),
            "average_risk": round(
                risk_average,
                2
            ),
            "measurement_points": [
                "0H",
                "24H",
                "96H",
                "168H"
            ],
            "data_source": "Synthetic screening dataset",
            "screening_engine": (
                "Statistical Deviation + "
                "Isolation Forest + "
                "Temporal Drift + "
                "Future Drift Prediction"
            )
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/")
def get_screening_runs():
    run = build_run()

    return {
        "data": [run],
        "total": 1
    }


@router.get("/{run_id}")
def get_screening_run(
    run_id: str
):
    run = build_run()

    if run_id != run["run_id"]:
        raise HTTPException(
            status_code=404,
            detail=f"Screening run {run_id} not found"
        )

    return run