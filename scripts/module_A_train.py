from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
MODULE_A_DIR = DATA_DIR / "module_A"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
MODULE_A_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# CONFIGURATION
# ============================================================

BATCH_FILES = [
    DATA_DIR / "batch_1.csv",
    DATA_DIR / "batch_2.csv",
    DATA_DIR / "batch_3.csv",
    DATA_DIR / "batch_4.csv",
    DATA_DIR / "batch_5.csv",
]

TRAIN_BATCHES = [1, 2, 3, 4]
TEST_BATCH = 5

TEMP_BIN = 1.0
VOLTAGE_BIN = 0.05

MIN_EXACT_PEER_SIZE = 10

# Status thresholds are learned from TRAIN data only.
WATCH_QUANTILE = 0.95
ANOMALOUS_QUANTILE = 0.99

EPS = 1e-6


# ============================================================
# LOAD DATA
# ============================================================

def load_batches():
    frames = []

    for batch_no, file_path in enumerate(BATCH_FILES, start=1):
        df = pd.read_csv(file_path)

        df["batch"] = batch_no

        frames.append(df)

    data = pd.concat(frames, ignore_index=True)

    return data


# ============================================================
# PEER GROUP
# ============================================================

def add_peer_columns(df):
    df = df.copy()

    df["temp_bin"] = (
        np.floor(df["temperature_C"] / TEMP_BIN) * TEMP_BIN
    )

    df["voltage_bin"] = (
        np.floor(df["voltage_V"] / VOLTAGE_BIN) * VOLTAGE_BIN
    )

    df["peer_key"] = (
        df["component_type"].astype(str)
        + "|"
        + df["temp_bin"].round(2).astype(str)
        + "|"
        + df["voltage_bin"].round(2).astype(str)
    )

    return df


# ============================================================
# BUILD PEER STATISTICS
# ============================================================

def build_peer_statistics(train_df):

    train_df = add_peer_columns(train_df)

    peer_stats = {}

    # Exact peer groups
    grouped = train_df.groupby("peer_key")

    for key, group in grouped:

        if len(group) < MIN_EXACT_PEER_SIZE:
            continue

        peer_stats[key] = {
            "n": int(len(group)),

            "iddq_median": float(
                group["iddq_0h_uA"].median()
            ),

            "iddq_mad": float(
                np.median(
                    np.abs(
                        group["iddq_0h_uA"]
                        - group["iddq_0h_uA"].median()
                    )
                )
            ),

            "leakage_median": float(
                group["leakage_0h_uA"].median()
            ),

            "leakage_mad": float(
                np.median(
                    np.abs(
                        group["leakage_0h_uA"]
                        - group["leakage_0h_uA"].median()
                    )
                )
            ),
        }

    # Component-type fallback statistics
    type_stats = {}

    grouped_type = train_df.groupby("component_type")

    for component_type, group in grouped_type:

        type_stats[str(component_type)] = {
            "n": int(len(group)),

            "iddq_median": float(
                group["iddq_0h_uA"].median()
            ),

            "iddq_mad": float(
                np.median(
                    np.abs(
                        group["iddq_0h_uA"]
                        - group["iddq_0h_uA"].median()
                    )
                )
            ),

            "leakage_median": float(
                group["leakage_0h_uA"].median()
            ),

            "leakage_mad": float(
                np.median(
                    np.abs(
                        group["leakage_0h_uA"]
                        - group["leakage_0h_uA"].median()
                    )
                ),
            ),
        }

    return peer_stats, type_stats


# ============================================================
# ROBUST Z SCORE
# ============================================================

def robust_z(value, median, mad):

    # MAD -> standard deviation approximation
    robust_scale = 1.4826 * mad

    if robust_scale < EPS:
        return 0.0

    return abs(value - median) / robust_scale


# ============================================================
# CALCULATE COMPONENT SCORE
# ============================================================

def calculate_score(row, peer_stats, type_stats):

    peer_key = row["peer_key"]

    peer_source = "EXACT"

    stats = peer_stats.get(peer_key)

    # Fallback to component type
    if stats is None:
        stats = type_stats.get(str(row["component_type"]))
        peer_source = "TYPE"

    if stats is None:
        return {
            "peer_source": "UNAVAILABLE",
            "peer_group_size": 0,
            "iddq_peer_z": 0.0,
            "leakage_peer_z": 0.0,
            "module_a_score": 0.0,
        }

    iddq_z = robust_z(
        row["iddq_0h_uA"],
        stats["iddq_median"],
        stats["iddq_mad"],
    )

    leakage_z = robust_z(
        row["leakage_0h_uA"],
        stats["leakage_median"],
        stats["leakage_mad"],
    )

    # IDDQ is the primary burn-in signal.
    # Leakage provides supporting evidence.
    score = (
        0.70 * iddq_z
        + 0.30 * leakage_z
    )

    return {
        "peer_source": peer_source,
        "peer_group_size": stats["n"],
        "iddq_peer_z": iddq_z,
        "leakage_peer_z": leakage_z,
        "module_a_score": score,
    }


# ============================================================
# STATUS
# ============================================================

def assign_status(score, watch_threshold, anomalous_threshold):

    if score >= anomalous_threshold:
        return "ANOMALOUS"

    if score >= watch_threshold:
        return "WATCH"

    return "NORMAL"


# ============================================================
# HUMAN-READABLE REASON
# ============================================================

def build_reason(row):

    iddq_z = row["iddq_peer_z"]
    leakage_z = row["leakage_peer_z"]

    if row["module_a_status"] == "NORMAL":
        return (
            "0h electrical behavior is consistent with the "
            "component's peer group."
        )

    if row["module_a_status"] == "WATCH":

        if iddq_z > leakage_z:
            return (
                "IDDQ at 0h shows a moderate deviation from "
                "the peer group."
            )

        return (
            "Leakage at 0h shows a moderate deviation from "
            "the peer group."
        )

    # ANOMALOUS

    if iddq_z >= 3 and leakage_z >= 3:
        return (
            "Both IDDQ and leakage show strong 0h deviation "
            "from the peer group."
        )

    if iddq_z >= 3:
        return (
            "IDDQ at 0h shows strong deviation from the "
            "component's peer group."
        )

    if leakage_z >= 3:
        return (
            "Leakage at 0h shows strong deviation from the "
            "component's peer group."
        )

    return (
        "0h electrical behavior shows strong peer-group "
        "deviation."
    )


# ============================================================
# SCORE DATASET
# ============================================================

def score_dataset(
    df,
    peer_stats,
    type_stats,
    watch_threshold,
    anomalous_threshold,
):

    df = add_peer_columns(df)

    results = []

    for _, row in df.iterrows():

        result = calculate_score(
            row,
            peer_stats,
            type_stats,
        )

        result["component_id"] = row["component_id"]

        results.append(result)

    score_df = pd.DataFrame(results)

    df = df.merge(
        score_df,
        on="component_id",
        how="left",
    )

    df["module_a_status"] = df["module_a_score"].apply(
        lambda x: assign_status(
            x,
            watch_threshold,
            anomalous_threshold,
        )
    )

    df["module_a_reason"] = df.apply(
        build_reason,
        axis=1,
    )

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("MODULE A — 0h PEER-AWARE ANOMALY DETECTION")
    print("=" * 70)

    data = load_batches()

    train_df = data[
        data["batch"].isin(TRAIN_BATCHES)
    ].copy()

    test_df = data[
        data["batch"] == TEST_BATCH
    ].copy()

    print(f"Total rows       : {len(data):,}")
    print(f"Training rows    : {len(train_df):,}")
    print(f"Unseen test rows : {len(test_df):,}")

    # --------------------------------------------------------
    # Build peer statistics using ONLY training data
    # --------------------------------------------------------

    peer_stats, type_stats = build_peer_statistics(
        train_df
    )

    print(
        f"Exact peer groups: {len(peer_stats):,}"
    )

    # --------------------------------------------------------
    # Score training data
    # --------------------------------------------------------

    train_scored = score_dataset(
        train_df,
        peer_stats,
        type_stats,
        WATCH_QUANTILE,
        ANOMALOUS_QUANTILE,
    )

    # --------------------------------------------------------
    # Learn thresholds from TRAINING scores only
    # --------------------------------------------------------

    watch_threshold = float(
        train_scored["module_a_score"].quantile(
            WATCH_QUANTILE
        )
    )

    anomalous_threshold = float(
        train_scored["module_a_score"].quantile(
            ANOMALOUS_QUANTILE
        )
    )

    print(
        f"Watch threshold     : {watch_threshold:.4f}"
    )

    print(
        f"Anomalous threshold : {anomalous_threshold:.4f}"
    )

    # --------------------------------------------------------
    # Score complete dataset using frozen statistics
    # --------------------------------------------------------

    all_scored = score_dataset(
        data,
        peer_stats,
        type_stats,
        watch_threshold,
        anomalous_threshold,
    )

    # --------------------------------------------------------
    # Save useful columns
    # --------------------------------------------------------

    output_columns = [
        "component_id",
        "lot_id",
        "component_type",
        "temperature_C",
        "voltage_V",
        "iddq_0h_uA",
        "leakage_0h_uA",

        "peer_source",
        "peer_group_size",

        "iddq_peer_z",
        "leakage_peer_z",

        "module_a_score",
        "module_a_status",
        "module_a_reason",

        "ground_truth",
        "absolute_limit_uA",
        "batch",
    ]

    output = all_scored[
        output_columns
    ].copy()

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    all_output_path = (
        MODULE_A_DIR
        / "module_A_all_predictions.csv"
    )

    batch5_output_path = (
        MODULE_A_DIR
        / "module_A_batch5_results.csv"
    )

    output.to_csv(
        all_output_path,
        index=False,
    )

    output[
        output["batch"] == TEST_BATCH
    ].to_csv(
        batch5_output_path,
        index=False,
    )

    # --------------------------------------------------------
    # Save model/config
    # --------------------------------------------------------

    model_path = (
        MODEL_DIR
        / "module_A_0h_peer_anomaly.joblib"
    )

    config_path = (
        MODEL_DIR
        / "module_A_0h_config.json"
    )

    joblib.dump(
        {
            "peer_stats": peer_stats,
            "type_stats": type_stats,
        },
        model_path,
    )

    config = {
        "module": "A",
        "purpose": "0h peer-aware current-state anomaly detection",

        "input_features": [
            "temperature_C",
            "voltage_V",
            "component_type",
            "iddq_0h_uA",
            "leakage_0h_uA",
        ],

        "forbidden_features": [
            "iddq_24h_uA",
            "iddq_96h_uA",
            "iddq_168h_uA",
            "leakage_24h_uA",
            "leakage_96h_uA",
            "leakage_168h_uA",
            "ground_truth",
            "absolute_limit_uA",
            "lot_id",
            "component_id",
        ],

        "temp_bin_C": TEMP_BIN,
        "voltage_bin_V": VOLTAGE_BIN,

        "watch_quantile": WATCH_QUANTILE,
        "anomalous_quantile": ANOMALOUS_QUANTILE,

        "watch_threshold": watch_threshold,
        "anomalous_threshold": anomalous_threshold,

        "score_formula": (
            "0.70 * IDDQ robust z + "
            "0.30 * leakage robust z"
        ),

        "statuses": {
            "NORMAL": "No meaningful 0h peer deviation",
            "WATCH": "Moderate 0h peer deviation",
            "ANOMALOUS": "Strong 0h peer deviation",
        },

        "important": (
            "Module A status is anomaly evidence only. "
            "It is not the final PASS/REVIEW/REJECT decision."
        ),
    }

    with open(
        config_path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            config,
            f,
            indent=2,
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("\nMODULE A STATUS DISTRIBUTION")
    print("-" * 40)

    print(
        output[
            output["batch"] == TEST_BATCH
        ]["module_a_status"]
        .value_counts()
    )

    print("\nPEER SOURCE")
    print("-" * 40)

    print(
        output[
            output["batch"] == TEST_BATCH
        ]["peer_source"]
        .value_counts()
    )

    print("\nSaved:")
    print(all_output_path)
    print(batch5_output_path)
    print(model_path)
    print(config_path)

    print("\nModule A complete.")


if __name__ == "__main__":
    main()