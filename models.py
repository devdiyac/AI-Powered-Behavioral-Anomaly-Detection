"""
models.py — Baseline profiling, anomaly detection, risk scoring,
             anomaly-type classification, and concept-drift adaptation.
"""

import logging
import os
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import MinMaxScaler

from config import (
    W_ISOLATION, W_ZSCORE, W_SEQUENCE, MIN_HISTORY,
    CONCEPT_DRIFT_ALPHA, TRAIN_RATIO, MODELS_DIR, RANDOM_SEED,
)
from utils import detect_environment

logger = logging.getLogger("pipeline.models")

# Feature columns used for ML models
FEATURE_COLS = [
    "hour_deviation", "geo_velocity_kmh", "time_since_last_hrs",
    "session_count", "auth_failure_streak", "session_duration_zscore",
    "new_resource_flag", "new_device_flag", "resource_breadth_ratio",
    "sequence_log_likelihood", "is_off_hours", "is_cold_start",
]


# ─────────────────────────────────────────────────────────────────────
# Chronological train/test split
# ─────────────────────────────────────────────────────────────────────
def chronological_split(df: pd.DataFrame, ratio: float = TRAIN_RATIO):
    """Split DataFrame chronologically (first `ratio` fraction for training)."""
    df = df.sort_values("timestamp").reset_index(drop=True)
    split_idx = int(len(df) * ratio)
    train = df.iloc[:split_idx].copy()
    test = df.iloc[split_idx:].copy()
    logger.info(f"Chronological split: {len(train)} train / {len(test)} test")
    return train, test


# ─────────────────────────────────────────────────────────────────────
# Baseline Profiler
# ─────────────────────────────────────────────────────────────────────
class BaselineProfiler:
    """Per-entity and per-entity_type statistical profiles."""

    def __init__(self):
        self.entity_profiles = {}   # entity_id -> {feat: {mean, std}}
        self.population_profiles = {}  # entity_type -> {feat: {mean, std}}

    def fit(self, train_df: pd.DataFrame):
        """Build profiles from training data."""
        logger.info("Building baseline profiles …")

        # Per-entity profiles
        for eid, group in train_df.groupby("entity_id"):
            self.entity_profiles[eid] = {}
            for col in FEATURE_COLS:
                vals = group[col].values.astype(float)
                self.entity_profiles[eid][col] = {
                    "mean": float(np.mean(vals)),
                    "std": float(max(np.std(vals), 1e-6)),
                }

        # Per-entity_type population profiles
        for etype, group in train_df.groupby("entity_type"):
            self.population_profiles[etype] = {}
            for col in FEATURE_COLS:
                vals = group[col].values.astype(float)
                self.population_profiles[etype][col] = {
                    "mean": float(np.mean(vals)),
                    "std": float(max(np.std(vals), 1e-6)),
                }

        logger.info(f"  {len(self.entity_profiles)} entity profiles, "
                     f"{len(self.population_profiles)} population profiles")
        return self

    def get_profile(self, entity_id: str, entity_type: str):
        """Return entity profile, falling back to population if missing."""
        if entity_id in self.entity_profiles:
            return self.entity_profiles[entity_id], "personal"
        elif entity_type in self.population_profiles:
            return self.population_profiles[entity_type], "population"
        else:
            # Ultimate fallback: zero-mean, unit-std
            return {col: {"mean": 0.0, "std": 1.0} for col in FEATURE_COLS}, "population"

    def compute_zscore(self, entity_id: str, entity_type: str, features: dict):
        """Compute per-feature z-scores against the entity's baseline."""
        profile, source = self.get_profile(entity_id, entity_type)
        zscores = {}
        for col in FEATURE_COLS:
            if col in features and col in profile:
                m = profile[col]["mean"]
                s = profile[col]["std"]
                zscores[col] = (features[col] - m) / s
            else:
                zscores[col] = 0.0
        return zscores, source

    def save(self, path=None):
        path = path or os.path.join(MODELS_DIR, "profiles.pkl")
        with open(path, "wb") as f:
            pickle.dump({"entity": self.entity_profiles,
                         "population": self.population_profiles}, f)
        logger.info(f"Saved profiles → {path}")

    def load(self, path=None):
        path = path or os.path.join(MODELS_DIR, "profiles.pkl")
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.entity_profiles = data["entity"]
        self.population_profiles = data["population"]
        return self


