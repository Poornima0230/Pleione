from pathlib import Path
from threading import Lock

import numpy as np
import pandas as pd

from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/api/component-analysis",
    tags=["Component Analysis"],
)


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]


# ============================================================
# PIPELINE OUTPUTS
# ============================================================

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
# IN-MEMORY CACHE
# ============================================================

_CACHE = None
_CACHE_SIGNATURE = None
_CACHE_LOCK = Lock()


# ============================================================
# JSON CLEANING
# ============================================================

def clean_value(value):
    """
    Convert pandas / numpy values into JSON-safe values.
    """

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

    if isinstance(value, dict):
        return {
            str(key): clean_value(val)
            for key, val in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            clean_value(item)
            for item in value
        ]

    if isinstance(value, np.ndarray):
        return [
            clean_value(item)
            for item in value.tolist()
        ]

    return value


def clean_record(record):
    """
    Convert a pandas Series into a JSON-safe dictionary.
    """

    return {
        str(column): clean_value(value)
        for column, value in record.items()
    }


# ============================================================
# FILE SIGNATURE
# ============================================================

def get_file_signature(path: Path):
    """
    Used to detect whether a pipeline output changed.

    If a CSV changes, the cache is automatically rebuilt.
    """

    if not path.exists():
        return None

    stat = path.stat()

    return (
        stat.st_mtime_ns,
        stat.st_size,
    )


def get_cache_signature():
    return (
        get_file_signature(MODULE_A_FILE),
        get_file_signature(MODULE_B_FILE),
        get_file_signature(MODULE_C_FILE),
    )


# ============================================================
# CSV LOADING
# ============================================================

def load_csv(path: Path, source_name: str):
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                f"{source_name} output not found: "
                f"{path}"
            ),
        )

    try:
        return pd.read_csv(path)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to read {source_name} output: "
                f"{str(exc)}"
            ),
        )


# ============================================================
# INDEX BUILDING
# ============================================================

def build_index(df: pd.DataFrame, source_name: str):
    """
    Build:

        component_id -> pandas Series

    once.

    This avoids filtering a 10,000-row DataFrame on every
    component investigation request.
    """

    if "component_id" not in df.columns:
        raise HTTPException(
            status_code=500,
            detail=(
                f"{source_name} output does not contain "
                "component_id"
            ),
        )

    working = df.copy()

    working["component_id"] = (
        working["component_id"]
        .astype(str)
        .str.strip()
    )

    duplicates = working["component_id"].duplicated()

    if duplicates.any():
        duplicate_count = int(duplicates.sum())

        raise HTTPException(
            status_code=500,
            detail=(
                f"{source_name} contains "
                f"{duplicate_count} duplicate component_id "
                "values."
            ),
        )

    return {
        row["component_id"]: row
        for _, row in working.iterrows()
    }


# ============================================================
# BUILD COMPLETE CACHE
# ============================================================

def build_cache():
    """
    Load all pipeline outputs once and create O(1)-style
    component lookup indexes.
    """

    module_a_df = load_csv(
        MODULE_A_FILE,
        "Module A",
    )

    module_b_df = load_csv(
        MODULE_B_FILE,
        "Module B",
    )

    module_c_df = load_csv(
        MODULE_C_FILE,
        "Module C",
    )

    module_a_index = build_index(
        module_a_df,
        "Module A",
    )

    module_b_index = build_index(
        module_b_df,
        "Module B",
    )

    module_c_index = build_index(
        module_c_df,
        "Module C",
    )

    # --------------------------------------------------------
    # Verify that the three pipeline outputs describe the
    # same component population.
    # --------------------------------------------------------

    ids_a = set(module_a_index.keys())
    ids_b = set(module_b_index.keys())
    ids_c = set(module_c_index.keys())

    if ids_a != ids_b:
        raise HTTPException(
            status_code=500,
            detail=(
                "Module A and Module B component IDs "
                "do not match."
            ),
        )

    if ids_a != ids_c:
        raise HTTPException(
            status_code=500,
            detail=(
                "Module A and Module C component IDs "
                "do not match."
            ),
        )

    return {
        "module_a": module_a_index,
        "module_b": module_b_index,
        "module_c": module_c_index,
        "count": len(ids_a),
    }


def get_pipeline_cache():
    """
    Return cached pipeline data.

    The CSVs are only reloaded when their modification time
    or file size changes.
    """

    global _CACHE
    global _CACHE_SIGNATURE

    current_signature = get_cache_signature()

    if current_signature is None:
        raise HTTPException(
            status_code=404,
            detail="One or more pipeline output files are missing.",
        )

    if (
        _CACHE is not None
        and _CACHE_SIGNATURE == current_signature
    ):
        return _CACHE

    with _CACHE_LOCK:

        # Another request may have rebuilt the cache while
        # this request was waiting for the lock.
        current_signature = get_cache_signature()

        if (
            _CACHE is not None
            and _CACHE_SIGNATURE == current_signature
        ):
            return _CACHE

        _CACHE = build_cache()
        _CACHE_SIGNATURE = current_signature

        return _CACHE


