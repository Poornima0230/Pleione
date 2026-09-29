from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query


router = APIRouter(
    prefix="/api/forecast",
    tags=["Forecast"],
)


# ============================================================
# Paths
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

FORECAST_FILE = (
    ROOT_DIR
    / "data"
    / "module_B"
    / "module_B_predictions.csv"
)


# ============================================================
# Required columns
# ============================================================

REQUIRED_COLUMNS = [
    "component_id",
    "lot_id",
    "component_type",
    "temperature_C",
    "voltage_V",
    "iddq_0h_uA",
    "iddq_24h_uA",
    "leakage_0h_uA",
    "leakage_24h_uA",
    "delta_0_24",
    "predicted_168h_uA",
    "prediction_lower_uA",
    "prediction_upper_uA",
    "failure_probability",
    "failure_risk",
    "absolute_limit_uA",
]


# ============================================================
# Cache
# ============================================================

_CACHE = None
_CACHE_SIGNATURE = None


def get_file_signature():
    """
    Return a lightweight signature for the forecast CSV.

    If the CSV changes, the backend automatically reloads it.
    """
    if not FORECAST_FILE.exists():
        return None

    stat = FORECAST_FILE.stat()

    return (
        stat.st_mtime_ns,
        stat.st_size,
    )


def normalize_risk(value) -> str:
    """
    Normalize Module B risk labels so filtering and summary
    calculations are consistent.
    """
    if pd.isna(value):
        return "UNKNOWN"

    text = str(value).strip().upper()

    text = text.replace("-", "_")
    text = text.replace(" ", "_")

    if text in {"VERYLOW", "VERY_LOW"}:
        return "VERY_LOW"

    if text == "LOW":
        return "LOW"

    if text == "MEDIUM":
        return "MEDIUM"

    if text == "HIGH":
        return "HIGH"

    if text == "CRITICAL":
        return "CRITICAL"

    return text


