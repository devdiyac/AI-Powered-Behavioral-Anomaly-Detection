"""
data_generator.py — Synthetic access-log generator.

Produces a reproducible, timestamp-sorted CSV of access-log events with
injected attack patterns and concept-drift scenarios.
"""

import logging
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from config import (
    RANDOM_SEED, N_USERS, N_SERVICE_ACCOUNTS, N_EDGE_DEVICES,
    N_COLD_START_ENTITIES, TIME_START, TIME_END, EVENTS_PER_ENTITY_RANGE,
    ANOMALY_RATE, ATTACK_TYPE_WEIGHTS, N_DRIFT_ENTITIES,
    CITY_POOL, RESOURCE_POOL, COMMAND_POOL, AUTH_METHODS,
    OS_POOL, PROTOCOL_POOL, OUTPUT_DIR,
)

logger = logging.getLogger("pipeline.datagen")


# ─────────────────────────────────────────────────────────────────────
# Helper: generate a random MAC address
# ─────────────────────────────────────────────────────────────────────
def _random_mac(rng: np.random.Generator) -> str:
    octets = rng.integers(0, 256, size=6)
    return ":".join(f"{b:02X}" for b in octets)


def _random_ip(rng: np.random.Generator) -> str:
    return f"{rng.integers(1,224)}.{rng.integers(0,256)}.{rng.integers(0,256)}.{rng.integers(1,255)}"


# ─────────────────────────────────────────────────────────────────────
# Entity profile creation
# ─────────────────────────────────────────────────────────────────────
def _create_entity_profiles(rng: np.random.Generator):
    """
    Build a behavioural profile for every entity.
    Returns a list of profile dicts and a list of cold-start entity IDs.
    """
    profiles = []
    cold_start_ids = []

    total = N_USERS + N_SERVICE_ACCOUNTS + N_EDGE_DEVICES
    entity_counter = 0

    for entity_type, count in [("user", N_USERS),
                                ("service_account", N_SERVICE_ACCOUNTS),
                                ("edge_device", N_EDGE_DEVICES)]:
        for i in range(count):
            eid = f"{entity_type}_{entity_counter:04d}"
            entity_counter += 1

            # Is this a cold-start entity?
            is_cold = len(cold_start_ids) < N_COLD_START_ENTITIES and entity_counter > (total - N_COLD_START_ENTITIES)
            if is_cold:
                cold_start_ids.append(eid)

            # Home geo
            city_idx = rng.integers(0, len(CITY_POOL))
            home_lat, home_lon, home_city = CITY_POOL[city_idx]

            # Typical login hour
            if entity_type == "service_account":
                typical_hour_mean = rng.uniform(0, 24)
                typical_hour_std = 12.0  # nearly uniform
            else:
                typical_hour_mean = rng.choice([9.0, 10.0, 14.0, 22.0])
                typical_hour_std = rng.uniform(1.0, 3.0)

            # Typical resources (3–8)
            n_resources = rng.integers(3, 9)
            typical_resources = list(rng.choice(RESOURCE_POOL, size=n_resources, replace=False))

            # Primary auth method
            primary_auth = rng.choice(AUTH_METHODS)

            # Device fingerprint
            primary_os = rng.choice(OS_POOL)
            primary_mac = _random_mac(rng)
            primary_protocol = rng.choice(PROTOCOL_POOL)

            # Session duration (minutes)
            dur_mean = rng.uniform(5, 120)
            dur_std = rng.uniform(2, dur_mean * 0.4)

            # Command vocabulary (10–20 weighted commands)
            n_cmds = rng.integers(10, 21)
            cmd_vocab = list(rng.choice(COMMAND_POOL, size=n_cmds, replace=False))
            cmd_weights = rng.dirichlet(np.ones(n_cmds))

            # Events count
            n_events = rng.integers(*EVENTS_PER_ENTITY_RANGE)

            profiles.append({
                "entity_id": eid,
                "entity_type": entity_type,
                "is_cold_start": is_cold,
                "home_lat": home_lat,
                "home_lon": home_lon,
                "home_city": home_city,
                "typical_hour_mean": typical_hour_mean,
                "typical_hour_std": typical_hour_std,
                "typical_resources": typical_resources,
                "primary_auth": primary_auth,
                "primary_os": primary_os,
                "primary_mac": primary_mac,
                "primary_protocol": primary_protocol,
                "dur_mean": dur_mean,
                "dur_std": dur_std,
                "cmd_vocab": cmd_vocab,
                "cmd_weights": cmd_weights.tolist(),
                "n_events": int(n_events),
            })

    return profiles, cold_start_ids


# ─────────────────────────────────────────────────────────────────────
# Normal event generation
# ─────────────────────────────────────────────────────────────────────
def _generate_normal_events(profiles, cold_start_ids, rng):
    """Generate benign events from each entity's behavioural profile."""
    t_start = pd.Timestamp(TIME_START)
    t_end = pd.Timestamp(TIME_END)
    total_seconds = (t_end - t_start).total_seconds()

    # Cold-start entities only appear in last 10 %
    cold_start_begin = t_start + timedelta(seconds=total_seconds * 0.90)

    rows = []
    for prof in profiles:
        eid = prof["entity_id"]
        is_cold = prof["is_cold_start"]
        begin = cold_start_begin if is_cold else t_start

        available_seconds = (t_end - begin).total_seconds()
        n = prof["n_events"]

        # Random timestamps within the entity's active window
        offsets = np.sort(rng.uniform(0, available_seconds, size=n))
        timestamps = [begin + timedelta(seconds=float(o)) for o in offsets]

        for ts in timestamps:
            # Hour noise
            hour_noise = rng.normal(0, prof["typical_hour_std"])
            event_hour = (prof["typical_hour_mean"] + hour_noise) % 24
            ts = ts.replace(hour=int(event_hour) % 24,
                            minute=rng.integers(0, 60),
                            second=rng.integers(0, 60))

            # Geo: home + small jitter (< 50 km ≈ 0.45 degrees)
            lat = prof["home_lat"] + rng.normal(0, 0.15)
            lon = prof["home_lon"] + rng.normal(0, 0.15)
            geo = f"{lat:.4f},{lon:.4f}"

            # Resource
            if rng.random() < 0.80:
                resource = rng.choice(prof["typical_resources"])
            else:
                resource = rng.choice(RESOURCE_POOL)

            # Auth
            auth = prof["primary_auth"] if rng.random() < 0.80 else rng.choice(AUTH_METHODS)

            # Session duration (lognormal)
            duration = max(1.0, rng.lognormal(np.log(prof["dur_mean"]), 0.4))

            # Command sequence (3–10 commands from weighted vocab)
            seq_len = rng.integers(3, 11)
            cmds = rng.choice(prof["cmd_vocab"], size=seq_len,
                              p=prof["cmd_weights"]).tolist()

            # Device fingerprint
            fp = f"{prof['primary_os']}|{prof['primary_mac']}|{prof['primary_protocol']}"

            rows.append({
                "entity_id": eid,
                "entity_type": prof["entity_type"],
                "timestamp": ts,
                "source_ip": _random_ip(rng),
                "geo_location": geo,
                "resource_accessed": resource,
                "auth_method": auth,
                "session_duration": round(duration, 2),
                "command_sequence": json.dumps(cmds),
                "device_fingerprint": fp,
                "label": "normal",
            })

    return rows


# ─────────────────────────────────────────────────────────────────────
# Attack injection
# ─────────────────────────────────────────────────────────────────────
def _inject_attacks(normal_rows, profiles, rng):
    """
    Replace / overlay a fraction of events with attack patterns.
    Returns the full event list with attacks injected.
    """
    n_total = len(normal_rows)
    n_attacks = int(n_total * ANOMALY_RATE)

    # Build a mapping for quick lookup
    profile_map = {p["entity_id"]: p for p in profiles}
    # Only use non-cold-start entities for attacks (more realistic)
    eligible = [p for p in profiles if not p["is_cold_start"]]

    attack_rows = []
    attack_types = list(ATTACK_TYPE_WEIGHTS.keys())
    attack_probs = list(ATTACK_TYPE_WEIGHTS.values())

    t_start = pd.Timestamp(TIME_START)
    t_end = pd.Timestamp(TIME_END)

    chosen_types = rng.choice(attack_types, size=n_attacks, p=attack_probs)

    for atype in chosen_types:
        prof = eligible[rng.integers(0, len(eligible))]
        eid = prof["entity_id"]
        base_ts = t_start + timedelta(
            seconds=float(rng.uniform(0, (t_end - t_start).total_seconds()))
        )

        if atype == "brute_force":
            # Burst of 5–15 rapid failed-auth attempts
            burst_size = rng.integers(5, 16)
            for j in range(burst_size):
                ts = base_ts + timedelta(seconds=float(rng.uniform(0, 120)))
                attack_rows.append({
                    "entity_id": eid,
                    "entity_type": prof["entity_type"],
                    "timestamp": ts,
                    "source_ip": _random_ip(rng),
                    "geo_location": f"{prof['home_lat']:.4f},{prof['home_lon']:.4f}",
                    "resource_accessed": "/api/auth/login",
                    "auth_method": "password",
                    "session_duration": round(rng.uniform(0.1, 3.0), 2),
                    "command_sequence": json.dumps(["LOGIN", "AUTH_FAIL"]),
                    "device_fingerprint": f"{prof['primary_os']}|{prof['primary_mac']}|{prof['primary_protocol']}",
                    "label": "brute_force",
                })

        elif atype == "impossible_travel":
            # Login from distant geo within < 1 hour
            far_city_idx = rng.integers(0, len(CITY_POOL))
            far_lat, far_lon, _ = CITY_POOL[far_city_idx]
            ts = base_ts + timedelta(minutes=float(rng.uniform(5, 50)))
            attack_rows.append({
                "entity_id": eid,
                "entity_type": prof["entity_type"],
                "timestamp": ts,
                "source_ip": _random_ip(rng),
                "geo_location": f"{far_lat:.4f},{far_lon:.4f}",
                "resource_accessed": rng.choice(prof["typical_resources"]),
                "auth_method": prof["primary_auth"],
                "session_duration": round(rng.uniform(5, 60), 2),
                "command_sequence": json.dumps(["LOGIN", "READ_FILE", "EXPORT_DATA"]),
                "device_fingerprint": f"{prof['primary_os']}|{_random_mac(rng)}|{prof['primary_protocol']}",
                "label": "impossible_travel",
            })

        elif atype == "credential_stuffing":
            # Many entity_ids, few source_ips, high failure
            shared_ip = _random_ip(rng)
            n_victims = rng.integers(5, 15)
            victims = rng.choice(eligible, size=min(n_victims, len(eligible)), replace=False)
            for v in victims:
                ts = base_ts + timedelta(seconds=float(rng.uniform(0, 300)))
                attack_rows.append({
                    "entity_id": v["entity_id"],
                    "entity_type": v["entity_type"],
                    "timestamp": ts,
                    "source_ip": shared_ip,
                    "geo_location": f"{v['home_lat'] + rng.normal(0,5):.4f},{v['home_lon'] + rng.normal(0,5):.4f}",
                    "resource_accessed": "/api/auth/login",
                    "auth_method": "password",
                    "session_duration": round(rng.uniform(0.1, 2.0), 2),
                    "command_sequence": json.dumps(["LOGIN", "AUTH_FAIL"]),
                    "device_fingerprint": f"{rng.choice(OS_POOL)}|{_random_mac(rng)}|HTTPS",
                    "label": "credential_stuffing",
                })

        elif atype == "lateral_movement":
            # Access unusual resources rapidly
            n_hops = rng.integers(5, 16)
            unusual = [r for r in RESOURCE_POOL if r not in prof["typical_resources"]]
            for j in range(n_hops):
                ts = base_ts + timedelta(minutes=float(rng.uniform(0, 30)))
                attack_rows.append({
                    "entity_id": eid,
                    "entity_type": prof["entity_type"],
                    "timestamp": ts,
                    "source_ip": _random_ip(rng),
                    "geo_location": f"{prof['home_lat']:.4f},{prof['home_lon']:.4f}",
                    "resource_accessed": rng.choice(unusual) if unusual else rng.choice(RESOURCE_POOL),
                    "auth_method": prof["primary_auth"],
                    "session_duration": round(rng.uniform(1, 10), 2),
                    "command_sequence": json.dumps(["LOGIN", "SCAN_NETWORK", "SUDO_EXECUTE", "EXPORT_DATA"]),
                    "device_fingerprint": f"{prof['primary_os']}|{prof['primary_mac']}|{prof['primary_protocol']}",
                    "label": "lateral_movement",
                })

        elif atype == "device_spoofing":
            # Same entity_id, different fingerprint
            ts = base_ts
            attack_rows.append({
                "entity_id": eid,
                "entity_type": prof["entity_type"],
                "timestamp": ts,
                "source_ip": _random_ip(rng),
                "geo_location": f"{prof['home_lat']:.4f},{prof['home_lon']:.4f}",
                "resource_accessed": rng.choice(prof["typical_resources"]),
                "auth_method": prof["primary_auth"],
                "session_duration": round(rng.uniform(5, 60), 2),
                "command_sequence": json.dumps(["LOGIN", "READ_FILE"]),
                "device_fingerprint": f"{rng.choice(OS_POOL)}|{_random_mac(rng)}|{rng.choice(PROTOCOL_POOL)}",
                "label": "device_spoofing",
            })

        elif atype == "low_and_slow":
            # Small off-hours access over many days
            n_days = rng.integers(10, 21)
            for d in range(n_days):
                ts = base_ts + timedelta(days=int(d), hours=float(rng.uniform(1, 5)))
                if ts > t_end:
                    break
                attack_rows.append({
                    "entity_id": eid,
                    "entity_type": prof["entity_type"],
                    "timestamp": ts,
                    "source_ip": _random_ip(rng),
                    "geo_location": f"{prof['home_lat']:.4f},{prof['home_lon']:.4f}",
                    "resource_accessed": rng.choice(["/api/data/export", "/api/files/download", "/api/database/query"]),
                    "auth_method": prof["primary_auth"],
                    "session_duration": round(rng.uniform(1, 8), 2),
                    "command_sequence": json.dumps(["LOGIN", "READ_FILE", "EXPORT_DATA", "LOGOUT"]),
                    "device_fingerprint": f"{prof['primary_os']}|{prof['primary_mac']}|{prof['primary_protocol']}",
                    "label": "low_and_slow",
                })

        elif atype == "insider_drift":
            # Gradually expanding resource footprint
            n_weeks = rng.integers(4, 7)
            for w in range(n_weeks):
                n_new = rng.integers(1, 3)
                for _ in range(n_new):
                    ts = base_ts + timedelta(weeks=int(w), days=float(rng.uniform(0, 6)))
                    if ts > t_end:
                        break
                    attack_rows.append({
                        "entity_id": eid,
                        "entity_type": prof["entity_type"],
                        "timestamp": ts,
                        "source_ip": _random_ip(rng),
                        "geo_location": f"{prof['home_lat']:.4f},{prof['home_lon']:.4f}",
                        "resource_accessed": rng.choice(RESOURCE_POOL),
                        "auth_method": prof["primary_auth"],
                        "session_duration": round(rng.uniform(5, 60), 2),
                        "command_sequence": json.dumps(["LOGIN", "LIST_DIR", "READ_FILE", "MODIFY_PERMS"]),
                        "device_fingerprint": f"{prof['primary_os']}|{prof['primary_mac']}|{prof['primary_protocol']}",
                        "label": "insider_drift",
                    })

    return attack_rows


