HaulPlan

HaulPlan is a full-stack route and Hours-of-Service (HOS) planning application for a property-carrying driver. It converts a three-point trip into a routed itinerary, schedules HOS-related events, displays the route on a map, and generates printable daily duty records.

Live Demo

Frontend: https://haulplan-frontend.onrender.com/

Backend API: https://haulplan-api.onrender.com/

Main planning endpoint: https://haulplan-api.onrender.com/api/plan/

The Free Render web service may sleep after inactivity. The first request after a period of inactivity can therefore take longer than subsequent requests.

What the application does

HaulPlan accepts:

Current driver location

Pickup location

Drop-off location

Current 70-hour/8-day cycle usage

Driver duty start time

It then:

Geocodes all three locations using OpenStreetMap Nominatim.

Requests a driving route and route geometry from OSRM.

Calculates a deterministic HOS schedule.

Adds pickup and drop-off service time.

Inserts qualifying 30-minute driving breaks.

Inserts 10-hour off-duty rest periods when a duty period must reset.

Inserts a 34-hour restart when the 70-hour cycle is exhausted.

Adds fuel stops so planned driving does not exceed 1,000 miles between fuel events.

Displays the route and planned stops on a Leaflet map.

Shows a timeline and HOS guardrails.

Generates midnight-to-midnight printable daily duty logs with duty-status graphs and daily totals.

Technology stack

Frontend

React

Vite

React Leaflet

Leaflet

JavaScript/CSS

Backend

Python 3.11+

Django

Django CORS Headers

Requests

Gunicorn

WhiteNoise

External routing services

OpenStreetMap Nominatim for geocoding

OSRM for driving route geometry, distance, duration, and legs

OpenStreetMap tiles through Leaflet

Repository structure

HaulPlan/
├── backend/
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── planner/
│   │   ├── hos.py
│   │   ├── routing.py
│   │   ├── views.py
│   │   └── tests.py
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   └── .env.production.example
├── render.yaml
├── DEPLOYMENT.md
└── README.md

HOS planning assumptions

The implementation is intentionally based on the assumptions in the assessment brief:

Property-carrying driver

11 hours maximum driving per duty period

14-hour duty window

30-minute off-duty interruption after 8 cumulative driving hours

10-hour off-duty rest to reset the daily driving/duty window

70-hour / 8-day cycle

34-hour restart when the cycle is exhausted

1 hour for pickup/loading

1 hour for drop-off/unloading

Fuel planning before another 1,000 miles of driving

A conservative minimum travel speed of 65 mph is used when a routing provider reports an implausibly fast duration

The planner is a deterministic scheduling aid. It is not a replacement for the driver's final record-of-duty-status review or current FMCSA requirements.

Run locally

Prerequisites

Python 3.11+

Node.js 20+

npm

Start the Django backend

From the repository root:

cd backend

python -m venv .venv

Windows PowerShell:

.\.venv\Scripts\Activate.ps1

Git Bash:

source .venv/Scripts/activate

Install dependencies:

pip install -r requirements.txt

Run migrations:

python manage.py migrate

Start Django:

python manage.py runserver

The API will be available at:

http://127.0.0.1:8000

Start the Vite frontend

In a second terminal:

cd frontend
npm install
npm run dev

Open:

http://localhost:5173

The Vite development server proxies /api requests to:

http://127.0.0.1:8000

Environment variables

Backend

For local development, copy .env.example to .env or export the variables in your shell.

Important variables:

DJANGO_DEBUG=true
DJANGO_SECRET_KEY=development-only-change-me
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ROUTING_USER_AGENT=HaulPlan-assessment/1.0 (contact: your-email@example.com)

Optional routing-provider overrides:

NOMINATIM_URL=https://nominatim.openstreetmap.org/search
OSRM_URL=https://router.project-osrm.org/route/v1/driving

Use a truthful application name and contact email in ROUTING_USER_AGENT.

Frontend

For a production build:

VITE_API_URL=https://haulplan-api.onrender.com

Vite reads this variable at build time, so the frontend must be rebuilt/redeployed after changing it.

API

POST /api/plan/

Creates a route and HOS plan.

Example request:

{
  "current_location": "Dallas, TX",
  "pickup_location": "Memphis, TN",
  "dropoff_location": "Nashville, TN",
  "current_cycle_used": 12,
  "start_time": "2026-09-01T06:45"
}

Example response shape:

{
  "points": [],
  "route": {
    "distance_miles": 0,
    "duration_hours": 0,
    "legs": [],
    "geometry": []
  },
  "schedule": {
    "events": [],
    "cycle_used_end": 0,
    "limits": {
      "daily_driving": 11,
      "duty_window": 14,
      "cycle": 70
    }
  }
}

Each schedule event contains a start time, end time, duty status, label, location when applicable, and planned miles.

How to test the hosted application

Open:

https://haulplan-frontend.onrender.com/

Test 1 — Basic geocoding and route map

Use:

Current location: Dallas, TX
Pickup location: Memphis, TN
Drop-off location: Nashville, TN
Current cycle used: 12
Duty start: choose a reasonable start time

Click:

Generate route & logs

Expected result:

All three locations are accepted.

A route is drawn on the Leaflet map.

Three numbered location markers appear.

Route distance and duration are displayed.

Pickup and drop-off appear in the event timeline.

Daily logs are generated.

This verifies the complete chain:

React form
   ↓
POST /api/plan/
   ↓
Django
   ↓
Nominatim geocoding
   ↓
OSRM routing
   ↓
HOSPlanner
   ↓
JSON response
   ↓
React map + timeline + logs

