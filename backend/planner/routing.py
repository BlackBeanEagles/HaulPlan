"""Small, replaceable adapters for public geocoding and routing providers."""

import os
import requests


NOMINATIM_URL = os.getenv(
    "NOMINATIM_URL",
    "https://nominatim.openstreetmap.org/search",
)

OSRM_URL = os.getenv(
    "OSRM_URL",
    "https://router.project-osrm.org/route/v1/driving",
)

USER_AGENT = os.getenv(
    "ROUTING_USER_AGENT",
    "HaulPlan/1.0 (contact: hridyajain2004@example.com)",
)


class RoutingError(Exception):
    pass


def geocode(address: str) -> dict:
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={
                "q": address,
                "format": "jsonv2",
                "limit": 1,
            },
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Language": "en",
            },
            timeout=20,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise RoutingError(
            f"Geocoding provider is unavailable for '{address}': {exc}"
        ) from exc

    try:
        matches = response.json()
    except ValueError as exc:
        raise RoutingError(
            f"Geocoding provider returned an invalid response for '{address}'."
        ) from exc

    if not matches:
        raise RoutingError(
            f"We could not locate '{address}'. Try adding city and state."
        )

    match = matches[0]

    return {
        "label": match["display_name"],
        "lat": float(match["lat"]),
        "lon": float(match["lon"]),
    }


def route(points: list[dict]) -> dict:
    coordinates = ";".join(
        f"{point['lon']},{point['lat']}"
        for point in points
    )

    try:
        response = requests.get(
            f"{OSRM_URL}/{coordinates}",
            params={
                "overview": "full",
                "geometries": "geojson",
                "steps": "true",
            },
            headers={
                "User-Agent": USER_AGENT,
            },
            timeout=30,
        )

        response.raise_for_status()

    except requests.RequestException as exc:
        raise RoutingError(
            f"Routing provider is unavailable: {exc}"
        ) from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise RoutingError(
            "Routing provider returned an invalid response."
        ) from exc

    if payload.get("code") != "Ok" or not payload.get("routes"):
        raise RoutingError(
            "A driveable route could not be found for those locations."
        )

    result = payload["routes"][0]

    legs = [
        {
            "distance_miles": leg["distance"] / 1609.344,
            "duration_hours": leg["duration"] / 3600,
        }
        for leg in result["legs"]
    ]

    return {
        "distance_miles": round(
            result["distance"] / 1609.344,
            1,
        ),
        "duration_hours": round(
            result["duration"] / 3600,
            2,
        ),
        "legs": legs,
        "geometry": result["geometry"]["coordinates"],
    }