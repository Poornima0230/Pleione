from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query


router = APIRouter(
    prefix="/api/risk",
    tags=["Risk"],
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

RISK_FILE = (
    BASE_DIR
    / "data"
    / "risk"
    / "overall_risk_results.csv"
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
    "component_id",
    "lot_id",
    "risk_score",
    "qa_classification",
    "final_decision",
]


# ============================================================
# HELPERS
# ============================================================

def normalize_screening_decision(value) -> str:
    """
    Convert the backend's different decision labels into
    the three frontend screening states:

        PASS
        REVIEW
        REJECT
    """

    if pd.isna(value):
        return "PASS"

    value = str(value).strip().upper()

    if value in {
        "REJECT",
        "FAIL",
        "IMMEDIATE_REVIEW",
    }:
        return "REJECT"

    if value in {
        "REVIEW",
        "MONITOR",
        "ENHANCED_MONITORING",
        "PRIORITY_SCREENING",
    }:
        return "REVIEW"

    return "PASS"


def normalize_qa_classification(value) -> str:
    """
    Keep the original QA classification while making
    the returned value consistent.
    """

    if pd.isna(value):
        return ""

    return str(value).strip().upper()


def get_risk_bucket(risk_score) -> str:
    """
    Convert numeric risk score into the existing
    risk-level buckets.
    """

    try:
        score = float(risk_score)
    except (TypeError, ValueError):
        return "LOW"

    if score >= 80:
        return "CRITICAL"

    if score >= 60:
        return "HIGH"

    if score >= 30:
        return "MEDIUM"

    return "LOW"


# ============================================================
# LOAD DATA
# ============================================================

def load_risk_data() -> pd.DataFrame:

    if not RISK_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Risk output file not found: {RISK_FILE}",
        )

    try:
        df = pd.read_csv(RISK_FILE)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read risk output: {exc}",
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
                "message": "Risk output is missing required columns",
                "missing_columns": missing,
            },
        )

    df = df.copy()

    # --------------------------------------------------------
    # Clean identifiers
    # --------------------------------------------------------

    df["component_id"] = df["component_id"].astype(str)
    df["lot_id"] = df["lot_id"].astype(str)

    # --------------------------------------------------------
    # Numeric risk score
    # --------------------------------------------------------

    df["risk_score"] = pd.to_numeric(
        df["risk_score"],
        errors="coerce",
    ).fillna(0)

    # --------------------------------------------------------
    # Original QA classification
    # --------------------------------------------------------

    df["qa_classification"] = df[
        "qa_classification"
    ].apply(normalize_qa_classification)

    # --------------------------------------------------------
    # Original final decision
    # --------------------------------------------------------

    df["final_decision"] = df[
        "final_decision"
    ].apply(
        lambda value: ""
        if pd.isna(value)
        else str(value).strip().upper()
    )

    # --------------------------------------------------------
    # Frontend-normalized screening decision
    # --------------------------------------------------------

    df["screening_decision"] = df[
        "final_decision"
    ].apply(normalize_screening_decision)

    # --------------------------------------------------------
    # Risk bucket
    # --------------------------------------------------------

    df["risk_bucket"] = df["risk_score"].apply(
        get_risk_bucket
    )

    # --------------------------------------------------------
    # One record per component
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=["component_id"],
        keep="last",
    )

    return df


# ============================================================
# DATAFRAME → JSON RECORDS
# ============================================================

def dataframe_to_records(df: pd.DataFrame):

    records = df.to_dict(orient="records")

    cleaned_records = []

    for record in records:

        cleaned = {}

        for key, value in record.items():

            if pd.isna(value):
                cleaned[key] = None

            elif hasattr(value, "item"):
                try:
                    cleaned[key] = value.item()
                except Exception:
                    cleaned[key] = value

            else:
                cleaned[key] = value

        # Make sure these are always available
        cleaned["screening_decision"] = (
            normalize_screening_decision(
                cleaned.get("final_decision")
            )
        )

        cleaned["risk_bucket"] = get_risk_bucket(
            cleaned.get("risk_score")
        )

        cleaned_records.append(cleaned)

    return cleaned_records


# ============================================================
# GET ALL RISK RECORDS
# ============================================================

