# Astro Engine Backend (Sidereal Lahiri, Mumbai, Mean Node)

A FastAPI backend that powers your Vercel UI and provides deterministic astro features for backtesting & forecasting.

## Fixed configuration
- Zodiac: **Sidereal**
- Ayanamsa: **Lahiri**
- Location: **Mumbai, India** (19.0760, 72.8777)
- Timezone: **Asia/Kolkata**
- Nodes: **Mean node** (Rahu); Ketu = Rahu + 180°

## Endpoints
- `GET /v1/config` – configuration + config hash
- `GET /v1/snapshot?ts=ISO` – D1 + D9 + Panchang
  - optional: `include_aspects=true&orb=3`
- `GET /v1/health`

(Coming next iteration)
- `GET /v1/daily` – daily batch snapshots for backtesting
- `GET /v1/events` – event windows (nakshatra/sign/D9/aspect/retro windows)

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Test:
```bash
curl "http://localhost:8000/v1/config"
curl "http://localhost:8000/v1/snapshot?ts=2026-02-07T12:15:00+05:30"
```

## CORS
By default it allows all origins.
To restrict:

```bash
export CORS_ORIGINS="https://YOUR_UI.vercel.app,http://localhost:5173"
```

## Connect to your Vercel UI
Set in your UI project (Vercel → Environment Variables):
- `VITE_ASTRO_API_BASE` = `https://<your-backend-domain>`

