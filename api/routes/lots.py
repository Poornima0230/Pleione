from fastapi import APIRouter, HTTPException
from pathlib import Path

import pandas as pd

from api.services.data_service import clean_records


router = APIRouter(
    prefix="/api/lots",
    tags=["Lots"],
)


BASE_DIR = Path(__file__).resolve().parents[2]

ANOMALY_FILE = (
    BASE_DIR
    / "data"
    / "module_A_anomaly_results.csv"
)


@router.get("/")
def get_lots():
    try:
        # --------------------------------------------------
        # CHECK FILE
        # --------------------------------------------------

        if not ANOMALY_FILE.exists():
            raise HTTPException(
                status_code=404,
                detail=(
                    "Module A anomaly results "
                    "not found"
                ),
            )

        df = pd.read_csv(ANOMALY_FILE)

        # --------------------------------------------------
        # TOTAL COMPONENTS
        # --------------------------------------------------

        total_components = (
            df.groupby("lot_id")
            .size()
            .reset_index(
                name="component_count"
            )
        )

        # --------------------------------------------------
        # ANOMALIES
        # --------------------------------------------------
        # Actual backend field:
        # anomaly_flag
        #
        # It may be stored as 0/1 in the CSV.
        # --------------------------------------------------

        df["anomaly_flag_numeric"] = (
            pd.to_numeric(
                df["anomaly_flag"],
                errors="coerce",
            )
            .fillna(0)
            .astype(int)
        )

        anomaly_counts = (
            df.groupby("lot_id")[
                "anomaly_flag_numeric"
            ]
            .sum()
            .reset_index(
                name="anomaly_count"
            )
        )

        # --------------------------------------------------
        # CRITICAL
        # --------------------------------------------------
        # Actual backend field:
        # risk_level
        # --------------------------------------------------

        df["critical"] = (
            df["risk_level"]
            .astype(str)
            .str.upper()
            .eq("CRITICAL")
        )

        critical_counts = (
            df.groupby("lot_id")[
                "critical"
            ]
            .sum()
            .reset_index(
                name="critical_count"
            )
        )

        # --------------------------------------------------
        # AVERAGE RISK
        # --------------------------------------------------
        # Actual backend field:
        # risk_score
        #
        # risk_score is 0-1 in the current results.
        # Convert to 0-100 for the frontend.
        # --------------------------------------------------

        df["risk_score_numeric"] = pd.to_numeric(
            df["risk_score"],
            errors="coerce",
        )

        risk_average = (
            df.groupby("lot_id")[
                "risk_score_numeric"
            ]
            .mean()
            .reset_index(
                name="average_risk"
            )
        )

        risk_average["average_risk"] = (
            risk_average["average_risk"] * 100
        )

        # --------------------------------------------------
        # MERGE
        # --------------------------------------------------

        result = total_components

        result = result.merge(
            anomaly_counts,
            on="lot_id",
            how="left",
        )

        result = result.merge(
            critical_counts,
            on="lot_id",
            how="left",
        )

        result = result.merge(
            risk_average,
            on="lot_id",
            how="left",
        )

        # --------------------------------------------------
        # DEFAULT MISSING VALUES
        # --------------------------------------------------

        result["anomaly_count"] = (
            result["anomaly_count"]
            .fillna(0)
            .astype(int)
        )

        result["critical_count"] = (
            result["critical_count"]
            .fillna(0)
            .astype(int)
        )

        result["average_risk"] = (
            result["average_risk"]
            .fillna(0)
        )

        # --------------------------------------------------
        # ANOMALY RATE
        # --------------------------------------------------

        result["anomaly_rate"] = (
            result["anomaly_count"]
            /
            result["component_count"]
            *
            100
        )

        # --------------------------------------------------
        # LATENT RISK
        # --------------------------------------------------
        #
        # We are intentionally NOT calculating this from
        # ground_truth.
        #
        # ground_truth is evaluation information, not a
        # live model-discovered risk signal.
        #
        # Keep the API field for frontend compatibility,
        # but set it to 0 until a genuine model-generated
        # latent-risk field is available.
        # --------------------------------------------------

        result["latent_risk_count"] = 0

        # --------------------------------------------------
        # SORT BY AVERAGE RISK
        # --------------------------------------------------

        result = result.sort_values(
            "average_risk",
            ascending=False,
        )

        # --------------------------------------------------
        # CLEAN RECORDS
        # --------------------------------------------------

        records = result.to_dict(
            orient="records"
        )

        records = clean_records(
            records
        )

        # --------------------------------------------------
        # RESPONSE
        # --------------------------------------------------

        return {
            "total_lots": int(
                len(result)
            ),
            "data": records,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

