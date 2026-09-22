from fastapi import APIRouter, HTTPException
from pathlib import Path
import pandas as pd

from api.services.data_service import clean_records


router = APIRouter(
    prefix="/api/components",
    tags=["Component Investigation"]
)

BASE_DIR = Path(__file__).resolve().parents[2]

ANOMALY_FILE = (
    BASE_DIR
    / "data"
    / "module_A_anomaly_results.csv"
)


@router.get("/{component_id}")
def get_component(component_id: str):

    try:
        if not ANOMALY_FILE.exists():
            raise HTTPException(
                status_code=404,
                detail="Module A anomaly results not found"
            )

        df = pd.read_csv(ANOMALY_FILE)

        # Find requested component
        component = df[
            df["component_id"].astype(str) == str(component_id)
        ]

        if component.empty:
            raise HTTPException(
                status_code=404,
                detail=f"Component {component_id} not found"
            )

        # A component should have one record.
        record = component.iloc[0].to_dict()

        # Clean numpy/pandas values for JSON
        record = clean_records([record])[0]

        return {
            "component": record,

            "trajectory": {
                "iddq": [
                    {
                        "time": "0h",
                        "value": record.get("iddq_0h_uA")
                    },
                    {
                        "time": "24h",
                        "value": record.get("iddq_24h_uA")
                    },
                    {
                        "time": "96h",
                        "value": record.get("iddq_96h_uA")
                    },
                    {
                        "time": "168h",
                        "value": record.get("iddq_168h_uA")
                    }
                ],

                "leakage": [
                    {
                        "time": "0h",
                        "value": record.get("leakage_0h_uA")
                    },
                    {
                        "time": "24h",
                        "value": record.get("leakage_24h_uA")
                    },
                    {
                        "time": "96h",
                        "value": record.get("leakage_96h_uA")
                    },
                    {
                        "time": "168h",
                        "value": record.get("leakage_168h_uA")
                    }
                ]
            },

            "anomaly_evidence": {
                "max_robust_z": record.get("max_robust_z"),
                "statistical_evidence_count": record.get(
                    "statistical_evidence_count"
                ),
                "statistical_score": record.get(
                    "statistical_score"
                ),
                "temporal_anomaly_score": record.get(
                    "temporal_anomaly_score"
                ),
                "temporal_anomaly_flag": record.get(
                    "temporal_anomaly_flag"
                ),
                "isolation_forest_score": record.get(
                    "isolation_forest_score"
                ),
                "isolation_forest_flag": record.get(
                    "isolation_forest_flag"
                ),
                "combined_anomaly_score": record.get(
                    "combined_anomaly_score"
                ),
                "anomaly_flag": record.get(
                    "anomaly_flag"
                )
            },

            "risk": {
                "risk_score_100": record.get(
                    "risk_score_100"
                ),
                "risk_level": record.get(
                    "risk_level"
                ),
                "limit_violation": record.get(
                    "limit_violation"
                ),
                "limit_excess_uA": record.get(
                    "limit_excess_uA"
                ),
                "screening_decision": record.get(
                    "screening_decision"
                )
            },

            "explanation": record.get(
                "explanation"
            )
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )