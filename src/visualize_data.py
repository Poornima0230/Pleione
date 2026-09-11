"""
import pandas as pd
import matplotlib.pyplot as plt

import os

data_folder = "../data"
files = sorted([f for f in os.listdir(data_folder) if f.endswith(".csv")])

cumulative_df = pd.DataFrame()

for file in files:
    df = pd.read_csv(os.path.join(data_folder, file))
    cumulative_df = pd.concat([cumulative_df, df], ignore_index=True)

times = [0, 24, 96, 168]

# Select one component from each behavior
behaviors = [
    "Normal",
    "High_Stable",
    "Latent_Defect",
    "Absolute_Failure",
    "Sudden_Anomaly"
]

for behavior in behaviors:

    component = df[df["ground_truth"] == behavior].iloc[0]

    values = [
        component["iddq_0h_uA"],
        component["iddq_24h_uA"],
        component["iddq_96h_uA"],
        component["iddq_168h_uA"]
    ]

    plt.figure()

    plt.plot(times, values, marker="o")

    plt.axhline(
        component["absolute_limit_uA"],
        linestyle="--"
    )

    plt.title(
        f"{behavior} - {component['component_id']}"
    )

    plt.xlabel("Burn-In Time (hours)")
    plt.ylabel("Iddq (µA)")

    plt.show()
"""
import pandas as pd
import matplotlib.pyplot as plt
import os
import time

from preprocessing import preprocess_data
from config_loader import load_config

config = load_config()

files = sorted([f for f in os.listdir("../data") if f.endswith(".csv")])

cumulative_df = pd.DataFrame()

param = config["parameters"][0]

for file in files:

    print(f"\nProcessing: {file}")

    df = pd.read_csv(os.path.join("../data", file))

    cumulative_df = pd.concat([cumulative_df, df], ignore_index=True)


    df_clean, _ = preprocess_data(cumulative_df, config)
    df_clean.to_csv("../data/processed_latest.csv", index=False)
    df_clean.to_csv("../data/processed_latest.csv", index=False)

    comp_id = df_clean["component_id"].iloc[0]
    for param in config["parameters"]:
        comp_data = df_clean[
            (df_clean["component_id"] == comp_id) &
            (df_clean["parameter"] == param)
        ]

        if comp_data.empty:
            continue

        comp_data = comp_data.sort_values("time")

        plt.figure()
        plt.plot(comp_data["time"], comp_data["value"], marker="o")

        if "upper_limit" in comp_data.columns:
            plt.axhline(comp_data["upper_limit"].iloc[0], linestyle="--")

        plt.title(f"Cumulative - {comp_id}")
        plt.xlabel("Time")
        plt.ylabel(param)

        plt.show()

        time.sleep(3)