# ─────────────────────────────────────────────────────────────────────
# Concept drift injection
# ─────────────────────────────────────────────────────────────────────
def _inject_concept_drift(profiles, rng):
    """
    Pick N_DRIFT_ENTITIES entities and shift their behavioural profile midway.
    Returns the IDs of drifted entities and the shift details.
    """
    eligible = [p for p in profiles if not p["is_cold_start"]]
    drift_indices = rng.choice(len(eligible), size=min(N_DRIFT_ENTITIES, len(eligible)), replace=False)
    drift_info = {}

    for idx in drift_indices:
        prof = eligible[idx]
        eid = prof["entity_id"]

        # Shift typical hour
        old_hour = prof["typical_hour_mean"]
        new_hour = (old_hour + rng.uniform(4, 8)) % 24
        prof["typical_hour_mean"] = new_hour

        # Add a new device fingerprint
        old_fp = f"{prof['primary_os']}|{prof['primary_mac']}|{prof['primary_protocol']}"
        prof["primary_os"] = rng.choice(OS_POOL)
        prof["primary_mac"] = _random_mac(rng)
        new_fp = f"{prof['primary_os']}|{prof['primary_mac']}|{prof['primary_protocol']}"

        drift_info[eid] = {
            "old_hour": old_hour,
            "new_hour": new_hour,
            "old_fingerprint": old_fp,
            "new_fingerprint": new_fp,
        }
        logger.info(f"Concept drift: {eid} hour {old_hour:.1f}→{new_hour:.1f}")

    return drift_info


