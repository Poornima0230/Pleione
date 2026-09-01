import pandas as pd

module_a = pd.read_csv(
    "data/module_A_anomaly_results.csv"
)

module_b = pd.read_csv(
    "data/module_B_drift_predictions.csv"
)

print("\nMODULE A COLUMNS")
print("=" * 60)

for column in module_a.columns:
    print(column)


print("\nMODULE B COLUMNS")
print("=" * 60)

for column in module_b.columns:
    print(column)