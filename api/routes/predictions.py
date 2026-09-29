from fastapi import APIRouter, HTTPException
from pathlib import Path

import pandas as pd
import numpy as np


router = APIRouter(
    prefix="/api/predictions",
    tags=["Predictions"],
)


# ============================================================
# PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

PREDICTION_FILE = (
    BASE_DIR
    / "data"
    / "module_B"
    / "module_B_drift_predictions.csv"
)


# ============================================================
# FORECAST FIELDS
# ============================================================

FORECAST_FIELDS = [
    "component_id",
    "lot_id",
    "component_type",

    "temperature",
    "voltage",

    "iddq_0h_uA",
    "iddq_24h_uA",

    "predicted_168h_uA",
    "prediction_lower_uA",
    "prediction_upper_uA",

    "predicted_drift_uA",
    "predicted_drift_rate",
    "predicted_relative_drift",

    "safety_slope",
    "drift_slope_excess",

    "early_drift_flag",
    "predicted_limit_exceeded",
    "uncertainty_adjusted_failure",

    "absolute_limit_uA",
    "limit_margin_uA",
    "upper_bound_limit_margin_uA",

    "future_drift_risk",
    "module_b_status",
    "module_b_explanation",
]


# ============================================================
# HELPERS
# ============================================================

def prepare_dataframe():
    """
    Load the final Module B prediction output.
    """

    if not PREDICTION_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "Module B prediction results not found. "
                "Run Module B first to generate "
                "data/module_B/module_B_drift_predictions.csv"
            ),
        )

    try:
        df = pd.read_csv(PREDICTION_FILE)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read Module B predictions: {exc}",
        )

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail="Module B prediction file is empty.",
        )

    return df


def clean_value(value):
    """
    Convert numpy / pandas values into JSON-safe values.
    """

    if pd.isna(value):
        return None

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        return float(value)

    if isinstance(value, np.bool_):
        return bool(value)

    return value


def clean_dataframe(df):
    """
    Convert dataframe records into JSON-safe dictionaries.
    """

    records = df.to_dict(orient="records")

    cleaned = []

    for record in records:
        cleaned_record = {
            key: clean_value(value)
            for key, value in record.items()
        }

        cleaned.append(cleaned_record)

    return cleaned


def clean_forecast_dataframe(df):
    """
    Return only fields that are appropriate for
    prospective forecast display.
    """

    available_fields = [
        field
        for field in FORECAST_FIELDS
        if field in df.columns
    ]

    forecast_df = df[available_fields].copy()

    return clean_dataframe(forecast_df)


def normalize_flag(value):
    """
    Convert boolean-like values into 0/1.
    """

    if pd.isna(value):
        return 0

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, (int, float)):
        return int(value != 0)

    return int(
        str(value).strip().lower()
        in {
            "1",
            "true",
            "yes",
            "y",
            "detected",
        }
    )


# ============================================================
# GET ALL PREDICTIONS
# ============================================================

@router.get("/")
def get_predictions(
    page: int = 1,
    limit: int = 25,
    component_id: str | None = None,
    lot_id: str | None = None,
    risk_level: str | None = None,
    module_b_status: str | None = None,
):
    """
    Return prospective Module B drift predictions.

    Historical evaluation fields such as actual future
    measurements and prediction error are intentionally
    excluded from the response.
    """

    if page < 1:
        page = 1

    if limit < 1:
        limit = 25

    if limit > 200:
        limit = 200

    df = prepare_dataframe()

    # ========================================================
    # FILTER COMPONENT
    # ========================================================

    if component_id:

        df = df[
            df["component_id"]
            .astype(str)
            .str.upper()
            == component_id.upper()
        ]


    # ========================================================
    # FILTER LOT
    # ========================================================

    if lot_id:

        df = df[
            df["lot_id"]
            .astype(str)
            .str.upper()
            == lot_id.upper()
        ]


    # ========================================================
    # FILTER FUTURE DRIFT RISK
    # ========================================================

    if risk_level:

        if "future_drift_risk" not in df.columns:
            raise HTTPException(
                status_code=500,
                detail=(
                    "future_drift_risk column is missing "
                    "from Module B output."
                ),
            )

        df = df[
            df["future_drift_risk"]
            .astype(str)
            .str.upper()
            == risk_level.upper()
        ]


    # ========================================================
    # FILTER MODULE B STATUS
    # ========================================================

    if module_b_status:

        if "module_b_status" not in df.columns:
            raise HTTPException(
                status_code=500,
                detail=(
                    "module_b_status column is missing "
                    "from Module B output."
                ),
            )

        df = df[
            df["module_b_status"]
            .astype(str)
            .str.upper()
            == module_b_status.upper()
        ]


    # ========================================================
    # TOTAL
    # ========================================================

    total = len(df)


    # ========================================================
    # PAGINATION
    # ========================================================

    start = (page - 1) * limit
    end = start + limit

    page_df = df.iloc[start:end].copy()

    pages = (
        (total + limit - 1) // limit
        if total > 0
        else 0
    )


    # ========================================================
    # RETURN
    # ========================================================

    return {
        "total": int(total),
        "page": int(page),
        "limit": int(limit),
        "pages": int(pages),
        "data": clean_forecast_dataframe(page_df),
    }


