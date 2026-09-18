import os
import json
import math
import pandas as pd
import numpy as np


# ============================================================
# PLEIONE
# CONFIGURABLE RISK SCORING AND QA POLICY ENGINE
# ============================================================


# ============================================================
# PATHS
# ============================================================

MODULE_A_DIR = "data/module_A_results"

MODULE_B_PATH = (
    "data/module_B/module_B_drift_predictions.csv"
)

CONFIG_PATH = "risk_config.json"

OUTPUT_DIR = "data/risk"

SUMMARY_PATH = os.path.join(
    OUTPUT_DIR,
    "risk_stage_summary.csv"
)

OVERALL_OUTPUT_PATH = os.path.join(
    OUTPUT_DIR,
    "overall_risk_results.csv"
)


# ============================================================
# IMPORTANT PIPELINE LIMIT
# ============================================================

# Module A currently has stages 1-10.
#
# Module B currently contains predictions for 10,000
# components, which corresponds to cumulative stages 1-5.
#
# Therefore the risk engine must stop at stage 5.
#
# Stage 6-10 of Module A are intentionally ignored until
# corresponding Module B predictions are available.

MAX_SUPPORTED_STAGE = 5


# ============================================================
# BASIC HELPERS
# ============================================================

def safe_float(value, default=0.0):

    try:

        if pd.isna(value):
            return default

        value = float(value)

        if not np.isfinite(value):
            return default

        return value

    except (ValueError, TypeError):

        return default


def clamp(
    value,
    minimum=0.0,
    maximum=1.0
):

    return max(
        minimum,
        min(maximum, value)
    )


def normalize_component_id(series):

    return (
        series
        .astype(str)
        .str.strip()
    )


# ============================================================
# LOAD CONFIGURATION
# ============================================================

