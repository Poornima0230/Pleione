from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/components", tags=["components"])


# ============================================================
# PROJECT ROOT
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

MODULE_A_FILE = (
    BASE_DIR
    / "data"
    / "module_A"
    / "module_A_all_predictions.csv"
)

MODULE_B_FILE = (
    BASE_DIR
    / "data"
    / "module_B"
    / "module_B_predictions.csv"
)

MODULE_C_FILE = (
    BASE_DIR
    / "data"
    / "module_C"
    / "module_C_all_results.csv"
)


# ============================================================
# LOAD COMPLETE COMPONENT DATA
# ============================================================

def load_components() -> pd.DataFrame:
    """
    Load the complete 10,000-component screening dataset.

    Module A:
        0h anomaly evidence

    Module B:
        0h + 24h future prediction

    Module C:
        Final screening decision

    All three outputs are merged using component_id.
    """

    # --------------------------------------------------------
    # Check files
    # --------------------------------------------------------

    if not MODULE_A_FILE.exists():
        raise FileNotFoundError(
            f"Module A output not found: {MODULE_A_FILE}"
        )

    if not MODULE_B_FILE.exists():
        raise FileNotFoundError(
            f"Module B output not found: {MODULE_B_FILE}"
        )

    if not MODULE_C_FILE.exists():
        raise FileNotFoundError(
            f"Module C output not found: {MODULE_C_FILE}"
        )

    # --------------------------------------------------------
    # Read model outputs
    # --------------------------------------------------------

    module_a = pd.read_csv(MODULE_A_FILE)
    module_b = pd.read_csv(MODULE_B_FILE)
    module_c = pd.read_csv(MODULE_C_FILE)

    # --------------------------------------------------------
    # Basic validation
    # --------------------------------------------------------

    if "component_id" not in module_a.columns:
        raise ValueError(
            "Module A output is missing component_id"
        )

    if "component_id" not in module_b.columns:
        raise ValueError(
            "Module B output is missing component_id"
        )

    if "component_id" not in module_c.columns:
        raise ValueError(
            "Module C output is missing component_id"
        )

    # --------------------------------------------------------
    # Remove duplicate component IDs
    # --------------------------------------------------------

    module_a = module_a.drop_duplicates(
        subset=["component_id"],
        keep="last",
    )

    module_b = module_b.drop_duplicates(
        subset=["component_id"],
        keep="last",
    )

    module_c = module_c.drop_duplicates(
        subset=["component_id"],
        keep="last",
    )

    # --------------------------------------------------------
    # Module A
    # --------------------------------------------------------

    module_a_columns = [
        "component_id",
        "lot_id",
        "component_type",
        "temperature_C",
        "voltage_V",
        "iddq_0h_uA",
        "module_a_score",
        "module_a_status",
        "peer_source",
    ]

    module_a_columns = [
        column
        for column in module_a_columns
        if column in module_a.columns
    ]

    module_a = module_a[module_a_columns].copy()

    # --------------------------------------------------------
    # Module B
    # --------------------------------------------------------

    module_b_columns = [
        "component_id",
        "iddq_24h_uA",
        "predicted_168h_uA",
        "prediction_upper_uA",
        "failure_probability",
        "failure_risk",
    ]

    module_b_columns = [
        column
        for column in module_b_columns
        if column in module_b.columns
    ]

    module_b = module_b[module_b_columns].copy()

    # --------------------------------------------------------
    # Module C
    # --------------------------------------------------------

    module_c_columns = [
        "component_id",
        "absolute_limit_uA",
        "final_decision",
        "future_risk",
        "evidence_level",
        "evidence_score",
        "decision_reason",
        "investigation_summary",
        "recommended_action",
    ]

    module_c_columns = [
        column
        for column in module_c_columns
        if column in module_c.columns
    ]

    module_c = module_c[module_c_columns].copy()

    # --------------------------------------------------------
    # Merge Module A + Module B
    # --------------------------------------------------------

    data = module_a.merge(
        module_b,
        on="component_id",
        how="left",
        validate="one_to_one",
    )

    # --------------------------------------------------------
    # Merge Module C
    # --------------------------------------------------------

    data = data.merge(
        module_c,
        on="component_id",
        how="left",
        validate="one_to_one",
    )

    # --------------------------------------------------------
    # Validate final dataset
    # --------------------------------------------------------

    if len(data) != len(module_a):
        raise ValueError(
            "Component merge changed the number of Module A rows. "
            f"Module A={len(module_a)}, merged={len(data)}"
        )

    # --------------------------------------------------------
    # Normalize numeric columns
    # --------------------------------------------------------

    numeric_columns = [
        "temperature_C",
        "voltage_V",
        "iddq_0h_uA",
        "iddq_24h_uA",
        "module_a_score",
        "failure_probability",
        "predicted_168h_uA",
        "prediction_upper_uA",
        "absolute_limit_uA",
        "evidence_score",
    ]

    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(
                data[column],
                errors="coerce",
            )

    # --------------------------------------------------------
    # Normalize text columns
    # --------------------------------------------------------

    text_columns = [
        "component_id",
        "lot_id",
        "component_type",
        "module_a_status",
        "peer_source",
        "failure_risk",
        "final_decision",
        "future_risk",
        "evidence_level",
        "decision_reason",
        "investigation_summary",
        "recommended_action",
    ]

    for column in text_columns:
        if column in data.columns:
            data[column] = (
                data[column]
                .fillna("")
                .astype(str)
            )

    # --------------------------------------------------------
    # Sort by component ID
    # --------------------------------------------------------

    if "component_id" in data.columns:
        data = data.sort_values(
            by="component_id",
            kind="stable",
        )

    data = data.reset_index(drop=True)

    return data