# ============================================================
# GET SINGLE COMPONENT PREDICTION
# ============================================================

@router.get("/{component_id}")
def get_component_prediction(
    component_id: str,
):
    """
    Return prospective Module B prediction for one component.
    """

    df = prepare_dataframe()

    component_rows = df[
        df["component_id"]
        .astype(str)
        .str.upper()
        == component_id.upper()
    ]

    if component_rows.empty:

        raise HTTPException(
            status_code=404,
            detail=(
                f"No Module B prediction found for "
                f"{component_id}"
            ),
        )

    row = component_rows.iloc[0]

    available_fields = [
        field
        for field in FORECAST_FIELDS
        if field in row.index
    ]

    prediction = {
        key: clean_value(row[key])
        for key in available_fields
    }

    return {
        "component_id": component_id,
        "prediction": prediction,
    }


# ============================================================
# MODULE B SUMMARY
# ============================================================

@router.get("/summary/overview")
def get_prediction_summary():
    """
    Return an overall prospective forecast summary.
    """

    df = prepare_dataframe()

    total = len(df)


    # ========================================================
    # FUTURE DRIFT RISK
    # ========================================================

    risk_counts = {}

    if "future_drift_risk" in df.columns:

        risk_series = (
            df["future_drift_risk"]
            .astype(str)
            .str.upper()
        )

        risk_counts = {
            str(key): int(value)
            for key, value in risk_series.value_counts().items()
        }


    # ========================================================
    # MODULE B STATUS
    # ========================================================

    status_counts = {}

    if "module_b_status" in df.columns:

        status_series = (
            df["module_b_status"]
            .astype(str)
            .str.upper()
        )

        status_counts = {
            str(key): int(value)
            for key, value in status_series.value_counts().items()
        }


    # ========================================================
    # PREDICTED LIMIT EXCEEDED
    # ========================================================

    predicted_limit_exceeded = 0

    if "predicted_limit_exceeded" in df.columns:

        predicted_limit_exceeded = int(
            df["predicted_limit_exceeded"]
            .apply(normalize_flag)
            .sum()
        )


    # ========================================================
    # UNCERTAINTY ADJUSTED FAILURE
    # ========================================================

    uncertainty_adjusted_failure = 0

    if "uncertainty_adjusted_failure" in df.columns:

        uncertainty_adjusted_failure = int(
            df["uncertainty_adjusted_failure"]
            .apply(normalize_flag)
            .sum()
        )


    # ========================================================
    # EARLY DRIFT
    # ========================================================

    early_drift = 0

    if "early_drift_flag" in df.columns:

        early_drift = int(
            df["early_drift_flag"]
            .apply(normalize_flag)
            .sum()
        )


    # ========================================================
    # AVERAGE PREDICTED 168H IDDQ
    # ========================================================

    average_predicted_168h = None

    if "predicted_168h_uA" in df.columns:

        values = pd.to_numeric(
            df["predicted_168h_uA"],
            errors="coerce",
        ).dropna()

        if not values.empty:
            average_predicted_168h = float(
                values.mean()
            )


    # ========================================================
    # AVERAGE PREDICTED DRIFT
    # ========================================================

    average_predicted_drift = None

    if "predicted_drift_uA" in df.columns:

        values = pd.to_numeric(
            df["predicted_drift_uA"],
            errors="coerce",
        ).dropna()

        if not values.empty:
            average_predicted_drift = float(
                values.mean()
            )


    # ========================================================
    # MODEL INFORMATION
    # ========================================================

    model_name = None

    if "model_name" in df.columns:

        values = (
            df["model_name"]
            .dropna()
            .astype(str)
            .unique()
        )

        if len(values) > 0:
            model_name = values[0]


    # ========================================================
    # STAGE
    # ========================================================

    stage = None

    if "module_B_stage" in df.columns:

        values = pd.to_numeric(
            df["module_B_stage"],
            errors="coerce",
        ).dropna()

        if not values.empty:
            stage = int(values.max())


    # ========================================================
    # CUMULATIVE COMPONENTS
    # ========================================================

    cumulative_components = None

    if "cumulative_component_count" in df.columns:

        values = pd.to_numeric(
            df["cumulative_component_count"],
            errors="coerce",
        ).dropna()

        if not values.empty:
            cumulative_components = int(
                values.max()
            )


    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "total_components": int(total),

        "model_name": model_name,

        "stage": stage,

        "cumulative_components": cumulative_components,

        "average_predicted_168h_uA":
            average_predicted_168h,

        "average_predicted_drift_uA":
            average_predicted_drift,

        "predicted_limit_exceeded":
            predicted_limit_exceeded,

        "uncertainty_adjusted_failure":
            uncertainty_adjusted_failure,

        "early_drift":
            early_drift,

        "future_drift_risk":
            risk_counts,

        "module_b_status":
            status_counts,
    }