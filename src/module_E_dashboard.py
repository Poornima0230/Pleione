# ============================================================
# SIH 26170
# MODULE E: INTERACTIVE SCREENING DASHBOARD
#
# Purpose:
# ------------------------------------------------------------
# Convert Modules A-D outputs into an interactive engineering
# screening dashboard.
#
# Modules:
#
# A -> Current anomaly detection
# B -> Future drift prediction
# C -> Risk fusion
# D -> Explainability
# E -> Interactive dashboard
#
# IMPORTANT:
# ------------------------------------------------------------
# This dashboard is a prototype decision-support interface.
# It does NOT replace ISRO-qualified engineering screening.
# ============================================================


import os

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# CONFIGURATION
# ============================================================

DATA_DIR = "data"

MODULE_C_PATH = os.path.join(
    DATA_DIR,
    "final_risk_assessment.csv"
)

MODULE_D_PATH = os.path.join(
    DATA_DIR,
    "module_D_explanations.csv"
)

PRIORITY_PATH = os.path.join(
    DATA_DIR,
    "priority_screening_list.csv"
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(

    page_title="SIH 26170 | Component Screening",

    page_icon="🔬",

    layout="wide",

    initial_sidebar_state="expanded"

)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {

        font-size: 32px;
        font-weight: 700;
        margin-bottom: 5px;

    }

    .subtitle {

        color: #666;
        font-size: 16px;
        margin-bottom: 25px;

    }

    .risk-card {

        padding: 15px;
        border-radius: 10px;
        border: 1px solid #ddd;
        background-color: #fafafa;

    }

    .warning-box {

        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e0a800;
        background-color: #fff8e1;

    }

    .info-box {

        padding: 15px;
        border-radius: 8px;
        border: 1px solid #aaa;
        background-color: #f5f5f5;

    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🔬 AI-Driven Component Burn-In Screening</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'SIH 26170 | Early Anomaly Detection, Future Drift Prediction '
    '& Risk-Based Screening'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_data():

    module_c = pd.read_csv(
        MODULE_C_PATH
    )

    module_d = None

    if os.path.exists(MODULE_D_PATH):

        module_d = pd.read_csv(
            MODULE_D_PATH
        )

    priority = None

    if os.path.exists(PRIORITY_PATH):

        priority = pd.read_csv(
            PRIORITY_PATH
        )

    return module_c, module_d, priority


# ============================================================
# CHECK FILES
# ============================================================

if not os.path.exists(MODULE_C_PATH):

    st.error(
        "Module C output not found:\n\n"
        f"{MODULE_C_PATH}"
    )

    st.stop()


df, module_d, priority_df = load_data()


# ============================================================
# MERGE MODULE D IF NECESSARY
# ============================================================

if module_d is not None:

    if "component_id" in module_d.columns:

        d_columns = [

            column

            for column in module_d.columns

            if column not in df.columns
            or column == "component_id"

        ]

        d_subset = module_d[
            d_columns
        ].copy()

        df = pd.merge(

            df,

            d_subset,

            on="component_id",

            how="left",

            suffixes=("", "_D")

        )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("Screening Controls")

st.sidebar.markdown(
    """
    **Early-screening system**

    The dashboard uses:

    • 0h measurements  
    • 24h measurements  
    • early drift  
    • predicted 168h behavior  
    • prediction uncertainty  
    • dynamic drift boundary  
    • fused risk assessment
    """
)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.subheader("Filters")


# Risk filter

risk_levels = [

    "LOW",
    "WATCH",
    "MEDIUM",
    "HIGH",
    "CRITICAL"

]

selected_risks = st.sidebar.multiselect(

    "Risk Level",

    risk_levels,

    default=risk_levels

)


# Lot filter

if "lot_id" in df.columns:

    lots = sorted(
        df["lot_id"].dropna().unique()
    )

    selected_lots = st.sidebar.multiselect(

        "Lot",

        lots,

        default=lots

    )

else:

    selected_lots = []


# Component type filter

if "component_type" in df.columns:

    component_types = sorted(

        df[
            "component_type"
        ]
        .dropna()
        .unique()

    )

    selected_types = st.sidebar.multiselect(

        "Component Type",

        component_types,

        default=component_types

    )

else:

    selected_types = []


# Risk threshold

risk_threshold = st.sidebar.slider(

    "Minimum Risk Score",

    min_value=0,

    max_value=100,

    value=0

)


# ============================================================
# APPLY FILTERS
# ============================================================

filtered_df = df[
    df["final_risk_level"].isin(
        selected_risks
    )
].copy()


if selected_lots:

    filtered_df = filtered_df[
        filtered_df["lot_id"].isin(
            selected_lots
        )
    ]


if selected_types:

    filtered_df = filtered_df[
        filtered_df["component_type"].isin(
            selected_types
        )
    ]


filtered_df = filtered_df[
    filtered_df["risk_score"]
    >=
    risk_threshold
]


# ============================================================
# TOP KPI SECTION
# ============================================================

st.header("Screening Overview")


total_components = len(df)

critical_count = (

    df["final_risk_level"]
    == "CRITICAL"

).sum()


high_count = (

    df["final_risk_level"]
    == "HIGH"

).sum()


medium_count = (

    df["final_risk_level"]
    == "MEDIUM"

).sum()


watch_count = (

    df["final_risk_level"]
    == "WATCH"

).sum()


low_count = (

    df["final_risk_level"]
    == "LOW"

).sum()


immediate_review = (

    df["final_decision"]
    == "IMMEDIATE_REVIEW"

).sum()


future_drift_count = (

    df["future_drift_abnormal"]
    .astype(bool)
    .sum()

    if "future_drift_abnormal" in df.columns

    else 0

)


col1, col2, col3, col4, col5, col6 = st.columns(6)


with col1:

    st.metric(
        "Components",
        f"{total_components:,}"
    )


with col2:

    st.metric(
        "Critical",
        f"{critical_count:,}"
    )


with col3:

    st.metric(
        "High",
        f"{high_count:,}"
    )


with col4:

    st.metric(
        "Medium",
        f"{medium_count:,}"
    )


with col5:

    st.metric(
        "Watch",
        f"{watch_count:,}"
    )


with col6:

    st.metric(
        "Immediate Review",
        f"{immediate_review:,}"
    )


# ============================================================
# SAFETY NOTICE
# ============================================================

st.markdown("")

st.markdown(
    """
    <div class="warning-box">

    ⚠️ <b>Prototype engineering notice:</b>
    Risk scores and dynamic safety boundaries shown here are
    statistical prototype outputs and are not ISRO-qualified
    engineering limits.

    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# DASHBOARD ROW 1
# ============================================================

st.header("Risk Distribution")


col1, col2 = st.columns(2)


# ------------------------------------------------------------
# Risk distribution
# ------------------------------------------------------------

with col1:

    risk_counts = (

        df[
            "final_risk_level"
        ]
        .value_counts()
        .reindex(
            risk_levels,
            fill_value=0
        )
        .reset_index()

    )

    risk_counts.columns = [

        "Risk Level",
        "Components"

    ]

    fig = px.bar(

        risk_counts,

        x="Risk Level",

        y="Components",

        title="Final Risk Distribution",

        text="Components"

    )

    fig.update_layout(

        showlegend=False,

        xaxis_title="",

        yaxis_title="Number of Components"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )


# ------------------------------------------------------------
# Decision distribution
# ------------------------------------------------------------

with col2:

    decision_counts = (

        df[
            "final_decision"
        ]
        .value_counts()
        .reset_index()

    )

    decision_counts.columns = [

        "Decision",
        "Components"

    ]

    fig = px.pie(

        decision_counts,

        names="Decision",

        values="Components",

        title="Screening Decisions",

        hole=0.45

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )


# ============================================================
# DASHBOARD ROW 2
# ============================================================

st.header("Future Risk Analysis")


col1, col2 = st.columns(2)


# ------------------------------------------------------------
# Predicted Iddq distribution
# ------------------------------------------------------------

with col1:

    if "predicted_168h_uA" in df.columns:

        fig = px.histogram(

            df,

            x="predicted_168h_uA",

            nbins=40,

            title="Predicted 168h Iddq Distribution"

        )

        if "absolute_limit_uA" in df.columns:

            limit = df[
                "absolute_limit_uA"
            ].iloc[0]

            fig.add_vline(

                x=limit,

                line_dash="dash",

                annotation_text="Absolute Limit"

            )

        st.plotly_chart(

            fig,

            use_container_width=True

        )


# ------------------------------------------------------------
# Risk score distribution
# ------------------------------------------------------------

with col2:

    fig = px.histogram(

        df,

        x="risk_score",

        nbins=30,

        title="Risk Score Distribution"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )


# ============================================================
# LOT ANALYSIS
# ============================================================

st.header("Lot-Level Risk Analysis")


if "lot_id" in df.columns:

    lot_summary = (

        df.groupby(
            "lot_id"
        )
        .agg(

            components=(
                "component_id",
                "count"
            ),

            critical=(
                "final_risk_level",
                lambda x:
                (x == "CRITICAL").sum()
            ),

            high=(
                "final_risk_level",
                lambda x:
                (x == "HIGH").sum()
            ),

            medium=(
                "final_risk_level",
                lambda x:
                (x == "MEDIUM").sum()
            ),

            watch=(
                "final_risk_level",
                lambda x:
                (x == "WATCH").sum()
            ),

            average_risk=(
                "risk_score",
                "mean"
            )

        )

        .reset_index()

    )


    lot_summary["average_risk"] = (

        lot_summary[
            "average_risk"
        ]
        .round(2)

    )


    fig = px.bar(

        lot_summary,

        x="lot_id",

        y=[

            "critical",
            "high",
            "medium",
            "watch"

        ],

        title="Risk Concentration by Lot",

        barmode="stack"

    )

    st.plotly_chart(

        fig,

        use_container_width=True

    )


    st.dataframe(

        lot_summary,

        use_container_width=True,

        hide_index=True

    )


# ============================================================
# PRIORITY SCREENING QUEUE
# ============================================================

st.header("🚨 Priority Screening Queue")


priority_df_display = filtered_df.copy()


priority_df_display = (

    priority_df_display
    .sort_values(

        [

            "risk_score",

            "final_risk_level"

        ],

        ascending=[

            False,

            True

        ]

    )

)


priority_columns = [

    "component_id",

    "lot_id",

    "component_type",

    "iddq_0h_uA",

    "iddq_24h_uA",

    "predicted_168h_uA",

    "absolute_limit_uA",

    "risk_score",

    "final_risk_level",

    "final_decision"

]


priority_columns = [

    column

    for column in priority_columns

    if column in priority_df_display.columns

]


st.dataframe(

    priority_df_display[
        priority_columns
    ]
    .head(100),

    use_container_width=True,

    hide_index=True

)


st.caption(

    f"Showing {min(100, len(priority_df_display))} "
    f"of {len(priority_df_display)} filtered components."

)


# ============================================================
# COMPONENT INVESTIGATION
# ============================================================

st.header("🔎 Component Investigation")


component_ids = (

    df[
        "component_id"
    ]
    .astype(str)
    .tolist()

)


selected_component = st.selectbox(

    "Select a component",

    component_ids

)


component = (

    df[
        df["component_id"].astype(str)
        == str(selected_component)
    ]

    .iloc[0]

)


# ============================================================
# COMPONENT HEADER
# ============================================================

st.subheader(

    f"Component {component['component_id']}"

)


c1, c2, c3, c4 = st.columns(4)


with c1:

    st.metric(

        "Risk Level",

        component[
            "final_risk_level"
        ]

    )


with c2:

    st.metric(

        "Decision",

        component[
            "final_decision"
        ]

    )


with c3:

    st.metric(

        "Risk Score",

        f"{component['risk_score']:.1f}"

    )


with c4:

    if "primary_risk_driver" in component.index:

        st.metric(

            "Primary Driver",

            component[
                "primary_risk_driver"
            ]

        )


# ============================================================
# COMPONENT MEASUREMENTS
# ============================================================

st.subheader("Electrical Evidence")


measurement_data = {}


for column in [

    "iddq_0h_uA",

    "iddq_24h_uA",

    "drift_0_24_uA_per_h",

    "predicted_168h_uA",

    "prediction_lower_uA",

    "prediction_upper_uA",

    "absolute_limit_uA",

    "predicted_drift_rate",

    "safety_slope",

    "drift_slope_excess"

]:

    if column in component.index:

        measurement_data[column] = component[column]


measurement_df = pd.DataFrame(

    {

        "Parameter": list(
            measurement_data.keys()
        ),

        "Value": list(
            measurement_data.values()
        )

    }

)


st.dataframe(

    measurement_df,

    use_container_width=True,

    hide_index=True

)


# ============================================================
# PREDICTION VS LIMIT GRAPH
# ============================================================

if all(

    column in component.index

    for column in [

        "predicted_168h_uA",

        "prediction_lower_uA",

        "prediction_upper_uA",

        "absolute_limit_uA"

    ]

):

    st.subheader(
        "Future Iddq Prediction"
    )


    fig = go.Figure()


    # Prediction interval

    fig.add_trace(

        go.Scatter(

            x=[

                168,
                168

            ],

            y=[

                component[
                    "prediction_lower_uA"
                ],

                component[
                    "prediction_upper_uA"
                ]

            ],

            mode="lines",

            name="Prediction Interval"

        )

    )


    # Predicted value

    fig.add_trace(

        go.Scatter(

            x=[168],

            y=[

                component[
                    "predicted_168h_uA"
                ]

            ],

            mode="markers",

            marker=dict(
                size=12
            ),

            name="Predicted 168h"

        )

    )


    # Absolute limit

    fig.add_trace(

        go.Scatter(

            x=[

                0,
                168

            ],

            y=[

                component[
                    "absolute_limit_uA"
                ],

                component[
                    "absolute_limit_uA"
                ]

            ],

            mode="lines",

            line=dict(
                dash="dash"
            ),

            name="Absolute Limit"

        )

    )


    # Actual early measurements

    fig.add_trace(

        go.Scatter(

            x=[

                0,
                24

            ],

            y=[

                component[
                    "iddq_0h_uA"
                ],

                component[
                    "iddq_24h_uA"
                ]

            ],

            mode="lines+markers",

            name="Observed Early Iddq"

        )

    )


    fig.update_layout(

        title="Early Measurements → Predicted Future Behavior",

        xaxis_title="Burn-in Time (hours)",

        yaxis_title="Iddq (µA)",

        xaxis=dict(
            range=[0, 180]
        )

    )


    st.plotly_chart(

        fig,

        use_container_width=True

    )


# ============================================================
# WHY WAS THIS COMPONENT FLAGGED?
# ============================================================

st.subheader("🧠 Why Was This Component Flagged?")


reasons = []


if (

    "current_anomaly_level" in component.index

    and

    component[
        "current_anomaly_level"
    ] != "NONE"

):

    reasons.append(

        f"Current anomaly level: "
        f"{component['current_anomaly_level']}"

    )


if (

    "drift_0_24_uA_per_h" in component.index

    and

    component[
        "drift_0_24_uA_per_h"
    ] > 0

):

    reasons.append(

        "Iddq increased between 0h and 24h."

    )


if (

    "predicted_limit_exceeded" in component.index

    and

    bool(
        component[
            "predicted_limit_exceeded"
        ]
    )

):

    reasons.append(

        "Predicted 168h Iddq exceeds the "
        "absolute specification limit."

    )


if (

    "uncertainty_adjusted_failure" in component.index

    and

    bool(
        component[
            "uncertainty_adjusted_failure"
        ]
    )

):

    reasons.append(

        "Prediction uncertainty reaches or exceeds "
        "the absolute limit."

    )


if (

    "future_drift_abnormal" in component.index

    and

    bool(
        component[
            "future_drift_abnormal"
        ]
    )

):

    reasons.append(

        "Predicted future drift exceeds the "
        "dynamic safety boundary."

    )


if len(reasons) == 0:

    st.success(
        "No significant abnormality detected."
    )

else:

    for reason in reasons:

        st.warning(
            "• " + reason
        )


# ============================================================
# MODULE D EXPLANATION
# ============================================================

if "risk_explanation" in component.index:

    st.subheader(
        "Detailed Screening Explanation"
    )

    st.info(

        str(
            component[
                "risk_explanation"
            ]
        )

    )


# ============================================================
# SCREENING ACTION
# ============================================================

st.subheader("Recommended Screening Action")


decision = component[
    "final_decision"
]


if decision == "IMMEDIATE_REVIEW":

    st.error(

        "🚨 IMMEDIATE REVIEW\n\n"
        "Component should be prioritized for engineering "
        "review and additional screening."

    )

elif decision == "PRIORITY_SCREENING":

    st.warning(

        "⚠️ PRIORITY SCREENING\n\n"
        "Component should receive enhanced screening priority."

    )

elif decision == "ENHANCED_MONITORING":

    st.warning(

        "🟡 ENHANCED MONITORING\n\n"
        "Continue monitoring and review abnormal indicators."

    )

elif decision == "MONITOR":

    st.info(

        "🔵 MONITOR\n\n"
        "Component shows mild evidence requiring observation."

    )

else:

    st.success(

        "🟢 NORMAL\n\n"
        "No significant early risk detected."

    )


# ============================================================
# EXPORT FILTERED RESULTS
# ============================================================

st.header("📄 Export Screening Results")


csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(

    label="Download Filtered Screening Results",

    data=csv_data,

    file_name="screening_results.csv",

    mime="text/csv"

)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(

    "SIH 26170 Prototype | AI-Assisted Component Burn-In "
    "Anomaly Detection & Early Screening"

)

st.caption(

    "Prototype statistical outputs are for demonstration "
    "and decision-support only. Engineering qualification "
    "requires validated test procedures and authorized limits."

)