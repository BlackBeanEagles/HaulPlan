import json
from datetime import datetime
from unittest.mock import patch
from django.test import SimpleTestCase
from .hos import HOSPlanner


class HOSPlannerTests(SimpleTestCase):
    def plan(self, cycle=0, legs=None):
        return HOSPlanner(datetime(2026, 9, 1, 6), cycle, legs or [
            {"distance_miles": 550, "duration_hours": 10}, {"distance_miles": 660, "duration_hours": 12},
        ], "Memphis, TN", "Nashville, TN").plan()["events"]

    def test_pickup_occurs_after_first_leg_and_before_dropoff_leg(self):
        labels = [event["label"] for event in self.plan()]
        self.assertLess(labels.index("Drive to pickup"), labels.index("Pickup, pre-trip inspection and loading"))
        self.assertLess(labels.index("Pickup, pre-trip inspection and loading"), labels.index("Drive to drop-off"))

    def test_no_duty_period_has_more_than_eleven_driving_hours(self):
        driving = 0.0
        for event in self.plan():
            duration = (datetime.fromisoformat(event["end"]) - datetime.fromisoformat(event["start"])).total_seconds() / 3600
            if event["status"] == "off_duty" and duration >= 10:
                driving = 0.0
            elif event["status"] == "driving":
                driving += duration
                self.assertLessEqual(driving, 11.001)

    def test_break_is_scheduled_before_more_than_eight_hours_of_driving(self):
        driving = 0.0
        for event in self.plan():
            duration = (datetime.fromisoformat(event["end"]) - datetime.fromisoformat(event["start"])).total_seconds() / 3600
            if event["status"] == "off_duty" and duration >= .5:
                driving = 0.0
            elif event["status"] == "driving":
                driving += duration
                self.assertLessEqual(driving, 8.001)

    def test_no_driving_window_exceeds_fourteen_consecutive_hours(self):
        window = 0.0
        for event in self.plan():
            duration = (datetime.fromisoformat(event["end"]) - datetime.fromisoformat(event["start"])).total_seconds() / 3600
            if event["status"] == "off_duty" and duration >= 10:
                window = 0.0
            else:
                window += duration
                self.assertLessEqual(window, 14.001)

    def test_cycle_at_limit_triggers_restart_before_work(self):
        events = self.plan(cycle=70)
        self.assertEqual(events[0]["label"], "34-hour restart")

    def test_preserves_the_entered_duty_start_minutes(self):
        planner = HOSPlanner(datetime(2026, 9, 1, 6, 45), 0, [
            {"distance_miles": 55, "duration_hours": 1}, {"distance_miles": 55, "duration_hours": 1},
        ], "Pickup", "Drop-off")
        self.assertEqual(planner.plan()["events"][0]["start"], "2026-09-01T06:45:00")

    def test_conservative_speed_keeps_all_route_miles(self):
        # A provider duration below 65 mph would otherwise complete the time
        # budget while leaving miles unscheduled.
        events = self.plan(legs=[
            {"distance_miles": 650, "duration_hours": 8}, {"distance_miles": 650, "duration_hours": 8},
        ])
        scheduled_miles = sum(event["miles"] for event in events)
        self.assertAlmostEqual(scheduled_miles, 1300, places=1)

    def test_plan_api_rejects_missing_required_locations(self):
        response = self.client.post("/api/plan/", data=json.dumps({"current_location": "Dallas"}), content_type="application/json", secure=True)
        self.assertEqual(response.status_code, 400)
        self.assertIn("required", response.json()["error"])

    @patch("planner.views.route")
    @patch("planner.views.geocode")
    def test_plan_api_returns_a_route_schedule_and_loggable_events(self, geocode_mock, route_mock):
        geocode_mock.side_effect = [
            {"label": "Dallas, Texas", "lat": 32.7767, "lon": -96.7970},
            {"label": "Memphis, Tennessee", "lat": 35.1495, "lon": -90.0490},
            {"label": "Nashville, Tennessee", "lat": 36.1627, "lon": -86.7816},
        ]
        route_mock.return_value = {
            "distance_miles": 1210,
            "duration_hours": 22,
            "legs": [{"distance_miles": 650, "duration_hours": 12}, {"distance_miles": 560, "duration_hours": 10}],
            "geometry": [[-96.7970, 32.7767], [-90.0490, 35.1495], [-86.7816, 36.1627]],
        }
        response = self.client.post("/api/plan/", data=json.dumps({
            "current_location": "Dallas", "pickup_location": "Memphis", "dropoff_location": "Nashville",
            "current_cycle_used": 12, "start_time": "2026-09-01T06:45",
        }), content_type="application/json", secure=True)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["points"]), 3)
        self.assertEqual(payload["route"]["distance_miles"], 1210)
        self.assertTrue(payload["schedule"]["events"])
        self.assertEqual(payload["schedule"]["events"][0]["start"], "2026-09-01T06:45:00")