def load_config():

    if not os.path.exists(CONFIG_PATH):

        raise FileNotFoundError(
            f"Configuration file not found: "
            f"{CONFIG_PATH}"
        )

    with open(
        CONFIG_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        config = json.load(file)

    validate_config(config)

    return config


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

def validate_config(config):

    if "risk_calculation" not in config:

        raise ValueError(
            "Config must contain "
            "'risk_calculation'."
        )

    if "weights" not in config[
        "risk_calculation"
    ]:

        raise ValueError(
            "Config must contain "
            "risk_calculation.weights."
        )

    required_weights = [
        "anomaly",
        "drift",
        "future",
        "specification"
    ]

    weights = config[
        "risk_calculation"
    ][
        "weights"
    ]

    for key in required_weights:

        if key not in weights:

            raise ValueError(
                f"Missing risk weight: {key}"
            )

        if safe_float(
            weights[key]
        ) < 0:

            raise ValueError(
                f"Risk weight cannot be "
                f"negative: {key}"
            )

    weight_sum = sum(
        safe_float(
            weights[key]
        )
        for key in required_weights
    )

    if weight_sum <= 0:

        raise ValueError(
            "At least one risk weight "
            "must be greater than zero."
        )

    if "qa_policy" not in config:

        raise ValueError(
            "Config must contain "
            "'qa_policy'."
        )

    if "classifications" not in config[
        "qa_policy"
    ]:

        raise ValueError(
            "qa_policy must contain "
            "classifications."
        )

    classifications = config[
        "qa_policy"
    ][
        "classifications"
    ]

    if not classifications:

        raise ValueError(
            "At least one QA classification "
            "is required."
        )

    for classification in classifications:

        if "name" not in classification:

            raise ValueError(
                "Every classification needs "
                "a name."
            )

        if "min_risk" not in classification:

            raise ValueError(
                f"Missing min_risk for "
                f"{classification['name']}"
            )

        if "max_risk" not in classification:

            raise ValueError(
                f"Missing max_risk for "
                f"{classification['name']}"
            )


# ============================================================
# VALIDATE MODULE A
# ============================================================

def validate_module_a(
    df,
    filename
):

    required_columns = [

        "component_id",

        "component_type",

        "combined_anomaly_score",

        "anomaly_flag",

        "statistical_score",

        "statistical_anomaly_flag",

        "temporal_anomaly_score",

        "temporal_anomaly_flag",

        "isolation_forest_score",

        "isolation_forest_flag",

        "statistical_evidence_count",

        "limit_violation",

        "limit_excess_uA",

        "absolute_limit_uA"
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            f"\nModule A file "
            f"'{filename}' is missing columns:\n"
            +
            "\n".join(
                f"  - {column}"
                for column in missing
            )
        )


# ============================================================
# VALIDATE MODULE B
# ============================================================

def validate_module_b(df):

    required_columns = [

        "component_id",

        "component_type",

        "predicted_168h_uA",

        "prediction_lower_uA",

        "prediction_upper_uA",

        "predicted_drift_uA",

        "predicted_drift_rate",

        "predicted_relative_drift",

        "drift_slope_excess",

        "early_drift_flag",

        "predicted_limit_exceeded",

        "uncertainty_adjusted_failure",

        "limit_margin_uA",

        "upper_bound_limit_margin_uA",

        "future_drift_risk"
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            "\nModule B is missing columns:\n"
            +
            "\n".join(
                f"  - {column}"
                for column in missing
            )
        )


# ============================================================
# MODULE A
# ANOMALY RISK FACTOR
# ============================================================

def calculate_anomaly_factor(row):

    combined_score = clamp(
        safe_float(
            row[
                "combined_anomaly_score"
            ]
        )
    )

    anomaly_flag = safe_float(
        row[
            "anomaly_flag"
        ]
    )

    evidence_count = safe_float(
        row[
            "statistical_evidence_count"
        ]
    )

    statistical_flag = safe_float(
        row[
            "statistical_anomaly_flag"
        ]
    )

    temporal_flag = safe_float(
        row[
            "temporal_anomaly_flag"
        ]
    )

    isolation_flag = safe_float(
        row[
            "isolation_forest_flag"
        ]
    )

    # --------------------------------------------------------
    # Combined anomaly score is the primary anomaly signal.
    #
    # The individual detector flags are supporting evidence.
    #
    # We deliberately do not give every detector an independent
    # full weight because that would double-count correlated
    # anomaly evidence.
    # --------------------------------------------------------

    evidence_strength = clamp(
        evidence_count / 3.0
    )

    supporting_flags = (
        statistical_flag
        +
        temporal_flag
        +
        isolation_flag
    )

    supporting_strength = clamp(
        supporting_flags / 3.0
    )

    anomaly_factor = (

        0.70
        * combined_score

        +

        0.20
        * evidence_strength

        +

        0.10
        * supporting_strength
    )

    # If Module A explicitly marked an anomaly,
    # maintain a meaningful minimum anomaly contribution.

    if anomaly_flag >= 1:

        anomaly_factor = max(
            anomaly_factor,
            0.60
        )

    return clamp(
        anomaly_factor
    )


# ============================================================
# MODULE B
# DRIFT RISK FACTOR
# ============================================================

def calculate_drift_factor(
    row,
    config
):

    predicted_drift_rate = abs(
        safe_float(
            row[
                "predicted_drift_rate"
            ]
        )
    )

    predicted_relative_drift = abs(
        safe_float(
            row[
                "predicted_relative_drift"
            ]
        )
    )

    drift_slope_excess = abs(
        safe_float(
            row[
                "drift_slope_excess"
            ]
        )
    )

    early_drift_flag = safe_float(
        row[
            "early_drift_flag"
        ]
    )

    # --------------------------------------------------------
    # Convert drift measurements into bounded values.
    # --------------------------------------------------------

    rate_factor = (
        1.0
        -
        math.exp(
            -predicted_drift_rate
        )
    )

    relative_factor = (
        1.0
        -
        math.exp(
            -predicted_relative_drift
        )
    )

    slope_factor = (
        1.0
        -
        math.exp(
            -drift_slope_excess
        )
    )

    drift_factor = (

        0.45
        * rate_factor

        +

        0.30
        * relative_factor

        +

        0.15
        * slope_factor

        +

        0.10
        * early_drift_flag
    )

    return clamp(
        drift_factor
    )


# ============================================================
# MODULE B
# FUTURE RISK FACTOR
# ============================================================

def calculate_future_factor(
    row,
    config
):

    predicted_value = safe_float(
        row[
            "predicted_168h_uA"
        ]
    )

    lower_value = safe_float(
        row[
            "prediction_lower_uA"
        ]
    )

    upper_value = safe_float(
        row[
            "prediction_upper_uA"
        ]
    )

    # lower_value is retained as part of the prediction
    # evidence, even though upper-bound uncertainty is the
    # safety-relevant direction for this risk calculation.

    _ = lower_value

    absolute_limit = safe_float(
        row.get(
            "absolute_limit_uA",
            config
            .get(
                "risk_limits",
                {}
            )
            .get(
                "default_absolute_limit_uA",
                50.0
            )
        )
    )

    if absolute_limit <= 0:

        absolute_limit = safe_float(
            config
            .get(
                "risk_limits",
                {}
            )
            .get(
                "default_absolute_limit_uA",
                50.0
            ),
            50.0
        )

    # --------------------------------------------------------
    # Prediction relative to safety limit.
    # --------------------------------------------------------

    predicted_ratio = (
        predicted_value
        /
        absolute_limit
    )

    upper_ratio = (
        upper_value
        /
        absolute_limit
    )

    watch_ratio = safe_float(
        config
        .get(
            "risk_limits",
            {}
        )
        .get(
            "future_limit_watch_ratio",
            0.80
        ),
        0.80
    )

    high_ratio = safe_float(
        config
        .get(
            "risk_limits",
            {}
        )
        .get(
            "future_limit_high_ratio",
            1.00
        ),
        1.00
    )

    # --------------------------------------------------------
    # Predicted future-value risk.
    # --------------------------------------------------------

    if predicted_ratio >= high_ratio:

        predicted_risk = 1.0

    elif predicted_ratio >= watch_ratio:

        predicted_risk = (

            predicted_ratio
            -
            watch_ratio

        ) / max(
            high_ratio
            -
            watch_ratio,
            0.000001
        )

    else:

        predicted_risk = (

            predicted_ratio
            /
            watch_ratio

        ) * 0.35

    predicted_risk = clamp(
        predicted_risk
    )

    # --------------------------------------------------------
    # Prediction interval uncertainty.
    # --------------------------------------------------------

    if upper_ratio >= high_ratio:

        uncertainty_risk = 1.0

    elif upper_ratio >= watch_ratio:

        uncertainty_risk = 0.60

    else:

        uncertainty_risk = 0.0

    # --------------------------------------------------------
    # Explicit Module B future-risk flags.
    # --------------------------------------------------------

    predicted_limit_flag = safe_float(
        row[
            "predicted_limit_exceeded"
        ]
    )

    uncertainty_failure_flag = safe_float(
        row[
            "uncertainty_adjusted_failure"
        ]
    )

    future_drift_risk = clamp(
        safe_float(
            row[
                "future_drift_risk"
            ]
        )
    )

    # --------------------------------------------------------
    # Do not add correlated future flags together.
    #
    # Instead, use the strongest explicit future signal.
    # --------------------------------------------------------

    explicit_future_flag = max(

        predicted_limit_flag,

        uncertainty_failure_flag
    )

    future_factor = max(

        predicted_risk,

        0.60
        * uncertainty_risk,

        0.80
        * future_drift_risk,

        explicit_future_flag
    )

    return clamp(
        future_factor
    )


# ============================================================
# MODULE A
# SPECIFICATION RISK FACTOR
# ============================================================

def calculate_specification_factor(
    row
):

    limit_violation = safe_float(
        row[
            "limit_violation"
        ]
    )

    limit_excess = safe_float(
        row[
            "limit_excess_uA"
        ]
    )

    absolute_limit = safe_float(
        row[
            "absolute_limit_uA"
        ]
    )

    # Actual specification violation = maximum specification
    # risk contribution.

    if limit_violation >= 1:

        return 1.0

    if absolute_limit <= 0:

        return 0.0

    excess_ratio = (
        limit_excess
        /
        absolute_limit
    )

    return clamp(
        excess_ratio
    )


# ============================================================
# FINAL RISK FUSION
# ============================================================

def calculate_overall_risk(

    anomaly_factor,

    drift_factor,

    future_factor,

    specification_factor,

    config
):

    weights = config[
        "risk_calculation"
    ][
        "weights"
    ]

    anomaly_weight = safe_float(
        weights[
            "anomaly"
        ]
    )

    drift_weight = safe_float(
        weights[
            "drift"
        ]
    )

    future_weight = safe_float(
        weights[
            "future"
        ]
    )

    specification_weight = safe_float(
        weights[
            "specification"
        ]
    )

    total_weight = (

        anomaly_weight
        +
        drift_weight
        +
        future_weight
        +
        specification_weight
    )

    if total_weight <= 0:

        return 0.0

    weighted_score = (

        anomaly_factor
        * anomaly_weight

        +

        drift_factor
        * drift_weight

        +

        future_factor
        * future_weight

        +

        specification_factor
        * specification_weight
    )

    normalized_score = (
        weighted_score
        /
        total_weight
    )

    return (
        clamp(
            normalized_score
        )
        *
        100.0
    )


# ============================================================
# QA POLICY CLASSIFICATION
# ============================================================

def classify_risk(
    risk_score,
    config
):

    classifications = config[
        "qa_policy"
    ][
        "classifications"
    ]

    for classification in classifications:

        minimum = safe_float(
            classification[
                "min_risk"
            ]
        )

        maximum = safe_float(
            classification[
                "max_risk"
            ]
        )

        if (
            minimum
            <=
            risk_score
            <
            maximum
        ):

            return classification[
                "name"
            ]

    # Handle exact 100 boundary.

    for classification in classifications:

        maximum = safe_float(
            classification[
                "max_risk"
            ]
        )

        if (
            risk_score
            ==
            maximum
        ):

            return classification[
                "name"
            ]

    return "Unclassified"


# ============================================================
# EXPLANATION
# ============================================================

def build_explanation(

    anomaly_factor,

    drift_factor,

    future_factor,

    specification_factor,

    risk_score,

    classification
):

    factors = {

        "Anomaly":
            anomaly_factor,

        "Drift":
            drift_factor,

        "Future":
            future_factor,

        "Specification":
            specification_factor
    }

    sorted_factors = sorted(

        factors.items(),

        key=lambda item:
            item[1],

        reverse=True
    )

    main_factor = sorted_factors[0]

    factor_text = (

        f"{main_factor[0]} evidence is the "
        f"strongest risk contributor "
        f"({main_factor[1] * 100:.1f}%)."
    )

    return (

        f"Risk score: "
        f"{risk_score:.2f}/100. "

        f"QA classification: "
        f"{classification}. "

        f"{factor_text}"
    )


# ============================================================
# PROCESS ONE CUMULATIVE STAGE
# ============================================================

def process_stage(

    module_a_path,

    module_b_df,

    config,

    stage_number
):

    print("\n" + "=" * 70)

    print(
        f"PROCESSING CUMULATIVE STAGE "
        f"{stage_number}"
    )

    print("=" * 70)

    print(
        f"Module A: {module_a_path}"
    )

    # --------------------------------------------------------
    # Read cumulative Module A stage.
    # --------------------------------------------------------

    module_a_df = pd.read_csv(
        module_a_path
    )

    validate_module_a(
        module_a_df,
        module_a_path
    )

    module_a_df[
        "component_id"
    ] = normalize_component_id(
        module_a_df[
            "component_id"
        ]
    )

    # --------------------------------------------------------
    # Normalize Module B IDs.
    # --------------------------------------------------------

    module_b_df[
        "component_id"
    ] = normalize_component_id(
        module_b_df[
            "component_id"
        ]
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # Module A stage is already cumulative.
    #
    # For example:
    #
    # stage 01 = 2,000
    # stage 02 = 4,000
    # stage 03 = 6,000
    #
    # We DO NOT combine:
    #
    # stage01 + stage02
    #
    # Instead we directly process stage02 as the cumulative
    # 4,000-component dataset.
    # --------------------------------------------------------

    current_ids = set(
        module_a_df[
            "component_id"
        ]
    )

    matching_module_b = module_b_df[
        module_b_df[
            "component_id"
        ].isin(
            current_ids
        )
    ].copy()

    print(
        f"Module A cumulative components: "
        f"{len(module_a_df)}"
    )

    print(
        f"Unique Module A components: "
        f"{module_a_df['component_id'].nunique()}"
    )

    print(
        f"Module B matching components: "
        f"{len(matching_module_b)}"
    )

    # --------------------------------------------------------
    # Remove duplicate Module B IDs.
    # --------------------------------------------------------

    duplicate_count = (
        matching_module_b[
            "component_id"
        ]
        .duplicated()
        .sum()
    )

    if duplicate_count > 0:

        print(
            f"WARNING: Module B contains "
            f"{duplicate_count} duplicate IDs."
        )

        matching_module_b = (
            matching_module_b
            .drop_duplicates(
                subset=[
                    "component_id"
                ],
                keep="last"
            )
        )

    # --------------------------------------------------------
    # Index Module B by component ID.
    # --------------------------------------------------------

    module_b_indexed = (
        matching_module_b
        .set_index(
            "component_id"
        )
    )

    result_rows = []

    missing_module_b = 0

    # ========================================================
    # PROCESS EVERY COMPONENT IN CURRENT CUMULATIVE STAGE
    # ========================================================

    for _, module_a_row in (
        module_a_df.iterrows()
    ):

        component_id = (
            module_a_row[
                "component_id"
            ]
        )

        # ----------------------------------------------------
        # Find Module B evidence.
        # ----------------------------------------------------

        if (
            component_id
            in
            module_b_indexed.index
        ):

            module_b_row = (
                module_b_indexed.loc[
                    component_id
                ]
            )

        else:

            module_b_row = None

            missing_module_b += 1

        # ----------------------------------------------------
        # 1. ANOMALY
        # ----------------------------------------------------

        anomaly_factor = (
            calculate_anomaly_factor(
                module_a_row
            )
        )

        # ----------------------------------------------------
        # 2. DRIFT + FUTURE
        # ----------------------------------------------------

        if module_b_row is not None:

            drift_factor = (
                calculate_drift_factor(
                    module_b_row,
                    config
                )
            )

            future_factor = (
                calculate_future_factor(
                    module_b_row,
                    config
                )
            )

        else:

            drift_factor = 0.0

            future_factor = 0.0

        # ----------------------------------------------------
        # 3. SPECIFICATION
        # ----------------------------------------------------

        specification_factor = (
            calculate_specification_factor(
                module_a_row
            )
        )

        # ----------------------------------------------------
        # 4. FINAL RISK
        # ----------------------------------------------------

        risk_score = (
            calculate_overall_risk(

                anomaly_factor,

                drift_factor,

                future_factor,

                specification_factor,

                config
            )
        )

        # ----------------------------------------------------
        # 5. QA POLICY
        # ----------------------------------------------------

        classification = (
            classify_risk(
                risk_score,
                config
            )
        )

        # ----------------------------------------------------
        # 6. EXPLANATION
        # ----------------------------------------------------

        explanation = (
            build_explanation(

                anomaly_factor,

                drift_factor,

                future_factor,

                specification_factor,

                risk_score,

                classification
            )
        )

        # ----------------------------------------------------
        # BASE RESULT
        # ----------------------------------------------------

        result = {

            "stage":
                stage_number,

            "component_id":
                component_id,

            "lot_id":
                module_a_row.get(
                    "lot_id",
                    ""
                ),

            "component_type":
                module_a_row.get(
                    "component_type",
                    ""
                ),

            "temperature_C":
                module_a_row.get(
                    "temperature_C",
                    ""
                ),

            "voltage_V":
                module_a_row.get(
                    "voltage_V",
                    ""
                ),

            # ==============================================
            # RISK FACTORS
            # ==============================================

            "anomaly_factor":
                anomaly_factor,

            "drift_factor":
                drift_factor,

            "future_factor":
                future_factor,

            "specification_factor":
                specification_factor,

            # ==============================================
            # FINAL RISK
            # ==============================================

            "risk_score":
                risk_score,

            "qa_classification":
                classification,

            "risk_explanation":
                explanation,

            # ==============================================
            # MODULE A EVIDENCE
            # ==============================================

            "combined_anomaly_score":
                module_a_row.get(
                    "combined_anomaly_score",
                    0
                ),

            "anomaly_flag":
                module_a_row.get(
                    "anomaly_flag",
                    0
                ),

            "statistical_score":
                module_a_row.get(
                    "statistical_score",
                    0
                ),

            "statistical_anomaly_flag":
                module_a_row.get(
                    "statistical_anomaly_flag",
                    0
                ),

            "temporal_anomaly_score":
                module_a_row.get(
                    "temporal_anomaly_score",
                    0
                ),

            "temporal_anomaly_flag":
                module_a_row.get(
                    "temporal_anomaly_flag",
                    0
                ),

            "isolation_forest_score":
                module_a_row.get(
                    "isolation_forest_score",
                    0
                ),

            "isolation_forest_flag":
                module_a_row.get(
                    "isolation_forest_flag",
                    0
                ),

            "statistical_evidence_count":
                module_a_row.get(
                    "statistical_evidence_count",
                    0
                ),

            "limit_violation":
                module_a_row.get(
                    "limit_violation",
                    0
                ),

            "limit_excess_uA":
                module_a_row.get(
                    "limit_excess_uA",
                    0
                ),

            "absolute_limit_uA":
                module_a_row.get(
                    "absolute_limit_uA",
                    ""
                )
        }

        # ----------------------------------------------------
        # MODULE B EVIDENCE
        # ----------------------------------------------------

        if module_b_row is not None:

            module_b_columns = [

                "predicted_168h_uA",

                "prediction_lower_uA",

                "prediction_upper_uA",

                "prediction_error_uA",

                "absolute_prediction_error_uA",

                "predicted_drift_uA",

                "predicted_drift_rate",

                "predicted_relative_drift",

                "safety_slope",

                "drift_slope_excess",

                "early_drift_flag",

                "predicted_limit_exceeded",

                "uncertainty_adjusted_failure",

                "limit_margin_uA",

                "upper_bound_limit_margin_uA",

                "future_drift_risk",

                "module_b_status"
            ]

            for column in module_b_columns:

                if column in module_b_row.index:

                    result[
                        column
                    ] = module_b_row[
                        column
                    ]

            result[
                "module_b_match"
            ] = True

        else:

            result[
                "module_b_match"
            ] = False

        result_rows.append(
            result
        )

    # ========================================================
    # CREATE RESULT DATAFRAME
    # ========================================================

    result_df = pd.DataFrame(
        result_rows
    )

    # --------------------------------------------------------
    # Highest risk first.
    # --------------------------------------------------------

    result_df = (
        result_df
        .sort_values(
            by="risk_score",
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )

    # ========================================================
    # SAVE CURRENT STAGE
    # ========================================================

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    stage_output = os.path.join(

        OUTPUT_DIR,

        f"risk_stage_"
        f"{stage_number:02d}.csv"
    )

    result_df.to_csv(
        stage_output,
        index=False
    )

    print(
        f"\nSaved: {stage_output}"
    )

    print(
        f"Rows written: "
        f"{len(result_df)}"
    )

    if missing_module_b > 0:

        print(
            f"WARNING: "
            f"{missing_module_b} components "
            f"have no Module B prediction."
        )

    # ========================================================
    # STAGE SUMMARY
    # ========================================================

    summary = {

        "stage":
            stage_number,

        "components_processed":
            len(result_df),

        "module_b_matches":
            int(
                result_df[
                    "module_b_match"
                ].sum()
            ),

        "module_b_missing":
            int(
                missing_module_b
            ),

        "mean_risk_score":
            round(
                result_df[
                    "risk_score"
                ].mean(),
                4
            ),

        "max_risk_score":
            round(
                result_df[
                    "risk_score"
                ].max(),
                4
            ),

        "min_risk_score":
            round(
                result_df[
                    "risk_score"
                ].min(),
                4
            )
    }

    # --------------------------------------------------------
    # Add configurable QA counts.
    # --------------------------------------------------------

    classification_counts = (

        result_df[
            "qa_classification"
        ]
        .value_counts()
        .to_dict()
    )

    for (
        classification,
        count
    ) in classification_counts.items():

        safe_name = (

            str(
                classification
            )
            .strip()
            .lower()
            .replace(
                " ",
                "_"
            )
        )

        summary[
            f"qa_{safe_name}"
        ] = int(
            count
        )

    return (
        result_df,
        summary
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("\n")

    print("=" * 70)

    print(
        "PLEIONE - CONFIGURABLE RISK SCORING "
        "& QA POLICY ENGINE"
    )

    print("=" * 70)

    # ========================================================
    # LOAD CONFIGURATION
    # ========================================================

    print(
        "\nLoading configuration..."
    )

    config = load_config()

    print(
        "Configuration loaded successfully."
    )

    # --------------------------------------------------------
    # Display weights.
    # --------------------------------------------------------

    weights = config[
        "risk_calculation"
    ][
        "weights"
    ]

    print(
        "\nRisk weights:"
    )

    for (
        name,
        weight
    ) in weights.items():

        print(
            f"  {name:<15}: "
            f"{weight}"
        )

    # --------------------------------------------------------
    # Display QA policy.
    # --------------------------------------------------------

    print(
        "\nQA classifications:"
    )

    for classification in config[
        "qa_policy"
    ][
        "classifications"
    ]:

        print(

            f"  {classification['name']}: "
            f"{classification['min_risk']} - "
            f"{classification['max_risk']}"
        )

    # ========================================================
    # FIND ONLY MODULE A STAGES 1-5
    # ========================================================

    print(
        "\nChecking Module A cumulative stages..."
    )

    stage_files = []

    for stage_number in range(
        1,
        MAX_SUPPORTED_STAGE + 1
    ):

        stage_path = os.path.join(

            MODULE_A_DIR,

            f"stage_"
            f"{stage_number:02d}.csv"
        )

        if os.path.exists(
            stage_path
        ):

            stage_files.append(
                stage_path
            )

        else:

            print(
                f"WARNING: Expected stage "
                f"{stage_number} not found:"
            )

            print(
                f"         {stage_path}"
            )

    if not stage_files:

        raise FileNotFoundError(

            "No supported Module A "
            "stage files were found."
        )

    print(
        "\nStages that WILL be processed:"
    )

    for path in stage_files:

        print(
            f"  {os.path.basename(path)}"
        )

    print(
        "\nStages 6-10 are intentionally "
        "ignored because Module B currently "
        "has only 10,000 predictions."
    )

    # ========================================================
    # LOAD MODULE B
    # ========================================================

    print(
        "\nLoading Module B predictions..."
    )

    if not os.path.exists(
        MODULE_B_PATH
    ):

        raise FileNotFoundError(

            f"Module B file not found:\n"
            f"{MODULE_B_PATH}"
        )

    module_b_df = pd.read_csv(
        MODULE_B_PATH
    )

    validate_module_b(
        module_b_df
    )

    module_b_df[
        "component_id"
    ] = normalize_component_id(
        module_b_df[
            "component_id"
        ]
    )

    print(
        f"Module B rows: "
        f"{len(module_b_df)}"
    )

    print(
        f"Module B unique components: "
        f"{module_b_df['component_id'].nunique()}"
    )

    # ========================================================
    # PROCESS STAGES 1-5
    # ========================================================

    all_summaries = []

    latest_result = None

    for stage_file in stage_files:

        # ----------------------------------------------------
        # Get stage number directly from filename.
        #
        # No stage_summary.csv can reach this point because
        # we explicitly constructed stage_files above.
        # ----------------------------------------------------

        filename = os.path.basename(
            stage_file
        )

        stage_number = int(

            filename
            .replace(
                "stage_",
                ""
            )
            .replace(
                ".csv",
                ""
            )
        )

        result_df, summary = process_stage(

            stage_file,

            module_b_df,

            config,

            stage_number
        )

        all_summaries.append(
            summary
        )

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # This is NOT accumulating risk scores.
        #
        # latest_result simply points to the newest cumulative
        # stage.
        #
        # Therefore after stage 5, it contains all 10,000
        # components.
        # ----------------------------------------------------

        latest_result = result_df

    # ========================================================
    # SAVE STAGE SUMMARY
    # ========================================================

    summary_df = pd.DataFrame(
        all_summaries
    )

    summary_df.to_csv(

        SUMMARY_PATH,

        index=False
    )

    print(
        f"\nSaved stage summary:"
    )

    print(
        SUMMARY_PATH
    )

    # ========================================================
    # SAVE FINAL OVERALL RESULT
    # ========================================================

    if latest_result is not None:

        latest_result.to_csv(

            OVERALL_OUTPUT_PATH,

            index=False
        )

        print(
            "\n"
            + "=" * 70
        )

        print(
            "FINAL CUMULATIVE RISK RESULT"
        )

        print(
            "=" * 70
        )

        print(
            f"Saved: "
            f"{OVERALL_OUTPUT_PATH}"
        )

        print(
            f"Total components: "
            f"{len(latest_result)}"
        )

        print(
            f"Average risk: "
            f"{latest_result['risk_score'].mean():.2f}"
        )

        print(
            f"Maximum risk: "
            f"{latest_result['risk_score'].max():.2f}"
        )

        # ----------------------------------------------------
        # QA distribution
        # ----------------------------------------------------

        print(
            "\nQA classification counts:"
        )

        print(
            latest_result[
                "qa_classification"
            ]
            .value_counts()
            .to_string()
        )

        # ----------------------------------------------------
        # Top risk components
        # ----------------------------------------------------

        print(
            "\nTop 10 highest-risk components:"
        )

        display_columns = [

            "component_id",

            "component_type",

            "risk_score",

            "qa_classification",

            "anomaly_factor",

            "drift_factor",

            "future_factor",

            "specification_factor"
        ]

        print(

            latest_result[
                display_columns
            ]
            .head(10)
            .to_string(
                index=False
            )
        )

    # ========================================================
    # FINISHED
    # ========================================================

    print(
        "\n"
        + "=" * 70
    )

    print(
        "RISK ENGINE COMPLETED SUCCESSFULLY"
    )

    print(
        "=" * 70
    )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()