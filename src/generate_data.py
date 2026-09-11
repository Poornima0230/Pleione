import pandas as pd
import numpy as np
import os
import random

# Create data folder if not exists
os.makedirs("../data", exist_ok=True)

NUM_FILES = 10
ROWS_PER_FILE = 2000

component_types = ["TypeA", "TypeB", "TypeC"]
behaviors = [
    "Normal",
    "Latent_Defect",
    "High_Stable",
    "Sudden_Anomaly",
    "Absolute_Failure"
]

def generate_component(cid, lot):

    comp_type = random.choice(component_types)
    behavior = random.choice(behaviors)

    temp = round(random.uniform(25, 35), 2)
    voltage = round(random.uniform(1.0, 1.3), 2)

    base = random.uniform(8, 15)

    # Generate IDDQ pattern
    if behavior == "Normal":
        iddq = [base + i for i in [0, 1, 2, 3]]

    elif behavior == "Latent_Defect":
        iddq = [base, base+2, base+5, base+10]

    elif behavior == "High_Stable":
        iddq = [base]*4

    elif behavior == "Sudden_Anomaly":
        iddq = [base, base+1, base+20, base+22]

    elif behavior == "Absolute_Failure":
        iddq = [base, base+1, base+2, 60]  # exceeds limit

    # Leakage (smaller values)
    leakage = [round(v * 0.1, 2) for v in iddq]

    return {
        "component_id": f"C{cid}",
        "lot_id": f"L{lot}",
        "component_type": comp_type,
        "temperature_C": temp,
        "voltage_V": voltage,

        "iddq_0h_uA": round(iddq[0], 2),
        "iddq_24h_uA": round(iddq[1], 2),
        "iddq_96h_uA": round(iddq[2], 2),
        "iddq_168h_uA": round(iddq[3], 2),

        "leakage_0h_uA": leakage[0],
        "leakage_24h_uA": leakage[1],
        "leakage_96h_uA": leakage[2],
        "leakage_168h_uA": leakage[3],

        "ground_truth": behavior,
        "absolute_limit_uA": 50
    }


# 🔥 Generate files
component_counter = 1

for file_num in range(1, NUM_FILES + 1):

    data = []

    for i in range(ROWS_PER_FILE):
        row = generate_component(component_counter, file_num)
        data.append(row)
        component_counter += 1

    df = pd.DataFrame(data)

    file_path = f"../data/batch_{file_num}.csv"
    df.to_csv(file_path, index=False)

    print(f"✅ Generated {file_path} with {ROWS_PER_FILE} rows")