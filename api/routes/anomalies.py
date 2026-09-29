from pathlib import Path
from threading import Lock

import pandas as pd
from fastapi import APIRouter, HTTPException, Query


router = APIRouter(
    prefix="/api/anomalies",
    tags=["Anomalies"],
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

MODULE_A_FILE = (
    BASE_DIR
    / "data"
    / "module_A"
    / "module_A_all_predictions.csv"
)


# ============================================================
# REQUIRED CURRENT MODULE A COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "component_id",
    "lot_id",
    "component_type",
    "temperature_C",
    "voltage_V",
    "iddq_0h_uA",
    "leakage_0h_uA",
    "module_a_score",
    "module_a_status",
    "peer_source",
]


# ============================================================
# IN-MEMORY CACHE
# ============================================================

_CACHE_LOCK = Lock()
_CACHE_DF: pd.DataFrame | None = None
_CACHE_SIGNATURE: tuple[int, int] | None = None


def get_file_signature() -> tuple[int, int]:
    if not MODULE_A_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Current Module A output was not found at: "
                f"{MODULE_A_FILE}"
            ),
        )

    stat = MODULE_A_FILE.stat()

    return (
        int(stat.st_mtime_ns),
        int(stat.st_size),
    )


def load_module_a_data() -> pd.DataFrame:
    """
    Load the current Module A all-predictions file.

    The file is cached in memory so the CSV is not read from disk
    on every frontend request.
    """

    global _CACHE_DF
    global _CACHE_SIGNATURE

    signature = get_file_signature()

    with _CACHE_LOCK:
        if (
            _CACHE_DF is not None
            and _CACHE_SIGNATURE == signature
        ):
            return _CACHE_DF.copy()

        try:
            df = pd.read_csv(MODULE_A_FILE)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read Module A output: {exc}",
            )

        missing = [
            column
            for column in REQUIRED_COLUMNS
            if column not in df.columns
        ]

        if missing:
            raise HTTPException(
                status_code=500,
                detail={
                    "message": (
                        "Current Module A output is missing "
                        "required columns."
                    ),
                    "missing_columns": missing,
                    "file": str(MODULE_A_FILE),
                },
            )

        # ----------------------------------------------------
        # Keep only the columns needed by this page.
        # ----------------------------------------------------

        df = df[REQUIRED_COLUMNS].copy()

        # ----------------------------------------------------
        # Normalize text columns.
        # ----------------------------------------------------

        for column in [
            "component_id",
            "lot_id",
            "component_type",
            "module_a_status",
            "peer_source",
        ]:
            df[column] = (
                df[column]
                .astype("string")
                .fillna("")
                .str.strip()
            )

        # ----------------------------------------------------
        # Normalize numeric columns.
        # ----------------------------------------------------

        numeric_columns = [
            "temperature_C",
            "voltage_V",
            "iddq_0h_uA",
            "leakage_0h_uA",
            "module_a_score",
        ]

        for column in numeric_columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

        # ----------------------------------------------------
        # One current record per component.
        # ----------------------------------------------------

        df = df.drop_duplicates(
            subset=["component_id"],
            keep="last",
        ).copy()

        # ----------------------------------------------------
        # Normalize status.
        # ----------------------------------------------------

        df["module_a_status"] = (
            df["module_a_status"]
            .str.upper()
        )

        # ----------------------------------------------------
        # Sort strongest anomaly first.
        # ----------------------------------------------------

        df = df.sort_values(
            by="module_a_score",
            ascending=False,
            na_position="last",
        ).reset_index(drop=True)

        _CACHE_DF = df
        _CACHE_SIGNATURE = signature

        return df.copy()


# ============================================================
# HELPERS
# ============================================================

def clean_value(value):
    if pd.isna(value):
        return None

    if isinstance(value, float):
        return round(float(value), 6)

    return value


def clean_record(row: pd.Series) -> dict:
    return {
        "component_id": clean_value(
            row["component_id"]
        ),
        "lot_id": clean_value(
            row["lot_id"]
        ),
        "component_type": clean_value(
            row["component_type"]
        ),

        "temperature_C": clean_value(
            row["temperature_C"]
        ),
        "voltage_V": clean_value(
            row["voltage_V"]
        ),

        "iddq_0h_uA": clean_value(
            row["iddq_0h_uA"]
        ),
        "leakage_0h_uA": clean_value(
            row["leakage_0h_uA"]
        ),

        "module_a_score": clean_value(
            row["module_a_score"]
        ),
        "module_a_status": clean_value(
            row["module_a_status"]
        ),
        "peer_source": clean_value(
            row["peer_source"]
        ),
    }


# ============================================================
# SUMMARY
# ============================================================

@router.get("/summary")
def get_anomaly_summary():
    df = load_module_a_data()

    total = len(df)

    anomalous = int(
        (df["module_a_status"] == "ANOMALOUS").sum()
    )

    watch = int(
        (df["module_a_status"] == "WATCH").sum()
    )

    normal = int(
        (df["module_a_status"] == "NORMAL").sum()
    )

    attention = anomalous + watch

    return {
        "total_components": total,
        "anomalous": anomalous,
        "watch": watch,
        "normal": normal,
        "attention": attention,
        "anomaly_rate": (
            round(
                anomalous / total * 100,
                2,
            )
            if total
            else 0
        ),
        "attention_rate": (
            round(
                attention / total * 100,
                2,
            )
            if total
            else 0
        ),
    }


# ============================================================
# FILTER OPTIONS
# ============================================================

@router.get("/filters")
def get_anomaly_filters():
    df = load_module_a_data()

    lots = sorted(
        [
            value
            for value in df["lot_id"].dropna().unique()
            if str(value).strip()
        ]
    )

    component_types = sorted(
        [
            value
            for value in df["component_type"].dropna().unique()
            if str(value).strip()
        ]
    )

    statuses = sorted(
        [
            value
            for value in df["module_a_status"].dropna().unique()
            if str(value).strip()
        ]
    )

    return {
        "lots": lots,
        "component_types": component_types,
        "statuses": statuses,
    }


# ============================================================
# ANOMALIES
# ============================================================

@router.get("/")
def get_anomalies(
    page: int = Query(
        default=1,
        ge=1,
    ),
    limit: int = Query(
        default=25,
        ge=1,
        le=200,
    ),
    search: str | None = Query(
        default=None,
    ),
    lot_id: str | None = Query(
        default=None,
    ),
    component_type: str | None = Query(
        default=None,
    ),
    status: str | None = Query(
        default=None,
    ),
):
    df = load_module_a_data()

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:
        query = search.strip().lower()

        if query:
            mask = (
                df["component_id"]
                .str.lower()
                .str.contains(
                    query,
                    na=False,
                )
                |
                df["lot_id"]
                .str.lower()
                .str.contains(
                    query,
                    na=False,
                )
                |
                df["component_type"]
                .str.lower()
                .str.contains(
                    query,
                    na=False,
                )
            )

            df = df[mask].copy()

    # --------------------------------------------------------
    # LOT
    # --------------------------------------------------------

    if lot_id and lot_id != "ALL":
        df = df[
            df["lot_id"].str.upper()
            == lot_id.strip().upper()
        ].copy()

    # --------------------------------------------------------
    # COMPONENT TYPE
    # --------------------------------------------------------

    if component_type and component_type != "ALL":
        df = df[
            df["component_type"].str.upper()
            == component_type.strip().upper()
        ].copy()

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    if status and status != "ALL":
        df = df[
            df["module_a_status"].str.upper()
            == status.strip().upper()
        ].copy()

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    df = df.sort_values(
        by="module_a_score",
        ascending=False,
        na_position="last",
    )

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    total = len(df)

    pages = (
        (total + limit - 1) // limit
        if total
        else 0
    )

    # If filters reduce the result and the requested page
    # is now beyond the last page, return the last page.
    if pages > 0 and page > pages:
        page = pages

    start = (page - 1) * limit
    end = start + limit

    page_df = df.iloc[start:end]

    data = [
        clean_record(row)
        for _, row in page_df.iterrows()
    ]

    return {
        "page": page,
        "limit": limit,
        "pages": pages,
        "total": total,
        "data": data,
    }