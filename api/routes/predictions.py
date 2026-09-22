from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd
import numpy as np

from api.services.data_service import clean_records


router = APIRouter(
    prefix="/api/predictions",
    tags=["Predictions"]
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

    if isinstance(value, (np.integer,)):
        return int(value)

    if isinstance(value, (np.floating,)):
        return float(value)

    if isinstance(value, (np.bool_,)):
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
    Return Module B drift predictions.

    Supports:

        /api/predictions/

        /api/predictions/?page=1&limit=25

        /api/predictions/?component_id=C9

        /api/predictions/?lot_id=L1

        /api/predictions/?risk_level=HIGH

        /api/predictions/?module_b_status=EARLY_DRIFT_RISK
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
                detail="future_drift_risk column is missing from Module B output.",
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
                detail="module_b_status column is missing from Module B output.",
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
        "data": clean_dataframe(page_df),
    }


# ============================================================
# GET SINGLE COMPONENT PREDICTION
# ============================================================

@router.get("/{component_id}")
def get_component_prediction(
    component_id: str,
):
    """
    Return Module B prediction for one component.
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
            detail=f"No Module B prediction found for {component_id}",
        )

    row = component_rows.iloc[0]

    prediction = {
        key: clean_value(value)
        for key, value in row.to_dict().items()
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
    Return an overall Module B prediction summary.
    """

    df = prepare_dataframe()

    total = len(df)

    # --------------------------------------------------------
    # Future drift risk
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Module B status
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Predicted limit exceeded
    # --------------------------------------------------------

    predicted_limit_exceeded = 0

    if "predicted_limit_exceeded" in df.columns:

        predicted_limit_exceeded = int(
            pd.to_numeric(
                df["predicted_limit_exceeded"],
                errors="coerce"
            )
            .fillna(0)
            .astype(bool)
            .sum()
        )


    # --------------------------------------------------------
    # Uncertainty adjusted failure
    # --------------------------------------------------------

    uncertainty_adjusted_failure = 0

    if "uncertainty_adjusted_failure" in df.columns:

        uncertainty_adjusted_failure = int(
            pd.to_numeric(
                df["uncertainty_adjusted_failure"],
                errors="coerce"
            )
            .fillna(0)
            .astype(bool)
            .sum()
        )


    # --------------------------------------------------------
    # Average predicted 168h IDDQ
    # --------------------------------------------------------

    average_predicted_168h = None

    if "predicted_168h_uA" in df.columns:

        values = pd.to_numeric(
            df["predicted_168h_uA"],
            errors="coerce"
        ).dropna()

        if not values.empty:
            average_predicted_168h = float(
                values.mean()
            )


    # --------------------------------------------------------
    # Average predicted drift
    # --------------------------------------------------------

    average_predicted_drift = None

    if "predicted_drift_uA" in df.columns:

        values = pd.to_numeric(
            df["predicted_drift_uA"],
            errors="coerce"
        ).dropna()

        if not values.empty:
            average_predicted_drift = float(
                values.mean()
            )


    # --------------------------------------------------------
    # Model information
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Stage
    # --------------------------------------------------------

    stage = None

    if "module_B_stage" in df.columns:

        values = pd.to_numeric(
            df["module_B_stage"],
            errors="coerce"
        ).dropna()

        if not values.empty:
            stage = int(values.max())


    cumulative_components = None

    if "cumulative_component_count" in df.columns:

        values = pd.to_numeric(
            df["cumulative_component_count"],
            errors="coerce"
        ).dropna()

        if not values.empty:
            cumulative_components = int(values.max())


    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "total_components": int(total),

        "model_name": model_name,

        "stage": stage,

        "cumulative_components": cumulative_components,

        "average_predicted_168h_uA": average_predicted_168h,

        "average_predicted_drift_uA": average_predicted_drift,

        "predicted_limit_exceeded": predicted_limit_exceeded,

        "uncertainty_adjusted_failure": (
            uncertainty_adjusted_failure
        ),

        "future_drift_risk": risk_counts,

        "module_b_status": status_counts,
    }