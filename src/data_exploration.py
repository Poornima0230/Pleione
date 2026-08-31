import pandas as pd

# Path to our dataset
file_path = "data/sih_26170_burn_in_synthetic_dataset.csv"

# Load dataset
df = pd.read_csv(file_path)

print("Dataset loaded successfully!")

print("\nShape:")
print(df.shape)

print("\nFirst 5 rows:")
print(df.head())

print("\nColumns:")
print(df.columns.tolist())

print("\nBehavior distribution:")
print(df["ground_truth"].value_counts())