from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, Query

from .config import ASTRO_CONFIG, config_hash
from .astro import compute_snapshot, compute_aspects

APP_NAME = os.getenv("APP_NAME", "astro-engine")

app = FastAPI(title=APP_NAME, version="0.1.0")

# CORS: allow your Vercel UI (and local dev). Set CORS_ORIGINS="https://your-ui.vercel.app,https://other" if you want to lock down.
_origins = os.getenv("CORS_ORIGINS", "*").split(",")


@app.get("/v1/config")
def get_config():
    """Return fixed engine configuration (for auditing/determinism)."""
    return {
        "config": ASTRO_CONFIG,
        "config_hash": config_hash(),
        "swisseph_version": getattr(__import__("swisseph"), "__version__", "unknown"),
    }


@app.get("/v1/snapshot")
def snapshot(
    ts: str = Query(..., description="ISO timestamp with offset, e.g. 2026-02-07T12:15:00+05:30"),
    include_aspects: bool = Query(False),
    orb: float = Query(3.0, ge=0.0, le=15.0),
):
    """Compute a snapshot (D1 + D9 + Panchang) for a timestamp."""
    data = compute_snapshot(ts)
    if include_aspects:
        data["aspects"] = compute_aspects(data["d1"]["planets"], orb_deg=orb)
    data["meta"]["config_hash"] = config_hash()
    return data


# Placeholder endpoints for next phase (event windows/daily batches)
@app.get("/v1/health")
def health():
    return {"ok": True}


@app.get("/v1/daily")
def daily():
    return {
        "error": "NotImplemented",
        "message": "Daily batch endpoint will be added in next iteration (requires caching + paging).",
    }


@app.get("/v1/events")
def events():
    return {
        "error": "NotImplemented",
        "message": "Event windows endpoint will be added in next iteration (sign/nakshatra/D9/aspect windows).",
    }