# ============================================================
# MODULE A
# ============================================================

def get_module_a_data(record):
    """
    Deployment-time anomaly evidence.

    Module A uses 0H information only.
    """

    required_columns = [
        "component_id",
        "module_a_score",
        "module_a_status",
        "peer_source",
    ]

    missing = [
        column
        for column in required_columns
        if column not in record.index
    ]

    if missing:
        raise HTTPException(
            status_code=500,
            detail=(
                "Module A output is missing required columns: "
                + ", ".join(missing)
            ),
        )

    component_fields = [
        "component_id",
        "lot_id",
        "component_type",
        "temperature_C",
        "voltage_V",
        "iddq_0h_uA",
        "leakage_0h_uA",
    ]

    component = {}

    for field in component_fields:
        if field in record.index:
            component[field] = clean_value(
                record.get(field)
            )

    module_a_fields = [
        "module_a_score",
        "module_a_status",
        "peer_source",
    ]

    module_a = {}

    for field in module_a_fields:
        if field in record.index:
            module_a[field] = clean_value(
                record.get(field)
            )

    return component, module_a


# ============================================================
# MODULE B
# ============================================================

def get_module_b_data(record):
    """
    Deployment-time future prediction.

    Inputs are based on 0H + 24H.
    """

    allowed_fields = [

        # Operating context
        "component_id",
        "lot_id",
        "component_type",
        "temperature_C",
        "voltage_V",

        # Early measurements
        "iddq_0h_uA",
        "iddq_24h_uA",
        "leakage_0h_uA",
        "leakage_24h_uA",
        "delta_0_24",

        # Prediction
        "predicted_168h_uA",
        "prediction_lower_uA",
        "prediction_upper_uA",
        "prediction_interval_width_uA",

        # Future failure classifier
        "failure_probability",
        "predicted_future_violation",
        "failure_risk",

        # Specification
        "absolute_limit_uA",
    ]

    prediction = {}

    for field in allowed_fields:
        if field in record.index:
            prediction[field] = clean_value(
                record.get(field)
            )

    return prediction


# ============================================================
# MODULE C
# ============================================================

def get_module_c_data(record):
    """
    Module C is the final screening decision.

    It combines Module A + Module B + specification.
    """

    required_columns = [
        "component_id",
        "final_decision",
        "future_risk",
        "evidence_level",
        "evidence_score",
        "decision_reason",
        "investigation_summary",
        "recommended_action",
    ]

    missing = [
        column
        for column in required_columns
        if column not in record.index
    ]

    if missing:
        raise HTTPException(
            status_code=500,
            detail=(
                "Module C output is missing required columns: "
                + ", ".join(missing)
            ),
        )

    # --------------------------------------------------------
    # FINAL DECISION
    # --------------------------------------------------------

    risk = {
        "component_id": clean_value(
            record.get("component_id")
        ),

        "final_decision": clean_value(
            record.get("final_decision")
        ),

        "future_risk": clean_value(
            record.get("future_risk")
        ),

        "evidence_level": clean_value(
            record.get("evidence_level")
        ),

        "evidence_score": clean_value(
            record.get("evidence_score")
        ),

        # Human-readable explanation
        "decision_reason": clean_value(
            record.get("decision_reason")
        ),

        "investigation_summary": clean_value(
            record.get("investigation_summary")
        ),

        "recommended_action": clean_value(
            record.get("recommended_action")
        ),
    }

    # --------------------------------------------------------
    # Module A evidence carried into Module C
    # --------------------------------------------------------

    module_a_evidence_fields = [
        "module_a_score",
        "module_a_status",
        "peer_source",
        "module_a_watch_or_higher",
        "module_a_anomalous",
    ]

    for field in module_a_evidence_fields:
        if field in record.index:
            risk[field] = clean_value(
                record.get(field)
            )

    # --------------------------------------------------------
    # Module B evidence carried into Module C
    # --------------------------------------------------------

    module_b_evidence_fields = [
        "predicted_168h_uA",
        "prediction_lower_uA",
        "prediction_upper_uA",
        "prediction_interval_width_uA",
        "failure_probability",
        "predicted_future_violation",
        "failure_risk",
        "absolute_limit_uA",
    ]

    for field in module_b_evidence_fields:
        if field in record.index:
            risk[field] = clean_value(
                record.get(field)
            )

    # --------------------------------------------------------
    # Evidence flags
    # --------------------------------------------------------

    evidence_flags = [
        "point_prediction_exceeds_limit",
        "uncertainty_crosses_limit",
        "classifier_high_risk",
        "classifier_medium_or_higher",
    ]

    for field in evidence_flags:
        if field in record.index:
            risk[field] = clean_value(
                record.get(field)
            )

    return risk