@router.get("/")
def get_risk_records(
    page: int = Query(
        default=1,
        ge=1,
        description="Page number",
    ),

    limit: int = Query(
        default=25,
        ge=1,
        le=200,
        description="Records per page",
    ),

    risk_level: str | None = Query(
        default=None,
        description="Filter by risk bucket",
    ),

    search: str | None = Query(
        default=None,
        description="Search component ID",
    ),

    lot_id: str | None = Query(
        default=None,
        description="Filter by lot",
    ),

    screening_decision: str | None = Query(
        default=None,
        description="Filter by PASS, REVIEW, or REJECT",
    ),
):

    df = load_risk_data()

    # ========================================================
    # FILTER: RISK LEVEL
    # ========================================================

    if risk_level:

        normalized_risk = risk_level.strip().upper()

        valid_risk_levels = {
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        }

        if normalized_risk in valid_risk_levels:

            df = df[
                df["risk_bucket"] == normalized_risk
            ]

    # ========================================================
    # FILTER: SEARCH
    # ========================================================

    if search:

        search_value = search.strip().lower()

        df = df[
            df["component_id"]
            .str.lower()
            .str.contains(
                search_value,
                na=False,
            )
        ]

    # ========================================================
    # FILTER: LOT
    # ========================================================

    if lot_id:

        df = df[
            df["lot_id"].astype(str)
            == str(lot_id)
        ]

    # ========================================================
    # FILTER: SCREENING DECISION
    # ========================================================

    if screening_decision:

        normalized_decision = (
            screening_decision.strip().upper()
        )

        valid_decisions = {
            "PASS",
            "REVIEW",
            "REJECT",
        }

        if normalized_decision in valid_decisions:

            df = df[
                df["screening_decision"]
                == normalized_decision
            ]

    # ========================================================
    # SORT
    # ========================================================

    df = df.sort_values(
        by="risk_score",
        ascending=False,
    )

    # ========================================================
    # PAGINATION
    # ========================================================

    total = len(df)

    pages = (
        (total + limit - 1) // limit
        if total > 0
        else 1
    )

    start = (page - 1) * limit
    end = start + limit

    page_df = df.iloc[start:end]

    records = dataframe_to_records(page_df)

    return {
        "page": page,
        "limit": limit,
        "pages": pages,
        "total": total,
        "records": records,
    }


# ============================================================
# RISK SUMMARY
# ============================================================

@router.get("/summary")
def get_risk_summary():

    df = load_risk_data()

    total_components = len(df)

    # --------------------------------------------------------
    # Risk distribution
    # --------------------------------------------------------

    risk_distribution = {
        "LOW": int(
            (df["risk_bucket"] == "LOW").sum()
        ),
        "MEDIUM": int(
            (df["risk_bucket"] == "MEDIUM").sum()
        ),
        "HIGH": int(
            (df["risk_bucket"] == "HIGH").sum()
        ),
        "CRITICAL": int(
            (df["risk_bucket"] == "CRITICAL").sum()
        ),
    }

    # --------------------------------------------------------
    # Screening distribution
    # --------------------------------------------------------

    screening_distribution = {
        "PASS": int(
            (
                df["screening_decision"]
                == "PASS"
            ).sum()
        ),

        "REVIEW": int(
            (
                df["screening_decision"]
                == "REVIEW"
            ).sum()
        ),

        "REJECT": int(
            (
                df["screening_decision"]
                == "REJECT"
            ).sum()
        ),
    }

    # --------------------------------------------------------
    # Original backend decision distribution
    #
    # Keep this because Module C may contain MONITOR,
    # ENHANCED_MONITORING, etc.
    # --------------------------------------------------------

    raw_decision_distribution = (
        df["final_decision"]
        .value_counts()
        .to_dict()
    )

    # --------------------------------------------------------
    # Average risk
    # --------------------------------------------------------

    average_risk_score = (
        float(df["risk_score"].mean())
        if total_components > 0
        else 0.0
    )

    return {
        "total_components": total_components,

        "average_risk_score": round(
            average_risk_score,
            2,
        ),

        "risk_distribution": risk_distribution,

        "screening_distribution": (
            screening_distribution
        ),

        "raw_decision_distribution": (
            raw_decision_distribution
        ),
    }


# ============================================================
# SINGLE COMPONENT RISK
# ============================================================

@router.get("/{component_id}")
def get_component_risk(
    component_id: str,
):

    df = load_risk_data()

    component_df = df[
        df["component_id"].astype(str)
        == str(component_id)
    ]

    if component_df.empty:

        raise HTTPException(
            status_code=404,
            detail=(
                f"Risk data not found for "
                f"component {component_id}"
            ),
        )

    record = dataframe_to_records(
        component_df.iloc[:1]
    )[0]

    return record