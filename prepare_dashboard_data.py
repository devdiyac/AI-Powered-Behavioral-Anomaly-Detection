"""
prepare_dashboard_data.py — Convert pipeline outputs to a single JSON bundle
for the React dashboard.
"""

import json
import os
import pandas as pd
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
METRICS_DIR = os.path.join(OUTPUT_DIR, "metrics")


def load_json(filename):
    fpath = os.path.join(METRICS_DIR, filename)
    if os.path.exists(fpath):
        with open(fpath) as f:
            return json.load(f)
    return {}


def main():
    print("Preparing dashboard data bundle …")

    # Load scored events
    scored_path = os.path.join(OUTPUT_DIR, "scored_events.csv")
    df = pd.read_csv(scored_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%dT%H:%M:%S")

    # All events (for drill-down) — keep key columns
    all_events = df[[
        "entity_id", "entity_type", "timestamp", "risk_score",
        "predicted_type", "confidence", "explanation", "label",
        "primary_inference_source", "top_features",
        "geo_location", "resource_accessed", "auth_method",
        "session_duration", "is_cold_start",
        "hour_deviation", "geo_velocity_kmh", "time_since_last_hrs",
        "session_count", "auth_failure_streak", "session_duration_zscore",
        "new_resource_flag", "new_device_flag", "sequence_log_likelihood",
        "is_off_hours", "isolation_score", "max_zscore",
    ]].copy()

    # Replace NaN with None for JSON
    all_events = all_events.where(pd.notnull(all_events), None)

    # Parse top_features from string to list
    def parse_top_features(x):
        if pd.isna(x) or x is None:
            return []
        try:
            return json.loads(x)
        except:
            return []

    all_events["top_features"] = all_events["top_features"].apply(parse_top_features)

    # Convert to list of dicts
    events_list = all_events.to_dict(orient="records")

    # Compute summary stats
    total_events = len(df)
    total_anomalies = int((df["label"] != "normal").sum())
    anomaly_rate = total_anomalies / total_events if total_events > 0 else 0

    # Alerts over time (daily counts)
    df["date"] = pd.to_datetime(df["timestamp"]).dt.date.astype(str)
    alerts_by_date = df[df["risk_score"] >= 25].groupby("date").size().reset_index(name="count")
    all_events_by_date = df.groupby("date").size().reset_index(name="count")

    # Anomaly type breakdown
    anomaly_type_counts = df[df["risk_score"] >= 25]["predicted_type"].value_counts().to_dict()

    # Risk score distribution (binned)
    risk_bins = list(range(0, 105, 5))
    risk_hist, _ = np.histogram(df["risk_score"].values, bins=risk_bins)
    risk_distribution = [{"bin": f"{risk_bins[i]}-{risk_bins[i+1]}", "count": int(risk_hist[i])}
                          for i in range(len(risk_hist))]

    # Entity type breakdown
    entity_type_counts = df["entity_type"].value_counts().to_dict()

    # Unique entities
    unique_entities = int(df["entity_id"].nunique())

    # Load all metrics
    detection_metrics = load_json("detection_metrics.json")
    classification_report = load_json("classification_report.json")
    alert_budget = load_json("alert_budget.json")
    cold_start_metrics = load_json("cold_start_metrics.json")
    concept_drift_results = load_json("concept_drift_results.json")

    # Load drift info
    drift_path = os.path.join(OUTPUT_DIR, "drift_info.json")
    drift_info = {}
    if os.path.exists(drift_path):
        with open(drift_path) as f:
            drift_info = json.load(f)

    # Concept drift time series (for drifted entities)
    drift_timeseries = {}
    for eid in drift_info.keys():
        entity_events = df[df["entity_id"] == eid].sort_values("timestamp")
        if len(entity_events) > 0:
            drift_timeseries[eid] = {
                "timestamps": entity_events["timestamp"].tolist(),
                "risk_scores": entity_events["risk_score"].tolist(),
                "info": drift_info[eid],
            }

    # Build the bundle
    bundle = {
        "summary": {
            "total_events": total_events,
            "total_anomalies": total_anomalies,
            "anomaly_rate": round(anomaly_rate, 4),
            "unique_entities": unique_entities,
            "entity_type_counts": entity_type_counts,
        },
        "detection_metrics": detection_metrics,
        "classification_report": classification_report,
        "alert_budget": alert_budget,
        "cold_start_metrics": cold_start_metrics,
        "concept_drift_results": concept_drift_results,
        "drift_timeseries": drift_timeseries,
        "alerts_by_date": alerts_by_date.to_dict(orient="records"),
        "all_events_by_date": all_events_by_date.to_dict(orient="records"),
        "anomaly_type_counts": anomaly_type_counts,
        "risk_distribution": risk_distribution,
        "events": events_list,
    }

    # Save to React app's public dir
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "dashboard-react", "public", "data.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w") as f:
        json.dump(bundle, f)

    size_mb = os.path.getsize(out_path) / 1024 / 1024
    print(f"[OK] Data bundle saved -> {out_path} ({size_mb:.1f} MB)")
    print(f"  {total_events} events, {total_anomalies} anomalies")


if __name__ == "__main__":
    main()
