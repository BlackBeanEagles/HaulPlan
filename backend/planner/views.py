import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .hos import HOSPlanner
from .routing import geocode, route, RoutingError


@csrf_exempt
@require_POST
def plan_trip(request):
    try:
        payload = json.loads(request.body)
        required = ("current_location", "pickup_location", "dropoff_location")
        if any(not str(payload.get(field, "")).strip() for field in required):
            return JsonResponse({"error": "Current, pickup, and drop-off locations are required."}, status=400)
        points = [geocode(payload[field].strip()) for field in required]
        route_data = route(points)
        start = datetime.fromisoformat(payload.get("start_time") or datetime.now().replace(hour=6, minute=0).isoformat())
        schedule = HOSPlanner(start, payload.get("current_cycle_used", 0), route_data["legs"], points[1]["label"], points[2]["label"]).plan()
        return JsonResponse({"points": points, "route": route_data, "schedule": schedule})
    except RoutingError as error:
        return JsonResponse({"error": str(error)}, status=422)
    except (ValueError, TypeError, KeyError) as error:
        return JsonResponse({"error": f"Invalid trip details: {error}"}, status=400)
    except Exception:
        return JsonResponse({"error": "The routing provider is unavailable. Please try again shortly."}, status=502)
