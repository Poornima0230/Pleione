from pathlib import Path

import pandas as pd
import numpy as np


BASE_DIR = Path(__file__).resolve().parents[2]

DATA_FILE = (
    BASE_DIR
    / "data"
    / "sih_26170_burn_in_synthetic_dataset.csv"
)


def clean_value(value):
    """
    Convert pandas / NumPy values into
    standard Python values that FastAPI
    can safely serialize.
    """

    # None
    if value is None:
        return None

    # pandas / NumPy missing values
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    # NumPy boolean
    if isinstance(value, np.bool_):
        return bool(value)

    # NumPy integer
    if isinstance(value, np.integer):
        return int(value)

    # NumPy floating point
    if isinstance(value, np.floating):
        return float(value)

    # Normal Python values
    return value


def clean_records(records):
    """
    Convert every value in a list of dictionaries
    into JSON-safe Python values.
    """

    cleaned = []

    for record in records:

        cleaned_record = {}

        for key, value in record.items():

            cleaned_record[key] = clean_value(
                value
            )

        cleaned.append(
            cleaned_record
        )

    return cleaned


def load_components():

    df = pd.read_csv(
        DATA_FILE
    )

    columns = [
        "component_id",
        "lot_id",
        "component_type",
        "temperature_C",
        "voltage_V",
        "iddq_0h_uA",
        "iddq_24h_uA",
        "iddq_96h_uA",
        "iddq_168h_uA",
        "absolute_limit_uA",
        "ground_truth",
        "static_pass_168h",
        "drift_0_24_uA_per_h",
        "drift_24_96_uA_per_h",
        "drift_96_168_uA_per_h",
        "overall_drift_uA_per_h",
        "lot_baseline_mean_uA",
        "lot_baseline_std_uA",
        "iddq_24h_zscore",
        "iddq_96h_zscore",
        "iddq_168h_zscore",
    ]

    df = df[columns]

    return df