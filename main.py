"""
main.py — AI-Powered Behavioral Anomaly Detection Pipeline.

Single entry point: `python main.py`
Generates all artifacts (data, models, metrics, dashboard, report) into outputs/.
"""

import os
import sys
import time
import logging

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import OUTPUT_DIR
from utils import setup_logging, ensure_output_dirs, detect_environment


def main():
    """Run the full anomaly detection pipeline end-to-end."""
    logger = setup_logging()
    start_time = time.time()

    logger.info("=" * 65)
    logger.info("  AI-Powered Behavioral Anomaly Detection Pipeline")
    logger.info("=" * 65)

    # ── Step 0: Setup ──
    logger.info("\n▶ Step 0: Environment setup")
    env = detect_environment()
    ensure_output_dirs()

    # ── Step 1: Generate synthetic data ──
    logger.info("\n▶ Step 1: Generating synthetic access logs")
    from data_generator import generate_access_logs
    df = generate_access_logs()
    logger.info(f"  Generated {len(df)} events")

    # ── Step 2: Feature engineering ──
    logger.info("\n▶ Step 2: Feature engineering (causal)")
    from feature_engineering import extract_features
    features_df = extract_features(df)
    logger.info(f"  Extracted {features_df.shape[1]} features for {len(features_df)} events")

    # ── Step 3: Train models ──
    logger.info("\n▶ Step 3: Training models")
    from models import (
        chronological_split, BaselineProfiler, AnomalyDetector,
        AnomalyClassifier, ConceptDriftAdapter, score_events,
    )

    train_df, test_df = chronological_split(features_df)

    profiler = BaselineProfiler().fit(train_df)
    profiler.save()

    detector = AnomalyDetector().fit(train_df)
    detector.save()

    classifier = AnomalyClassifier().fit(train_df)
    classifier.save()

    drift_adapter = ConceptDriftAdapter(profiler)

    # ── Step 4: Score test set ──
    logger.info("\n▶ Step 4: Scoring test events")
    scored_df = score_events(test_df, profiler, detector, classifier, drift_adapter)

    # ── Step 5: Explainability ──
    logger.info("\n▶ Step 5: Adding explanations")
    from explainability import add_explanations
    explained_df = add_explanations(scored_df, classifier, profiler)

    # Save scored events for dashboard
    scored_path = os.path.join(OUTPUT_DIR, "scored_events.csv")
    # Convert feature_zscores dict to string for CSV storage
    save_df = explained_df.copy()
    save_df["feature_zscores"] = save_df["feature_zscores"].apply(
        lambda x: str(x) if isinstance(x, dict) else x
    )
    save_df.to_csv(scored_path, index=False)
    logger.info(f"  Saved scored events → {scored_path}")

    # ── Step 6: Evaluation ──
    logger.info("\n▶ Step 6: Running evaluation suite")
    from evaluation import run_evaluation
    run_evaluation(explained_df)

    # ── Step 7: Report & Presentation ──
    logger.info("\n▶ Step 7: Generating report and presentation")
    from report import generate_report, generate_presentation
    generate_report()
    generate_presentation()

    # ── Summary ──
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 65)
    logger.info("  ✅ Pipeline complete!")
    logger.info(f"  ⏱  Elapsed: {elapsed:.1f}s")
    logger.info(f"  📁 All artifacts in: {OUTPUT_DIR}")
    logger.info("  📊 Dashboard: streamlit run dashboard.py")
    logger.info("=" * 65)

    # Print deliverables checklist
    deliverables = [
        ("Synthetic data", "outputs/access_logs.csv"),
        ("Feature matrix", "outputs/features.csv"),
        ("Scored events", "outputs/scored_events.csv"),
        ("Baseline profiles", "outputs/models/profiles.pkl"),
        ("IsolationForest", "outputs/models/isolation_forest.pkl"),
        ("Classifier", "outputs/models/classifier.pkl"),
        ("Detection metrics", "outputs/metrics/detection_metrics.json"),
        ("Classification report", "outputs/metrics/classification_report.json"),
        ("PR curve", "outputs/metrics/pr_curve.png"),
        ("ROC curve", "outputs/metrics/roc_curve.png"),
        ("Confusion matrix", "outputs/metrics/confusion_matrix.png"),
        ("Alert budget", "outputs/metrics/alert_budget.png"),
        ("Cold-start metrics", "outputs/metrics/cold_start_metrics.json"),
        ("Concept drift plot", "outputs/metrics/concept_drift_plot.png"),
        ("Technical report", "outputs/report.md"),
        ("Presentation", "outputs/presentation.md"),
    ]

    logger.info("\nDeliverables:")
    for name, path in deliverables:
        full = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        status = "✓" if os.path.exists(full) else "✗ MISSING"
        logger.info(f"  {status} {name}: {path}")


if __name__ == "__main__":
    main()
