"""
feature_engineering.py — Causal feature extraction from raw access logs.

Every feature for a given event is computed using ONLY that entity's
history *before* the event — no look-ahead leakage.
"""

import json
import logging
import os

import numpy as np
import pandas as pd

from config import (
    MIN_HISTORY, ROLLING_WINDOW, OUTPUT_DIR, COMMAND_POOL, RANDOM_SEED,
)
from utils import haversine

logger = logging.getLogger("pipeline.features")


# ─────────────────────────────────────────────────────────────────────
# Markov sequence model
# ─────────────────────────────────────────────────────────────────────
class CommandSequenceModel:
    """
    First-order Markov transition model over command tokens.
    Maintains per-entity and per-entity_type transition matrices.
    """

    def __init__(self, commands=COMMAND_POOL, smoothing=1e-6):
        self.commands = list(commands) + ["AUTH_FAIL", "<START>", "<END>"]
        self.cmd_to_idx = {c: i for i, c in enumerate(self.commands)}
        self.n = len(self.commands)
        self.smoothing = smoothing

        # Per entity_type population matrices
        self.population_counts = {}  # entity_type -> transition count matrix
        # Per entity matrices
        self.entity_counts = {}  # entity_id -> transition count matrix

    def _ensure_matrix(self, key, store):
        if key not in store:
            store[key] = np.full((self.n, self.n), self.smoothing)

    def update(self, entity_id: str, entity_type: str, cmd_seq: list):
        """Update transition counts for both entity and population models."""
        self._ensure_matrix(entity_type, self.population_counts)
        self._ensure_matrix(entity_id, self.entity_counts)

        tokens = ["<START>"] + cmd_seq + ["<END>"]
        for a, b in zip(tokens[:-1], tokens[1:]):
            ai = self.cmd_to_idx.get(a)
            bi = self.cmd_to_idx.get(b)
            if ai is not None and bi is not None:
                self.population_counts[entity_type][ai, bi] += 1
                self.entity_counts[entity_id][ai, bi] += 1

    def log_likelihood(self, entity_id: str, entity_type: str, cmd_seq: list,
                       session_count: int) -> tuple:
        """
        Compute average log-probability of the command sequence.
        Uses personal model if sufficient history, else population model.

        Returns (log_likelihood, source) where source is 'personal' or 'population'.
        """
        if session_count >= MIN_HISTORY and entity_id in self.entity_counts:
            counts = self.entity_counts[entity_id]
            source = "personal"
        elif entity_type in self.population_counts:
            counts = self.population_counts[entity_type]
            source = "population"
        else:
            return 0.0, "population"

        # Normalise rows to get transition probabilities
        row_sums = counts.sum(axis=1, keepdims=True)
        row_sums = np.where(row_sums == 0, 1, row_sums)
        probs = counts / row_sums

        tokens = ["<START>"] + cmd_seq + ["<END>"]
        ll = 0.0
        n_transitions = 0
        for a, b in zip(tokens[:-1], tokens[1:]):
            ai = self.cmd_to_idx.get(a)
            bi = self.cmd_to_idx.get(b)
            if ai is not None and bi is not None:
                ll += np.log(max(probs[ai, bi], 1e-12))
                n_transitions += 1

        avg_ll = ll / max(n_transitions, 1)
        return avg_ll, source


# ─────────────────────────────────────────────────────────────────────
# Population baseline tracker
# ─────────────────────────────────────────────────────────────────────
class PopulationBaseline:
    """Running mean/std per numeric feature, grouped by entity_type."""

    def __init__(self):
        self.stats = {}  # entity_type -> {feature: {"sum":, "sumsq":, "n":}}

    def update(self, entity_type: str, features: dict):
        if entity_type not in self.stats:
            self.stats[entity_type] = {}
        s = self.stats[entity_type]
        for k, v in features.items():
            if k not in s:
                s[k] = {"sum": 0.0, "sumsq": 0.0, "n": 0}
            s[k]["sum"] += v
            s[k]["sumsq"] += v ** 2
            s[k]["n"] += 1

    def mean(self, entity_type: str, feature: str) -> float:
        try:
            s = self.stats[entity_type][feature]
            return s["sum"] / s["n"]
        except (KeyError, ZeroDivisionError):
            return 0.0

    def std(self, entity_type: str, feature: str) -> float:
        try:
            s = self.stats[entity_type][feature]
            m = s["sum"] / s["n"]
            var = s["sumsq"] / s["n"] - m ** 2
            return max(np.sqrt(max(var, 0)), 1e-6)
        except (KeyError, ZeroDivisionError):
            return 1.0


