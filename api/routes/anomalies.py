from fastapi import APIRouter, HTTPException
from pathlib import Path
from functools import lru_cache

import pandas as pd

from api.services.data_service import clean_records


router = APIRouter(
    prefix="/api/anomalies",
    tags=["Anomalies"],
)


BASE_DIR = Path(__file__).resolve().parents[2]

ANOMALY_FILE = (
    BASE_DIR
    / "data"
    / "module_A_anomaly_results.csv"
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

@lru_cache(maxsize=1)
def _load_anomaly_data(file_mtime: float):
    """
    Load the anomaly result CSV into memory.

    The file modification time is used as the cache key.
    If ML writes a new CSV, the modification time changes and
    the data is automatically reloaded.
    """

    df = pd.read_csv(ANOMALY_FILE)

    return df


def get_anomaly_dataframe() -> pd.DataFrame:
    """
    Return the current anomaly dataframe.

    Cached between requests so the CSV is not repeatedly
    parsed by pandas.
    """

    if not ANOMALY_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="Module A anomaly results not found",
        )

    file_mtime = ANOMALY_FILE.stat().st_mtime

    return _load_anomaly_data(file_mtime).copy()


# ---------------------------------------------------------
# ANOMALIES
# ---------------------------------------------------------

@router.get("/")
def get_anomalies(
    page: int = 1,
    limit: int = 25,
    lot_id: str = "",
):
    try:
        # -------------------------------------------------
        # VALIDATE PAGINATION
        # -------------------------------------------------

        if page < 1:
            page = 1

        if limit < 1:
            limit = 25

        # This is only the number of records returned
        # per request. It is NOT a limit on the dataset.
        limit = min(limit, 100)

        # -------------------------------------------------
        # LOAD DATA
        # -------------------------------------------------

        df = get_anomaly_dataframe()

        # -------------------------------------------------
        # ANOMALY FILTER
        # -------------------------------------------------

        if "anomaly_flag" in df.columns:

            anomaly_values = (
                df["anomaly_flag"]
                .astype(str)
                .str.strip()
                .str.lower()
            )

            df = df[
                anomaly_values.isin(
                    [
                        "true",
                        "1",
                        "yes",
                    ]
                )
            ]

        # -------------------------------------------------
        # LOT FILTER
        # -------------------------------------------------

        if lot_id.strip():

            lot_value = (
                lot_id
                .strip()
                .lower()
            )

            df = df[
                df["lot_id"]
                .astype(str)
                .str.strip()
                .str.lower()
                == lot_value
            ]

        # -------------------------------------------------
        # TOTAL
        # -------------------------------------------------

        total = len(df)

        # -------------------------------------------------
        # PAGINATION
        # -------------------------------------------------

        start = (page - 1) * limit
        end = start + limit

        page_data = df.iloc[start:end]

        # -------------------------------------------------
        # SERIALIZE
        # -------------------------------------------------

        records = page_data.to_dict(
            orient="records"
        )

        records = clean_records(records)

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return {
            "total": int(total),
            "page": int(page),
            "limit": int(limit),
            "pages": (
                (total + limit - 1) // limit
                if total > 0
                else 0
            ),
            "lot_id": (
                lot_id
                if lot_id.strip()
                else None
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