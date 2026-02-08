from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from dateutil import parser
import swisseph as swe

from .config import ASTRO_CONFIG

# ----------------------
# Constants / mappings
# ----------------------

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha", "Ardra", "Punarvasu",
    "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra",
    "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

TITHI_NAMES = [
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami",
    "Ashtami", "Navami", "Dashami", "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami",
    "Ashtami", "Navami", "Dashami", "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Amavasya"
]

PLANET_IDS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
    # Nodes handled separately
}

# ----------------------
# Swiss Ephemeris setup
# ----------------------

def _init_swe() -> None:
    # Sidereal Lahiri
    swe.set_sid_mode(swe.SIDM_LAHIRI)

_init_swe()

FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL


def parse_ts(ts_iso: str) -> datetime:
    """Parse an ISO timestamp (with offset) to aware datetime."""
    dt = parser.isoparse(ts_iso)
    if dt.tzinfo is None:
        # Assume UTC if missing; UI always provides +05:30
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def to_jd_ut(dt: datetime) -> float:
    """Convert aware datetime to Julian day (UT)."""
    dt_utc = dt.astimezone(timezone.utc)
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                      dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0)


def norm360(x: float) -> float:
    x = x % 360.0
    return x + 360.0 if x < 0 else x


def angular_sep(a: float, b: float) -> float:
    """Minimum separation between two angles in degrees (0..180)."""
    d = abs(norm360(a) - norm360(b))
    return 360.0 - d if d > 180.0 else d


