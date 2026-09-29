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

OUTPUT_FILE = (
    OUTPUT_DIR
    / "module_C_missed_failure_analysis.csv"
)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("MODULE C - MISSED FAILURE ANALYSIS")
    print("=" * 70)

    module_c = pd.read_csv(MODULE_C_FILE)
    batch_5 = pd.read_csv(BATCH_5_FILE)

    print(f"Module C rows : {len(module_c)}")
    print(f"Batch 5 rows  : {len(batch_5)}")


    # ========================================================
    # SELECT BATCH 5 COLUMNS NEEDED FOR OFFLINE ANALYSIS
    # ========================================================

    actual_columns = [
        "component_id",

        # Early information available to the models
        "iddq_0h_uA",
        "iddq_24h_uA",
        "leakage_0h_uA",
        "leakage_24h_uA",

        # Future values - evaluation only
        "iddq_96h_uA",
        "iddq_168h_uA",

        # Offline diagnostic label
        "ground_truth",
    ]

    missing = [
        column
        for column in actual_columns
        if column not in batch_5.columns
    ]

    if missing:
        raise ValueError(
            f"Batch 5 is missing columns: {missing}"
        )

    actual = batch_5[actual_columns].copy()


    # ========================================================
    # CALCULATE DELTA 0 → 24
    # ========================================================

    actual["delta_0_24"] = (
        actual["iddq_24h_uA"]
        - actual["iddq_0h_uA"]
    )


    # ========================================================
    # MERGE MODULE C + BATCH 5
    # ========================================================

    data = pd.merge(
        module_c,
        actual,
        on="component_id",
        how="inner",
        validate="one_to_one",
    )

    if len(data) != len(module_c):
        raise ValueError(
            "Some Module C components could not be matched "
            "with Batch 5."
        )

    print(f"Merged rows  : {len(data)}")


    # ========================================================
    # ACTUAL 168h SPECIFICATION VIOLATION
    # ========================================================
    #
    # This is OFFLINE evaluation only.
    #
    # Module C itself did not use this value.
    # ========================================================

    data["actual_168h_violation"] = (
        data["iddq_168h_uA"]
        > data["absolute_limit_uA"]
    )


    # ========================================================
    # MISSED FAILURES
    # ========================================================
    #
    # Module C said PASS
    # but actual 168h value exceeded the specification.
    # ========================================================

    missed = data[
        (data["final_decision"] == "PASS")
        & (data["actual_168h_violation"])
    ].copy()


    print()
    print("=" * 70)
    print("BASIC RESULTS")
    print("=" * 70)

    print(
        f"Total Batch 5 components : {len(data)}"
    )

    print(
        f"Actual 168h violations   : "
        f"{data['actual_168h_violation'].sum()}"
    )

    print(
        f"Missed failures          : {len(missed)}"
    )


    # ========================================================
    # GROUND TRUTH
    # ========================================================

    print()
    print("=" * 70)
    print("MISSED FAILURES BY GROUND TRUTH")
    print("=" * 70)

    print(
        missed["ground_truth"]
        .value_counts()
        .to_string()
    )


    # ========================================================
    # MODULE A STATUS
    # ========================================================

    print()
    print("=" * 70)
    print("MISSED FAILURES BY MODULE A STATUS")
    print("=" * 70)

    print(
        missed["module_a_status"]
        .value_counts()
        .to_string()
    )


    # ========================================================
    # STATISTICS
    # ========================================================

    analysis_columns = [
        "iddq_0h_uA",
        "iddq_24h_uA",
        "delta_0_24",
        "leakage_0h_uA",
        "leakage_24h_uA",
        "module_a_score",
        "predicted_168h_uA",
        "prediction_lower_uA",
        "prediction_upper_uA",
        "iddq_96h_uA",
        "iddq_168h_uA",
    ]

    print()
    print("=" * 70)
    print("MISSED FAILURE STATISTICS")
    print("=" * 70)

    print(
        missed[analysis_columns]
        .describe()
        .round(3)
        .to_string()
    )


    # ========================================================
    # DETECTED FAILURES
    # ========================================================
    #
    # Actual failures that Module C sent to REVIEW or REJECT.
    # ========================================================

    detected = data[
        data["actual_168h_violation"]
        & (data["final_decision"] != "PASS")
    ].copy()


    # ========================================================
    # MISSED VS DETECTED
    # ========================================================

    print()
    print("=" * 70)
    print("MISSED VS DETECTED ACTUAL FAILURES")
    print("=" * 70)

    comparison = pd.DataFrame(
        {
            "Missed_Pass": missed[analysis_columns].mean(),
            "Detected_Review_or_Reject": (
                detected[analysis_columns].mean()
            ),
        }
    )

    comparison["difference"] = (
        comparison["Detected_Review_or_Reject"]
        - comparison["Missed_Pass"]
    )

    print(
        comparison.round(3).to_string()
    )


    # ========================================================
    # TOP MISSED FAILURES
    # ========================================================

    print()
    print("=" * 70)
    print("TOP MISSED FAILURES BY ACTUAL 168h IDDQ")
    print("=" * 70)

    top_columns = [
        "component_id",
        "ground_truth",
        "iddq_0h_uA",
        "iddq_24h_uA",
        "delta_0_24",
        "module_a_status",
        "module_a_score",
        "predicted_168h_uA",
        "prediction_upper_uA",
        "iddq_96h_uA",
        "iddq_168h_uA",
    ]

    top = missed[
        top_columns
    ].sort_values(
        "iddq_168h_uA",
        ascending=False,
    )

    print(
        top.head(20)
        .round(3)
        .to_string(index=False)
    )


    # ========================================================
    # ADD DIAGNOSTIC COLUMNS
    # ========================================================

    missed["prediction_error_uA"] = (
        missed["iddq_168h_uA"]
        - missed["predicted_168h_uA"]
    )

    missed["absolute_prediction_error_uA"] = (
        missed["prediction_error_uA"]
        .abs()
    )

    missed["upper_bound_gap_to_actual_uA"] = (
        missed["iddq_168h_uA"]
        - missed["prediction_upper_uA"]
    )

    missed["actual_excess_over_limit_uA"] = (
        missed["iddq_168h_uA"]
        - missed["absolute_limit_uA"]
    )


    # ========================================================
    # SAVE
    # ========================================================

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    missed.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print()
    print("=" * 70)
    print("SAVED")
    print("=" * 70)

    print(OUTPUT_FILE)

    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()