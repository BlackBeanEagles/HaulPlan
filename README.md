# HaulPlan

A Django + React assessment project that turns a truck trip into a route plan and compliant-looking Hours of Service (HOS) daily logs for a property-carrying driver on the 70-hour / 8-day cycle.

## What is implemented

- Address geocoding and route geometry through configurable OpenStreetMap/Nominatim and OSRM endpoints.
- 11-hour driving, 14-hour duty-window, 30-minute break after 8 cumulative driving hours, 10-hour rest, 70-hour / 8-day budget, 34-hour restart, 1-hour pickup/drop-off, and fuel stops no more than 1,000 miles apart.
- A responsive route map, HOS dashboard, stop timeline, and printable per-day ELD-style graph logs.

## Run locally

Use Python 3.11+ and Node 20+.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Optional environment variables are `NOMINATIM_URL`, `OSRM_URL`, and `ROUTING_USER_AGENT`.
