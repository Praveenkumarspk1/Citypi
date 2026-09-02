"""
GTFS (General Transit Feed Specification) Client
"""
import csv
import io
import zipfile
from dataclasses import dataclass
from datetime import datetime, time
from typing import Any

import aiohttp

from ...application.ports.external_services import (
    RealtimeTransitServicePort,
    TransitDataServicePort,
)
from ...domain.entities.transit import TransitAgency, TransitRoute, TransitStop, TransitTrip
from ...domain.value_objects.coordinates import Coordinates


@dataclass
class GTFSConfig:
    """GTFS configuration"""
    static_feed_urls: list[str] = None
    realtime_feed_urls: list[str] = None
    api_key: str | None = None
    update_interval_hours: int = 24
    timeout: int = 30


class GTFSClient(TransitDataServicePort, RealtimeTransitServicePort):
    """GTFS static and real-time transit data client"""

    def __init__(self, config: GTFSConfig | None = None):
        self.config = config or GTFSConfig()
        self._session: aiohttp.ClientSession | None = None

        # In-memory storage for parsed GTFS data
        self._agencies: dict[str, TransitAgency] = {}
        self._routes: dict[str, TransitRoute] = {}
        self._stops: dict[str, TransitStop] = {}
        self._trips: dict[str, TransitTrip] = {}
        self._stop_times: dict[str, list[dict[str, Any]]] = {}  # trip_id -> list of stop times
        self._calendar: dict[str, dict[str, Any]] = {}  # service_id -> calendar info
        self._calendar_dates: dict[str, list[dict[str, Any]]] = {}  # service_id -> exceptions

        # Real-time data
        self._vehicle_positions: list[dict[str, Any]] = []
        self._trip_updates: list[dict[str, Any]] = []
        self._alerts: list[dict[str, Any]] = []

        self._last_update: datetime | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close the session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def load_feeds(self) -> None:
        """Load all configured GTFS feeds"""
        if self.config.static_feed_urls:
            for url in self.config.static_feed_urls:
                await self._load_static_feed(url)

        if self.config.realtime_feed_urls:
            for url in self.config.realtime_feed_urls:
                await self._load_realtime_feed(url)

        self._last_update = datetime.utcnow()

    async def _load_static_feed(self, url: str) -> None:
        """Load and parse static GTFS feed from URL"""
        session = await self._get_session()

        headers = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        async with session.get(url, headers=headers or None) as response:
            response.raise_for_status()
            content = await response.read()

        # Parse ZIP file
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            # Parse agency.txt
            if "agency.txt" in zf.namelist():
                with zf.open("agency.txt") as f:
                    self._parse_agency(f)

            # Parse routes.txt
            if "routes.txt" in zf.namelist():
                with zf.open("routes.txt") as f:
                    self._parse_routes(f)

            # Parse stops.txt
            if "stops.txt" in zf.namelist():
                with zf.open("stops.txt") as f:
                    self._parse_stops(f)

            # Parse trips.txt
            if "trips.txt" in zf.namelist():
                with zf.open("trips.txt") as f:
                    self._parse_trips(f)

            # Parse stop_times.txt
            if "stop_times.txt" in zf.namelist():
                with zf.open("stop_times.txt") as f:
                    self._parse_stop_times(f)

            # Parse calendar.txt
            if "calendar.txt" in zf.namelist():
                with zf.open("calendar.txt") as f:
                    self._parse_calendar(f)

            # Parse calendar_dates.txt
            if "calendar_dates.txt" in zf.namelist():
                with zf.open("calendar_dates.txt") as f:
                    self._parse_calendar_dates(f)

    def _parse_agency(self, file) -> None:
        """Parse agency.txt"""
        reader = csv.DictReader(io.TextIOWrapper(file, encoding='utf-8'))
        for row in reader:
            agency = TransitAgency(
                id=row.get("agency_id", ""),
                name=row.get("agency_name", ""),
                url=row.get("agency_url", ""),
                timezone=row.get("agency_timezone", "UTC"),
                lang=row.get("agency_lang"),
                phone=row.get("agency_phone"),
                fare_url=row.get("agency_fare_url"),
            )
            self._agencies[agency.id] = agency

    def _parse_routes(self, file) -> None:
        """Parse routes.txt"""
        reader = csv.DictReader(io.TextIOWrapper(file, encoding='utf-8'))
        for row in reader:
            route = TransitRoute(
                id=row.get("route_id", ""),
                agency_id=row.get("agency_id", ""),
                short_name=row.get("route_short_name", ""),
                long_name=row.get("route_long_name", ""),
                desc=row.get("route_desc", ""),
                route_type=int(row.get("route_type", 3)),
                url=row.get("route_url", ""),
                color=row.get("route_color", ""),
                text_color=row.get("route_text_color", ""),
            )
            self._routes[route.id] = route

    def _parse_stops(self, file) -> None:
        """Parse stops.txt"""
        reader = csv.DictReader(io.TextIOWrapper(file, encoding='utf-8'))
        for row in reader:
            stop = TransitStop(
                id=row.get("stop_id", ""),
                code=row.get("stop_code", ""),
                name=row.get("stop_name", ""),
                desc=row.get("stop_desc", ""),
                latitude=float(row.get("stop_lat", 0)),
                longitude=float(row.get("stop_lon", 0)),
                zone_id=row.get("zone_id", ""),
                url=row.get("stop_url", ""),
                location_type=int(row.get("location_type", 0)),
                parent_station=row.get("parent_station", ""),
                wheelchair_boarding=row.get("wheelchair_boarding", ""),
            )
            self._stops[stop.id] = stop

    def _parse_trips(self, file) -> None:
        """Parse trips.txt"""
        reader = csv.DictReader(io.TextIOWrapper(file, encoding='utf-8'))
        for row in reader:
            trip = TransitTrip(
                id=row.get("trip_id", ""),
                route_id=row.get("route_id", ""),
                service_id=row.get("service_id", ""),
                trip_headsign=row.get("trip_headsign", ""),
                trip_short_name=row.get("trip_short_name", ""),
                direction_id=int(row.get("direction_id", 0)) if row.get("direction_id") else 0,
                block_id=row.get("block_id", ""),
                shape_id=row.get("shape_id", ""),
                wheelchair_accessible=row.get("wheelchair_accessible", ""),
                bikes_allowed=row.get("bikes_allowed", ""),
            )
            self._trips[trip.id] = trip

    def _parse_stop_times(self, file) -> None:
        """Parse stop_times.txt"""
        reader = csv.DictReader(io.TextIOWrapper(file, encoding='utf-8'))
        for row in reader:
            trip_id = row.get("trip_id", "")
            if trip_id not in self._stop_times:
                self._stop_times[trip_id] = []

            self._stop_times[trip_id].append({
                "stop_id": row.get("stop_id", ""),
                "stop_sequence": int(row.get("stop_sequence", 0)),
                "arrival_time": row.get("arrival_time", ""),
                "departure_time": row.get("departure_time", ""),
                "pickup_type": int(row.get("pickup_type", 0)),
                "drop_off_type": int(row.get("drop_off_type", 0)),
                "shape_dist_traveled": float(row.get("shape_dist_traveled", 0)) if row.get("shape_dist_traveled") else 0,
            })

        # Sort by stop_sequence
        for trip_id in self._stop_times:
            self._stop_times[trip_id].sort(key=lambda x: x["stop_sequence"])

    def _parse_calendar(self, file) -> None:
        """Parse calendar.txt"""
        reader = csv.DictReader(io.TextIOWrapper(file, encoding='utf-8'))
        for row in reader:
            service_id = row.get("service_id", "")
            self._calendar[service_id] = {
                "monday": row.get("monday") == "1",
                "tuesday": row.get("tuesday") == "1",
                "wednesday": row.get("wednesday") == "1",
                "thursday": row.get("thursday") == "1",
                "friday": row.get("friday") == "1",
                "saturday": row.get("saturday") == "1",
                "sunday": row.get("sunday") == "1",
                "start_date": row.get("start_date", ""),
                "end_date": row.get("end_date", ""),
            }

    def _parse_calendar_dates(self, file) -> None:
        """Parse calendar_dates.txt"""
        reader = csv.DictReader(io.TextIOWrapper(file, encoding='utf-8'))
        for row in reader:
            service_id = row.get("service_id", "")
            if service_id not in self._calendar_dates:
                self._calendar_dates[service_id] = []

            self._calendar_dates[service_id].append({
                "date": row.get("date", ""),
                "exception_type": int(row.get("exception_type", 1)),  # 1=added, 2=removed
            })

    async def _load_realtime_feed(self, url: str) -> None:
        """Load real-time GTFS-RT feed"""
        # This would parse protobuf GTFS-RT data
        # For now, placeholder for future implementation
        pass

    # TransitDataServicePort implementation

    async def get_agencies(self, coordinates: Coordinates | None = None) -> list[dict[str, Any]]:
        """Get transit agencies"""
        agencies = list(self._agencies.values())

        if coordinates:
            # Filter agencies by proximity (simplified)
            pass

        return [{"id": a.id, "name": a.name, "url": a.url, "timezone": a.timezone} for a in agencies]

    async def get_routes(
        self,
        agency_id: str | None = None,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
    ) -> list[TransitRoute]:
        """Get transit routes"""
        routes = list(self._routes.values())

        if agency_id:
            routes = [r for r in routes if r.agency_id == agency_id]

        if coordinates and radius_meters:
            # Filter by proximity to coordinates
            filtered = []
            for route in routes:
                # Check if any stop on this route is within radius
                for trip in self._trips.values():
                    if trip.route_id == route.id:
                        stop_times = self._stop_times.get(trip.id, [])
                        for st in stop_times:
                            stop = self._stops.get(st["stop_id"])
                            if stop:
                                stop_coords = Coordinates(stop.latitude, stop.longitude)
                                if stop_coords.distance_to(coordinates) <= radius_meters:
                                    filtered.append(route)
                                    break
                        if route in filtered:
                            break
            routes = filtered

        return routes

    async def get_stops(
        self,
        route_id: str | None = None,
        coordinates: Coordinates | None = None,
        radius_meters: float | None = None,
    ) -> list[TransitStop]:
        """Get transit stops"""
        stops = list(self._stops.values())

        if route_id:
            # Get stops for this route
            route_stop_ids = set()
            for trip in self._trips.values():
                if trip.route_id == route_id:
                    stop_times = self._stop_times.get(trip.id, [])
                    for st in stop_times:
                        route_stop_ids.add(st["stop_id"])
            stops = [s for s in stops if s.id in route_stop_ids]

        if coordinates and radius_meters:
            stops = [
                s for s in stops
                if Coordinates(s.latitude, s.longitude).distance_to(coordinates) <= radius_meters
            ]

        return stops

    async def get_trips(
        self,
        route_id: str,
        date: datetime,
    ) -> list[TransitTrip]:
        """Get trips for a route on a date"""
        trips = [t for t in self._trips.values() if t.route_id == route_id]

        # Filter by service calendar
        weekday = date.weekday()  # 0=Monday
        day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        day_name = day_names[weekday]

        date_str = date.strftime("%Y%m%d")
        filtered_trips = []

        for trip in trips:
            service = self._calendar.get(trip.service_id, {})
            if service.get(day_name, False):
                # Check exceptions
                exceptions = self._calendar_dates.get(trip.service_id, [])
                is_exception = False
                for exc in exceptions:
                    if exc["date"] == date_str:
                        if exc["exception_type"] == 1:  # Added
                            is_exception = True
                        elif exc["exception_type"] == 2:  # Removed
                            is_exception = False

                if service.get("start_date", "") <= date_str <= service.get("end_date", "") or is_exception:
                    filtered_trips.append(trip)

        return filtered_trips

    async def get_schedule(
        self,
        stop_id: str,
        date: datetime,
        route_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get schedule for a stop"""
        schedule = []

        # Find all trips that stop here
        for trip_id, stop_times in self._stop_times.items():
            trip = self._trips.get(trip_id)
            if not trip:
                continue

            if route_ids and trip.route_id not in route_ids:
                continue

            # Check if trip runs on this date
            service = self._calendar.get(trip.service_id, {})
            weekday = date.weekday()
            day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            day_name = day_names[weekday]

            if not service.get(day_name, False):
                continue

            date_str = date.strftime("%Y%m%d")
            if not (service.get("start_date", "") <= date_str <= service.get("end_date", "")):
                continue

            # Check exceptions
            exceptions = self._calendar_dates.get(trip.service_id, [])
            is_cancelled = False
            for exc in exceptions:
                if exc["date"] == date_str and exc["exception_type"] == 2:
                    is_cancelled = True
                    break

            if is_cancelled:
                continue

            # Find stop time for this stop
            for st in stop_times:
                if st["stop_id"] == stop_id:
                    schedule.append({
                        "trip_id": trip_id,
                        "route_id": trip.route_id,
                        "arrival_time": st["arrival_time"],
                        "departure_time": st["departure_time"],
                        "stop_sequence": st["stop_sequence"],
                        "trip_headsign": trip.trip_headsign,
                    })
                    break

        # Sort by departure time
        schedule.sort(key=lambda x: x["departure_time"])
        return schedule

    # RealtimeTransitServicePort implementation

    async def get_arrivals(
        self,
        stop_id: str,
        route_ids: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get real-time arrivals"""
        # This would use GTFS-RT trip updates
        # For now, return static schedule as fallback
        now = datetime.now()
        today = now.date()

        schedule = await self.get_schedule(stop_id, datetime.combine(today, time.min), route_ids)

        # Filter future arrivals
        current_time = now.strftime("%H:%M:%S")
        future = [s for s in schedule if s["departure_time"] >= current_time]

        return future[:limit]

    async def get_vehicle_positions(
        self,
        route_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get real-time vehicle positions"""
        # This would parse GTFS-RT vehicle positions
        return self._vehicle_positions

    async def get_alerts(
        self,
        route_ids: list[str] | None = None,
        stop_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Get service alerts"""
        return self._alerts

    def get_stop_times(self, trip_id: str) -> list[dict[str, Any]]:
        """Get stop times for a trip"""
        return self._stop_times.get(trip_id, [])

    def get_route(self, route_id: str) -> TransitRoute | None:
        """Get route by ID"""
        return self._routes.get(route_id)

    def get_stop(self, stop_id: str) -> TransitStop | None:
        """Get stop by ID"""
        return self._stops.get(stop_id)

    def get_trip(self, trip_id: str) -> TransitTrip | None:
        """Get trip by ID"""
        return self._trips.get(trip_id)

    def get_agency(self, agency_id: str) -> TransitAgency | None:
        """Get agency by ID"""
        return self._agencies.get(agency_id)
