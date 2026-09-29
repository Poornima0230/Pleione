from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[1]

path = (
    BASE_DIR
    / "data"
    / "module_B"
    / "module_B_batch5_results.csv"
)

df = pd.read_csv(path)

print("=" * 70)
print("MODULE B CLASSIFIER DIAGNOSTIC")
print("=" * 70)

print(f"Total components: {len(df)}")

# ------------------------------------------------------------
# BASIC
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("RISK DISTRIBUTION")
print("=" * 70)

print(
    df["failure_risk"]
    .value_counts()
    .sort_index()
)


# ------------------------------------------------------------
# RISK VS ACTUAL FAILURE
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FAILURE RISK VS ACTUAL 168h VIOLATION")
print("=" * 70)

risk_table = (
    df.groupby("failure_risk")
    .agg(
        components=("component_id", "count"),
        actual_failures=("actual_violation", "sum"),
        mean_probability=("failure_probability", "mean"),
    )
)

risk_table["failure_rate"] = (
    risk_table["actual_failures"]
    / risk_table["components"]
)

print(risk_table)


# ------------------------------------------------------------
# GROUND TRUTH VS RISK
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("GROUND TRUTH VS FAILURE RISK")
print("=" * 70)

ground_truth_table = pd.crosstab(
    df["ground_truth"],
    df["failure_risk"],
)

print(ground_truth_table)


# ------------------------------------------------------------
# PROBABILITY BANDS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("PROBABILITY BANDS")
print("=" * 70)

bins = [
    0.00,
    0.10,
    0.20,
    0.30,
    0.40,
    0.50,
    0.60,
    0.70,
    0.80,
    0.90,
    1.01,
]

labels = [
    "0-10%",
    "10-20%",
    "20-30%",
    "30-40%",
    "40-50%",
    "50-60%",
    "60-70%",
    "70-80%",
    "80-90%",
    "90-100%",
]

df["probability_band"] = pd.cut(
    df["failure_probability"],
    bins=bins,
    labels=labels,
    right=False,
)

probability_table = (
    df.groupby(
        "probability_band",
        observed=False,
    )
    .agg(
        components=("component_id", "count"),
        actual_failures=("actual_violation", "sum"),
    )
)

probability_table["actual_failure_rate"] = (
    probability_table["actual_failures"]
    / probability_table["components"]
)

print(probability_table)


# ------------------------------------------------------------
# HIGH RISK ANALYSIS
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("HIGH RISK >= 0.75")
print("=" * 70)

high = df[
    df["failure_probability"] >= 0.75
]

print(
    f"Components : {len(high)}"
)

print(
    f"Actual failures : "
    f"{high['actual_violation'].sum()}"
)

if len(high) > 0:
    print(
        f"Failure rate : "
        f"{high['actual_violation'].mean():.4f}"
    )

print("\nGround truth:")

print(
    high["ground_truth"]
    .value_counts()
)


# ------------------------------------------------------------
# MEDIUM + HIGH
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("MEDIUM + HIGH >= 0.40")
print("=" * 70)

medium_high = df[
    df["failure_probability"] >= 0.40
]

print(
    f"Components : {len(medium_high)}"
)

print(
    f"Actual failures : "
    f"{medium_high['actual_violation'].sum()}"
)

if len(medium_high) > 0:
    print(
        f"Failure rate : "
        f"{medium_high['actual_violation'].mean():.4f}"
    )

print("\nGround truth:")

print(
    medium_high["ground_truth"]
    .value_counts()
)


# ------------------------------------------------------------
# MISSED FAILURES
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("MISSED FUTURE FAILURES")
print("=" * 70)

missed = df[
    (df["actual_violation"] == True)
    &
    (df["predicted_future_violation"] == False)
]

print(
    f"Missed failures: {len(missed)}"
)

if len(missed) > 0:

    print(
        "\nProbability statistics:"
    )

    print(
        missed["failure_probability"]
        .describe()
    )

    print(
        "\nGround truth:"
    )

    print(
        missed["ground_truth"]
        .value_counts()
    )


# ------------------------------------------------------------
# CORRECTLY DETECTED FAILURES
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("CORRECTLY DETECTED FAILURES")
print("=" * 70)

detected = df[
    (df["actual_violation"] == True)
    &
    (df["predicted_future_violation"] == True)
]

print(
    f"Detected failures: {len(detected)}"
)

if len(detected) > 0:

    print(
        "\nProbability statistics:"
    )

    print(
        detected["failure_probability"]
        .describe()
    )


# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

output = (
    BASE_DIR
    / "data"
    / "module_B"
    / "module_B_classifier_diagnostic.csv"
)

df.to_csv(
    output,
    index=False,
)

print("\nSaved:")
print(output)

print("\n" + "=" * 70)