# ============================================================
# JSON-SAFE VALUE
# ============================================================

def clean_value(value):
    """
    Convert pandas values into JSON-safe values.
    """

    if pd.isna(value):
        return None

    if isinstance(value, float):
        return round(value, 6)

    return value


# ============================================================
# GET COMPONENTS
# ============================================================

@router.get("/")
def get_components(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    component_id: str | None = None,
    lot_id: str | None = None,
    component_type: str | None = None,
    screening_decision: str | None = None,
):
    """
    Return paginated component screening data.

    Default:
        all 10,000 components

    Optional filters:
        component_id
        lot_id
        component_type
        screening_decision
    """

    # ========================================================
    # LOAD ALL COMPONENTS
    # ========================================================

    data = load_components()

    # Keep an unfiltered copy for filter options.
    all_data = data.copy()

    # ========================================================
    # FILTER OPTIONS
    # ========================================================

    filter_options = {
        "lots": sorted(
            [
                value
                for value in all_data["lot_id"]
                .dropna()
                .unique()
                if str(value).strip()
            ]
        ),
        "component_types": sorted(
            [
                value
                for value in all_data["component_type"]
                .dropna()
                .unique()
                if str(value).strip()
            ]
        ),
        "screening_decisions": [
            value
            for value in ["PASS", "REVIEW", "REJECT"]
            if value in set(
                all_data["final_decision"]
                .dropna()
                .astype(str)
                .str.upper()
            )
        ],
    }

    # ========================================================
    # COMPONENT ID FILTER
    # ========================================================

    if component_id:
        component_id_lower = (
            component_id.strip().lower()
        )

        data = data[
            data["component_id"]
            .str.lower()
            .str.contains(
                component_id_lower,
                na=False,
            )
        ]

    # ========================================================
    # LOT FILTER
    # ========================================================

    if lot_id:
        lot_id_lower = lot_id.strip().lower()

        data = data[
            data["lot_id"]
            .str.lower()
            == lot_id_lower
        ]

    # ========================================================
    # COMPONENT TYPE FILTER
    # ========================================================

    if component_type:
        component_type_lower = (
            component_type.strip().lower()
        )

        data = data[
            data["component_type"]
            .str.lower()
            == component_type_lower
        ]

    # ========================================================
    # SCREENING DECISION FILTER
    # ========================================================

    if screening_decision:
        decision_upper = (
            screening_decision.strip().upper()
        )

        data = data[
            data["final_decision"]
            .str.upper()
            == decision_upper
        ]

    # ========================================================
    # PAGINATION
    # ========================================================

    total = len(data)

    total_pages = (
        (total + limit - 1) // limit
        if total > 0
        else 0
    )

    if total_pages > 0 and page > total_pages:
        page = total_pages

    start = (page - 1) * limit
    end = start + limit

    page_data = data.iloc[start:end].copy()

    # ========================================================
    # DATAFRAME → JSON
    # ========================================================

    records = []

    for _, row in page_data.iterrows():

        record = {
            column: clean_value(row[column])
            for column in page_data.columns
        }

        records.append(record)

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "data": records,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "filter_options": filter_options,
    }