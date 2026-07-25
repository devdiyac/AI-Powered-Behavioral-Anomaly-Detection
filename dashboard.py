"""
dashboard.py — Streamlit-based analyst-facing dashboard.

Run with:  streamlit run dashboard.py
Displays ranked alert queue, per-alert drill-down, summary charts,
and detection metrics.
"""

import json
import os

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import OUTPUT_DIR, METRICS_DIR

# ─────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CyberShield — Behavioral Anomaly Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────
# Custom CSS for dark SOC-analyst aesthetic
# ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    .stApp {
        font-family: 'Inter', sans-serif;
    }

    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #0f3460;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .metric-card h3 {
        color: #e94560;
        font-size: 2rem;
        margin: 0;
    }
    .metric-card p {
        color: #a8b2d1;
        font-size: 0.85rem;
        margin: 5px 0 0 0;
    }

    .risk-critical { color: #ff4757; font-weight: 700; }
    .risk-high { color: #ff6b6b; font-weight: 600; }
    .risk-medium { color: #ffa502; font-weight: 500; }
    .risk-low { color: #2ed573; font-weight: 400; }

    .header-banner {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        padding: 30px;
        border-radius: 16px;
        margin-bottom: 20px;
        border: 1px solid #4a4a8a;
    }
    .header-banner h1 {
        color: #e94560;
        font-size: 2.2rem;
        margin: 0;
    }
    .header-banner p {
        color: #a8b2d1;
        font-size: 1rem;
        margin: 5px 0 0 0;
    }

    div[data-testid="stExpander"] {
        border: 1px solid #2a2a4a;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    """Load scored events and metrics from outputs/."""
    scored_path = os.path.join(OUTPUT_DIR, "scored_events.csv")
    if not os.path.exists(scored_path):
        st.error(f"Scored events not found at {scored_path}. Run `python main.py` first.")
        st.stop()

    df = pd.read_csv(scored_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Load metrics
    metrics = {}
    for fname in ["detection_metrics.json", "classification_report.json",
                   "alert_budget.json", "cold_start_metrics.json",
                   "concept_drift_results.json"]:
        fpath = os.path.join(METRICS_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath) as f:
                metrics[fname.replace(".json", "")] = json.load(f)

    return df, metrics


def risk_color(score):
    """Return CSS class based on risk score."""
    if score >= 75:
        return "risk-critical"
    elif score >= 50:
        return "risk-high"
    elif score >= 25:
        return "risk-medium"
    return "risk-low"


def risk_label(score):
    if score >= 75:
        return "🔴 CRITICAL"
    elif score >= 50:
        return "🟠 HIGH"
    elif score >= 25:
        return "🟡 MEDIUM"
    return "🟢 LOW"


# ─────────────────────────────────────────────────────────────────────
# Main dashboard
# ─────────────────────────────────────────────────────────────────────
def main():
    df, metrics = load_data()

    # ── Header ──
    st.markdown("""
    <div class="header-banner">
        <h1>🛡️ CyberShield — Behavioral Anomaly Detection</h1>
        <p>AI-Powered SOC Analyst Dashboard · Real-time Threat Intelligence · Explainable Risk Scoring</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Sidebar filters ──
    st.sidebar.title("🔎 Filters")

    risk_min = st.sidebar.slider("Minimum Risk Score", 0, 100, 0, step=5)
    selected_types = st.sidebar.multiselect(
        "Anomaly Types",
        options=sorted(df["predicted_type"].unique()),
        default=sorted(df["predicted_type"].unique()),
    )
    selected_entity_types = st.sidebar.multiselect(
        "Entity Types",
        options=sorted(df["entity_type"].unique()),
        default=sorted(df["entity_type"].unique()),
    )
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(df["timestamp"].min().date(), df["timestamp"].max().date()),
    )

    # Apply filters
    filtered = df[
        (df["risk_score"] >= risk_min) &
        (df["predicted_type"].isin(selected_types)) &
        (df["entity_type"].isin(selected_entity_types))
    ]
    if len(date_range) == 2:
        filtered = filtered[
            (filtered["timestamp"].dt.date >= date_range[0]) &
            (filtered["timestamp"].dt.date <= date_range[1])
        ]

    # ── Metric cards ──
    det = metrics.get("detection_metrics", {})

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""<div class="metric-card">
            <h3>{len(filtered):,}</h3><p>Total Events</p></div>""", unsafe_allow_html=True)
    with col2:
        n_alerts = len(filtered[filtered["risk_score"] >= 50])
        st.markdown(f"""<div class="metric-card">
            <h3>{n_alerts:,}</h3><p>Active Alerts (≥50)</p></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card">
            <h3>{det.get('pr_auc', 0):.3f}</h3><p>PR-AUC</p></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card">
            <h3>{det.get('precision', 0):.3f}</h3><p>Precision</p></div>""", unsafe_allow_html=True)
    with col5:
        st.markdown(f"""<div class="metric-card">
            <h3>{det.get('recall', 0):.3f}</h3><p>Recall</p></div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Summary charts ──
    st.subheader("📊 Threat Landscape Overview")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Alerts over time
        time_df = filtered.copy()
        time_df["date"] = time_df["timestamp"].dt.date
        alerts_over_time = time_df[time_df["risk_score"] >= 25].groupby("date").size().reset_index(name="count")

        fig = px.area(alerts_over_time, x="date", y="count",
                      title="Alerts Over Time (Risk ≥ 25)",
                      color_discrete_sequence=["#e94560"])
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Date",
            yaxis_title="Alert Count",
        )
        st.plotly_chart(fig, use_container_width=True)

    with chart_col2:
        # Risk score distribution
        fig = px.histogram(filtered, x="risk_score", nbins=50,
                           title="Risk Score Distribution",
                           color_discrete_sequence=["#4ECDC4"])
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Risk Score",
            yaxis_title="Count",
        )
        st.plotly_chart(fig, use_container_width=True)

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        # Anomaly type breakdown
        type_counts = filtered[filtered["risk_score"] >= 25]["predicted_type"].value_counts()
        fig = px.pie(values=type_counts.values, names=type_counts.index,
                     title="Anomaly Type Breakdown (Risk ≥ 25)",
                     color_discrete_sequence=px.colors.qualitative.Set2,
                     hole=0.4)
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    with chart_col4:
        # Alert budget curve
        budget_data = metrics.get("alert_budget", [])
        if budget_data:
            budget_df = pd.DataFrame(budget_data)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=budget_df["alert_budget_pct"], y=budget_df["precision"],
                mode="lines+markers", name="Precision",
                line=dict(color="#FF6B6B", width=2)))
            fig.add_trace(go.Scatter(
                x=budget_df["alert_budget_pct"], y=budget_df["recall"],
                mode="lines+markers", name="Recall",
                line=dict(color="#4ECDC4", width=2)))
            fig.add_vline(x=1.0, line_dash="dash", line_color="gray",
                          annotation_text="1% budget")
            fig.update_layout(
                title="Precision & Recall vs Alert Budget",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Alert Budget (%)",
                yaxis_title="Score",
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ── Metric images ──
    img_col1, img_col2 = st.columns(2)
    pr_path = os.path.join(METRICS_DIR, "pr_curve.png")
    cm_path = os.path.join(METRICS_DIR, "confusion_matrix.png")
    if os.path.exists(pr_path):
        with img_col1:
            st.image(pr_path, caption="Precision-Recall Curve", use_container_width=True)
    if os.path.exists(cm_path):
        with img_col2:
            st.image(cm_path, caption="Anomaly Type Confusion Matrix", use_container_width=True)

    st.markdown("---")

    # ── Alert Queue ──
    st.subheader("🚨 Ranked Alert Queue")

    alert_df = filtered.sort_values("risk_score", ascending=False).head(200)

    display_cols = ["entity_id", "entity_type", "timestamp", "risk_score",
                    "predicted_type", "confidence", "explanation"]
    display_df = alert_df[display_cols].copy()
    display_df["risk_level"] = display_df["risk_score"].apply(risk_label)
    display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    display_df = display_df[["risk_level", "risk_score", "entity_id", "entity_type",
                             "timestamp", "predicted_type", "confidence", "explanation"]]

    st.dataframe(
        display_df,
        use_container_width=True,
        height=400,
        column_config={
            "risk_score": st.column_config.ProgressColumn(
                "Risk Score", min_value=0, max_value=100, format="%d"),
            "confidence": st.column_config.NumberColumn("Confidence %", format="%.1f"),
        },
    )

    # ── Drill-Down ──
    st.markdown("---")
    st.subheader("🔍 Alert Drill-Down")

    if len(alert_df) > 0:
        entity_options = alert_df.sort_values("risk_score", ascending=False)["entity_id"].unique()
        selected_entity = st.selectbox("Select entity to investigate:", entity_options)

        if selected_entity:
            entity_events = df[df["entity_id"] == selected_entity].sort_values("timestamp")

            # Entity profile summary
            prof_col1, prof_col2, prof_col3, prof_col4 = st.columns(4)
            with prof_col1:
                st.metric("Entity Type", entity_events["entity_type"].iloc[0])
            with prof_col2:
                st.metric("Total Events", len(entity_events))
            with prof_col3:
                st.metric("First Seen", entity_events["timestamp"].min().strftime("%Y-%m-%d"))
            with prof_col4:
                max_risk = entity_events["risk_score"].max()
                st.metric("Max Risk Score", f"{max_risk:.1f}")

            # Recent events timeline
            st.markdown("##### Recent Event Timeline")
            recent = entity_events.tail(30)
            fig = px.scatter(recent, x="timestamp", y="risk_score",
                             color="predicted_type", size="risk_score",
                             hover_data=["resource_accessed", "auth_method", "explanation"],
                             color_discrete_sequence=px.colors.qualitative.Vivid)
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Time",
                yaxis_title="Risk Score",
                height=350,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Contributing factors for the highest-risk event
            top_event = entity_events.sort_values("risk_score", ascending=False).iloc[0]
            st.markdown("##### Top Alert — Contributing Factors")

            factor_col1, factor_col2 = st.columns([2, 1])
            with factor_col1:
                st.info(f"**Explanation:** {top_event.get('explanation', 'N/A')}")
                st.info(f"**Inference Source:** {top_event.get('primary_inference_source', 'N/A')}")

            with factor_col2:
                try:
                    top_feats = json.loads(top_event.get("top_features", "[]"))
                    if top_feats:
                        feat_df = pd.DataFrame(top_feats)
                        fig = px.bar(feat_df, x="importance_score", y="description",
                                     orientation="h",
                                     color="source",
                                     color_discrete_map={
                                         "personal": "#4ECDC4",
                                         "population": "#FF6B6B",
                                         "sequence": "#FFE66D",
                                     },
                                     title="Feature Importance")
                        fig.update_layout(
                            template="plotly_dark",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            height=250,
                            showlegend=True,
                        )
                        st.plotly_chart(fig, use_container_width=True)
                except Exception:
                    st.write("No feature details available")

    # ── Cold-start & Drift info ──
    st.markdown("---")
    cold_start = metrics.get("cold_start_metrics", {})
    drift = metrics.get("concept_drift_results", {})

    cs_col, dr_col = st.columns(2)

    with cs_col:
        st.subheader("🆕 Cold-Start Analysis")
        if cold_start:
            for name, data in cold_start.items():
                if isinstance(data, dict) and data.get("n_events", 0) > 0:
                    st.markdown(f"**{name.replace('_', ' ').title()}**")
                    st.write(f"- Events: {data['n_events']:,}")
                    st.write(f"- Anomalies: {data.get('n_anomalies', 'N/A')}")
                    st.write(f"- PR-AUC: {data.get('pr_auc', 0):.3f}")

    with dr_col:
        st.subheader("🔄 Concept Drift")
        drift_plot_path = os.path.join(METRICS_DIR, "concept_drift_plot.png")
        if os.path.exists(drift_plot_path):
            st.image(drift_plot_path, caption="Risk Score Adaptation Over Time",
                     use_container_width=True)
        elif drift:
            for eid, data in drift.items():
                st.write(f"**{eid}**: avg risk {data.get('first_half_avg_risk',0):.1f} → "
                         f"{data.get('second_half_avg_risk',0):.1f}")


if __name__ == "__main__":
    main()
