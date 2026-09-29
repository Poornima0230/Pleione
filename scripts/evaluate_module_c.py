from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

MODULE_C_FILE = (
    ROOT
    / "data"
    / "module_C"
    / "module_C_batch5_results.csv"
)

BATCH_5_FILE = (
    ROOT
    / "data"
    / "batch_5.csv"
)

OUTPUT_DIR = ROOT / "data" / "module_C"

EVALUATION_FILE = (
    OUTPUT_DIR
    / "module_C_batch5_evaluation.csv"
)

CONFUSION_FILE = (
    OUTPUT_DIR
    / "module_C_decision_evaluation.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    if not MODULE_C_FILE.exists():
        raise FileNotFoundError(
            f"Module C result file not found:\n{MODULE_C_FILE}"
        )

    if not BATCH_5_FILE.exists():
        raise FileNotFoundError(
            f"Batch 5 dataset not found:\n{BATCH_5_FILE}"
        )

    module_c = pd.read_csv(MODULE_C_FILE)
    batch_5 = pd.read_csv(BATCH_5_FILE)

    print("=" * 70)
    print("MODULE C - OFFLINE EVALUATION")
    print("=" * 70)

    print(f"Module C rows : {len(module_c)}")
    print(f"Batch 5 rows  : {len(batch_5)}")

    return module_c, batch_5


# ============================================================
# PREPARE ACTUAL OUTCOME
# ============================================================

def prepare_actual_outcome(batch_5):

    required = [
        "component_id",
        "iddq_168h_uA",
        "leakage_168h_uA",
        "absolute_limit_uA",
        "ground_truth",
    ]

    missing = [
        column
        for column in required
        if column not in batch_5.columns
    ]

    if missing:
        raise ValueError(
            f"Batch 5 is missing columns: {missing}"
        )

    actual = batch_5[required].copy()

    # --------------------------------------------------------
    # Actual specification violation
    #
    # The screening limit is applied to the actual 168h IDDQ.
    # --------------------------------------------------------

    actual["actual_168h_violation"] = (
        actual["iddq_168h_uA"]
        > actual["absolute_limit_uA"]
    )

    return actual


# ============================================================
# MERGE
# ============================================================

def merge_results(module_c, actual):

    merged = pd.merge(
        module_c,
        actual,
        on="component_id",
        how="inner",
        validate="one_to_one",
    )

    if len(merged) != len(module_c):
        raise ValueError(
            "Some Module C components could not be matched "
            "with Batch 5 actual measurements."
        )

    return merged


# ============================================================
# DECISION EVALUATION
# ============================================================

def evaluate_decisions(data):

    # --------------------------------------------------------
    # Actual outcome
    # --------------------------------------------------------

    actual_failure = data["actual_168h_violation"]

    # --------------------------------------------------------
    # REJECT
    #
    # Treat REJECT as the system's strongest predicted failure.
    # --------------------------------------------------------

    predicted_reject = (
        data["final_decision"] == "REJECT"
    )

    reject_tp = (
        predicted_reject & actual_failure
    ).sum()

    reject_fp = (
        predicted_reject & ~actual_failure
    ).sum()

    reject_fn = (
        ~predicted_reject & actual_failure
    ).sum()

    reject_tn = (
        ~predicted_reject & ~actual_failure
    ).sum()

    reject_precision = (
        reject_tp / (reject_tp + reject_fp)
        if (reject_tp + reject_fp) > 0
        else 0.0
    )

    reject_recall = (
        reject_tp / (reject_tp + reject_fn)
        if (reject_tp + reject_fn) > 0
        else 0.0
    )

    reject_f1 = (
        2
        * reject_precision
        * reject_recall
        / (reject_precision + reject_recall)
        if (reject_precision + reject_recall) > 0
        else 0.0
    )

    # --------------------------------------------------------
    # REVIEW + REJECT
    #
    # This measures whether the system successfully sends
    # future failures into an investigation path.
    # --------------------------------------------------------

    predicted_review_or_reject = data[
        "final_decision"
    ].isin(
        ["REVIEW", "REJECT"]
    )

    investigation_tp = (
        predicted_review_or_reject & actual_failure
    ).sum()

    investigation_fp = (
        predicted_review_or_reject & ~actual_failure
    ).sum()

    investigation_fn = (
        ~predicted_review_or_reject & actual_failure
    ).sum()

    investigation_tn = (
        ~predicted_review_or_reject & ~actual_failure
    ).sum()

    investigation_precision = (
        investigation_tp
        / (investigation_tp + investigation_fp)
        if (investigation_tp + investigation_fp) > 0
        else 0.0
    )

    investigation_recall = (
        investigation_tp
        / (investigation_tp + investigation_fn)
        if (investigation_tp + investigation_fn) > 0
        else 0.0
    )

    investigation_f1 = (
        2
        * investigation_precision
        * investigation_recall
        / (
            investigation_precision
            + investigation_recall
        )
        if (
            investigation_precision
            + investigation_recall
        ) > 0
        else 0.0
    )

    # --------------------------------------------------------
    # SAVE COMPONENT-LEVEL EVALUATION
    # --------------------------------------------------------

    evaluation = data.copy()

    evaluation["evaluation_actual_failure"] = (
        evaluation["actual_168h_violation"]
    )

    evaluation["evaluation_correct_reject"] = (
        predicted_reject
        & actual_failure
    )

    evaluation["evaluation_missed_failure"] = (
        ~predicted_review_or_reject
        & actual_failure
    )

    evaluation["evaluation_safe_pass"] = (
        (evaluation["final_decision"] == "PASS")
        & ~actual_failure
    )

    return (
        evaluation,
        {
            "reject_tp": int(reject_tp),
            "reject_fp": int(reject_fp),
            "reject_fn": int(reject_fn),
            "reject_tn": int(reject_tn),
            "reject_precision": reject_precision,
            "reject_recall": reject_recall,
            "reject_f1": reject_f1,
            "investigation_tp": int(investigation_tp),
            "investigation_fp": int(investigation_fp),
            "investigation_fn": int(investigation_fn),
            "investigation_tn": int(investigation_tn),
            "investigation_precision": investigation_precision,
            "investigation_recall": investigation_recall,
            "investigation_f1": investigation_f1,
        },
    )


# ============================================================
# PRINT DECISION × ACTUAL TABLE
# ============================================================

def print_decision_table(data):

    table = pd.crosstab(
        data["final_decision"],
        data["actual_168h_violation"],
    )

    table = table.rename(
        columns={
            False: "Actual Safe",
            True: "Actual Violation",
        }
    )

    print()
    print("=" * 70)
    print("FINAL DECISION × ACTUAL 168h OUTCOME")
    print("=" * 70)

    print(table.to_string())


# ============================================================
# PRINT GROUND TRUTH BREAKDOWN
# ============================================================

def print_ground_truth_breakdown(data):

    table = pd.crosstab(
        data["ground_truth"],
        data["final_decision"],
    )

    print()
    print("=" * 70)
    print("GROUND TRUTH × FINAL DECISION")
    print("=" * 70)

    print(table.to_string())


# ============================================================
# PRINT DECISION STATISTICS
# ============================================================

def print_metrics(metrics):

    print()
    print("=" * 70)
    print("REJECT PERFORMANCE")
    print("=" * 70)

    print(
        f"TP : {metrics['reject_tp']}"
    )

    print(
        f"FP : {metrics['reject_fp']}"
    )

    print(
        f"FN : {metrics['reject_fn']}"
    )

    print(
        f"TN : {metrics['reject_tn']}"
    )

    print(
        f"Precision : {metrics['reject_precision']:.4f}"
    )

    print(
        f"Recall    : {metrics['reject_recall']:.4f}"
    )

    print(
        f"F1        : {metrics['reject_f1']:.4f}"
    )

    print()
    print("=" * 70)
    print("REVIEW + REJECT INVESTIGATION COVERAGE")
    print("=" * 70)

    print(
        f"TP : {metrics['investigation_tp']}"
    )

    print(
        f"FP : {metrics['investigation_fp']}"
    )

    print(
        f"FN : {metrics['investigation_fn']}"
    )

    print(
        f"TN : {metrics['investigation_tn']}"
    )

    print(
        f"Precision : "
        f"{metrics['investigation_precision']:.4f}"
    )

    print(
        f"Recall    : "
        f"{metrics['investigation_recall']:.4f}"
    )

    print(
        f"F1        : "
        f"{metrics['investigation_f1']:.4f}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    module_c, batch_5 = load_data()

    actual = prepare_actual_outcome(batch_5)

    data = merge_results(
        module_c,
        actual,
    )

    evaluation, metrics = evaluate_decisions(
        data
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    evaluation.to_csv(
        EVALUATION_FILE,
        index=False,
    )

    # Decision × actual evaluation table
    decision_table = pd.crosstab(
        data["final_decision"],
        data["actual_168h_violation"],
    )

    decision_table.to_csv(
        CONFUSION_FILE
    )

    print_decision_table(data)

    print_ground_truth_breakdown(data)

    print_metrics(metrics)

    print()
    print("=" * 70)
    print("OFFLINE EVALUATION SAVED")
    print("=" * 70)

    print(
        f"Component evaluation:\n{EVALUATION_FILE}"
    )

    print(
        f"Decision table:\n{CONFUSION_FILE}"
    )

    print()
    print(
        "IMPORTANT: Actual 168h measurements and ground truth "
        "were used ONLY for offline evaluation."
    )

    print(
        "They were NOT used to generate Module C decisions."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()