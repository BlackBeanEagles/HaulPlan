# Deploying HaulPlan on Render

This repository includes `render.yaml` for a Django API and a Vite static frontend.

1. Push the repository to GitHub.
2. In Render, create a **Blueprint** from that repository.
3. Let Render create both services. It generates the Django secret automatically.
4. After the API service receives its public URL, set these API service variables:
   - `DJANGO_ALLOWED_HOSTS`: the API hostname only, for example `haulplan-api.onrender.com`.
   - `CORS_ALLOWED_ORIGINS`: the full frontend origin, for example `https://haulplan-frontend.onrender.com`.
   - `CSRF_TRUSTED_ORIGINS`: the same full frontend origin.
   - `ROUTING_USER_AGENT`: a truthful app name and contact email, as required by the public geocoding provider's usage policy.
5. Set the frontend's `VITE_API_URL` to the full public API origin, for example `https://haulplan-api.onrender.com`, then redeploy the frontend.
6. Open the frontend URL and plan a real trip to confirm route lookup, map tiles, break/rest markers, and printable logs.

The production API uses `DJANGO_DEBUG=false`, a generated secret, allowed-host validation, explicit CORS/CSRF origins, Gunicorn, and WhiteNoise static handling. This deployment template keeps SQLite because the assessment app has no app-owned persistent records. Add Render PostgreSQL before introducing user accounts, saved trips, or shared dispatch data.
