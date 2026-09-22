from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd

from api.services.data_service import clean_records


router = APIRouter(
    prefix="/api/components",
    tags=["Components"],
)


BASE_DIR = Path(__file__).resolve().parents[2]

ANOMALY_FILE = (
    BASE_DIR
    / "data"
    / "module_A_anomaly_results.csv"
)


@router.get("/")
def get_components(
    page: int = 1,
    limit: int = 25,
    component_id: str = "",
    lot_id: str = "",
    component_type: str = "",
    screening_decision: str = "",
):
    try:
        # -----------------------------
        # Pagination validation
        # -----------------------------

        page = max(page, 1)

        if limit < 1 or limit > 100:
            limit = 25

        # -----------------------------
        # Load Module A results
        # -----------------------------

        if not ANOMALY_FILE.exists():
            raise HTTPException(
                status_code=404,
                detail="Module A anomaly results not found",
            )

        df = pd.read_csv(ANOMALY_FILE)

        # -----------------------------
        # Remove duplicate components
        # -----------------------------
        #
        # A component must appear only once
        # in the Components explorer.
        #
        # We keep the latest occurrence.
        # -----------------------------

        if "component_id" in df.columns:
            df = df.drop_duplicates(
                subset=["component_id"],
                keep="last",
            )

        # -----------------------------
        # Component ID search
        # -----------------------------

        if component_id.strip():
            search_value = (
                component_id
                .strip()
                .lower()
            )

            df = df[
                df["component_id"]
                .astype(str)
                .str.lower()
                .str.contains(
                    search_value,
                    na=False,
                )
            ]

        # -----------------------------
        # Lot filter
        # -----------------------------

        if lot_id.strip():
            lot_value = (
                lot_id
                .strip()
                .lower()
            )

            df = df[
                df["lot_id"]
                .astype(str)
                .str.lower()
                == lot_value
            ]

        # -----------------------------
        # Component type filter
        # -----------------------------

        if component_type.strip():
            type_value = (
                component_type
                .strip()
                .lower()
            )

            df = df[
                df["component_type"]
                .astype(str)
                .str.lower()
                == type_value
            ]

        # -----------------------------
        # Screening decision filter
        # -----------------------------

        if screening_decision.strip():
            decision_value = (
                screening_decision
                .strip()
                .upper()
            )

            df = df[
                df["screening_decision"]
                .astype(str)
                .str.upper()
                == decision_value
            ]

        # -----------------------------
        # Total AFTER filters
        # -----------------------------

        total = len(df)

        # -----------------------------
        # Pagination
        # -----------------------------

        start = (page - 1) * limit
        end = start + limit

        page_data = df.iloc[start:end].copy()

        # -----------------------------
        # Fields required by Components
        # -----------------------------

        component_columns = [
            "component_id",
            "lot_id",
            "component_type",

            "temperature_C",
            "voltage_V",

            "iddq_0h_uA",
            "iddq_24h_uA",
            "iddq_96h_uA",
            "iddq_168h_uA",

            "anomaly_flag",
            "combined_anomaly_score",

            "risk_score_100",
            "risk_level",

            "limit_violation",
            "screening_decision",

            "explanation",
        ]

        available_columns = [
            column
            for column in component_columns
            if column in page_data.columns
        ]

        page_data = page_data[
            available_columns
        ]

        records = page_data.to_dict(
            orient="records"
        )

        records = clean_records(records)

        # -----------------------------
        # Filter options
        # -----------------------------

        filter_options = {
            "lots": sorted(
                df["lot_id"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            "component_types": sorted(
                df["component_type"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            ),
            "screening_decisions": sorted(
                df["screening_decision"]
                .dropna()
                .astype(str)
                .str.upper()
                .unique()
                .tolist()
            ),
        }

        # -----------------------------
        # Response
        # -----------------------------

        return {
            "total": int(total),

            "page": int(page),

            "limit": int(limit),

            "filter_options": filter_options,

            "data": records,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )