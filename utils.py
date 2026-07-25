"""
utils.py — Shared utilities: haversine, environment detection, directory setup, logging.
"""

import os
import math
import logging
import importlib

from config import OUTPUT_DIR, MODELS_DIR, METRICS_DIR


# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
def setup_logging(level=logging.INFO):
    """Configure structured console logging for the pipeline."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)-22s | %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger("pipeline")


# ──────────────────────────────────────────────
# Directory helpers
# ──────────────────────────────────────────────
def ensure_output_dirs():
    """Create the outputs/ directory tree if it does not exist."""
    for d in [OUTPUT_DIR, MODELS_DIR, METRICS_DIR]:
        os.makedirs(d, exist_ok=True)


# ──────────────────────────────────────────────
# Environment detection
# ──────────────────────────────────────────────
def detect_environment():
    """
    Probe for optional libraries and return a dict of availability flags.
    The pipeline degrades gracefully when optional libs are missing.
    """
    optional_libs = ["xgboost", "shap", "torch", "tensorflow", "faker"]
    env = {}
    for lib in optional_libs:
        try:
            importlib.import_module(lib)
            env[lib] = True
        except ImportError:
            env[lib] = False

    logger = logging.getLogger("pipeline.env")
    logger.info("Environment scan:")
    for lib, available in env.items():
        status = "✓ available" if available else "✗ not found (will use fallback)"
        logger.info(f"  {lib:15s} : {status}")

    return env


# ──────────────────────────────────────────────
# Haversine distance
# ──────────────────────────────────────────────
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute great-circle distance in **kilometres** between two
    (latitude, longitude) points using the Haversine formula.
    """
    R = 6_371.0  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))