# ─────────────────────────────────────────────────────────────────────
# Anomaly Detector (IsolationForest)
# ─────────────────────────────────────────────────────────────────────
class AnomalyDetector:
    """Unsupervised anomaly detector using IsolationForest."""

    def __init__(self, contamination=0.05, random_state=RANDOM_SEED):
        self.model = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,
        )
        self.scaler = MinMaxScaler()
        self._fitted = False

    def fit(self, train_df: pd.DataFrame):
        """Fit IsolationForest on the training feature matrix."""
        logger.info("Training IsolationForest …")
        X = train_df[FEATURE_COLS].values.astype(float)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        self.model.fit(X)

        # Compute raw scores on training set and fit scaler
        raw = -self.model.decision_function(X)  # invert: higher = more anomalous
        self.scaler.fit(raw.reshape(-1, 1))
        self._fitted = True
        logger.info("  IsolationForest trained")
        return self

    def score(self, X: np.ndarray) -> np.ndarray:
        """Return normalised anomaly scores in [0, 1]. Higher = more anomalous."""
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        raw = -self.model.decision_function(X)
        scaled = self.scaler.transform(raw.reshape(-1, 1)).flatten()
        return np.clip(scaled, 0, 1)

    def save(self, path=None):
        path = path or os.path.join(MODELS_DIR, "isolation_forest.pkl")
        with open(path, "wb") as f:
            pickle.dump({"model": self.model, "scaler": self.scaler}, f)

    def load(self, path=None):
        path = path or os.path.join(MODELS_DIR, "isolation_forest.pkl")
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.model = data["model"]
        self.scaler = data["scaler"]
        self._fitted = True
        return self


# ─────────────────────────────────────────────────────────────────────
# Risk Scorer
# ─────────────────────────────────────────────────────────────────────
class RiskScorer:
    """Combines IsolationForest score, z-score deviation, and sequence
    log-likelihood into a single 0–100 risk score."""

    def __init__(self, w_iso=W_ISOLATION, w_z=W_ZSCORE, w_seq=W_SEQUENCE):
        self.w_iso = w_iso
        self.w_z = w_z
        self.w_seq = w_seq

    def score(self, iso_score: float, max_abs_zscore: float,
              seq_ll_normalised: float) -> float:
        """
        Compute combined risk score.

        Parameters
        ----------
        iso_score : float in [0, 1] — IsolationForest anomaly score
        max_abs_zscore : float — max |z-score| across features, clipped to [0, 5], scaled to [0, 1]
        seq_ll_normalised : float in [0, 1] — sequence anomaly score (0 = normal, 1 = very unusual)
        """
        z_component = min(max_abs_zscore / 5.0, 1.0)
        risk = 100 * (self.w_iso * iso_score +
                      self.w_z * z_component +
                      self.w_seq * seq_ll_normalised)
        return round(min(max(risk, 0), 100), 2)


# ─────────────────────────────────────────────────────────────────────
# Anomaly-Type Classifier
# ─────────────────────────────────────────────────────────────────────
class AnomalyClassifier:
    """Supervised classifier for anomaly-type prediction."""

    def __init__(self, random_state=RANDOM_SEED):
        self.random_state = random_state
        self.model = None
        self.model_type = "RandomForest"
        self._classes = []

    def fit(self, train_df: pd.DataFrame):
        """
        Train on labeled anomaly events (plus a sample of normals).
        """
        logger.info("Training anomaly-type classifier …")

        # Separate anomalies and normals
        anomalies = train_df[train_df["label"] != "normal"]
        normals = train_df[train_df["label"] == "normal"]

        if len(anomalies) == 0:
            logger.warning("No anomalies in training set — classifier will be trivial")
            self.model = None
            return self

        # Sample normals to balance (up to 2× anomaly count)
        n_normal_sample = min(len(normals), 2 * len(anomalies))
        normal_sample = normals.sample(n=n_normal_sample, random_state=self.random_state)

        train_cls = pd.concat([anomalies, normal_sample], ignore_index=True)

        X = train_cls[FEATURE_COLS].values.astype(float)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        y = train_cls["label"].values

        # Try XGBoost first, fall back to RandomForest
        env = detect_environment()
        if env.get("xgboost", False):
            try:
                from xgboost import XGBClassifier
                from sklearn.preprocessing import LabelEncoder
                le = LabelEncoder()
                y_enc = le.fit_transform(y)
                self.model = XGBClassifier(
                    n_estimators=200,
                    max_depth=6,
                    random_state=self.random_state,
                    use_label_encoder=False,
                    eval_metric="mlogloss",
                )
                self.model.fit(X, y_enc)
                self._classes = list(le.classes_)
                self._label_encoder = le
                self.model_type = "XGBoost"
                logger.info("  Using XGBoost classifier")
            except Exception as e:
                logger.warning(f"  XGBoost failed ({e}), falling back to RandomForest")
                env["xgboost"] = False

        if not env.get("xgboost", False):
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                class_weight="balanced",
                random_state=self.random_state,
                n_jobs=-1,
            )
            self.model.fit(X, y)
            self._classes = list(self.model.classes_)
            self._label_encoder = None
            self.model_type = "RandomForest"
            logger.info("  Using RandomForest classifier")

        logger.info(f"  Classes: {self._classes}")
        return self

    def predict(self, X: np.ndarray):
        """Return predicted class and class probabilities."""
        if self.model is None:
            n = X.shape[0]
            return np.full(n, "normal"), np.zeros((n, 1))

        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

        if self.model_type == "XGBoost" and self._label_encoder is not None:
            probs = self.model.predict_proba(X)
            pred_enc = np.argmax(probs, axis=1)
            pred = self._label_encoder.inverse_transform(pred_enc)
        else:
            pred = self.model.predict(X)
            probs = self.model.predict_proba(X)

        return pred, probs

    @property
    def classes(self):
        return self._classes

    @property
    def feature_importances(self):
        if self.model is None:
            return np.ones(len(FEATURE_COLS)) / len(FEATURE_COLS)
        if hasattr(self.model, "feature_importances_"):
            return self.model.feature_importances_
        return np.ones(len(FEATURE_COLS)) / len(FEATURE_COLS)

    def save(self, path=None):
        path = path or os.path.join(MODELS_DIR, "classifier.pkl")
        with open(path, "wb") as f:
            pickle.dump({
                "model": self.model,
                "model_type": self.model_type,
                "classes": self._classes,
                "label_encoder": getattr(self, "_label_encoder", None),
            }, f)

    def load(self, path=None):
        path = path or os.path.join(MODELS_DIR, "classifier.pkl")
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.model = data["model"]
        self.model_type = data["model_type"]
        self._classes = data["classes"]
        self._label_encoder = data.get("label_encoder")
        return self


# ─────────────────────────────────────────────────────────────────────
# Concept Drift Adapter
# ─────────────────────────────────────────────────────────────────────
class ConceptDriftAdapter:
    """
    Updates entity profiles incrementally using exponential moving average.
    A legitimately changed behaviour stops being flagged over time.
    """

    def __init__(self, profiler: BaselineProfiler, alpha: float = CONCEPT_DRIFT_ALPHA):
        self.profiler = profiler
        self.alpha = alpha

    def update(self, entity_id: str, entity_type: str, features: dict):
        """
        Update the entity's profile with a new observation using EMA.
        """
        if entity_id not in self.profiler.entity_profiles:
            # First time: initialise from population
            pop_prof, _ = self.profiler.get_profile(entity_id, entity_type)
            self.profiler.entity_profiles[entity_id] = {
                col: {"mean": pop_prof[col]["mean"],
                       "std": pop_prof[col]["std"]}
                for col in FEATURE_COLS if col in pop_prof
            }

        profile = self.profiler.entity_profiles[entity_id]
        for col in FEATURE_COLS:
            if col in features and col in profile:
                old_mean = profile[col]["mean"]
                new_val = features[col]
                new_mean = self.alpha * new_val + (1 - self.alpha) * old_mean
                # Update std with EMA of squared deviation
                old_std = profile[col]["std"]
                new_std = np.sqrt(
                    self.alpha * (new_val - new_mean) ** 2 +
                    (1 - self.alpha) * old_std ** 2
                )
                profile[col]["mean"] = new_mean
                profile[col]["std"] = max(new_std, 1e-6)