# ============================================================
# INVESTIGATION OBJECT
# ============================================================

def build_investigation(
    component,
    module_a,
    prediction,
    risk,
):
    """
    Build a frontend-friendly investigation object.

    This intentionally duplicates the important final
    decision fields so the UI does not need to understand
    internal Module C nesting.
    """

    return {
        "component_id": clean_value(
            component.get("component_id")
        ),

        "lot_id": clean_value(
            component.get("lot_id")
        ),

        "component_type": clean_value(
            component.get("component_type")
        ),

        "temperature_C": clean_value(
            component.get("temperature_C")
        ),

        "voltage_V": clean_value(
            component.get("voltage_V")
        ),

        # ----------------------------------------------------
        # Final decision
        # ----------------------------------------------------

        "final_decision": clean_value(
            risk.get("final_decision")
        ),

        "future_risk": clean_value(
            risk.get("future_risk")
        ),

        "evidence_level": clean_value(
            risk.get("evidence_level")
        ),

        "evidence_score": clean_value(
            risk.get("evidence_score")
        ),

        # ----------------------------------------------------
        # Explanation
        # ----------------------------------------------------

        "decision_reason": clean_value(
            risk.get("decision_reason")
        ),

        "investigation_summary": clean_value(
            risk.get("investigation_summary")
        ),

        "recommended_action": clean_value(
            risk.get("recommended_action")
        ),

        # ----------------------------------------------------
        # Key prediction evidence
        # ----------------------------------------------------

        "failure_probability": clean_value(
            prediction.get("failure_probability")
        ),

        "failure_risk": clean_value(
            prediction.get("failure_risk")
        ),

        "predicted_168h_uA": clean_value(
            prediction.get("predicted_168h_uA")
        ),

        "prediction_lower_uA": clean_value(
            prediction.get("prediction_lower_uA")
        ),

        "prediction_upper_uA": clean_value(
            prediction.get("prediction_upper_uA")
        ),

        "absolute_limit_uA": clean_value(
            prediction.get("absolute_limit_uA")
        ),
    }


# ============================================================
# MAIN ENDPOINT
# ============================================================

@router.get("/{component_id}")
def get_component_analysis(
    component_id: str,
):
    """
    Return complete deployment-time investigation data
    for one component.

    Deployment-time information boundary:

        Module A:
            0H

        Module B:
            0H + 24H

        Module C:
            Module A + Module B + specification

    Actual 96H / 168H measurements and ground truth are
    never used as live decision inputs or returned here.
    """

    component_id = component_id.strip()

    if not component_id:
        raise HTTPException(
            status_code=400,
            detail="component_id cannot be empty",
        )

    try:

        # ----------------------------------------------------
        # Get cached pipeline indexes
        # ----------------------------------------------------

        cache = get_pipeline_cache()

        module_a_index = cache["module_a"]
        module_b_index = cache["module_b"]
        module_c_index = cache["module_c"]

        # ----------------------------------------------------
        # Component existence
        # ----------------------------------------------------

        if component_id not in module_a_index:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Component {component_id} "
                    "was not found in Module A output"
                ),
            )

        if component_id not in module_b_index:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Component {component_id} "
                    "was not found in Module B output"
                ),
            )

        if component_id not in module_c_index:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Component {component_id} "
                    "was not found in Module C output"
                ),
            )

        # ----------------------------------------------------
        # Retrieve records
        # ----------------------------------------------------

        module_a_record = module_a_index[
            component_id
        ]

        module_b_record = module_b_index[
            component_id
        ]

        module_c_record = module_c_index[
            component_id
        ]

        # ----------------------------------------------------
        # Build response sections
        # ----------------------------------------------------

        component, module_a = get_module_a_data(
            module_a_record
        )

        prediction = get_module_b_data(
            module_b_record
        )

        risk = get_module_c_data(
            module_c_record
        )

        investigation = build_investigation(
            component,
            module_a,
            prediction,
            risk,
        )

        # ----------------------------------------------------
        # Final response
        # ----------------------------------------------------

        response = {
            "component": component,
            "module_a": module_a,
            "prediction": prediction,
            "risk": risk,
            "investigation": investigation,
        }

        return clean_value(response)

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to load component analysis: "
                f"{str(exc)}"
            ),
        )