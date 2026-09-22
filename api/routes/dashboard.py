from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd

from api.services.data_service import clean_records


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"]
)


BASE_DIR = Path(__file__).resolve().parents[2]

ANOMALY_FILE = (
    BASE_DIR
    / "data"
    / "module_A_anomaly_results.csv"
)


@router.get("/summary")
def get_dashboard_summary():

    try:
        if not ANOMALY_FILE.exists():
            raise HTTPException(
                status_code=404,
                detail="Module A anomaly results not found"
            )

        df = pd.read_csv(ANOMALY_FILE)

        # ---------------------------------------------------------
        # BASIC COUNTS
        # ---------------------------------------------------------

        total_components = len(df)

        total_lots = (
            df["lot_id"]
            .dropna()
            .astype(str)
            .nunique()
        )

        # ---------------------------------------------------------
        # ANOMALY COUNT
        # ---------------------------------------------------------

        total_anomalies = int(
            (df["anomaly_flag"] == 1).sum()
        )

        active_signals = total_anomalies

        # ---------------------------------------------------------
        # RISK LEVEL
        #
        # These values come directly from Module A.
        # ---------------------------------------------------------

        risk_level = (
            df["risk_level"]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.strip()
        )

        critical = int(
            (risk_level == "CRITICAL").sum()
        )

        high = int(
            (risk_level == "HIGH").sum()
        )

        # High-risk components = HIGH + CRITICAL
        high_risk_components = high + critical

        # Latent risks
        #
        # Ground truth is used here only to identify latent-defect
        # records in the evaluation dataset.
        latent_risks = int(
            (
                df["ground_truth"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.lower()
                == "latent_defect"
            ).sum()
        )

        # ---------------------------------------------------------
        # SCREENING DECISIONS
        # ---------------------------------------------------------

        decision = (
            df["screening_decision"]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.strip()
        )

        passed = int(
            (decision == "PASS").sum()
        )

        review = int(
            (decision == "REVIEW").sum()
        )

        reject = int(
            (decision == "REJECT").sum()
        )

        # ---------------------------------------------------------
        # RETURN DASHBOARD DATA
        # ---------------------------------------------------------

        return {
            "total_components": int(total_components),
            "total_lots": int(total_lots),

            "active_signals": int(active_signals),
            "total_anomalies": int(total_anomalies),

            "latent_risks": int(latent_risks),

            "high_risk_components": int(high_risk_components),
            "critical": int(critical),
            "high": int(high),

            "passed": int(passed),
            "review": int(review),
            "reject": int(reject),
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )