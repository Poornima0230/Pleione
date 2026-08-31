import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv(
    "data/sih_26170_burn_in_synthetic_dataset.csv"
)

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