# ─────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────
def generate_access_logs() -> pd.DataFrame:
    """
    Generate the full synthetic dataset.
    Returns a timestamp-sorted DataFrame and saves CSV to outputs/.
    """
    rng = np.random.default_rng(RANDOM_SEED)

    logger.info("Creating entity profiles …")
    profiles, cold_start_ids = _create_entity_profiles(rng)
    logger.info(f"  {len(profiles)} entities ({len(cold_start_ids)} cold-start)")

    # Inject concept drift into some profiles *before* generating events
    logger.info("Injecting concept drift …")
    drift_info = _inject_concept_drift(profiles, rng)

    logger.info("Generating normal events …")
    normal_rows = _generate_normal_events(profiles, cold_start_ids, rng)
    logger.info(f"  {len(normal_rows)} normal events")

    logger.info("Injecting attack patterns …")
    attack_rows = _inject_attacks(normal_rows, profiles, rng)
    logger.info(f"  {len(attack_rows)} attack events")

    all_rows = normal_rows + attack_rows
    df = pd.DataFrame(all_rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Save
    out_path = os.path.join(OUTPUT_DIR, "access_logs.csv")
    df.to_csv(out_path, index=False)
    logger.info(f"Saved {len(df)} events → {out_path}")

    # Summary
    label_counts = df["label"].value_counts()
    anomaly_frac = 1 - label_counts.get("normal", 0) / len(df)
    logger.info(f"  Anomaly rate: {anomaly_frac:.2%}")
    logger.info(f"  Label distribution:\n{label_counts.to_string()}")

    # Save drift info for evaluation
    import json as _json
    drift_path = os.path.join(OUTPUT_DIR, "drift_info.json")
    with open(drift_path, "w") as f:
        _json.dump(drift_info, f, indent=2)

    # Save cold-start IDs
    cs_path = os.path.join(OUTPUT_DIR, "cold_start_ids.json")
    with open(cs_path, "w") as f:
        _json.dump(cold_start_ids, f, indent=2)

    return df


import os  # ensure import at top level (already imported)

if __name__ == "__main__":
    from utils import setup_logging, ensure_output_dirs
    setup_logging()
    ensure_output_dirs()
    generate_access_logs()
