# RailPulse Germany - Train Delay Analytics Dashboard

Monorepo project with a Django backend and React frontend for German train delay analytics.

The app pulls live data from Deutsche Bahn APIs, normalizes it into a local database, and provides:
- station board data (departures/arrivals)
- delay KPIs
- hourly/daily/weekly delay trends
- line rankings and line risk analytics

## Screenshots

Desktop dashboard:

![Dashboard Overview](./docs/screenshots/dashboard-overview.svg)

Mobile layout:

![Dashboard Mobile](./docs/screenshots/dashboard-mobile.svg)

## Project Structure

- `backend/` - Django + DRF API and data ingestion logic
- `frontend/` - React + Vite dashboard UI
- `backend/sample_data/` - backend fallback sample payloads
- `frontend/public/fallback/` - frontend fallback sample payloads
- `docs/screenshots/` - README visuals

## Tech Stack

- Frontend: React, Vite, TypeScript, Tailwind CSS, Zustand, Axios, Recharts, React Leaflet
- Backend: Django, Django REST Framework, requests, PostgreSQL/SQLite (env-based)

## Data Flow

1. Frontend requests backend endpoints only.
2. Backend fetches from Deutsche Bahn Timetables and Station Data APIs.
3. Data is normalized and upserted into `TrainSnapshot`.
4. `delay_minutes` is computed in backend (negative delays are clamped to `0`).
5. Stats and charts are generated from normalized DB data.

## Backend Models

- `Station`
- `TrainSnapshot`
- `DailyStationStats`

Main `TrainSnapshot` fields:
- `station`
- `board_type`
- `train_name`
- `planned_time`
- `updated_time`
- `delay_minutes`
- `platform`
- `status`
- `raw_payload`
- `record_uid` (unique)

## Local Setup

### 1) Clone repository

```bash
git clone https://github.com/sertaclevent/railpulse-germany.git
cd railpulse-germany
```

### 2) Backend setup

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

Backend default URL: `http://127.0.0.1:8000`

### 3) Frontend setup

```bash
cd ../frontend
npm install
copy .env.example .env
npm run dev
```

Frontend default URL: `http://localhost:5174`

## Tests

Backend:

```bash
cd backend
.\.venv\Scripts\python manage.py test
```

Frontend:

```bash
cd frontend
npm run test
npm run build
```

## Background Snapshot Collection

For richer daily/weekly trends, run periodic snapshot ingestion:

```bash
cd backend
.\.venv\Scripts\python manage.py collect_delay_snapshots --station-id 1 --board-type both --window-hours 4
```

For wider country coverage:

```bash
cd backend
.\.venv\Scripts\python manage.py sync_stations_catalog --limit 10000
.\.venv\Scripts\python manage.py collect_delay_snapshots --all-stations --board-type both --window-hours 2 --station-limit 300 --skip-errors
```

## Environment Variables

Root template: `.env.example`  
Service templates:
- `backend/.env.example`
- `frontend/.env.example`

Important backend vars:
- `DB_CLIENT_ID`
- `DB_API_KEY` (backend only)
- `DATABASE_URL`
- `DJANGO_CORS_ALLOWED_ORIGINS`
- `DEMO_USE_SAMPLE_DATA`
- `REFRESH_TTL_SECONDS`

Important frontend vars:
- `VITE_API_BASE_URL`
- `VITE_USE_SAMPLE_DATA`

Recommended local frontend API config:
- `VITE_API_BASE_URL=/api` (via Vite proxy to backend)

## API Endpoints

- `GET /api/health`
- `GET /api/stations/search?q=`
- `GET /api/stations/:id/board?type=departure&window=2h&delay_threshold=all&category=&line=`
- `GET /api/stations/:id/stats?type=departure&window=2h&delay_threshold=all&category=&line=`
- `GET /api/stations/:id/hourly-delay?type=departure&line=`
- `GET /api/stations/:id/delay-trends?type=departure&days=14&line=`
- `GET /api/stations/:id/line-probabilities?type=departure&days=30&min_trains=6&top_n=8`
- `GET /api/lines/catalog?days=30&limit=200&q=`
- `GET /api/lines/rankings?days=14&min_trains=20&top_n=5`
- `GET /api/lines/:line_name/stats?days=30&top_stations=10`

All responses are JSON.

Time window values:
- `window=1h|2h|4h|6h`
- For `board` and `stats`: if selected window has no records, backend can auto-expand to `6h` and return both `requested_window_hours` and effective `window_hours`.

## License Notice

This dataset is provided under the Creative Commons Attribution 4.0 International license (CC BY 4.0).

If Deutsche Bahn (DB) data becomes part of the OpenStreetMap database, it is sufficient to credit Deutsche Bahn AG in the contributors list. For downstream uses by database licensees, explicit DB attribution for every individual use is not required; indirect attribution is sufficient.

## Deployment

- Render config: `render.yaml`
- Backend Procfile: `backend/Procfile`
- Frontend Vercel config: `frontend/vercel.json`

## Known Limitations

- Deutsche Bahn API payload formats can vary; parser is defensive but not exhaustive.
- Historical analytics quality depends on periodic snapshot ingestion coverage.

