from pathlib import Path
from threading import Lock

import pandas as pd
from fastapi import APIRouter, HTTPException


router = APIRouter(
    prefix="/api/lots",
    tags=["Lots"],
)


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


_CACHE = None
_CACHE_SIGNATURE = None
_CACHE_LOCK = Lock()


def file_signature(path: Path):
    if not path.exists():
        return None

    stat = path.stat()
    return (
        stat.st_mtime_ns,
        stat.st_size,
    )


def current_signature():
    return (
        file_signature(MODULE_A_FILE),
        file_signature(MODULE_B_FILE),
        file_signature(MODULE_C_FILE),
    )


def clean_value(value):
    if pd.isna(value):
        return None

    if isinstance(value, float):
        return round(value, 6)

    return value


def require_columns(
    df: pd.DataFrame,
    required: list[str],
    source: str,
):
    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"{source} is missing required columns",
                "missing_columns": missing,
            },
        )


def build_cache():
    if not MODULE_A_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Module A output not found: {MODULE_A_FILE}",
        )

    if not MODULE_B_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Module B output not found: {MODULE_B_FILE}",
        )

    if not MODULE_C_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Module C output not found: {MODULE_C_FILE}",
        )

    try:
        module_a = pd.read_csv(MODULE_A_FILE)
        module_b = pd.read_csv(MODULE_B_FILE)
        module_c = pd.read_csv(MODULE_C_FILE)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read screening outputs: {exc}",
        )

    require_columns(
        module_a,
        [
            "component_id",
            "lot_id",
            "component_type",
            "temperature_C",
            "voltage_V",
            "iddq_0h_uA",
            "module_a_score",
            "module_a_status",
        ],
        "Module A",
    )

    require_columns(
        module_b,
        [
            "component_id",
            "failure_probability",
            "failure_risk",
            "predicted_168h_uA",
            "prediction_upper_uA",
            "absolute_limit_uA",
        ],
        "Module B",
    )

    require_columns(
        module_c,
        [
            "component_id",
            "final_decision",
            "future_risk",
            "evidence_level",
            "evidence_score",
        ],
        "Module C",
    )

    # ---------------------------------------------------------
    # NORMALIZE COMPONENT IDs
    # ---------------------------------------------------------

    for df in (module_a, module_b, module_c):
        df["component_id"] = (
            df["component_id"]
            .astype(str)
            .str.strip()
        )

    # ---------------------------------------------------------
    # REMOVE DUPLICATES
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # SELECT ONLY LOT-LEVEL INFORMATION WE NEED
    # ---------------------------------------------------------

    a = module_a[
        [
            "component_id",
            "lot_id",
            "component_type",
            "temperature_C",
            "voltage_V",
            "iddq_0h_uA",
            "module_a_score",
            "module_a_status",
        ]
    ].copy()

    b = module_b[
        [
            "component_id",
            "failure_probability",
            "failure_risk",
            "predicted_168h_uA",
            "prediction_upper_uA",
            "absolute_limit_uA",
        ]
    ].copy()

    c = module_c[
        [
            "component_id",
            "final_decision",
            "future_risk",
            "evidence_level",
            "evidence_score",
        ]
    ].copy()

    # ---------------------------------------------------------
    # MERGE A + B + C
    # ---------------------------------------------------------

    merged = a.merge(
        b,
        on="component_id",
        how="inner",
        validate="one_to_one",
    )

    merged = merged.merge(
        c,
        on="component_id",
        how="inner",
        validate="one_to_one",
    )

    if len(merged) != len(a):
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Module A/B/C component counts do not match",
                "module_a": len(a),
                "merged": len(merged),
            },
        )

    merged["lot_id"] = (
        merged["lot_id"]
        .astype(str)
        .str.strip()
    )

    # Numeric normalization
    numeric_columns = [
        "temperature_C",
        "voltage_V",
        "iddq_0h_uA",
        "module_a_score",
        "failure_probability",
        "predicted_168h_uA",
        "prediction_upper_uA",
        "absolute_limit_uA",
        "evidence_score",
    ]

    for column in numeric_columns:
        merged[column] = pd.to_numeric(
            merged[column],
            errors="coerce",
        )

    return merged


def get_data():
    global _CACHE
    global _CACHE_SIGNATURE

    signature = current_signature()

    with _CACHE_LOCK:
        if (
            _CACHE is None
            or _CACHE_SIGNATURE != signature
        ):
            _CACHE = build_cache()
            _CACHE_SIGNATURE = signature

    return _CACHE


def build_lot_summary(df: pd.DataFrame):
    lots = []

    for lot_id, lot_df in df.groupby(
        "lot_id",
        sort=True,
    ):
        component_count = len(lot_df)

        anomaly_count = int(
            lot_df["module_a_status"]
            .isin(["WATCH", "ANOMALOUS"])
            .sum()
        )

        anomalous_count = int(
            (
                lot_df["module_a_status"]
                == "ANOMALOUS"
            ).sum()
        )

        watch_count = int(
            (
                lot_df["module_a_status"]
                == "WATCH"
            ).sum()
        )

        pass_count = int(
            (
                lot_df["final_decision"]
                == "PASS"
            ).sum()
        )

        review_count = int(
            (
                lot_df["final_decision"]
                == "REVIEW"
            ).sum()
        )

        reject_count = int(
            (
                lot_df["final_decision"]
                == "REJECT"
            ).sum()
        )

        critical_count = int(
            (
                lot_df["future_risk"]
                == "CRITICAL"
            ).sum()
        )

        high_count = int(
            (
                lot_df["future_risk"]
                == "HIGH"
            ).sum()
        )

        medium_count = int(
            (
                lot_df["future_risk"]
                == "MEDIUM"
            ).sum()
        )

        low_count = int(
            (
                lot_df["future_risk"]
                .isin(["LOW", "VERY_LOW"])
            ).sum()
        )

        avg_iddq_0h = lot_df[
            "iddq_0h_uA"
        ].mean()

        avg_predicted_168h = lot_df[
            "predicted_168h_uA"
        ].mean()

        max_predicted_168h = lot_df[
            "predicted_168h_uA"
        ].max()

        limit_violations_predicted = int(
            (
                lot_df["predicted_168h_uA"]
                > lot_df["absolute_limit_uA"]
            ).sum()
        )

        lots.append(
            {
                "lot_id": str(lot_id),
                "component_count": component_count,

                "anomaly_count": anomaly_count,
                "anomalous_count": anomalous_count,
                "watch_count": watch_count,

                "pass_count": pass_count,
                "review_count": review_count,
                "reject_count": reject_count,

                "critical_count": critical_count,
                "high_count": high_count,
                "medium_count": medium_count,
                "low_count": low_count,

                "average_iddq_0h_uA": clean_value(
                    avg_iddq_0h
                ),

                "average_predicted_168h_uA": clean_value(
                    avg_predicted_168h
                ),

                "maximum_predicted_168h_uA": clean_value(
                    max_predicted_168h
                ),

                "predicted_limit_exceedance_count": (
                    limit_violations_predicted
                ),
            }
        )

    return lots


@router.get("/")
def get_lots():
    df = get_data()

    lots = build_lot_summary(df)

    return {
        "total_lots": len(lots),
        "total_components": int(len(df)),
        "lots": lots,
    }


@router.get("/{lot_id}")
def get_lot(lot_id: str):
    df = get_data()

    lot_id = lot_id.strip()

    lot_df = df[
        df["lot_id"].astype(str) == lot_id
    ].copy()

    if lot_df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Lot '{lot_id}' was not found.",
        )

    summary = build_lot_summary(lot_df)[0]

    return summary