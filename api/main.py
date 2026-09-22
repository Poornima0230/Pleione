import json
from pathlib import Path

import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.routes import (
    dashboard,
    components,
    anomalies,
    lots,
    predictions,
    risk,
    screening_runs,
    reports,
    component_analysis,
    component_detail,
)

app = FastAPI(
    title="Pleione Reliability Intelligence API",
    version="1.0.0",
)

# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

app.include_router(dashboard.router)
app.include_router(components.router)
app.include_router(anomalies.router)
app.include_router(lots.router)
app.include_router(predictions.router)
app.include_router(risk.router)
app.include_router(screening_runs.router)
app.include_router(reports.router)
app.include_router(component_analysis.router)
app.include_router(component_detail.router)


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Pleione Reliability Intelligence API",
        "status": "running",
    }


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "Pleione backend",
    }
# ============================================================
# MODULE D — COMPONENT EXPLANATION
# ============================================================

MODULE_D_EXPLANATIONS_FILE = Path(
    "data/module_D_explanations.csv"
)

MODULE_D_PRIORITY_FILE = Path(
    "data/priority_screening_list.csv"
)


@app.get("/api/explanations/{component_id}")
def get_component_explanation(component_id: str):
    """
    Return Module D's generated explanation for one component.

    Module D is the source of explanation/rationale.
    This endpoint does not calculate anomaly, drift,
    prediction, risk, or screening decisions.

    It only reads Module D generated CSV files.
    """

    component_id = component_id.strip()

    # --------------------------------------------------------
    # Check Module D explanation file
    # --------------------------------------------------------

    if not MODULE_D_EXPLANATIONS_FILE.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                "Module D explanation file not found: "
                "data/module_D_explanations.csv"
            ),
        )

    try:
        # ----------------------------------------------------
        # Read Module D explanations
        # ----------------------------------------------------

        df = pd.read_csv(
            MODULE_D_EXPLANATIONS_FILE,
            dtype=str,
        )

        # ----------------------------------------------------
        # Validate required column
        # ----------------------------------------------------

        if "component_id" not in df.columns:
            raise HTTPException(
                status_code=500,
                detail=(
                    "module_D_explanations.csv does not "
                    "contain component_id"
                ),
            )

        # ----------------------------------------------------
        # Normalize component IDs
        # ----------------------------------------------------

        df["component_id"] = (
            df["component_id"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        # ----------------------------------------------------
        # Find requested component
        # ----------------------------------------------------

        matches = df[
            df["component_id"] == component_id
        ]

        if matches.empty:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No Module D explanation found "
                    f"for {component_id}"
                ),
            )

        row = matches.iloc[0]

        # ----------------------------------------------------
        # Parse structured explanation JSON
        # ----------------------------------------------------

        explanation = {}

        raw_json = row.get("explanation_json")

        if (
            raw_json is not None
            and not pd.isna(raw_json)
            and str(raw_json).strip()
        ):
            try:
                explanation = json.loads(
                    str(raw_json)
                )
            except json.JSONDecodeError:
                explanation = {}

        # ----------------------------------------------------
        # Build flat response
        # ----------------------------------------------------

        flat = {}

        for column in df.columns:

            if column == "explanation_json":
                continue

            value = row[column]

            try:
                if pd.isna(value):
                    value = None
            except Exception:
                pass

            flat[column] = value

        # ----------------------------------------------------
        # Convert numeric fields
        # ----------------------------------------------------

        numeric_fields = [
            "latest_observed_value",
            "latest_observed_time_hours",
            "spec_limit",
            "combined_anomaly_score",
            "prediction_horizon_hours",
            "predicted_value",
            "prediction_lower",
            "prediction_upper",
            "anomaly_factor",
            "drift_factor",
            "future_factor",
            "specification_factor",
            "risk_score",
        ]

        for field in numeric_fields:

            if (
                field in flat
                and flat[field] is not None
            ):
                try:
                    flat[field] = float(
                        flat[field]
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

        # ----------------------------------------------------
        # Load Module D priority information
        # ----------------------------------------------------

        priority = None

        if MODULE_D_PRIORITY_FILE.exists():

            priority_df = pd.read_csv(
                MODULE_D_PRIORITY_FILE,
                dtype=str,
            )

            if "component_id" in priority_df.columns:

                priority_df["component_id"] = (
                    priority_df["component_id"]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )

                priority_matches = priority_df[
                    priority_df["component_id"]
                    == component_id
                ]

                if not priority_matches.empty:

                    priority_row = (
                        priority_matches.iloc[0]
                    )

                    priority = {}

                    for column in priority_df.columns:

                        value = priority_row[column]

                        try:
                            if pd.isna(value):
                                value = None
                        except Exception:
                            pass

                        priority[column] = value

        # ----------------------------------------------------
        # Final response
        # ----------------------------------------------------

        return {
            "component_id": component_id,
            "explanation": explanation,
            "flat": flat,
            "priority": priority,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to load Module D explanation: "
                f"{str(exc)}"
            ),
        )