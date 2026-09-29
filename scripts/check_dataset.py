from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


print("=" * 70)
print("DATASET VERSION CHECK")
print("=" * 70)

all_data = []

for batch_no in range(1, 6):

    path = DATA_DIR / f"batch_{batch_no}.csv"

    print(f"\nBatch {batch_no}")
    print("-" * 50)
    print("File:", path)

    if not path.exists():
        print("ERROR: FILE DOES NOT EXIST")
        continue

    df = pd.read_csv(path)

    print("Rows:", len(df))

    print("\nGround truth:")
    print(
        df["ground_truth"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\n168h violations:")

    violations = (
        df["iddq_168h_uA"]
        > df["absolute_limit_uA"]
    )

    print(
        f"Violations    : {violations.sum()}"
    )

    print(
        f"Non-violations: {(~violations).sum()}"
    )

    print("\nEarly signal:")

    delta = (
        df["iddq_24h_uA"]
        - df["iddq_0h_uA"]
    )

    print(
        f"delta 0→24 mean: {delta.mean():.4f}"
    )

    print(
        f"iddq 0h mean   : "
        f"{df['iddq_0h_uA'].mean():.4f}"
    )

    print(
        f"iddq 24h mean  : "
        f"{df['iddq_24h_uA'].mean():.4f}"
    )

    all_data.append(df)


if all_data:

    data = pd.concat(
        all_data,
        ignore_index=True,
    )

    print("\n")
    print("=" * 70)
    print("TOTAL DATASET")
    print("=" * 70)

    print("Rows:", len(data))

    print("\nOverall ground truth:")
    print(
        data["ground_truth"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    violations = (
        data["iddq_168h_uA"]
        > data["absolute_limit_uA"]
    )

    print(
        f"\nTotal 168h violations: "
        f"{violations.sum()}"
    )

    print(
        f"Total non-violations: "
        f"{(~violations).sum()}"
    )

    print("\nExpected final generator profile:")
    print("Normal            ≈ 60%")
    print("High_Stable       ≈ 12%")
    print("Latent_Defect     ≈ 10%")
    print("Sudden_Anomaly    ≈ 8%")
    print("Absolute_Failure  ≈ 10%")

    print("\nExpected Batch 5 approximate counts:")
    print("Normal            ≈ 1165")
    print("High_Stable       ≈ 235")
    print("Latent_Defect     ≈ 224")
    print("Sudden_Anomaly    ≈ 165")
    print("Absolute_Failure  ≈ 211")
    print("168h violations   ≈ 210")