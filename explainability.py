"""
explainability.py — Per-alert feature attribution with inference-source tagging.

Generates human-readable explanation strings for every flagged event,
using SHAP (if available) or a z-score × importance fallback.
"""

import json
import logging
import os

import numpy as np
import pandas as pd

from config import RANDOM_SEED
from models import FEATURE_COLS
from utils import detect_environment

logger = logging.getLogger("pipeline.explain")


# ─────────────────────────────────────────────────────────────────────
# Feature importance (global)
# ─────────────────────────────────────────────────────────────────────
def _get_global_importance(classifier) -> dict:
    """Get feature importance dict from the classifier."""
    importances = classifier.feature_importances
    return {col: float(imp) for col, imp in zip(FEATURE_COLS, importances)}


# ─────────────────────────────────────────────────────────────────────
# Human-readable feature names
# ─────────────────────────────────────────────────────────────────────
FEATURE_DESCRIPTIONS = {
    "hour_deviation": "login hour deviation",
    "geo_velocity_kmh": "geo-velocity (km/h)",
    "time_since_last_hrs": "time since last session",
    "session_count": "session history depth",
    "auth_failure_streak": "consecutive auth failures",
    "session_duration_zscore": "session duration anomaly",
    "new_resource_flag": "new resource accessed",
    "new_device_flag": "new device fingerprint",
    "resource_breadth_ratio": "resource breadth",
    "sequence_log_likelihood": "command sequence likelihood",
    "is_off_hours": "off-hours access",
    "is_cold_start": "cold-start entity",
}


def _source_tag(source: str) -> str:
    """Map inference source to a human-readable tag."""
    tags = {
        "personal": "[PERSONAL]",
        "population": "[POPULATION]",
        "sequence": "[SEQUENCE]",
        "ensemble": "[ENSEMBLE]",
    }
    return tags.get(source, "[UNKNOWN]")


# ─────────────────────────────────────────────────────────────────────
# Explanation generator
# ─────────────────────────────────────────────────────────────────────
def add_explanations(scored_df: pd.DataFrame, classifier, profiler) -> pd.DataFrame:
    """
    Add per-event explanation columns:
      - explanation: human-readable reason string
      - top_features: JSON list of {feature, value, z_score, source}
      - primary_inference_source: tag for the dominant inference pathway
    """
    logger.info("Generating explanations …")

    env = detect_environment()
    use_shap = env.get("shap", False)

    global_imp = _get_global_importance(classifier)

    explanations = []
    top_features_list = []
    primary_sources = []

    # Try SHAP if available
    shap_values = None
    if use_shap and classifier.model is not None:
        try:
            import shap
            X = scored_df[FEATURE_COLS].values.astype(float)
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

            if classifier.model_type == "RandomForest":
                explainer = shap.TreeExplainer(classifier.model)
                shap_values = explainer.shap_values(X)
            elif classifier.model_type == "XGBoost":
                explainer = shap.TreeExplainer(classifier.model)
                shap_values = explainer.shap_values(X)
            logger.info("  Using SHAP for explanations")
        except Exception as e:
            logger.warning(f"  SHAP failed ({e}), using z-score fallback")
            shap_values = None

    for i, (idx, row) in enumerate(scored_df.iterrows()):
        # Get z-scores for this event
        feature_zscores = row.get("feature_zscores", {})
        if isinstance(feature_zscores, str):
            feature_zscores = json.loads(feature_zscores)

        zscore_source = row.get("zscore_source", "personal")
        is_cold = row.get("is_cold_start", 0) == 1

        # Compute weighted importance: |z-score| × global_importance
        scored_features = []
        for col in FEATURE_COLS:
            z = abs(feature_zscores.get(col, 0))
            imp = global_imp.get(col, 0)
            val = row.get(col, 0)

            # Determine source for this feature
            if col == "sequence_log_likelihood":
                feat_source = "sequence"
            elif is_cold:
                feat_source = "population"
            else:
                feat_source = zscore_source

            # Use SHAP if available
            if shap_values is not None:
                if isinstance(shap_values, list):
                    # Multi-class: take max absolute SHAP across classes
                    shap_val = max(abs(sv[i, FEATURE_COLS.index(col)])
                                   for sv in shap_values if sv.shape[0] > i)
                else:
                    shap_val = abs(shap_values[i, FEATURE_COLS.index(col)])
                score_val = shap_val
            else:
                score_val = z * imp

            scored_features.append({
                "feature": col,
                "description": FEATURE_DESCRIPTIONS.get(col, col),
                "value": round(float(val), 3),
                "z_score": round(float(feature_zscores.get(col, 0)), 3),
                "importance_score": round(float(score_val), 4),
                "source": feat_source,
            })

        # Sort by importance and take top 3
        scored_features.sort(key=lambda x: x["importance_score"], reverse=True)
        top_3 = scored_features[:3]

        # Build explanation string
        parts = []
        for f in top_3:
            z_str = f"{abs(f['z_score']):.1f}σ"
            direction = "above" if f["z_score"] > 0 else "below"

            if f["feature"] == "new_resource_flag" and f["value"] == 1:
                parts.append("New resource accessed")
            elif f["feature"] == "new_device_flag" and f["value"] == 1:
                parts.append("New device fingerprint")
            elif f["feature"] == "is_off_hours" and f["value"] == 1:
                parts.append("Off-hours access")
            elif f["feature"] == "auth_failure_streak" and f["value"] > 0:
                parts.append(f"{int(f['value'])} consecutive auth failures")
            else:
                parts.append(f"{f['description']} ({z_str} {direction} baseline)")

        explanation = " • ".join(parts) if parts else "Normal behavioral profile"

        # Determine primary inference source
        sources = [f["source"] for f in top_3]
        if is_cold:
            primary_source = "population"
        elif "sequence" in sources:
            primary_source = "sequence"
        elif "personal" in sources:
            primary_source = "personal"
        else:
            primary_source = "ensemble"

        explanations.append(explanation)
        top_features_list.append(json.dumps(top_3))
        primary_sources.append(primary_source)

    scored_df = scored_df.copy()
    scored_df["explanation"] = explanations
    scored_df["top_features"] = top_features_list
    scored_df["primary_inference_source"] = primary_sources

    logger.info(f"  Generated explanations for {len(scored_df)} events")
    return scored_df