# ─────────────────────────────────────────────────────────────────────
# Scoring pipeline
# ─────────────────────────────────────────────────────────────────────
def score_events(test_df: pd.DataFrame, profiler: BaselineProfiler,
                 detector: AnomalyDetector, classifier: AnomalyClassifier,
                 drift_adapter: ConceptDriftAdapter) -> pd.DataFrame:
    """
    Score every event in the test set:
    1. IsolationForest anomaly score
    2. Personal z-score deviation
    3. Sequence log-likelihood → normalised score
    4. Combined risk score
    5. Anomaly-type classification
    6. Concept-drift profile updates
    """
    logger.info("Scoring test events …")

    X = test_df[FEATURE_COLS].values.astype(float)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    # 1. Isolation scores
    iso_scores = detector.score(X)

    # 2. Per-event z-scores
    max_zscores = []
    all_zscores = []
    zscore_sources = []
    for idx, row in test_df.iterrows():
        feats = {col: row[col] for col in FEATURE_COLS}
        zs, source = profiler.compute_zscore(row["entity_id"], row["entity_type"], feats)
        max_z = max(abs(v) for v in zs.values())
        max_zscores.append(max_z)
        all_zscores.append(zs)
        zscore_sources.append(source)

    max_zscores = np.array(max_zscores)

    # 3. Sequence log-likelihood → normalised (higher = more anomalous)
    seq_scores_raw = test_df["sequence_log_likelihood"].values.astype(float)
    # More negative = more unusual → invert and normalise
    seq_inverted = -seq_scores_raw
    seq_min, seq_max = seq_inverted.min(), seq_inverted.max()
    if seq_max - seq_min > 1e-8:
        seq_normalised = (seq_inverted - seq_min) / (seq_max - seq_min)
    else:
        seq_normalised = np.zeros_like(seq_inverted)

    # 4. Risk scores
    risk_scorer = RiskScorer()
    risk_scores = [
        risk_scorer.score(iso_scores[i], max_zscores[i], seq_normalised[i])
        for i in range(len(test_df))
    ]

    # 5. Classification
    pred_classes, pred_probs = classifier.predict(X)
    max_confidence = np.max(pred_probs, axis=1) if pred_probs.ndim > 1 else pred_probs.flatten()

    # 6. Concept-drift updates
    for i, (idx, row) in enumerate(test_df.iterrows()):
        feats = {col: row[col] for col in FEATURE_COLS}
        drift_adapter.update(row["entity_id"], row["entity_type"], feats)

    # Build result DataFrame
    result = test_df.copy()
    result["isolation_score"] = iso_scores
    result["max_zscore"] = max_zscores
    result["seq_score_normalised"] = seq_normalised
    result["risk_score"] = risk_scores
    result["predicted_type"] = pred_classes
    result["confidence"] = np.round(max_confidence * 100, 2)
    result["zscore_source"] = zscore_sources

    # Store per-event z-scores as JSON for explainability
    result["feature_zscores"] = [
        {k: round(v, 3) for k, v in zs.items()} for zs in all_zscores
    ]

    logger.info(f"Scored {len(result)} events. "
                f"Mean risk: {np.mean(risk_scores):.2f}, "
                f"Max risk: {np.max(risk_scores):.2f}")

    return result