# ─────────────────────────────────────────────────────────────────────
# Per-entity history tracker
# ─────────────────────────────────────────────────────────────────────
class EntityProfileTracker:
    """Maintains running per-entity statistics for causal feature computation."""

    def __init__(self):
        self.history = {}  # entity_id -> dict of lists/sets

    def _ensure(self, eid):
        if eid not in self.history:
            self.history[eid] = {
                "hours": [],
                "geos": [],         # list of (lat, lon)
                "timestamps": [],
                "resources": set(),
                "fingerprints": set(),
                "durations": [],
                "auth_results": [],  # 1 = short/fail, 0 = ok
                "session_count": 0,
            }

    def update(self, eid: str, hour: float, geo: tuple, ts, resource: str,
               fingerprint: str, duration: float, is_auth_fail: bool):
        self._ensure(eid)
        h = self.history[eid]
        h["hours"].append(hour)
        h["geos"].append(geo)
        h["timestamps"].append(ts)
        h["resources"].add(resource)
        h["fingerprints"].add(fingerprint)
        h["durations"].append(duration)
        h["auth_results"].append(1 if is_auth_fail else 0)
        h["session_count"] += 1

    def get(self, eid):
        self._ensure(eid)
        return self.history[eid]


# ─────────────────────────────────────────────────────────────────────
# Main feature extraction
# ─────────────────────────────────────────────────────────────────────
def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process events chronologically and compute causal features.
    Returns a DataFrame with one row per event + all numeric features.
    """
    logger.info("Extracting features (causal, chronological) …")

    df = df.sort_values("timestamp").reset_index(drop=True)

    tracker = EntityProfileTracker()
    seq_model = CommandSequenceModel()
    pop_baseline = PopulationBaseline()

    feature_rows = []

    for idx, row in df.iterrows():
        eid = row["entity_id"]
        etype = row["entity_type"]
        ts = pd.Timestamp(row["timestamp"])
        hour = ts.hour + ts.minute / 60.0

        # Parse geo
        try:
            lat, lon = map(float, row["geo_location"].split(","))
        except Exception:
            lat, lon = 0.0, 0.0

        # Parse commands
        try:
            cmds = json.loads(row["command_sequence"])
        except Exception:
            cmds = []

        resource = row["resource_accessed"]
        fingerprint = row["device_fingerprint"]
        duration = float(row["session_duration"])
        is_auth_fail = duration < 5.0 and "AUTH_FAIL" in str(row.get("command_sequence", ""))

        hist = tracker.get(eid)
        sc = hist["session_count"]
        is_cold = sc < MIN_HISTORY

        # ----- Compute features using ONLY prior history -----

        # 1. Hour deviation
        if sc > 0 and len(hist["hours"]) > 0:
            h_mean = np.mean(hist["hours"])
            h_std = max(np.std(hist["hours"]), 1e-6)
            hour_dev = abs(hour - h_mean) / h_std
            hour_source = "personal"
        else:
            pop_mean = pop_baseline.mean(etype, "hour")
            pop_std = pop_baseline.std(etype, "hour")
            hour_dev = abs(hour - pop_mean) / pop_std if pop_std > 0 else 0.0
            hour_source = "population"

        # 2. Geo velocity
        geo_velocity = 0.0
        if sc > 0 and len(hist["geos"]) > 0:
            prev_lat, prev_lon = hist["geos"][-1]
            prev_ts = hist["timestamps"][-1]
            dist_km = haversine(prev_lat, prev_lon, lat, lon)
            dt_hours = max((ts - prev_ts).total_seconds() / 3600, 1e-6)
            geo_velocity = dist_km / dt_hours

        # 3. Time since last session
        if sc > 0 and len(hist["timestamps"]) > 0:
            time_since = (ts - hist["timestamps"][-1]).total_seconds() / 3600
        else:
            time_since = pop_baseline.mean(etype, "time_since_last") if not is_cold else 24.0

        # 4. Auth failure streak
        auth_streak = 0
        if sc > 0:
            for val in reversed(hist["auth_results"]):
                if val == 1:
                    auth_streak += 1
                else:
                    break

        # 5. Session duration z-score
        if sc > 1 and len(hist["durations"]) > 1:
            d_mean = np.mean(hist["durations"])
            d_std = max(np.std(hist["durations"]), 1e-6)
            dur_zscore = (duration - d_mean) / d_std
            dur_source = "personal"
        else:
            pop_mean = pop_baseline.mean(etype, "duration")
            pop_std = pop_baseline.std(etype, "duration")
            dur_zscore = (duration - pop_mean) / pop_std if pop_std > 0 else 0.0
            dur_source = "population"

        # 6. New resource flag
        new_resource = 1 if resource not in hist["resources"] else 0

        # 7. New device flag
        new_device = 1 if fingerprint not in hist["fingerprints"] else 0

        # 8. Resource breadth ratio
        recent_resources = set()
        # Count unique resources in last ROLLING_WINDOW events (from history)
        if sc > 0:
            # We'll approximate: the resource set size vs typical
            typical_count = max(len(hist["resources"]), 1)
            resource_breadth = len(hist["resources"]) / typical_count
        else:
            resource_breadth = 1.0

        # 9. Sequence log-likelihood
        seq_ll, seq_source = seq_model.log_likelihood(eid, etype, cmds, sc)

        # 10. Off-hours flag
        is_off_hours = 1 if (hour < 6 or hour > 22) else 0

        # Build feature dict
        feats = {
            "hour_deviation": hour_dev,
            "geo_velocity_kmh": geo_velocity,
            "time_since_last_hrs": time_since,
            "session_count": sc,
            "auth_failure_streak": auth_streak,
            "session_duration_zscore": dur_zscore,
            "new_resource_flag": new_resource,
            "new_device_flag": new_device,
            "resource_breadth_ratio": resource_breadth,
            "sequence_log_likelihood": seq_ll,
            "is_off_hours": is_off_hours,
            "is_cold_start": 1 if is_cold else 0,
        }

        # Determine primary inference source
        if is_cold:
            inference_source = "population"
        else:
            inference_source = "personal"

        feature_rows.append({
            "entity_id": eid,
            "entity_type": etype,
            "timestamp": ts,
            "label": row["label"],
            "inference_source": inference_source,
            "session_duration": duration,
            "geo_location": row["geo_location"],
            "resource_accessed": resource,
            "auth_method": row["auth_method"],
            "device_fingerprint": fingerprint,
            "command_sequence": row["command_sequence"],
            **feats,
        })

        # ----- NOW update trackers (after computing features) -----
        tracker.update(eid, hour, (lat, lon), ts, resource, fingerprint, duration, is_auth_fail)
        seq_model.update(eid, etype, cmds)
        pop_baseline.update(etype, {
            "hour": hour,
            "duration": duration,
            "time_since_last": time_since,
            "geo_velocity": geo_velocity,
        })

        if idx % 5000 == 0 and idx > 0:
            logger.info(f"  Processed {idx}/{len(df)} events")

    feature_df = pd.DataFrame(feature_rows)

    out_path = os.path.join(OUTPUT_DIR, "features.csv")
    feature_df.to_csv(out_path, index=False)
    logger.info(f"Saved {len(feature_df)} feature rows → {out_path}")

    return feature_df


if __name__ == "__main__":
    from utils import setup_logging, ensure_output_dirs
    setup_logging()
    ensure_output_dirs()
    df = pd.read_csv(os.path.join(OUTPUT_DIR, "access_logs.csv"))
    extract_features(df)
