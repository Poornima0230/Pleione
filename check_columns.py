import pandas as pd

df = pd.read_csv("data/batch_1.csv")

print(df.columns.tolist())
print(df.head())