from fastapi import APIRouter, HTTPException

from pathlib import Path

import pandas as pd
import numpy as np


router = APIRouter(
    prefix="/api/component-analysis",
    tags=["Component Analysis"]
)


BASE_DIR = Path(
    __file__
).resolve().parents[2]


ANOMALY_FILE = (
    BASE_DIR
    / "data"
    / "module_A_anomaly_results.csv"
)

PREDICTION_FILE = (
    BASE_DIR
    / "data"
    / "module_B_drift_predictions.csv"
)

EXPLANATION_FILE = (
    BASE_DIR
    / "data"
    / "module_D_explanations.csv"
)


# ============================================================
# JSON SAFE VALUE CONVERTER
# ============================================================

def clean_value(value):

    # None
    if value is None:
        return None

    # NumPy boolean
    if isinstance(value, np.bool_):
        return bool(value)

    # NumPy integer
    if isinstance(value, np.integer):
        return int(value)

    # NumPy float
    if isinstance(value, np.floating):

        if np.isnan(value):
            return None

        return float(value)

    # Python float NaN
    if isinstance(value, float):

        if pd.isna(value):
            return None

        return value

    # Pandas NA / NaT
    try:

        if pd.isna(value):
            return None

    except (TypeError, ValueError):
        pass

    # Dictionary
    if isinstance(value, dict):

        return {
            str(key): clean_value(val)
            for key, val in value.items()
        }

    # List / tuple
    if isinstance(value, (list, tuple)):

        return [
            clean_value(item)
            for item in value
        ]

    # NumPy array
    if isinstance(value, np.ndarray):

        return [
            clean_value(item)
            for item in value.tolist()
        ]

    # Normal Python value
    return value


# ============================================================
# CONVERT PANDAS RECORD
# ============================================================

def clean_record(record):

    cleaned = {}

    for column, value in record.items():

        cleaned[str(column)] = clean_value(
            value
        )

    return cleaned


# ============================================================
# COMPONENT ANALYSIS
# ============================================================

@router.get("/{component_id}")
def get_component_analysis(
    component_id: str
):

    try:

        # ----------------------------------------------------
        # CHECK MODULE A
        # ----------------------------------------------------

        if not ANOMALY_FILE.exists():

            raise HTTPException(
                status_code=404,
                detail=(
                    "Module A anomaly results "
                    "not found"
                )
            )


        # ----------------------------------------------------
        # LOAD MODULE A
        # ----------------------------------------------------

        anomaly_df = pd.read_csv(
            ANOMALY_FILE
        )


        if "component_id" not in anomaly_df.columns:

            raise HTTPException(
                status_code=500,
                detail=(
                    "component_id column missing "
                    "from Module A results"
                )
            )


        # ----------------------------------------------------
        # FIND COMPONENT
        # ----------------------------------------------------

        result = anomaly_df[
            anomaly_df["component_id"]
            .astype(str)
            == str(component_id)
        ]


        if result.empty:

            raise HTTPException(
                status_code=404,
                detail=(
                    f"Component {component_id} "
                    "was not found"
                )
            )


        # ----------------------------------------------------
        # MODULE A RECORD
        # ----------------------------------------------------

        record = result.iloc[0]


        response = clean_record(
            record.to_dict()
        )


        # ====================================================
        # MODULE B — FUTURE DRIFT PREDICTION
        # ====================================================

        response["prediction"] = None


        if PREDICTION_FILE.exists():

            prediction_df = pd.read_csv(
                PREDICTION_FILE
            )


            if "component_id" in prediction_df.columns:

                prediction_result = (
                    prediction_df[
                        prediction_df["component_id"]
                        .astype(str)
                        == str(component_id)
                    ]
                )


                if not prediction_result.empty:

                    prediction_record = (
                        prediction_result.iloc[0]
                    )


                    prediction = (
                        clean_record(
                            prediction_record
                            .to_dict()
                        )
                    )


                    # Remove duplicate ID
                    prediction.pop(
                        "component_id",
                        None
                    )


                    response["prediction"] = (
                        prediction
                    )


        # ====================================================
        # MODULE D — EXPLAINABILITY
        # ====================================================

        response["explanation"] = None

        response["explainability"] = {}


        if EXPLANATION_FILE.exists():

            explanation_df = pd.read_csv(
                EXPLANATION_FILE
            )


            if "component_id" in explanation_df.columns:

                explanation_result = (
                    explanation_df[
                        explanation_df["component_id"]
                        .astype(str)
                        == str(component_id)
                    ]
                )


                if not explanation_result.empty:

                    explanation_record = (
                        explanation_result.iloc[0]
                    )


                    # ----------------------------------------
                    # MAIN EXPLANATION
                    # ----------------------------------------

                    possible_columns = [

                        "detailed_explanation",

                        "evidence_summary",

                        "explanation",

                        "reason",

                        "anomaly_explanation",

                        "model_explanation",

                        "explanation_text",

                    ]


                    for column in possible_columns:

                        if (
                            column
                            in explanation_df.columns
                        ):

                            value = (
                                explanation_record[
                                    column
                                ]
                            )


                            cleaned = clean_value(
                                value
                            )


                            if cleaned is not None:

                                response[
                                    "explanation"
                                ] = str(cleaned)

                                break


                    # ----------------------------------------
                    # OTHER EXPLAINABILITY DATA
                    # ----------------------------------------

                    for column in explanation_df.columns:

                        if column == "component_id":
                            continue


                        value = (
                            explanation_record[
                                column
                            ]
                        )


                        cleaned = clean_value(
                            value
                        )


                        if cleaned is not None:

                            response[
                                "explainability"
                            ][column] = cleaned


        # ====================================================
        # INVESTIGATION SUMMARY
        # ====================================================

        response["investigation"] = {

            "component_id":
                str(component_id),

            "lot_id":
                clean_value(
                    record.get("lot_id")
                ),

            "detection_engine":
                (
                    "Statistical Deviation + "
                    "Isolation Forest + "
                    "Temporal Drift"
                ),

            "screening_decision":
                clean_value(
                    record.get(
                        "screening_status"
                    )
                ),

            "severity":
                clean_value(
                    record.get(
                        "anomaly_severity"
                    )
                ),

            "latent_risk":
                clean_value(
                    record.get(
                        "latent_risk_flag"
                    )
                ),

            "anomaly_detected":
                clean_value(
                    record.get(
                        "combined_anomaly"
                    )
                ),

        }


        # ====================================================
        # FINAL SAFETY PASS
        # ====================================================

        response = clean_value(
            response
        )


        return response


    except HTTPException:

        raise


    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )