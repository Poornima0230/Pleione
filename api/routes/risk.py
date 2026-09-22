from fastapi import APIRouter, HTTPException
from pathlib import Path

import pandas as pd
import numpy as np


router = APIRouter(
    prefix="/api/risk",
    tags=["Risk Assessment"]
)


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)


RISK_FILE = (
    BASE_DIR
    / "data"
    / "final_risk_assessment.csv"
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


def load_risk_data():

    if not RISK_FILE.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Final risk assessment file "
                "not found"
            )
        )

    try:

        df = pd.read_csv(
            RISK_FILE
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to read risk assessment: {e}"
            )
        )

    if "component_id" not in df.columns:

        raise HTTPException(
            status_code=500,
            detail=(
                "component_id column is missing "
                "from final risk assessment"
            )
        )

    return df


def build_summary(df):

    total = len(df)

    def count_value(
        column,
        value
    ):

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

    critical = count_value(
        "final_risk_level",
        "CRITICAL"
    )

    high = count_value(
        "final_risk_level",
        "HIGH"
    )

    medium = count_value(
        "final_risk_level",
        "MEDIUM"
    )

    low = count_value(
        "final_risk_level",
        "LOW"
    )

    failure_predicted = count_value(
        "future_failure_predicted",
        True
    )

    early_drift = count_value(
        "early_drift_flag",
        True
    )

    if (
        "risk_score" in df.columns
        and len(df) > 0
    ):

        average_risk = float(
            pd.to_numeric(
                df["risk_score"],
                errors="coerce"
            )
            .mean()
        )

    else:

        average_risk = 0.0

    if (
        "predicted_limit_exceeded"
        in df.columns
    ):

        predicted_limit_exceeded = int(
            pd.to_numeric(
                df[
                    "predicted_limit_exceeded"
                ],
                errors="coerce"
            )
            .fillna(0)
            .astype(bool)
            .sum()
        )

    else:

        predicted_limit_exceeded = 0

    return {
        "total_components": total,

        "critical": critical,

        "high": high,

        "medium": medium,

        "low": low,

        "failure_predicted":
            failure_predicted,

        "early_drift":
            early_drift,

        "predicted_limit_exceeded":
            predicted_limit_exceeded,

        "average_risk":
            round(
                average_risk,
                3
            ),
    }


@router.get("/")
def get_risk_assessment(
    page: int = 1,
    limit: int = 1000,
    risk_level: str = "",
    search: str = "",
    lot_id: str = "",
):

    df = load_risk_data()

    if page < 1:
        page = 1

    if limit < 1:
        limit = 100

    if limit > 5000:
        limit = 5000

    filtered = df.copy()


    # -----------------------------------------------------
    # Search
    # -----------------------------------------------------

    if search.strip():

        search_value = (
            search
            .strip()
            .lower()
        )

        component_match = (
            filtered[
                "component_id"
            ]
            .astype(str)
            .str.lower()
            .str.contains(
                search_value,
                na=False
            )
        )

        if "lot_id" in filtered.columns:

            lot_match = (
                filtered[
                    "lot_id"
                ]
                .astype(str)
                .str.lower()
                .str.contains(
                    search_value,
                    na=False
                )
            )

            filtered = filtered[
                component_match
                | lot_match
            ]

        else:

            filtered = filtered[
                component_match
            ]


    # -----------------------------------------------------
    # Risk level
    # -----------------------------------------------------

    if (
        risk_level.strip()
        and
        "final_risk_level"
        in filtered.columns
    ):

        filtered = filtered[
            filtered[
                "final_risk_level"
            ]
            .astype(str)
            .str.upper()
            ==
            risk_level
            .strip()
            .upper()
        ]


    # -----------------------------------------------------
    # Lot
    # -----------------------------------------------------

    if (
        lot_id.strip()
        and
        "lot_id"
        in filtered.columns
    ):

        filtered = filtered[
            filtered[
                "lot_id"
            ]
            .astype(str)
            ==
            lot_id.strip()
        ]


    # -----------------------------------------------------
    # Highest risk first
    # -----------------------------------------------------

    if "risk_score" in filtered.columns:

        filtered[
            "_risk_sort"
        ] = pd.to_numeric(
            filtered[
                "risk_score"
            ],
            errors="coerce"
        )

        filtered = (
            filtered
            .sort_values(
                "_risk_sort",
                ascending=False
            )
            .drop(
                columns=["_risk_sort"]
            )
        )


    total = len(filtered)

    start = (
        page - 1
    ) * limit

    end = start + limit

    page_df = filtered.iloc[
        start:end
    ]


    records = [
        clean_record(record)
        for record
        in page_df.to_dict(
            orient="records"
        )
    ]


    return {
        "data": records,

        "total": total,

        "page": page,

        "limit": limit,

        "pages": (
            (
                total
                + limit
                - 1
            )
            // limit
            if total
            else 0
        ),

        "summary":
            build_summary(df),
    }


@router.get("/summary")
def get_risk_summary():

    df = load_risk_data()

    return build_summary(
        df
    )


@router.get("/{component_id}")
def get_component_risk(
    component_id: str
):

    df = load_risk_data()

    result = df[
        df[
            "component_id"
        ]
        .astype(str)
        ==
        str(component_id)
    ]

    if result.empty:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Risk assessment for "
                f"{component_id} was not found"
            )
        )

    record = result.iloc[0]

    return clean_record(
        record.to_dict()
    )