"""
MODULE C - MULTI-EVIDENCE RISK ENGINE

Module A:
    0h peer-aware anomaly evidence

Module B:
    0h + 24h future-risk evidence

Module C:
    Specification-aware evidence aggregation

IMPORTANT
---------
The decision uses only:

    Module A
    Module B
    absolute specification limit

96h, 168h and ground_truth are NOT used
to generate decisions.

The 168h historical values remain available
only for offline evaluation.

Outputs:

    module_C_all_results.csv
        -> 10,000 components

    module_C_batch5_results.csv
        -> Batch 5 evaluation subset
"""


from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parents[1]

MODULE_A_PATH = (
    BASE_DIR
    / "data"
    / "module_A"
    / "module_A_all_predictions.csv"
)

MODULE_B_PATH = (
    BASE_DIR
    / "data"
    / "module_B"
    / "module_B_predictions.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "module_C"
)

ALL_OUTPUT_PATH = (
    OUTPUT_DIR
    / "module_C_all_results.csv"
)

BATCH5_OUTPUT_PATH = (
    OUTPUT_DIR
    / "module_C_batch5_results.csv"
)


# ============================================================
# CONFIGURATION
# ============================================================

CLASSIFIER_HIGH_THRESHOLD = 0.75
CLASSIFIER_MEDIUM_THRESHOLD = 0.40

MODULE_A_WATCH_STATUSES = {
    "WATCH",
    "ANOMALOUS",
}


# ============================================================
# HELPERS
# ============================================================

def require_columns(
    df,
    required_columns,
    source_name,
):

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            f"{source_name} is missing required columns:\n"
            + "\n".join(
                f"  - {column}"
                for column in missing
            )
        )


def safe_bool(value):

    if isinstance(value, bool):
        return value

    if pd.isna(value):
        return False

    if isinstance(value, str):

        return (
            value.strip().lower()
            in {
                "true",
                "1",
                "yes",
                "y",
            }
        )

    return bool(value)


# ============================================================
# EXPLANATIONS
# ============================================================

def build_decision_reason(row):

    reasons = []

    if safe_bool(
        row[
            "point_prediction_exceeds_limit"
        ]
    ):

        reasons.append(
            "Projected 168h value exceeds "
            "the specification limit."
        )

    if safe_bool(
        row[
            "classifier_high_risk"
        ]
    ):

        reasons.append(
            "Module B assigns a high probability "
            "of future specification violation."
        )

    elif safe_bool(
        row[
            "classifier_medium_or_higher"
        ]
    ):

        reasons.append(
            "Module B assigns elevated probability "
            "of future specification violation."
        )

    if safe_bool(
        row[
            "uncertainty_crosses_limit"
        ]
    ):

        reasons.append(
            "The prediction uncertainty range "
            "crosses the specification limit."
        )

    if (
        row["module_a_status"]
        == "ANOMALOUS"
    ):

        reasons.append(
            "Module A detected a strong "
            "0h peer-level anomaly."
        )

    elif (
        row["module_a_status"]
        == "WATCH"
    ):

        reasons.append(
            "Module A detected a mild "
            "0h peer-level deviation."
        )

    if not reasons:

        reasons.append(
            "No strong early-warning "
            "evidence was detected."
        )

    return " ".join(reasons)


def build_investigation_summary(row):

    decision = row[
        "final_decision"
    ]

    risk = row[
        "future_risk"
    ]

    evidence = row[
        "evidence_level"
    ]

    if decision == "REJECT":

        return (
            f"Critical future-risk case with "
            f"{evidence.lower()} evidence. "
            "The available early measurements "
            "indicate that the component is "
            "projected to exceed the "
            "specification limit."
        )

    if decision == "REVIEW":

        if row[
            "module_a_status"
        ] in {
            "WATCH",
            "ANOMALOUS",
        }:

            return (
                f"{risk} future-risk case "
                "requiring investigation. "
                "Early peer behavior and/or "
                "future-risk evidence indicates "
                "that the component should "
                "receive additional review."
            )

        return (
            f"{risk} future-risk case "
            "requiring investigation. "
            "Module B and/or prediction "
            "uncertainty indicates elevated "
            "future specification risk."
        )

    return (
        "Low current and projected risk "
        "based on the available 0h and "
        "24h evidence. Continue normal "
        "screening."
    )


def build_recommended_action(row):

    decision = row[
        "final_decision"
    ]

    if decision == "REJECT":

        return (
            "Remove from normal screening flow "
            "and investigate component disposition."
        )

    if decision == "REVIEW":

        return (
            "Investigate component and compare "
            "with its peer group before final "
            "screening disposition."
        )

    return (
        "Continue normal screening."
    )


# ============================================================
# LOAD DATA
# ============================================================

print()

print("=" * 70)
print(
    "MODULE C - MULTI-EVIDENCE RISK ENGINE"
)
print("=" * 70)

module_a = pd.read_csv(
    MODULE_A_PATH
)

module_b = pd.read_csv(
    MODULE_B_PATH
)

print()

print("INPUTS")
print("-" * 70)

print(
    f"Module A rows : {len(module_a):,}"
)

print(
    f"Module B rows : {len(module_b):,}"
)


# ============================================================
# REQUIRED COLUMNS
# ============================================================

require_columns(
    module_a,
    [
        "component_id",
        "module_a_score",
        "module_a_status",
        "peer_source",
    ],
    "Module A",
)

require_columns(
    module_b,
    [
        "component_id",
        "lot_id",
        "component_type",
        "temperature_C",
        "voltage_V",
        "iddq_0h_uA",
        "iddq_24h_uA",
        "delta_0_24",
        "predicted_168h_uA",
        "prediction_lower_uA",
        "prediction_upper_uA",
        "prediction_interval_width_uA",
        "failure_probability",
        "predicted_future_violation",
        "failure_risk",
        "absolute_limit_uA",
        "batch",
    ],
    "Module B",
)


# ============================================================
# DUPLICATE CHECK
# ============================================================

if module_a[
    "component_id"
].duplicated().any():

    raise ValueError(
        "Duplicate component_id values "
        "found in Module A."
    )


if module_b[
    "component_id"
].duplicated().any():

    raise ValueError(
        "Duplicate component_id values "
        "found in Module B."
    )


# ============================================================
# SELECT MODULE A
# ============================================================

module_a = module_a[
    [
        "component_id",
        "module_a_score",
        "module_a_status",
        "peer_source",
    ]
].copy()


# ============================================================
# SELECT MODULE B
# ============================================================

module_b = module_b[
    [
        "component_id",
        "lot_id",
        "component_type",
        "temperature_C",
        "voltage_V",
        "iddq_0h_uA",
        "iddq_24h_uA",
        "delta_0_24",
        "predicted_168h_uA",
        "prediction_lower_uA",
        "prediction_upper_uA",
        "prediction_interval_width_uA",
        "failure_probability",
        "predicted_future_violation",
        "failure_risk",
        "absolute_limit_uA",
        "batch",
    ]
].copy()


# ============================================================
# MERGE
# ============================================================

results = module_b.merge(
    module_a,
    on="component_id",
    how="inner",
    validate="one_to_one",
)

print(
    f"Merged components : "
    f"{len(results):,}"
)

if len(results) != 10000:

    raise ValueError(
        "Expected 10,000 merged components "
        f"but received {len(results):,}."
    )


# ============================================================
# NORMALIZE NUMERIC VALUES
# ============================================================

numeric_columns = [
    "module_a_score",
    "predicted_168h_uA",
    "prediction_lower_uA",
    "prediction_upper_uA",
    "prediction_interval_width_uA",
    "failure_probability",
    "absolute_limit_uA",
]

for column in numeric_columns:

    results[column] = pd.to_numeric(
        results[column],
        errors="coerce",
    )


if results[
    numeric_columns
].isna().any().any():

    raise ValueError(
        "Invalid numeric values found "
        "in Module C inputs."
    )


# ============================================================
# EVIDENCE FLAGS
# ============================================================

results[
    "point_prediction_exceeds_limit"
] = (
    results[
        "predicted_168h_uA"
    ]
    >
    results[
        "absolute_limit_uA"
    ]
)

results[
    "uncertainty_crosses_limit"
] = (
    results[
        "prediction_upper_uA"
    ]
    >
    results[
        "absolute_limit_uA"
    ]
)

results[
    "classifier_high_risk"
] = (
    results[
        "failure_probability"
    ]
    >= CLASSIFIER_HIGH_THRESHOLD
)

results[
    "classifier_medium_or_higher"
] = (
    results[
        "failure_probability"
    ]
    >= CLASSIFIER_MEDIUM_THRESHOLD
)

results[
    "module_a_watch_or_higher"
] = (
    results[
        "module_a_status"
    ]
    .astype(str)
    .str.upper()
    .isin(
        MODULE_A_WATCH_STATUSES
    )
)

results[
    "module_a_anomalous"
] = (
    results[
        "module_a_status"
    ]
    .astype(str)
    .str.upper()
    == "ANOMALOUS"
)


# ============================================================
# EVIDENCE SCORE
# ============================================================

results[
    "evidence_score"
] = 0

results.loc[
    results[
        "point_prediction_exceeds_limit"
    ],
    "evidence_score",
] += 3

results.loc[
    results[
        "uncertainty_crosses_limit"
    ],
    "evidence_score",
] += 1

results.loc[
    results[
        "classifier_high_risk"
    ],
    "evidence_score",
] += 2

results.loc[
    results[
        "classifier_medium_or_higher"
    ]
    &
    ~results[
        "classifier_high_risk"
    ],
    "evidence_score",
] += 1

results.loc[
    results[
        "module_a_anomalous"
    ],
    "evidence_score",
] += 2

results.loc[
    results[
        "module_a_status"
    ]
    .astype(str)
    .str.upper()
    == "WATCH",
    "evidence_score",
] += 1


# ============================================================
# EVIDENCE LEVEL
# ============================================================

def get_evidence_level(score):

    if score >= 5:
        return "STRONG"

    if score >= 3:
        return "HIGH"

    if score >= 2:
        return "MEDIUM"

    return "LOW"


results[
    "evidence_level"
] = results[
    "evidence_score"
].apply(
    get_evidence_level
)


# ============================================================
# FINAL DECISION
# ============================================================

def make_final_decision(row):

    predicted = row[
        "predicted_168h_uA"
    ]

    upper = row[
        "prediction_upper_uA"
    ]

    limit = row[
        "absolute_limit_uA"
    ]

    probability = row[
        "failure_probability"
    ]

    module_a_status = str(
        row[
            "module_a_status"
        ]
    ).upper()

    # 1. Direct projected violation.
    if predicted > limit:
        return "REJECT"

    # 2. Strong classifier evidence.
    if (
        probability
        >= CLASSIFIER_HIGH_THRESHOLD
    ):
        return "REVIEW"

    # 3. Uncertainty + Module A evidence.
    if (
        upper > limit
        and module_a_status
        in {
            "WATCH",
            "ANOMALOUS",
        }
    ):
        return "REVIEW"

    # 4. Medium classifier evidence.
    if (
        probability
        >= CLASSIFIER_MEDIUM_THRESHOLD
    ):
        return "REVIEW"

    # 5. Uncertainty crosses limit.
    if upper > limit:
        return "REVIEW"

    # 6. Strong Module A anomaly.
    if module_a_status == "ANOMALOUS":
        return "REVIEW"

    # 7. Module A WATCH.
    if module_a_status == "WATCH":
        return "PASS"

    return "PASS"


results[
    "final_decision"
] = results.apply(
    make_final_decision,
    axis=1,
)


# ============================================================
# FUTURE RISK
# ============================================================

def get_future_risk(row):

    decision = row[
        "final_decision"
    ]

    probability = row[
        "failure_probability"
    ]

    if decision == "REJECT":
        return "CRITICAL"

    if decision == "REVIEW":

        if (
            probability
            >= CLASSIFIER_HIGH_THRESHOLD
        ):
            return "HIGH"

        return "MEDIUM"

    return "LOW"


results[
    "future_risk"
] = results.apply(
    get_future_risk,
    axis=1,
)


# ============================================================
# EXPLANATIONS
# ============================================================

results[
    "decision_reason"
] = results.apply(
    build_decision_reason,
    axis=1,
)

results[
    "investigation_summary"
] = results.apply(
    build_investigation_summary,
    axis=1,
)

results[
    "recommended_action"
] = results.apply(
    build_recommended_action,
    axis=1,
)


# ============================================================
# OUTPUT COLUMN ORDER
# ============================================================

output_columns = [

    "component_id",
    "lot_id",
    "component_type",

    "temperature_C",
    "voltage_V",

    "iddq_0h_uA",
    "iddq_24h_uA",
    "delta_0_24",

    "module_a_score",
    "module_a_status",
    "peer_source",

    "predicted_168h_uA",
    "prediction_lower_uA",
    "prediction_upper_uA",
    "prediction_interval_width_uA",

    "failure_probability",
    "predicted_future_violation",
    "failure_risk",

    "absolute_limit_uA",

    "point_prediction_exceeds_limit",
    "uncertainty_crosses_limit",
    "classifier_high_risk",
    "classifier_medium_or_higher",
    "module_a_watch_or_higher",
    "module_a_anomalous",

    "evidence_score",
    "evidence_level",

    "final_decision",
    "future_risk",

    "decision_reason",
    "investigation_summary",
    "recommended_action",

    "batch",
]

results = results[
    output_columns
]


# ============================================================
# BATCH 5 SUBSET
# ============================================================

batch5_results = results[
    results["batch"] == "batch_5"
].copy()


# ============================================================
# SAVE
# ============================================================

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

results.to_csv(
    ALL_OUTPUT_PATH,
    index=False,
)

batch5_results.to_csv(
    BATCH5_OUTPUT_PATH,
    index=False,
)


# ============================================================
# REPORT
# ============================================================

print()

print("=" * 70)
print("MODULE C DATASET COUNTS")
print("=" * 70)

print(
    f"All components : "
    f"{len(results):,}"
)

print(
    f"Batch 5        : "
    f"{len(batch5_results):,}"
)

print()

print("BY LOT")
print("-" * 70)

print(
    results[
        "lot_id"
    ]
    .value_counts()
    .sort_index()
    .to_string()
)

print()

print("=" * 70)
print("FINAL DECISION - ALL 10,000")
print("=" * 70)

print(
    results[
        "final_decision"
    ].value_counts()
)

print()

print("=" * 70)
print("FUTURE RISK - ALL 10,000")
print("=" * 70)

print(
    results[
        "future_risk"
    ].value_counts()
)

print()

print("=" * 70)
print("EVIDENCE LEVEL - ALL 10,000")
print("=" * 70)

print(
    results[
        "evidence_level"
    ].value_counts()
)

print()

print("=" * 70)
print("MODULE A STATUS - ALL 10,000")
print("=" * 70)

print(
    results[
        "module_a_status"
    ].value_counts()
)

print()

print("=" * 70)
print("MODULE B FAILURE RISK - ALL 10,000")
print("=" * 70)

print(
    results[
        "failure_risk"
    ].value_counts()
)

print()

print("=" * 70)
print("FILES")
print("=" * 70)

print(
    ALL_OUTPUT_PATH
)

print(
    BATCH5_OUTPUT_PATH
)

print()

print("=" * 70)
print("MODULE C COMPLETE")
print("=" * 70)