Test 2 — Force a 30-minute driving break

Use a trip long enough that the driver must drive for more than 8 hours.

Example:

Current location: Dallas, TX
Pickup location: Little Rock, AR
Drop-off location: Nashville, TN

Click Generate route & logs.

Look in the timeline for:

30-minute break from driving

Expected result:

The break appears before the driver exceeds 8 cumulative driving hours.

The map may show a break marker.

The printed daily log includes the break as an off-duty event.

Test 3 — Force daily rest / multi-day scheduling

Use a substantially longer route so the 14-hour duty window and/or 11-hour driving limit require a new duty period.

Example:

Current location: Dallas, TX
Pickup location: Oklahoma City, OK
Drop-off location: New York, NY

Expected result:

The plan spans multiple calendar days.

A Required 10-hour off-duty rest event appears.

The daily records section contains more than one day.

The HOS graph is split into midnight-to-midnight records.

Test 4 — Force a fuel stop

The fuel rule is based on planned driving miles, so use a route comfortably above 1,000 miles.

Example:

Current location: Los Angeles, CA
Pickup location: Phoenix, AZ
Drop-off location: Dallas, TX

If the calculated route is above 1,000 miles, look for:

Fuel stop (within 1,000 miles)

Expected result:

A fuel event appears before another 1,000 miles of driving is scheduled.

The fuel event appears in the timeline.

The map displays a fuel marker.

If the chosen route is under 1,000 miles, no fuel stop is expected. Choose a longer route.

Test 5 — Test the 70-hour cycle restart

Enter a high current cycle usage:

Current cycle used: 70

Then generate a normal trip.

Expected result:

The first event is:
34-hour restart

Cycle usage resets before additional work is scheduled.

Test 6 — Test printable daily logs

After generating a plan, scroll to:

Daily duty records

Click:

Print all logs

Expected result:

The browser print dialog opens.

Each calendar day has its own record.

The record includes the duty-status graph.

Daily totals are displayed.

Planned remarks and locations are shown.

For a clean PDF test, choose Save to PDF in the browser print dialog.

Direct API testing

The hosted API endpoint is:

https://haulplan-api.onrender.com/api/plan/

The endpoint expects POST, not GET.

Using PowerShell:

$body = @{
  current_location = "Dallas, TX"
  pickup_location = "Memphis, TN"
  dropoff_location = "Nashville, TN"
  current_cycle_used = 12
  start_time = "2026-09-01T06:45"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "https://haulplan-api.onrender.com/api/plan/" `
  -Method Post `
  -ContentType "application/json" `
  -Body $body

A successful response should contain:

points
route
schedule

If you receive a routing-provider error, check the Django service logs in Render.

Automated backend tests

Run:

cd backend
python manage.py test

The test suite covers:

Pickup before drop-off

11-hour driving limit

8-hour break threshold

14-hour duty window

70-hour cycle restart

Preservation of entered duty-start minutes

Preservation of all route miles

API validation for missing locations

API response structure

Render deployment

The project uses a Render Blueprint:

render.yaml

It creates:

haulplan-api
haulplan-frontend

The Django service uses:

pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT

The frontend uses:

npm ci
npm run build

and publishes:

dist

Production environment values

Backend:

DJANGO_ALLOWED_HOSTS=haulplan-api.onrender.com
CORS_ALLOWED_ORIGINS=https://haulplan-frontend.onrender.com
CSRF_TRUSTED_ORIGINS=https://haulplan-frontend.onrender.com
ROUTING_USER_AGENT=HaulPlan-assessment/1.0 (contact: your-email@example.com)

Frontend:

VITE_API_URL=https://haulplan-api.onrender.com

After changing VITE_API_URL, rebuild/redeploy the frontend because Vite embeds the value into the production bundle.

Render/production notes

The assessment deployment intentionally uses Render's Free web service for the Django API and a free static site for the frontend.

Free Render web services can spin down after 15 minutes without inbound traffic, so the first request after inactivity can take longer.

The Django project currently uses SQLite. Render's Free web service filesystem is ephemeral, so SQLite data should not be treated as durable production storage. The current assessment application does not use application-owned persistent records. If user accounts, saved trips, dispatch records, or other persistent application data are added later, move the database to PostgreSQL.

Security and operational notes

Do not commit .env files or production secrets.

Keep DJANGO_SECRET_KEY in Render's environment configuration.

Keep production CORS and CSRF origins restricted to the actual frontend origin.

Use a truthful ROUTING_USER_AGENT with a contact email.

Do not expose secret credentials in render.yaml.

Verify generated plans against current FMCSA requirements before operational use.

Troubleshooting

Frontend loads but "Failed to fetch" appears

Check:

VITE_API_URL is exactly:
https://haulplan-api.onrender.com

The frontend was rebuilt after changing VITE_API_URL.

haulplan-api is Live in Render.

Backend CORS allows:
https://haulplan-frontend.onrender.com

CORS error in the browser

Backend must contain:

CORS_ALLOWED_ORIGINS=https://haulplan-frontend.onrender.com

Do not add a trailing slash.

Django says DisallowedHost

Backend must contain:

DJANGO_ALLOWED_HOSTS=haulplan-api.onrender.com

The hostname is used without https://.

Routing provider unavailable

Check the Render backend logs. The application depends on external Nominatim and OSRM services. Retry after a short wait if the provider is temporarily unavailable.

Map is blank

Check the browser console and network tab. Confirm the route response contains geometry and that OpenStreetMap tile requests are loading.

First request is slow

The Render Free backend may have spun down after inactivity. Wait for it to wake and retry.