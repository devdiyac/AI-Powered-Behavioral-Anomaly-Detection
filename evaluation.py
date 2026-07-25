"""
evaluation.py — Comprehensive evaluation: detection metrics, classification metrics,
                 alert-budget analysis, cold-start and concept-drift demonstrations.
"""

import json
import logging
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    precision_recall_fscore_support,
    precision_recall_curve,
    average_precision_score,
    roc_curve,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

from config import METRICS_DIR, OUTPUT_DIR

logger = logging.getLogger("pipeline.eval")


def run_evaluation(scored_df: pd.DataFrame):
    """Run all evaluation suites and save results to outputs/metrics/."""
    logger.info("═" * 60)
    logger.info("Running evaluation suite …")
    logger.info("═" * 60)

    os.makedirs(METRICS_DIR, exist_ok=True)

    _detection_metrics(scored_df)
    _classification_metrics(scored_df)
    _alert_budget_analysis(scored_df)
    _cold_start_analysis(scored_df)
    _concept_drift_analysis(scored_df)

    logger.info("Evaluation complete ✓")


# ─────────────────────────────────────────────────────────────────────
# 1. Binary detection metrics
# ─────────────────────────────────────────────────────────────────────
def _detection_metrics(df: pd.DataFrame):
    """Precision, recall, F1, PR-AUC, ROC-AUC for binary detection."""
    logger.info("── Detection metrics (binary) ──")

    y_true = (df["label"] != "normal").astype(int).values
    y_scores = df["risk_score"].values

    # Use a threshold based on top percentile
    threshold = np.percentile(y_scores, 95)
    y_pred = (y_scores >= threshold).astype(int)

    prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)

    # PR-AUC
    pr_auc = average_precision_score(y_true, y_scores)

    # ROC-AUC
    try:
        roc_auc = roc_auc_score(y_true, y_scores)
    except ValueError:
        roc_auc = 0.0

    metrics = {
        "threshold": float(threshold),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "pr_auc": float(pr_auc),
        "roc_auc": float(roc_auc),
        "n_positive": int(y_true.sum()),
        "n_negative": int((1 - y_true).sum()),
    }

    logger.info(f"  Precision: {prec:.3f} | Recall: {rec:.3f} | F1: {f1:.3f}")
    logger.info(f"  PR-AUC: {pr_auc:.3f} | ROC-AUC: {roc_auc:.3f}")

    # Save
    with open(os.path.join(METRICS_DIR, "detection_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    # PR curve plot
    fig, ax = plt.subplots(figsize=(8, 6))
    prec_curve, rec_curve, _ = precision_recall_curve(y_true, y_scores)
    ax.plot(rec_curve, prec_curve, color="#4ECDC4", linewidth=2)
    ax.fill_between(rec_curve, prec_curve, alpha=0.15, color="#4ECDC4")
    ax.set_xlabel("Recall", fontsize=12)
    ax.set_ylabel("Precision", fontsize=12)
    ax.set_title(f"Precision-Recall Curve (PR-AUC = {pr_auc:.3f})", fontsize=14)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(METRICS_DIR, "pr_curve.png"), dpi=150)
    plt.close(fig)

    # ROC curve plot
    fig, ax = plt.subplots(figsize=(8, 6))
    fpr, tpr, _ = roc_curve(y_true, y_scores)
    ax.plot(fpr, tpr, color="#FF6B6B", linewidth=2)
    ax.plot([0, 1], [0, 1], "k--", alpha=0.3)
    ax.fill_between(fpr, tpr, alpha=0.15, color="#FF6B6B")
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title(f"ROC Curve (AUC = {roc_auc:.3f})", fontsize=14)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(METRICS_DIR, "roc_curve.png"), dpi=150)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────
# 2. Multi-class classification metrics
# ─────────────────────────────────────────────────────────────────────
def _classification_metrics(df: pd.DataFrame):
    """Per-class precision/recall/F1 and confusion matrix for anomaly types."""
    logger.info("── Classification metrics (multi-class) ──")

    # Only evaluate on actual anomalies
    anomaly_df = df[df["label"] != "normal"]

    if len(anomaly_df) == 0:
        logger.warning("  No anomalies in test set — skipping classification metrics")
        return

    y_true = anomaly_df["label"].values
    y_pred = anomaly_df["predicted_type"].values

    # Classification report
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    logger.info(f"\n{classification_report(y_true, y_pred, zero_division=0)}")

    with open(os.path.join(METRICS_DIR, "classification_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    # Confusion matrix
    labels = sorted(set(list(y_true) + list(y_pred)))
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="YlOrRd", xticklabels=labels,
                yticklabels=labels, ax=ax, linewidths=0.5)
    ax.set_xlabel("Predicted", fontsize=12)
    ax.set_ylabel("Actual", fontsize=12)
    ax.set_title("Anomaly Type Confusion Matrix", fontsize=14)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    fig.tight_layout()
    fig.savefig(os.path.join(METRICS_DIR, "confusion_matrix.png"), dpi=150)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────
# 3. Alert-budget analysis
# ─────────────────────────────────────────────────────────────────────
def _alert_budget_analysis(df: pd.DataFrame):
    """Precision and recall at various alert-budget percentiles."""
    logger.info("── Alert-budget analysis ──")

    y_true = (df["label"] != "normal").astype(int).values
    y_scores = df["risk_score"].values

    percentiles = np.arange(0.5, 10.5, 0.5)
    results = []

    for pct in percentiles:
        threshold = np.percentile(y_scores, 100 - pct)
        y_pred = (y_scores >= threshold).astype(int)

        tp = ((y_pred == 1) & (y_true == 1)).sum()
        fp = ((y_pred == 1) & (y_true == 0)).sum()
        fn = ((y_pred == 0) & (y_true == 1)).sum()

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0

        results.append({
            "alert_budget_pct": float(pct),
            "threshold": float(threshold),
            "precision": float(prec),
            "recall": float(rec),
            "true_positives": int(tp),
            "false_positives": int(fp),
        })

    # Log key result
    for r in results:
        if r["alert_budget_pct"] == 1.0:
            logger.info(f"  @Top-1%: Precision={r['precision']:.3f}, Recall={r['recall']:.3f}")

    with open(os.path.join(METRICS_DIR, "alert_budget.json"), "w") as f:
        json.dump(results, f, indent=2)

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    precs = [r["precision"] for r in results]
    recs = [r["recall"] for r in results]
    pcts = [r["alert_budget_pct"] for r in results]

    ax.plot(pcts, precs, "o-", color="#FF6B6B", linewidth=2, label="Precision", markersize=5)
    ax.plot(pcts, recs, "s-", color="#4ECDC4", linewidth=2, label="Recall", markersize=5)
    ax.axvline(x=1.0, color="gray", linestyle="--", alpha=0.5, label="1% budget")
    ax.set_xlabel("Alert Budget (% of events reviewed)", fontsize=12)
    ax.set_ylabel("Score", fontsize=12)
    ax.set_title("Precision & Recall vs. Alert Budget", fontsize=14)
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    fig.savefig(os.path.join(METRICS_DIR, "alert_budget.png"), dpi=150)
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────
# 4. Cold-start analysis
# ─────────────────────────────────────────────────────────────────────
def _cold_start_analysis(df: pd.DataFrame):
    """Separate detection metrics for cold-start entities."""
    logger.info("── Cold-start analysis ──")

    cold = df[df["is_cold_start"] == 1]
    warm = df[df["is_cold_start"] == 0]

    results = {}

    for name, subset in [("cold_start", cold), ("warm", warm)]:
        if len(subset) == 0:
            logger.info(f"  {name}: no events")
            results[name] = {"n_events": 0}
            continue

        y_true = (subset["label"] != "normal").astype(int).values
        y_scores = subset["risk_score"].values

        if y_true.sum() > 0:
            pr_auc = average_precision_score(y_true, y_scores)
            try:
                roc_auc = roc_auc_score(y_true, y_scores)
            except ValueError:
                roc_auc = 0.0
        else:
            pr_auc = 0.0
            roc_auc = 0.0

        results[name] = {
            "n_events": int(len(subset)),
            "n_anomalies": int(y_true.sum()),
            "mean_risk_score": float(np.mean(y_scores)),
            "pr_auc": float(pr_auc),
            "roc_auc": float(roc_auc),
        }

        logger.info(f"  {name}: {len(subset)} events, "
                     f"{y_true.sum()} anomalies, "
                     f"PR-AUC={pr_auc:.3f}")

    with open(os.path.join(METRICS_DIR, "cold_start_metrics.json"), "w") as f:
        json.dump(results, f, indent=2)


# ─────────────────────────────────────────────────────────────────────
# 5. Concept drift demonstration
# ─────────────────────────────────────────────────────────────────────
def _concept_drift_analysis(df: pd.DataFrame):
    """Show that risk scores taper for entities with injected concept drift."""
    logger.info("── Concept drift demonstration ──")

    # Load drift info
    drift_path = os.path.join(OUTPUT_DIR, "drift_info.json")
    if not os.path.exists(drift_path):
        logger.warning("  No drift_info.json found — skipping")
        return

    with open(drift_path) as f:
        drift_info = json.load(f)

    if not drift_info:
        logger.info("  No drifted entities — skipping")
        return

    fig, axes = plt.subplots(len(drift_info), 1,
                              figsize=(12, 3 * len(drift_info)),
                              squeeze=False)

    drift_results = {}
    for i, (eid, info) in enumerate(drift_info.items()):
        entity_df = df[df["entity_id"] == eid].sort_values("timestamp")
        if len(entity_df) == 0:
            continue

        ax = axes[i, 0]
        timestamps = pd.to_datetime(entity_df["timestamp"])
        risk_scores = entity_df["risk_score"].values

        ax.plot(timestamps, risk_scores, "o-", markersize=3, alpha=0.7, color="#FF6B6B")
        ax.set_ylabel("Risk Score")
        ax.set_title(f"{eid}: hour {info['old_hour']:.0f}→{info['new_hour']:.0f}h", fontsize=11)
        ax.grid(alpha=0.3)

        # Compute trend: average risk score in first half vs second half
        mid = len(risk_scores) // 2
        if mid > 0:
            first_half_avg = np.mean(risk_scores[:mid])
            second_half_avg = np.mean(risk_scores[mid:])
            drift_results[eid] = {
                "first_half_avg_risk": float(first_half_avg),
                "second_half_avg_risk": float(second_half_avg),
                "drift_reduced": bool(second_half_avg <= first_half_avg),
            }
            logger.info(f"  {eid}: avg risk {first_half_avg:.1f} → {second_half_avg:.1f}")

    axes[-1, 0].set_xlabel("Time")
    fig.suptitle("Concept Drift Adaptation: Risk Scores Over Time", fontsize=14, y=1.01)
    fig.tight_layout()
    fig.savefig(os.path.join(METRICS_DIR, "concept_drift_plot.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)

    with open(os.path.join(METRICS_DIR, "concept_drift_results.json"), "w") as f:
        json.dump(drift_results, f, indent=2)
