"""
PLEIONE — MODULE A + MODULE B DIAGNOSTIC ANALYSIS

Purpose
-------
Analyze whether current anomaly evidence from Module A and
future prediction/uncertainty from Module B can be combined
into a useful risk signal for Module C.

IMPORTANT INFORMATION BOUNDARY
------------------------------
Deployment-time inputs:

Module A:
    0h only

Module B:
    0h + 24h only

This script does NOT train a model.

Historical 168h information is used ONLY as an evaluation target.

It must never be used to construct a deployment feature.
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data"

MODULE_A_FILE = (
    DATA_DIR
    / "module_A"
    / "module_A_batch5_results.csv"
)

MODULE_B_FILE = (
    DATA_DIR
    / "module_B"
    / "module_B_batch5_results.csv"
)

OUTPUT_DIR = (
    DATA_DIR
    / "module_C"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# HELPERS
# ============================================================

def find_column(
    df: pd.DataFrame,
    candidates: list[str],
    description: str,
) -> str:
    """
    Find a column from a list of possible names.
    """

    for candidate in candidates:
        if candidate in df.columns:
            return candidate

    raise ValueError(
        f"Could not find {description}.\n"
        f"Tried: {candidates}\n"
        f"Available columns:\n"
        f"{list(df.columns)}"
    )


def print_header(title: str) -> None:

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def safe_percentage(
    numerator: int,
    denominator: int,
) -> float:

    if denominator == 0:
        return 0.0

    return (
        numerator
        / denominator
        * 100.0
    )


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    print_header(
        "PLEIONE — MODULE A + MODULE B DIAGNOSTICS"
    )

    print()
    print("Loading Module A:")
    print(MODULE_A_FILE)

    module_a = pd.read_csv(
        MODULE_A_FILE
    )

    print(
        f"Module A rows: {len(module_a):,}"
    )

    print()
    print("Loading Module B:")
    print(MODULE_B_FILE)

    module_b = pd.read_csv(
        MODULE_B_FILE
    )

    print(
        f"Module B rows: {len(module_b):,}"
    )

    print()
    print("Module A columns:")
    print(
        module_a.columns.tolist()
    )

    print()
    print("Module B columns:")
    print(
        module_b.columns.tolist()
    )

    return module_a, module_b


# ============================================================
# NORMALIZE MODULE A
# ============================================================

def normalize_module_a(
    module_a: pd.DataFrame,
) -> pd.DataFrame:

    component_col = find_column(
        module_a,
        [
            "component_id",
            "id",
        ],
        "Module A component ID",
    )

    status_col = find_column(
        module_a,
        [
            "module_a_status",
            "status",
        ],
        "Module A status",
    )

    score_col = find_column(
        module_a,
        [
            "module_a_score",
            "anomaly_score",
            "score",
            "robust_score",
        ],
        "Module A anomaly score",
    )

    peer_col = find_column(
        module_a,
        [
            "peer_source",
        ],
        "Module A peer source",
    )

    result = module_a[
        [
            component_col,
            status_col,
            score_col,
            peer_col,
        ]
    ].copy()

    result = result.rename(
        columns={
            component_col: "component_id",
            status_col: "module_a_status",
            score_col: "module_a_score",
            peer_col: "peer_source",
        }
    )

    return result


# ============================================================
# NORMALIZE MODULE B
# ============================================================

def normalize_module_b(
    module_b: pd.DataFrame,
) -> pd.DataFrame:

    component_col = find_column(
        module_b,
        [
            "component_id",
            "id",
        ],
        "Module B component ID",
    )

    prediction_col = find_column(
        module_b,
        [
            "predicted_168h_uA",
            "prediction_168h_uA",
            "predicted_168h",
            "prediction",
            "predicted_value",
        ],
        "Module B prediction",
    )

    actual_col = find_column(
        module_b,
        [
            "actual_168h_uA",
            "iddq_168h_uA",
            "actual_168h",
            "target",
        ],
        "actual 168h value",
    )

    lower_col = find_column(
        module_b,
        [
            "lower_bound_uA",
            "prediction_lower_uA",
            "lower_168h_uA",
            "lower_bound",
            "lower",
        ],
        "Module B lower conformal bound",
    )

    upper_col = find_column(
        module_b,
        [
            "upper_bound_uA",
            "prediction_upper_uA",
            "upper_168h_uA",
            "upper_bound",
            "upper",
        ],
        "Module B upper conformal bound",
    )

    result = module_b[
        [
            component_col,
            prediction_col,
            actual_col,
            lower_col,
            upper_col,
        ]
    ].copy()

    result = result.rename(
        columns={
            component_col: "component_id",
            prediction_col: "predicted_168h_uA",
            actual_col: "actual_168h_uA",
            lower_col: "lower_bound_uA",
            upper_col: "upper_bound_uA",
        }
    )

    return result


# ============================================================
# MERGE
# ============================================================

def merge_modules(
    module_a: pd.DataFrame,
    module_b: pd.DataFrame,
) -> pd.DataFrame:

    print_header(
        "MERGING MODULE A + MODULE B"
    )

    merged = pd.merge(
        module_a,
        module_b,
        on="component_id",
        how="inner",
        validate="one_to_one",
    )

    print()
    print(
        f"Merged rows: {len(merged):,}"
    )

    if len(merged) != len(module_a):
        print(
            "WARNING: Module A and Module B "
            "did not have identical component sets."
        )

    # --------------------------------------------------------
    # Evaluation-only target
    # --------------------------------------------------------

    merged["actual_violation"] = (
        merged["actual_168h_uA"]
        > 50.0
    )

    # --------------------------------------------------------
    # Deployment-time signals
    # --------------------------------------------------------

    # Point prediction crossing the specification.
    merged["prediction_violation"] = (
        merged["predicted_168h_uA"]
        > 50.0
    )

    # Conformal upper bound crossing the specification.
    #
    # This is an uncertainty-aware warning:
    #
    # prediction itself may be below 50,
    # but the plausible upper range reaches above 50.
    merged["interval_risk"] = (
        merged["upper_bound_uA"]
        > 50.0
    )

    # Distance of point prediction from the limit.
    merged["prediction_margin_uA"] = (
        50.0
        - merged["predicted_168h_uA"]
    )

    # Distance of upper bound from the limit.
    merged["upper_bound_margin_uA"] = (
        50.0
        - merged["upper_bound_uA"]
    )

    # --------------------------------------------------------
    # Combined evidence
    # --------------------------------------------------------

    merged["module_a_warning"] = (
        merged["module_a_status"]
        != "NORMAL"
    )

    merged["module_a_anomalous"] = (
        merged["module_a_status"]
        == "ANOMALOUS"
    )

    # --------------------------------------------------------
    # Evidence levels
    # --------------------------------------------------------

    def classify_evidence(row):

        a_status = row[
            "module_a_status"
        ]

        point_violation = row[
            "prediction_violation"
        ]

        interval_risk = row[
            "interval_risk"
        ]

        if (
            point_violation
            and a_status == "ANOMALOUS"
        ):
            return "STRONG"

        if point_violation:
            return "HIGH"

        if (
            interval_risk
            and a_status != "NORMAL"
        ):
            return "MEDIUM_HIGH"

        if interval_risk:
            return "MEDIUM"

        if a_status == "ANOMALOUS":
            return "MEDIUM"

        if a_status == "WATCH":
            return "LOW"

        return "LOW"

    merged["combined_evidence"] = (
        merged.apply(
            classify_evidence,
            axis=1,
        )
    )

    return merged


# ============================================================
# BASIC RESULTS
# ============================================================

def analyze_basic_results(
    df: pd.DataFrame,
) -> None:

    print_header(
        "BASIC MODULE A + MODULE B RESULTS"
    )

    total = len(df)

    actual = int(
        df["actual_violation"].sum()
    )

    prediction = int(
        df["prediction_violation"].sum()
    )

    interval = int(
        df["interval_risk"].sum()
    )

    module_a_warning = int(
        df["module_a_warning"].sum()
    )

    module_a_anomalous = int(
        df["module_a_anomalous"].sum()
    )

    print()
    print(
        f"Total components        : {total:,}"
    )

    print(
        f"Actual 168h violations  : {actual:,}"
    )

    print(
        f"Point prediction > 50   : {prediction:,}"
    )

    print(
        f"Upper interval > 50     : {interval:,}"
    )

    print(
        f"Module A WATCH+         : {module_a_warning:,}"
    )

    print(
        f"Module A ANOMALOUS      : {module_a_anomalous:,}"
    )

    # --------------------------------------------------------
    # Point prediction
    # --------------------------------------------------------

    tp = int(
        (
            df["prediction_violation"]
            & df["actual_violation"]
        ).sum()
    )

    fp = int(
        (
            df["prediction_violation"]
            & ~df["actual_violation"]
        ).sum()
    )

    fn = int(
        (
            ~df["prediction_violation"]
            & df["actual_violation"]
        ).sum()
    )

    precision = (
        tp / (tp + fp)
        if (tp + fp)
        else 0.0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn)
        else 0.0
    )

    print()
    print("POINT PREDICTION")

    print(
        f"TP        : {tp}"
    )

    print(
        f"FP        : {fp}"
    )

    print(
        f"FN        : {fn}"
    )

    print(
        f"Precision  : {precision:.4f}"
    )

    print(
        f"Recall     : {recall:.4f}"
    )

    # --------------------------------------------------------
    # Interval risk
    # --------------------------------------------------------

    interval_tp = int(
        (
            df["interval_risk"]
            & df["actual_violation"]
        ).sum()
    )

    interval_fp = int(
        (
            df["interval_risk"]
            & ~df["actual_violation"]
        ).sum()
    )

    interval_fn = int(
        (
            ~df["interval_risk"]
            & df["actual_violation"]
        ).sum()
    )

    interval_precision = (
        interval_tp
        / (interval_tp + interval_fp)
        if (interval_tp + interval_fp)
        else 0.0
    )

    interval_recall = (
        interval_tp
        / (interval_tp + interval_fn)
        if (interval_tp + interval_fn)
        else 0.0
    )

    print()
    print("CONFORMAL INTERVAL RISK")

    print(
        f"TP        : {interval_tp}"
    )

    print(
        f"FP        : {interval_fp}"
    )

    print(
        f"FN        : {interval_fn}"
    )

    print(
        f"Precision  : "
        f"{interval_precision:.4f}"
    )

    print(
        f"Recall     : "
        f"{interval_recall:.4f}"
    )


# ============================================================
# MODULE A × FUTURE FAILURE
# ============================================================

def analyze_module_a(
    df: pd.DataFrame,
) -> None:

    print_header(
        "MODULE A STATUS vs ACTUAL 168h VIOLATION"
    )

    summary = (
        df.groupby(
            "module_a_status"
        )
        .agg(
            components=(
                "component_id",
                "count",
            ),
            actual_violations=(
                "actual_violation",
                "sum",
            ),
        )
        .reset_index()
    )

    summary["violation_rate_%"] = (
        summary["actual_violations"]
        / summary["components"]
        * 100.0
    )

    print()
    print(
        summary.to_string(
            index=False,
            float_format=lambda x: f"{x:.2f}",
        )
    )


# ============================================================
# MODULE A + POINT PREDICTION
# ============================================================

def analyze_combined_signals(
    df: pd.DataFrame,
) -> None:

    print_header(
        "MODULE A + MODULE B COMBINED SIGNALS"
    )

    # --------------------------------------------------------
    # A status × point prediction
    # --------------------------------------------------------

    table = (
        df.groupby(
            [
                "module_a_status",
                "prediction_violation",
            ]
        )
        .agg(
            components=(
                "component_id",
                "count",
            ),
            actual_violations=(
                "actual_violation",
                "sum",
            ),
        )
        .reset_index()
    )

    table["actual_violation_rate_%"] = (
        table["actual_violations"]
        / table["components"]
        * 100.0
    )

    print()
    print(
        "Module A status × point prediction:"
    )

    print(
        table.to_string(
            index=False,
            float_format=lambda x: f"{x:.2f}",
        )
    )

    # --------------------------------------------------------
    # A status × interval risk
    # --------------------------------------------------------

    table2 = (
        df.groupby(
            [
                "module_a_status",
                "interval_risk",
            ]
        )
        .agg(
            components=(
                "component_id",
                "count",
            ),
            actual_violations=(
                "actual_violation",
                "sum",
            ),
        )
        .reset_index()
    )

    table2["actual_violation_rate_%"] = (
        table2["actual_violations"]
        / table2["components"]
        * 100.0
    )

    print()
    print(
        "Module A status × conformal interval:"
    )

    print(
        table2.to_string(
            index=False,
            float_format=lambda x: f"{x:.2f}",
        )
    )


# ============================================================
# EVIDENCE LEVEL ANALYSIS
# ============================================================

def analyze_evidence_levels(
    df: pd.DataFrame,
) -> None:

    print_header(
        "COMBINED EVIDENCE LEVELS"
    )

    summary = (
        df.groupby(
            "combined_evidence"
        )
        .agg(
            components=(
                "component_id",
                "count",
            ),
            actual_violations=(
                "actual_violation",
                "sum",
            ),
            mean_prediction=(
                "predicted_168h_uA",
                "mean",
            ),
            mean_upper_bound=(
                "upper_bound_uA",
                "mean",
            ),
        )
        .reset_index()
    )

    summary["violation_rate_%"] = (
        summary["actual_violations"]
        / summary["components"]
        * 100.0
    )

    order = [
        "LOW",
        "MEDIUM",
        "MEDIUM_HIGH",
        "HIGH",
        "STRONG",
    ]

    summary["order"] = (
        summary["combined_evidence"]
        .map(
            {
                name: index
                for index, name
                in enumerate(order)
            }
        )
    )

    summary = (
        summary
        .sort_values("order")
        .drop(columns=["order"])
    )

    print()
    print(
        summary.to_string(
            index=False,
            float_format=lambda x: f"{x:.2f}",
        )
    )


# ============================================================
# THRESHOLD EXPERIMENT
# ============================================================

def evaluate_upper_bound_thresholds(
    df: pd.DataFrame,
) -> None:

    print_header(
        "UPPER-BOUND THRESHOLD ANALYSIS"
    )

    print(
        """
This evaluates alternative future-risk thresholds.

IMPORTANT:
These are diagnostic thresholds only.
They are NOT yet Module C policy.
"""
    )

    thresholds = [
        40.0,
        42.0,
        44.0,
        45.0,
        46.0,
        48.0,
        50.0,
    ]

    rows = []

    for threshold in thresholds:

        predicted = (
            df["upper_bound_uA"]
            >= threshold
        )

        actual = (
            df["actual_violation"]
        )

        tp = int(
            (predicted & actual).sum()
        )

        fp = int(
            (predicted & ~actual).sum()
        )

        fn = int(
            (~predicted & actual).sum()
        )

        precision = (
            tp / (tp + fp)
            if (tp + fp)
            else 0.0
        )

        recall = (
            tp / (tp + fn)
            if (tp + fn)
            else 0.0
        )

        rows.append(
            {
                "upper_bound_threshold": threshold,
                "flagged": int(predicted.sum()),
                "TP": tp,
                "FP": fp,
                "FN": fn,
                "precision": precision,
                "recall": recall,
            }
        )

    result = pd.DataFrame(rows)

    print()
    print(
        result.to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )


# ============================================================
# FALSE NEGATIVE ANALYSIS
# ============================================================

def analyze_missed_failures(
    df: pd.DataFrame,
) -> None:

    print_header(
        "MISSED 168h FAILURES"
    )

    missed = df[
        df["actual_violation"]
        & ~df["prediction_violation"]
    ].copy()

    print()
    print(
        f"Missed failures: {len(missed):,}"
    )

    if len(missed) == 0:
        print(
            "No missed failures."
        )
        return

    print()
    print(
        "Module A status among missed failures:"
    )

    print(
        missed["module_a_status"]
        .value_counts()
        .to_string()
    )

    print()
    print(
        "Missed failures — prediction statistics:"
    )

    print(
        missed[
            [
                "predicted_168h_uA",
                "upper_bound_uA",
                "module_a_score",
            ]
        ]
        .describe()
        .to_string()
    )

    print()
    print(
        "Missed failures by ground truth:"
    )

    # ground_truth is expected to be present in Module B output
    # or not. This is evaluation-only and never a model input.
    if "ground_truth" in df.columns:

        print(
            missed["ground_truth"]
            .value_counts()
            .to_string()
        )

    print()
    print(
        "Lowest predicted values among missed failures:"
    )

    print(
        missed[
            [
                "component_id",
                "module_a_status",
                "module_a_score",
                "predicted_168h_uA",
                "upper_bound_uA",
                "actual_168h_uA",
            ]
        ]
        .sort_values(
            "actual_168h_uA",
            ascending=False,
        )
        .head(20)
        .to_string(
            index=False
        )
    )


# ============================================================
# SAVE DIAGNOSTIC DATASET
# ============================================================

def save_results(
    df: pd.DataFrame,
) -> None:

    output_path = (
        OUTPUT_DIR
        / "module_A_B_diagnostic_results.csv"
    )

    df.to_csv(
        output_path,
        index=False,
    )

    print()
    print(
        f"Diagnostic dataset saved:"
    )

    print(
        output_path
    )


# ============================================================
# MAIN
# ============================================================

def main():

    module_a_raw, module_b_raw = (
        load_data()
    )

    module_a = normalize_module_a(
        module_a_raw
    )

    module_b = normalize_module_b(
        module_b_raw
    )

    merged = merge_modules(
        module_a,
        module_b,
    )

    analyze_basic_results(
        merged
    )

    analyze_module_a(
        merged
    )

    analyze_combined_signals(
        merged
    )

    analyze_evidence_levels(
        merged
    )

    evaluate_upper_bound_thresholds(
        merged
    )

    analyze_missed_failures(
        merged
    )

    save_results(
        merged
    )

    print()
    print("=" * 70)
    print("MODULE A + MODULE B DIAGNOSTIC COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
    