"""
config.py — Central configuration for the Behavioral Anomaly Detection pipeline.
All tunable parameters, seeds, and paths live here.
"""

import os

# ──────────────────────────────────────────────
# Reproducibility
# ──────────────────────────────────────────────
RANDOM_SEED = 42

# ──────────────────────────────────────────────
# Entity pool sizes
# ──────────────────────────────────────────────
N_USERS = 120
N_SERVICE_ACCOUNTS = 40
N_EDGE_DEVICES = 40
N_COLD_START_ENTITIES = 15  # appear only in the last 10% of time range

# ──────────────────────────────────────────────
# Time range
# ──────────────────────────────────────────────
TIME_START = "2025-01-01"
TIME_END = "2025-03-31"
EVENTS_PER_ENTITY_RANGE = (100, 200)  # min, max events per entity

# ──────────────────────────────────────────────
# Attack injection
# ──────────────────────────────────────────────
ANOMALY_RATE = 0.02  # 2 % of total sessions

ATTACK_TYPE_WEIGHTS = {
    "brute_force": 0.20,
    "impossible_travel": 0.15,
    "credential_stuffing": 0.15,
    "lateral_movement": 0.20,
    "device_spoofing": 0.10,
    "low_and_slow": 0.10,
    "insider_drift": 0.10,
}

# ──────────────────────────────────────────────
# Risk-score combination weights (must sum to 1)
# ──────────────────────────────────────────────
W_ISOLATION = 0.35
W_ZSCORE = 0.35
W_SEQUENCE = 0.30

# ──────────────────────────────────────────────
# Feature engineering
# ──────────────────────────────────────────────
MIN_HISTORY = 5  # cold-start threshold (sessions)
ROLLING_WINDOW = 10  # events for rolling stats

# ──────────────────────────────────────────────
# Concept drift
# ──────────────────────────────────────────────
CONCEPT_DRIFT_ALPHA = 0.05  # EMA decay factor
N_DRIFT_ENTITIES = 5  # entities with injected concept drift

# ──────────────────────────────────────────────
# Train / test split
# ──────────────────────────────────────────────
TRAIN_RATIO = 0.70  # chronological split

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "outputs")
MODELS_DIR = os.path.join(OUTPUT_DIR, "models")
METRICS_DIR = os.path.join(OUTPUT_DIR, "metrics")

# ──────────────────────────────────────────────
# Geo city pool (lat, lon, name)
# ──────────────────────────────────────────────
CITY_POOL = [
    (40.7128, -74.0060, "New York"),
    (34.0522, -118.2437, "Los Angeles"),
    (51.5074, -0.1278, "London"),
    (48.8566, 2.3522, "Paris"),
    (35.6762, 139.6503, "Tokyo"),
    (28.6139, 77.2090, "New Delhi"),
    (55.7558, 37.6173, "Moscow"),
    (-33.8688, 151.2093, "Sydney"),
    (37.7749, -122.4194, "San Francisco"),
    (52.5200, 13.4050, "Berlin"),
    (1.3521, 103.8198, "Singapore"),
    (39.9042, 116.4074, "Beijing"),
    (-23.5505, -46.6333, "São Paulo"),
    (19.4326, -99.1332, "Mexico City"),
    (25.2048, 55.2708, "Dubai"),
    (41.0082, 28.9784, "Istanbul"),
    (59.9139, 10.7522, "Oslo"),
    (43.6532, -79.3832, "Toronto"),
    (35.6895, 51.3890, "Tehran"),
    (30.0444, 31.2357, "Cairo"),
]

# ──────────────────────────────────────────────
# Resource pool
# ──────────────────────────────────────────────
RESOURCE_POOL = [
    "/api/auth/login", "/api/auth/logout", "/api/users/profile",
    "/api/users/settings", "/api/data/export", "/api/data/import",
    "/api/admin/users", "/api/admin/config", "/api/admin/logs",
    "/api/reports/generate", "/api/reports/download", "/api/billing/invoices",
    "/api/billing/payments", "/api/inventory/list", "/api/inventory/update",
    "/api/devices/register", "/api/devices/status", "/api/devices/firmware",
    "/api/alerts/list", "/api/alerts/acknowledge", "/api/metrics/system",
    "/api/metrics/network", "/api/files/upload", "/api/files/download",
    "/api/keys/rotate", "/api/keys/generate", "/api/vpn/connect",
    "/api/vpn/disconnect", "/api/dns/lookup", "/api/dns/update",
    "/api/firewall/rules", "/api/firewall/logs", "/api/backup/create",
    "/api/backup/restore", "/api/certificates/issue", "/api/certificates/revoke",
    "/api/database/query", "/api/database/migrate", "/api/cache/flush",
    "/api/cache/stats", "/api/scheduler/jobs", "/api/scheduler/run",
    "/api/gateway/routes", "/api/gateway/health", "/api/iot/telemetry",
    "/api/iot/commands", "/api/scada/read", "/api/scada/write",
    "/api/pos/transaction", "/api/pos/refund",
]

# ──────────────────────────────────────────────
# Command pool (for command_sequence generation)
# ──────────────────────────────────────────────
COMMAND_POOL = [
    "LOGIN", "LOGOUT", "READ_FILE", "WRITE_FILE", "DELETE_FILE",
    "LIST_DIR", "CHANGE_DIR", "EXECUTE", "SUDO_EXECUTE", "INSTALL_PKG",
    "UPDATE_CONFIG", "RESTART_SERVICE", "VIEW_LOGS", "EXPORT_DATA",
    "IMPORT_DATA", "CREATE_USER", "DELETE_USER", "MODIFY_PERMS",
    "ENCRYPT", "DECRYPT", "SCAN_NETWORK", "PING_HOST", "TRACEROUTE",
    "DNS_LOOKUP", "CONNECT_VPN", "DISCONNECT_VPN", "DOWNLOAD",
    "UPLOAD", "COMPILE", "DEPLOY", "ROLLBACK", "SNAPSHOT",
    "BACKUP", "RESTORE", "QUERY_DB", "UPDATE_DB", "ROTATE_KEYS",
    "ISSUE_CERT", "REVOKE_CERT", "FLUSH_CACHE",
]

# ──────────────────────────────────────────────
# Auth methods
# ──────────────────────────────────────────────
AUTH_METHODS = ["password", "token", "certificate", "biometric"]

# ──────────────────────────────────────────────
# OS / protocol pools (for device fingerprint)
# ──────────────────────────────────────────────
OS_POOL = [
    "Windows 11", "Windows 10", "Ubuntu 22.04", "Ubuntu 20.04",
    "macOS Ventura", "macOS Sonoma", "RHEL 9", "Debian 12",
    "Android 14", "iOS 17", "FreeRTOS 10", "VxWorks 7",
]
PROTOCOL_POOL = ["HTTPS", "SSH", "MQTT", "CoAP", "Modbus", "OPC-UA", "TLS"]
