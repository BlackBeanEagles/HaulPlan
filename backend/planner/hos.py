"""Deterministic HOS scheduling for the assumptions in the assessment brief."""
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

MAX_DRIVING = 11.0
BREAK_AFTER_DRIVING = 8.0
BREAK_HOURS = 0.5
DAILY_DUTY_WINDOW = 14.0
DAILY_REST = 10.0
CYCLE_LIMIT = 70.0
RESTART_HOURS = 34.0
FUEL_INTERVAL_MILES = 1000.0


@dataclass
class Event:
    start: datetime
    end: datetime
    status: str
    label: str
    location: str = ""
    miles: float = 0.0

    def serialize(self):
        value = asdict(self)
        value["start"] = self.start.isoformat()
        value["end"] = self.end.isoformat()
        return value


class HOSPlanner:
    def __init__(self, start: datetime, cycle_used: float, legs: list[dict], pickup: str, dropoff: str):
        # Preserve the driver's entered duty-start time.  Rounding to the hour
        # makes the printed log disagree with the trip the driver entered.
        self.now = start.replace(second=0, microsecond=0)
        self.cycle_used = max(0.0, min(float(cycle_used), CYCLE_LIMIT))
        self.legs = legs
        self.pickup, self.dropoff = pickup, dropoff
        self.daily_driving = 0.0
        self.driving_since_break = 0.0
        self.daily_duty = 0.0
        self.daily_window = 0.0
        self.events: list[Event] = []
        self.miles_since_fuel = 0.0

    def add(self, hours: float, status: str, label: str, location="", miles=0.0):
        if hours <= 0:
            return
        start = self.now
        self.now += timedelta(hours=hours)
        self.events.append(Event(start, self.now, status, label, location, round(miles, 1)))
        self.daily_window += hours
        if status in {"driving", "on_duty"}:
            self.daily_duty += hours
            self.cycle_used += hours
        if status == "driving":
            self.daily_driving += hours
            self.driving_since_break += hours
            self.miles_since_fuel += miles

    def reset_day(self, restart=False):
        self.add(RESTART_HOURS if restart else DAILY_REST, "off_duty", "34-hour restart" if restart else "Required 10-hour off-duty rest")
        if restart:
            self.cycle_used = 0.0
        self.daily_driving = self.daily_duty = self.driving_since_break = self.daily_window = 0.0

    def ensure_room(self, required_duty: float = 0.0):
        if self.cycle_used + required_duty > CYCLE_LIMIT:
            self.reset_day(restart=True)
        elif self.daily_window + required_duty > DAILY_DUTY_WINDOW:
            self.reset_day()

    def service(self, label: str, location: str, hours=1.0):
        self.ensure_room(hours)
        self.add(hours, "on_duty", label, location)

    def drive(self, miles: float, route_hours: float, label: str):
        self.miles_remaining = miles
        # Do not silently discard route miles when a routing provider reports
        # an implausibly fast duration.  The plan uses the longer of the route
        # duration and a conservative 65 mph minimum travel duration.
        self.hours_remaining = max(float(route_hours), miles / 65 if miles else 0)
        speed = self.miles_remaining / self.hours_remaining if self.hours_remaining else 0
        while self.hours_remaining > 0.001:
            self.ensure_room(0.01)
            if self.daily_driving >= MAX_DRIVING - 0.001:
                self.reset_day()
                continue
            if self.driving_since_break >= BREAK_AFTER_DRIVING - 0.001:
                self.ensure_room(BREAK_HOURS)
                self.add(BREAK_HOURS, "off_duty", "30-minute break from driving")
                self.driving_since_break = 0.0
                continue
            duty_room = DAILY_DUTY_WINDOW - self.daily_window
            drive_room = MAX_DRIVING - self.daily_driving
            break_room = BREAK_AFTER_DRIVING - self.driving_since_break
            cycle_room = CYCLE_LIMIT - self.cycle_used
            hours = min(self.hours_remaining, duty_room, drive_room, break_room, cycle_room)
            if hours <= 0.001:
                self.reset_day()
                continue
            miles = min(self.miles_remaining, hours * speed)
            if self.miles_since_fuel + miles > FUEL_INTERVAL_MILES:
                hours = (FUEL_INTERVAL_MILES - self.miles_since_fuel) / speed
                miles = hours * speed
            self.add(hours, "driving", label, miles=miles)
            self.hours_remaining -= hours
            self.miles_remaining -= miles
            if self.miles_since_fuel >= FUEL_INTERVAL_MILES - 0.01 and self.miles_remaining > 0.01:
                self.ensure_room(0.25)
                self.add(0.25, "on_duty", "Fuel stop (within 1,000 miles)")
                self.miles_since_fuel = 0.0

    def plan(self):
        if len(self.legs) != 2:
            raise ValueError("The route must include a current-to-pickup and pickup-to-drop-off leg.")
        self.drive(self.legs[0]["distance_miles"], self.legs[0]["duration_hours"], "Drive to pickup")
        self.service("Pickup, pre-trip inspection and loading", self.pickup)
        self.drive(self.legs[1]["distance_miles"], self.legs[1]["duration_hours"], "Drive to drop-off")
        self.service("Drop-off, post-trip inspection and unloading", self.dropoff)
        return {"events": [event.serialize() for event in self.events], "cycle_used_end": round(self.cycle_used, 2),
                "limits": {"daily_driving": MAX_DRIVING, "duty_window": DAILY_DUTY_WINDOW, "cycle": CYCLE_LIMIT}}
