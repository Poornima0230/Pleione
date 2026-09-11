import pandas as pd

def convert_wide_to_long(df, config):

    records = []

    for _, row in df.iterrows():
        for col in df.columns:

            if "_" in col and any(param in col for param in config["parameters"]):

                try:
                    parts = col.split("_")
                    param = parts[0]
                    time = int(parts[1].replace("h", ""))

                    value = row[col]

                    if pd.isna(value):
                        continue

                    records.append({
                        "component_id": row["component_id"],
                        "component_type": row.get("component_type", "default"),
                        "parameter": param,
                        "time": time,
                        "value": value
                    })

                except:
                    continue

    return pd.DataFrame(records)


def add_limits(df, config):

    def get_limits(row):
        limits = config["components"]["default"]["limits"].get(row["parameter"], {})
        return pd.Series([
            limits.get("min"),
            limits.get("max")
        ])

    df[["lower_limit", "upper_limit"]] = df.apply(get_limits, axis=1)

    return df


def handle_missing(df, config):

    df = df.sort_values(["component_id", "parameter", "time"])

    df["value"] = df.groupby(
        ["component_id", "parameter"]
    )["value"].transform(lambda x: x.interpolate())

    return df


def preprocess_data(df, config):

    print("🔹 Starting preprocessing...")

    df_long = convert_wide_to_long(df, config)

    df_long = handle_missing(df_long, config)

    df_long = add_limits(df_long, config)
        # ✅ ADD METADATA
    metadata = {
        "parameters": config["parameters"],
        "timepoints": sorted(df_long["time"].unique().tolist()),
        "num_components": df_long["component_id"].nunique(),
        "prediction_horizon": config["prediction_horizon"]
    }

    print("✅ Preprocessing complete")

    return df_long, metadata