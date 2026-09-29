from fastapi import APIRouter, HTTPException
from pathlib import Path

import pandas as pd


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


BASE_DIR = Path(__file__).resolve().parents[2]

# ============================================================
# CURRENT PIPELINE OUTPUTS
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
# HELPERS
# ============================================================

def load_csv(path: Path, name: str) -> pd.DataFrame:
    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"{name} file not found: {path}",
        )

    try:
        return pd.read_csv(path)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read {name}: {exc}",
        )


def require_columns(
    df: pd.DataFrame,
    columns: list[str],
    name: str,
):
    missing = [
        column
        for column in columns
        if column not in df.columns
    ]

    if missing:
        raise HTTPException(
            status_code=500,
            detail=(
                f"{name} is missing required columns: "
                + ", ".join(missing)
            ),
        )


def numeric_series(
    df: pd.DataFrame,
    column: str,
    default: float = 0.0,
) -> pd.Series:
    if column not in df.columns:
        return pd.Series(
            default,
            index=df.index,
            dtype=float,
        )

    return pd.to_numeric(
        df[column],
        errors="coerce",
    ).fillna(default)


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@router.get("/summary")
def get_dashboard_summary():

    try:
        # ====================================================
        # LOAD MODULE A
        # ====================================================

        module_a = load_csv(
            MODULE_A_FILE,
            "Module A",
        )

        require_columns(
            module_a,
            [
                "component_id",
                "lot_id",
                "module_a_score",
                "module_a_status",
            ],
            "Module A",
        )

        module_a = (
            module_a
            .drop_duplicates(
                subset=["component_id"],
                keep="last",
            )
            .copy()
        )

        # Normalize Module A fields
        module_a["module_a_score"] = numeric_series(
            module_a,
            "module_a_score",
        )

        module_a["module_a_status"] = (
            module_a["module_a_status"]
            .fillna("NORMAL")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        # ====================================================
        # LOAD MODULE B
        # ====================================================

        module_b = load_csv(
            MODULE_B_FILE,
            "Module B",
        )

        require_columns(
            module_b,
            [
                "component_id",
                "failure_probability",
                "failure_risk",
                "predicted_168h_uA",
                "prediction_upper_uA",
            ],
            "Module B",
        )

        module_b = (
            module_b
            .drop_duplicates(
                subset=["component_id"],
                keep="last",
            )
            .copy()
        )

        module_b["failure_probability"] = numeric_series(
            module_b,
            "failure_probability",
        )

        module_b["predicted_168h_uA"] = numeric_series(
            module_b,
            "predicted_168h_uA",
        )

        module_b["prediction_upper_uA"] = numeric_series(
            module_b,
            "prediction_upper_uA",
        )

        module_b["failure_risk"] = (
            module_b["failure_risk"]
            .fillna("VERY_LOW")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        # ====================================================
        # LOAD MODULE C
        # ====================================================

        module_c = load_csv(
            MODULE_C_FILE,
            "Module C",
        )

        require_columns(
            module_c,
            [
                "component_id",
                "lot_id",
                "component_type",
                "final_decision",
                "future_risk",
            ],
            "Module C",
        )

        module_c = (
            module_c
            .drop_duplicates(
                subset=["component_id"],
                keep="last",
            )
            .copy()
        )

        module_c["final_decision"] = (
            module_c["final_decision"]
            .fillna("PASS")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        module_c["future_risk"] = (
            module_c["future_risk"]
            .fillna("LOW")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        # ====================================================
        # BASIC DATASET COUNTS
        # ====================================================

        total_components = int(len(module_c))

        total_lots = int(
            module_c["lot_id"]
            .dropna()
            .astype(str)
            .nunique()
        )

        # ====================================================
        # MERGE A + B + C
        # ====================================================

        a_columns = [
            "component_id",
            "module_a_score",
            "module_a_status",
        ]

        b_columns = [
            "component_id",
            "failure_probability",
            "failure_risk",
            "predicted_168h_uA",
            "prediction_upper_uA",
        ]

        c_columns = [
            "component_id",
            "lot_id",
            "component_type",
            "final_decision",
            "future_risk",
        ]

        combined = module_c[c_columns].merge(
            module_a[a_columns],
            on="component_id",
            how="left",
            validate="one_to_one",
        )

        combined = combined.merge(
            module_b[b_columns],
            on="component_id",
            how="left",
            validate="one_to_one",
        )

        # ====================================================
        # MODULE A ANOMALY STATUS
        # ====================================================

        module_a_status = (
            combined["module_a_status"]
            .fillna("NORMAL")
            .astype(str)
            .str.upper()
        )

        normal_count = int(
            (module_a_status == "NORMAL").sum()
        )

        watch_count = int(
            (module_a_status == "WATCH").sum()
        )

        anomalous_count = int(
            (module_a_status == "ANOMALOUS").sum()
        )

        total_anomalies = anomalous_count

        active_signals = int(
            (module_a_status != "NORMAL").sum()
        )

        anomaly_rate = (
            active_signals / total_components * 100
            if total_components > 0
            else 0.0
        )

        # ====================================================
        # MODULE C FINAL DECISION
        # ====================================================

        final_decision = (
            combined["final_decision"]
            .fillna("PASS")
            .astype(str)
            .str.upper()
        )

        passed = int(
            (final_decision == "PASS").sum()
        )

        review = int(
            (final_decision == "REVIEW").sum()
        )

        reject = int(
            (final_decision == "REJECT").sum()
        )

        # ====================================================
        # FUTURE RISK
        # ====================================================

        future_risk = (
            combined["future_risk"]
            .fillna("LOW")
            .astype(str)
            .str.upper()
        )

        critical = int(
            (future_risk == "CRITICAL").sum()
        )

        high = int(
            (future_risk == "HIGH").sum()
        )

        medium = int(
            (future_risk == "MEDIUM").sum()
        )

        low = int(
            (future_risk == "LOW").sum()
        )

        # ====================================================
        # HIGH-PRIORITY COMPONENTS
        #
        # Priority is based on actual current evidence:
        #
        # 1. REJECT
        # 2. REVIEW with high/critical future risk
        # 3. ANOMALOUS Module A
        # 4. Higher failure probability
        # ====================================================

        priority_df = combined.copy()

        priority_df["priority_rank"] = 0

        priority_df.loc[
            priority_df["final_decision"] == "REVIEW",
            "priority_rank",
        ] = 2

        priority_df.loc[
            priority_df["final_decision"] == "REJECT",
            "priority_rank",
        ] = 3

        priority_df.loc[
            priority_df["module_a_status"] == "ANOMALOUS",
            "priority_rank",
        ] = (
            priority_df.loc[
                priority_df["module_a_status"] == "ANOMALOUS",
                "priority_rank",
            ].clip(lower=2)
        )

        priority_df.loc[
            priority_df["future_risk"].isin(
                ["HIGH", "CRITICAL"]
            ),
            "priority_rank",
        ] = (
            priority_df.loc[
                priority_df["future_risk"].isin(
                    ["HIGH", "CRITICAL"]
                ),
                "priority_rank",
            ].clip(lower=2)
        )

        priority_df["failure_probability"] = numeric_series(
            priority_df,
            "failure_probability",
        )

        priority_df["module_a_score"] = numeric_series(
            priority_df,
            "module_a_score",
        )

        priority_df = priority_df.sort_values(
            by=[
                "priority_rank",
                "failure_probability",
                "module_a_score",
            ],
            ascending=[
                False,
                False,
                False,
            ],
        )

        # Only actual attention items.
        priority_df = priority_df[
            (
                priority_df["final_decision"].isin(
                    ["REVIEW", "REJECT"]
                )
            )
            |
            (
                priority_df["module_a_status"]
                == "ANOMALOUS"
            )
            |
            (
                priority_df["future_risk"].isin(
                    ["HIGH", "CRITICAL"]
                )
            )
        ]

        priority_components = []

        for _, row in priority_df.head(10).iterrows():

            probability = float(
                row["failure_probability"]
            )

            priority_components.append(
                {
                    "component_id": str(
                        row["component_id"]
                    ),

                    "lot_id": (
                        None
                        if pd.isna(row["lot_id"])
                        else str(row["lot_id"])
                    ),

                    "component_type": (
                        None
                        if pd.isna(row["component_type"])
                        else str(row["component_type"])
                    ),

                    "module_a_score": round(
                        float(row["module_a_score"]),
                        4,
                    ),

                    "module_a_status": str(
                        row["module_a_status"]
                    ),

                    "failure_probability": round(
                        probability,
                        4,
                    ),

                    "failure_risk": str(
                        row["failure_risk"]
                    ),

                    "final_decision": str(
                        row["final_decision"]
                    ),

                    "future_risk": str(
                        row["future_risk"]
                    ),
                }
            )

        # ====================================================
        # HIGHEST MODULE A ANOMALY EVIDENCE
        # ====================================================

        anomaly_queue = combined.copy()

        anomaly_queue["module_a_score"] = numeric_series(
            anomaly_queue,
            "module_a_score",
        )

        anomaly_queue = anomaly_queue[
            anomaly_queue["module_a_status"].isin(
                ["WATCH", "ANOMALOUS"]
            )
        ]

        anomaly_queue = anomaly_queue.sort_values(
            by="module_a_score",
            ascending=False,
        )

        highest_anomalies = []

        for _, row in anomaly_queue.head(5).iterrows():
            highest_anomalies.append(
                {
                    "component_id": str(
                        row["component_id"]
                    ),

                    "lot_id": (
                        None
                        if pd.isna(row["lot_id"])
                        else str(row["lot_id"])
                    ),

                    "component_type": (
                        None
                        if pd.isna(row["component_type"])
                        else str(row["component_type"])
                    ),

                    "module_a_score": round(
                        float(row["module_a_score"]),
                        4,
                    ),

                    "module_a_status": str(
                        row["module_a_status"]
                    ),

                    "final_decision": str(
                        row["final_decision"]
                    ),
                }
            )

        # ====================================================
        # DISTRIBUTIONS
        # ====================================================

        risk_distribution = {
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
        }

        screening_distribution = {
            "pass": passed,
            "review": review,
            "reject": reject,
        }

        anomaly_distribution = {
            "normal": normal_count,
            "watch": watch_count,
            "anomalous": anomalous_count,
        }

        # ====================================================
        # RETURN
        # ====================================================

        return {
            "total_components": total_components,
            "total_lots": total_lots,

            "active_signals": active_signals,
            "total_anomalies": total_anomalies,
            "anomaly_rate": round(
                anomaly_rate,
                2,
            ),

            "normal": normal_count,
            "watch": watch_count,
            "anomalous": anomalous_count,

            "high_risk_components": int(
                high + critical
            ),

            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,

            "passed": passed,
            "review": review,
            "reject": reject,

            "risk_distribution": risk_distribution,
            "screening_distribution": screening_distribution,
            "anomaly_distribution": anomaly_distribution,

            "risk_components": total_components,
            "risk_coverage": 100.0,

            "priority_components": priority_components,
            "highest_anomalies": highest_anomalies,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Dashboard summary failed: {exc}",
        )