from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

BATCH_FILES = [
    ROOT / "data" / "batch_1.csv",
    ROOT / "data" / "batch_2.csv",
    ROOT / "data" / "batch_3.csv",
    ROOT / "data" / "batch_4.csv",
    ROOT / "data" / "batch_5.csv",
]


# ============================================================
# LOAD DATA
# ============================================================

def load_all_batches():

    frames = []

    for path in BATCH_FILES:

        if not path.exists():
            raise FileNotFoundError(
                f"Dataset not found:\n{path}"
            )

        df = pd.read_csv(path)

        df["batch"] = path.stem

        frames.append(df)

    data = pd.concat(
        frames,
        ignore_index=True,
    )

    return data


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("MODULE B - EARLY FAILURE SIGNATURE ANALYSIS")
    print("=" * 70)

    data = load_all_batches()

    print(
        f"Total components: {len(data)}"
    )


    # ========================================================
    # CREATE EARLY FEATURES
    # ========================================================

    data["delta_0_24"] = (
        data["iddq_24h_uA"]
        - data["iddq_0h_uA"]
    )


    # ========================================================
    # ONLY EARLY INFORMATION
    # ========================================================

    features = [
        "temperature_C",
        "voltage_V",
        "iddq_0h_uA",
        "iddq_24h_uA",
        "delta_0_24",
        "leakage_0h_uA",
        "leakage_24h_uA",
    ]


    # ========================================================
    # COMPARE NORMAL VS ABSOLUTE FAILURE
    # ========================================================

    selected = data[
        data["ground_truth"].isin(
            [
                "Normal",
                "Absolute_Failure",
            ]
        )
    ].copy()


    print()
    print("=" * 70)
    print("CLASS COUNTS")
    print("=" * 70)

    print(
        selected["ground_truth"]
        .value_counts()
        .to_string()
    )


    # ========================================================
    # GROUP STATISTICS
    # ========================================================

    print()
    print("=" * 70)
    print("EARLY FEATURE STATISTICS")
    print("=" * 70)

    stats = (
        selected
        .groupby("ground_truth")[features]
        .agg(
            [
                "mean",
                "std",
                "min",
                "median",
                "max",
            ]
        )
        .round(3)
    )

    print(stats.to_string())


    # ========================================================
    # QUANTILES
    # ========================================================

    print()
    print("=" * 70)
    print("EARLY FEATURE QUANTILES")
    print("=" * 70)

    for feature in features:

        print()
        print(f"--- {feature} ---")

        table = (
            selected
            .groupby("ground_truth")[feature]
            .quantile(
                [
                    0.10,
                    0.25,
                    0.50,
                    0.75,
                    0.90,
                ]
            )
            .unstack()
            .round(3)
        )

        print(table.to_string())


    # ========================================================
    # BATCH 5 MISSED FAILURES
    # ========================================================

    batch_5 = data[
        data["batch"] == "batch_5"
    ].copy()

    missed = batch_5[
        (batch_5["ground_truth"] == "Absolute_Failure")
    ].copy()


    print()
    print("=" * 70)
    print("BATCH 5 ABSOLUTE FAILURE EARLY SIGNATURE")
    print("=" * 70)

    print(
        missed[features]
        .describe()
        .round(3)
        .to_string()
    )


    # ========================================================
    # TRAINING ABSOLUTE FAILURE VS BATCH 5 MISSED FAILURES
    # ========================================================

    training_failures = selected[
        (selected["ground_truth"] == "Absolute_Failure")
        & (selected["batch"].isin(
            [
                "batch_1",
                "batch_2",
                "batch_3",
                "batch_4",
            ]
        ))
    ]

    print()
    print("=" * 70)
    print("TRAINING ABSOLUTE_FAILURE VS BATCH 5")
    print("=" * 70)

    comparison = pd.DataFrame(
        {
            "Training_Absolute_Failure": (
                training_failures[features].mean()
            ),
            "Batch5_Absolute_Failure": (
                missed[features].mean()
            ),
        }
    )

    comparison["difference"] = (
        comparison["Batch5_Absolute_Failure"]
        - comparison["Training_Absolute_Failure"]
    )

    print(
        comparison.round(3).to_string()
    )


    # ========================================================
    # EARLY FEATURE CORRELATION WITH FAILURE
    # ========================================================

    print()
    print("=" * 70)
    print("EARLY FEATURE CORRELATION WITH ABSOLUTE_FAILURE")
    print("=" * 70)

    binary = data.copy()

    binary["absolute_failure"] = (
        binary["ground_truth"]
        == "Absolute_Failure"
    ).astype(int)

    correlation = (
        binary[features + ["absolute_failure"]]
        .corr()["absolute_failure"]
        .drop("absolute_failure")
        .sort_values(
            key=lambda x: x.abs(),
            ascending=False,
        )
    )

    print(
        correlation.round(4).to_string()
    )


    print()
    print("=" * 70)
    print("INTERPRETATION")
    print("=" * 70)

    print(
        "These results use only 0h and 24h information "
        "for the early-feature analysis."
    )

    print(
        "96h and 168h measurements are NOT used as model inputs."
    )

    print("=" * 70)


if __name__ == "__main__":
    main()