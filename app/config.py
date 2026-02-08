from __future__ import annotations

import hashlib
import json

# Fixed research configuration (matches your requirements)
ASTRO_CONFIG = {
    "zodiac_system": "sidereal",
    "ayanamsa": "lahiri",
    "node_type": "mean",
    "location": {
        "name": "Mumbai, India",
        "lat": 19.0760,
        "lon": 72.8777,
        "tz": "Asia/Kolkata",
    },
    "defaults": {
        "daily_eval_time": "09:15:00",
        "stationary_speed_threshold_deg_per_day": 0.01,
        "default_orb_deg": 3.0,
    },
}


def config_hash() -> str:
    """Stable hash for caching/auditing."""
    s = json.dumps(ASTRO_CONFIG, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]