def sign_from_lon(lon: float) -> Tuple[str, float]:
    lon = norm360(lon)
    sign_idx = int(lon // 30.0)
    deg_in_sign = lon - sign_idx * 30.0
    return SIGN_NAMES[sign_idx], deg_in_sign


def nakshatra_from_lon(lon: float) -> Tuple[str, int]:
    lon = norm360(lon)
    nak_size = 360.0 / 27.0  # 13.333...
    idx = int(lon // nak_size)
    name = NAKSHATRA_NAMES[idx]
    # Pada: each nak is 4 padas
    pada_size = nak_size / 4.0
    pos_in_nak = lon - idx * nak_size
    pada = int(pos_in_nak // pada_size) + 1
    return name, pada


def navamsha_sign(sign_name: str, deg_in_sign: float) -> str:
    """Compute D9 sign (Navamsa) from D1 sign and degree-in-sign.

    Rule:
      - Movable signs (Aries, Cancer, Libra, Capricorn): start from same sign
      - Fixed signs (Taurus, Leo, Scorpio, Aquarius): start from 9th from sign
      - Dual signs (Gemini, Virgo, Sagittarius, Pisces): start from 5th from sign
    """
    sign_idx = SIGN_NAMES.index(sign_name)
    movable = {0, 3, 6, 9}
    fixed = {1, 4, 7, 10}
    dual = {2, 5, 8, 11}
    if sign_idx in movable:
        start = sign_idx
    elif sign_idx in fixed:
        start = (sign_idx + 8) % 12
    else:  # dual
        start = (sign_idx + 4) % 12

    segment = int(deg_in_sign // (30.0 / 9.0))  # 0..8, each 3.333...
    d9_idx = (start + segment) % 12
    return SIGN_NAMES[d9_idx]


def planet_lon_speed(jd_ut: float, planet_id: int) -> Tuple[float, float]:
    """Return sidereal longitude and speed (deg/day)."""
    # swe.calc_ut returns (xx, retflag). xx = [lon, lat, dist, lon_speed, lat_speed, dist_speed]
    xx, _ = swe.calc_ut(jd_ut, planet_id, FLAGS)
    lon = norm360(xx[0])
    speed = xx[3]
    return lon, speed


def mean_node_lon_speed(jd_ut: float) -> Tuple[float, float]:
    """Mean node (Rahu) longitude/speed; Ketu is opposite."""
    xx, _ = swe.calc_ut(jd_ut, swe.MEAN_NODE, FLAGS)
    lon = norm360(xx[0])
    speed = xx[3]
    return lon, speed


def tithi(sun_lon: float, moon_lon: float) -> Dict[str, object]:
    diff = norm360(moon_lon - sun_lon)
    idx = int(diff // 12.0) + 1  # 1..30
    name = TITHI_NAMES[idx - 1]
    paksha = "Shukla" if idx <= 15 else "Krishna"
    return {"tithi_index": idx, "tithi_name": name, "paksha": paksha}


def compute_snapshot(ts_iso: str) -> Dict[str, object]:
    dt = parse_ts(ts_iso)
    jd = to_jd_ut(dt)

    stationary_thr = ASTRO_CONFIG["defaults"]["stationary_speed_threshold_deg_per_day"]

    # Compute planets
    d1 = []
    d9 = []

    # Sun/Moon first for Panchang
    sun_lon, sun_spd = planet_lon_speed(jd, swe.SUN)
    moon_lon, moon_spd = planet_lon_speed(jd, swe.MOON)

    # Helper to add a body
    def add_body(name: str, lon: float, speed: float):
        sign, deg_in_sign = sign_from_lon(lon)
        nak, pada = nakshatra_from_lon(lon)
        is_retro = speed < 0
        is_stationary = abs(speed) < stationary_thr
        d1.append({
            "name": name,
            "lon_sid_deg": lon,
            "sign": sign,
            "deg_in_sign": round(deg_in_sign, 6),
            "nakshatra": nak,
            "pada": pada,
            "speed_deg_day": round(speed, 6),
            "is_retro": bool(is_retro),
            "is_stationary": bool(is_stationary),
        })
        d9_sign = navamsha_sign(sign, deg_in_sign)
        d9.append({
            "name": name,
            "sign_d9": d9_sign,
            "vargottam": (d9_sign == sign),
        })

    # Standard planets
    for pname, pid in PLANET_IDS.items():
        lon, spd = planet_lon_speed(jd, pid)
        add_body(pname, lon, spd)

    # Mean node Rahu / Ketu
    rahu_lon, rahu_spd = mean_node_lon_speed(jd)
    ketu_lon = norm360(rahu_lon + 180.0)
    ketu_spd = rahu_spd  # opposite node, same magnitude/signed speed model
    add_body("Rahu", rahu_lon, rahu_spd)
    add_body("Ketu", ketu_lon, ketu_spd)

    # Panchang
    panchang = tithi(sun_lon, moon_lon)

    return {
        "meta": {
            "ts": dt.isoformat(),
            "tz": ASTRO_CONFIG["location"]["tz"],
            "location": ASTRO_CONFIG["location"],
            "system": {
                "zodiac": ASTRO_CONFIG["zodiac_system"],
                "ayanamsa": ASTRO_CONFIG["ayanamsa"],
                "node": ASTRO_CONFIG["node_type"],
            },
        },
        "d1": {"planets": d1},
        "d9": {"planets": d9},
        "panchang": panchang,
    }


def compute_aspects(planets: List[Dict[str, object]], orb_deg: float = 3.0) -> List[Dict[str, object]]:
    """Compute basic aspects among planets in given snapshot. Optional."""
    # aspects: conj, opp, trine, square, sextile
    aspects = []
    aspect_defs = [
        ("CONJUNCTION", 0.0),
        ("SEXTILE", 60.0),
        ("SQUARE", 90.0),
        ("TRINE", 120.0),
        ("OPPOSITION", 180.0),
    ]

    names = [p["name"] for p in planets]
    lon_map = {p["name"]: float(p["lon_sid_deg"]) for p in planets}

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = names[i]
            b = names[j]
            sep = angular_sep(lon_map[a], lon_map[b])
            for aspect_name, target in aspect_defs:
                diff = abs(sep - target)
                if diff <= orb_deg:
                    aspects.append({
                        "a": a,
                        "b": b,
                        "aspect": aspect_name,
                        "sep_deg": round(sep, 6),
                        "orb_deg": round(diff, 6),
                        "orb_used": orb_deg,
                    })
                    break

    return aspects