def load_forecast_data() -> pd.DataFrame:
    """
    Load Module B prediction data.

    The CSV is cached in memory and reloaded only when the
    underlying file changes.
    """
    global _CACHE
    global _CACHE_SIGNATURE

    if not FORECAST_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                "Module B forecast file not found: "
                "data/module_B/module_B_predictions.csv"
            ),
        )

    signature = get_file_signature()

    if (
        _CACHE is not None
        and _CACHE_SIGNATURE == signature
    ):
        return _CACHE.copy()

    try:
        df = pd.read_csv(
            FORECAST_FILE,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to read Module B forecast file: "
                f"{str(exc)}"
            ),
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
                    "Module B forecast file is missing "
                    "required columns."
                ),
                "missing_columns": missing,
            },
        )

    # --------------------------------------------------------
    # Keep only fields needed by this API.
    # --------------------------------------------------------

    df = df[REQUIRED_COLUMNS].copy()

    # --------------------------------------------------------
    # Normalize text fields.
    # --------------------------------------------------------

    text_columns = [
        "component_id",
        "lot_id",
        "component_type",
    ]

    for column in text_columns:
        df[column] = (
            df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    df["failure_risk"] = (
        df["failure_risk"]
        .apply(normalize_risk)
    )

    # --------------------------------------------------------
    # Normalize numeric fields.
    # --------------------------------------------------------

    numeric_columns = [
        "temperature_C",
        "voltage_V",
        "iddq_0h_uA",
        "iddq_24h_uA",
        "leakage_0h_uA",
        "leakage_24h_uA",
        "delta_0_24",
        "predicted_168h_uA",
        "prediction_lower_uA",
        "prediction_upper_uA",
        "failure_probability",
        "absolute_limit_uA",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # --------------------------------------------------------
    # Clamp probability to [0, 1].
    # --------------------------------------------------------

    df["failure_probability"] = (
        df["failure_probability"]
        .clip(lower=0.0, upper=1.0)
    )

    # --------------------------------------------------------
    # Remove duplicate component IDs.
    #
    # Module B should contain one prediction per component.
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=["component_id"],
        keep="first",
    ).reset_index(drop=True)

    _CACHE = df
    _CACHE_SIGNATURE = signature

    return df.copy()


# ============================================================
# Summary
# ============================================================

def build_summary(
    df: pd.DataFrame,
) -> dict:
    """
    Build the Module B risk distribution from the exact same
    DataFrame used by the forecast endpoint.

    Nothing is hardcoded.
    """

    risk = df["failure_risk"]

    very_low = int(
        (risk == "VERY_LOW").sum()
    )

    low = int(
        (risk == "LOW").sum()
    )

    medium = int(
        (risk == "MEDIUM").sum()
    )

    high = int(
        (risk == "HIGH").sum()
    )

    critical = int(
        (risk == "CRITICAL").sum()
    )

    return {
        "very_low": very_low,
        "low": low,
        "medium": medium,
        "high": high,
        "critical": critical,
    }


# ============================================================
# Record serialization
# ============================================================

def serialize_record(
    row: pd.Series,
) -> dict:
    """
    Convert one DataFrame row into JSON-safe API data.
    """

    result = {}

    for column in REQUIRED_COLUMNS:
        value = row.get(column)

        if pd.isna(value):
            result[column] = None
            continue

        if isinstance(value, str):
            result[column] = value
            continue

        try:
            result[column] = float(value)
        except (TypeError, ValueError):
            result[column] = value

    return result


# ============================================================
# GET /api/forecast/
# ============================================================

@router.get("/")
def get_forecasts(
    page: int = Query(
        1,
        ge=1,
    ),
    limit: int = Query(
        20,
        ge=1,
        le=200,
    ),
    lot_id: Optional[str] = Query(
        None,
    ),
    component_type: Optional[str] = Query(
        None,
    ),
    risk: Optional[str] = Query(
        None,
    ),
    search: Optional[str] = Query(
        None,
    ),
):
    """
    Return paginated Module B forecasts.

    Module B information boundary:

        0h + 24h
            ↓
        predicted 168h
            ↓
        failure probability

    This endpoint does not calculate Module C screening
    decisions.
    """

    df = load_forecast_data()

    # --------------------------------------------------------
    # Summary must describe the complete Module B population,
    # not only the current filtered page.
    # --------------------------------------------------------

    summary = build_summary(df)

    # --------------------------------------------------------
    # Apply filters.
    # --------------------------------------------------------

    filtered = df

    if lot_id:
        lot_value = lot_id.strip()

        if lot_value:
            filtered = filtered[
                filtered["lot_id"].str.lower()
                == lot_value.lower()
            ]

    if component_type:
        type_value = component_type.strip()

        if type_value:
            filtered = filtered[
                filtered["component_type"].str.lower()
                == type_value.lower()
            ]

    if risk:
        risk_value = normalize_risk(risk)

        if risk_value != "ALL":
            filtered = filtered[
                filtered["failure_risk"]
                == risk_value
            ]

    if search:
        search_value = search.strip().lower()

        if search_value:
            filtered = filtered[
                filtered["component_id"]
                .str.lower()
                .str.contains(
                    search_value,
                    regex=False,
                    na=False,
                )
            ]

    # --------------------------------------------------------
    # Pagination.
    # --------------------------------------------------------

    total = int(len(filtered))

    pages = max(
        1,
        (total + limit - 1) // limit,
    )

    # If a filter reduces the result set and the frontend
    # requests a page beyond the available range, return the
    # last valid page rather than an empty page.
    safe_page = min(
        page,
        pages,
    )

    start = (
        safe_page - 1
    ) * limit

    end = start + limit

    page_df = filtered.iloc[
        start:end
    ]

    forecasts = [
        serialize_record(row)
        for _, row in page_df.iterrows()
    ]

    return {
        "page": safe_page,
        "limit": limit,
        "pages": pages,
        "total": total,
        "summary": summary,
        "forecasts": forecasts,
    }


# ============================================================
# GET /api/forecast/summary
# ============================================================

@router.get("/summary")
def get_forecast_summary():
    """
    Return the complete Module B forecast population summary.
    """

    df = load_forecast_data()

    summary = build_summary(df)

    return {
        "total_components": int(len(df)),
        "summary": summary,
    }


# ============================================================
# GET /api/forecast/{component_id}
# ============================================================

@router.get("/{component_id}")
def get_component_forecast(
    component_id: str,
):
    """
    Return Module B forecast information for one component.
    """

    df = load_forecast_data()

    component_id = component_id.strip()

    matches = df[
        df["component_id"]
        == component_id
    ]

    if matches.empty:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No Module B forecast found "
                f"for component {component_id}"
            ),
        )

    row = matches.iloc[0]

    return {
        "forecast": serialize_record(row),
    }