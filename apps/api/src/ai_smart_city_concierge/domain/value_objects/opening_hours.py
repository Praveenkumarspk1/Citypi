"""
OpeningHours Value Object
"""
import json
from dataclasses import dataclass, field
from datetime import time
from enum import IntEnum


class DayOfWeek(IntEnum):
    """Days of the week (Monday=0, Sunday=6)"""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    @classmethod
    def from_string(cls, day: str) -> "DayOfWeek":
        """Create from string (case-insensitive)"""
        day_map = {
            "monday": cls.MONDAY, "mon": cls.MONDAY,
            "tuesday": cls.TUESDAY, "tue": cls.TUESDAY,
            "wednesday": cls.WEDNESDAY, "wed": cls.WEDNESDAY,
            "thursday": cls.THURSDAY, "thu": cls.THURSDAY,
            "friday": cls.FRIDAY, "fri": cls.FRIDAY,
            "saturday": cls.SATURDAY, "sat": cls.SATURDAY,
            "sunday": cls.SUNDAY, "sun": cls.SUNDAY,
        }
        normalized = day.lower().strip()
        if normalized not in day_map:
            raise ValueError(f"Invalid day: {day}")
        return day_map[normalized]

    def to_string(self, short: bool = False) -> str:
        """Convert to string"""
        names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        short_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return (short_names if short_names else names)[self.value]


@dataclass(frozen=True, slots=True)
class DaySchedule:
    """
    Schedule for a single day.
    """
    day: DayOfWeek
    open_time: time | None = None
    close_time: time | None = None
    is_closed: bool = False
    breaks: tuple[tuple[time, time], ...] = ()  # (break_start, break_end)

    def __post_init__(self) -> None:
        """Validate after initialization"""
        if self.is_closed:
            object.__setattr__(self, 'open_time', None)
            object.__setattr__(self, 'close_time', None)
            object.__setattr__(self, 'breaks', ())
        else:
            if self.open_time is None or self.close_time is None:
                raise ValueError("Open and close times required when not closed")
            if self.open_time >= self.close_time:
                raise ValueError("Open time must be before close time")

            # Validate breaks
            for break_start, break_end in self.breaks:
                if break_start >= break_end:
                    raise ValueError("Break start must be before break end")
                if break_start < self.open_time or break_end > self.close_time:
                    raise ValueError("Breaks must be within open hours")

    @property
    def is_open(self) -> bool:
        """Check if open on this day"""
        return not self.is_closed and self.open_time is not None

    @property
    def duration_minutes(self) -> int:
        """Total open minutes (excluding breaks)"""
        if not self.is_open:
            return 0

        total = (self.close_time.hour * 60 + self.close_time.minute) - \
                (self.open_time.hour * 60 + self.open_time.minute)

        for break_start, break_end in self.breaks:
            total -= (break_end.hour * 60 + break_end.minute) - \
                     (break_start.hour * 60 + break_start.minute)

        return total

    @property
    def duration_hours(self) -> float:
        """Total open hours (excluding breaks)"""
        return self.duration_minutes / 60

    def is_open_at(self, check_time: time) -> bool:
        """Check if open at a specific time"""
        if not self.is_open:
            return False
        if check_time < self.open_time or check_time >= self.close_time:
            return False
        for break_start, break_end in self.breaks:
            if break_start <= check_time < break_end:
                return False
        return True

    def to_dict(self) -> dict:
        return {
            "day": self.day.name,
            "open_time": self.open_time.isoformat() if self.open_time else None,
            "close_time": self.close_time.isoformat() if self.close_time else None,
            "is_closed": self.is_closed,
            "breaks": [[b[0].isoformat(), b[1].isoformat()] for b in self.breaks],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DaySchedule":
        return cls(
            day=DayOfWeek[data["day"]],
            open_time=time.fromisoformat(data["open_time"]) if data.get("open_time") else None,
            close_time=time.fromisoformat(data["close_time"]) if data.get("close_time") else None,
            is_closed=data.get("is_closed", False),
            breaks=tuple((time.fromisoformat(b[0]), time.fromisoformat(b[1])) for b in data.get("breaks", [])),
        )

    @classmethod
    def closed(cls, day: DayOfWeek) -> "DaySchedule":
        """Create a closed day schedule"""
        return cls(day=day, is_closed=True)

    @classmethod
    def all_day(cls, day: DayOfWeek) -> "DaySchedule":
        """Create a 24/7 schedule"""
        return cls(day=day, open_time=time(0, 0), close_time=time(23, 59, 59))

    def __str__(self) -> str:
        if self.is_closed:
            return f"{self.day.name}: Closed"
        breaks_str = ""
        if self.breaks:
            breaks_str = f" (breaks: {', '.join(f'{b[0]}-{b[1]}' for b in self.breaks)})"
        return f"{self.day.name}: {self.open_time.strftime('%H:%M')}-{self.close_time.strftime('%H:%M')}{breaks_str}"


@dataclass(frozen=True, slots=True)
class OpeningHours:
    """
    Complete opening hours for a week.
    Immutable collection of day schedules.
    """
    schedules: tuple[DaySchedule, ...] = field(default_factory=tuple)
    timezone: str = "UTC"
    special_hours: tuple[tuple[str, DaySchedule], ...] = ()  # (date_str, schedule) for holidays

    def __post_init__(self) -> None:
        """Validate and ensure all days present"""
        if len(self.schedules) != 7:
            # Fill missing days with closed
            existing_days = {s.day for s in self.schedules}
            all_schedules = list(self.schedules)
            for day in DayOfWeek:
                if day not in existing_days:
                    all_schedules.append(DaySchedule.closed(day))
            # Sort by day
            all_schedules.sort(key=lambda s: s.day.value)
            object.__setattr__(self, 'schedules', tuple(all_schedules))

    def get_schedule(self, day: DayOfWeek) -> DaySchedule:
        """Get schedule for a specific day"""
        for schedule in self.schedules:
            if schedule.day == day:
                return schedule
        return DaySchedule.closed(day)

    def is_open_on(self, day: DayOfWeek) -> bool:
        """Check if open on a specific day"""
        return self.get_schedule(day).is_open

    def is_open_at(self, dt) -> bool:
        """Check if open at a specific datetime"""
        from datetime import datetime
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)

        day = DayOfWeek(dt.weekday())
        schedule = self.get_schedule(day)

        # Check special hours first
        date_str = dt.date().isoformat()
        for special_date, special_schedule in self.special_hours:
            if special_date == date_str:
                return special_schedule.is_open_at(dt.time())

        return schedule.is_open_at(dt.time())

    def next_open_time(self, from_dt) -> tuple[DayOfWeek, time] | None:
        """Find next opening time from a given datetime"""
        from datetime import datetime, timedelta
        if isinstance(from_dt, str):
            from_dt = datetime.fromisoformat(from_dt)

        current = from_dt
        for _ in range(14):  # Check up to 2 weeks
            day = DayOfWeek(current.weekday())
            schedule = self.get_schedule(day)

            # Check special hours
            date_str = current.date().isoformat()
            for special_date, special_schedule in self.special_hours:
                if special_date == date_str:
                    schedule = special_schedule
                    break

            if schedule.is_open:
                if current.time() < schedule.open_time:
                    return (day, schedule.open_time)
                elif current.time() < schedule.close_time:
                    return (day, current.time())

            current += timedelta(days=1)
            current = current.replace(hour=0, minute=0, second=0, microsecond=0)

        return None

    def add_special_hours(self, date: str, schedule: DaySchedule) -> "OpeningHours":
        """Add special hours for a specific date (holiday)"""
        new_special = self.special_hours + ((date, schedule),)
        return OpeningHours(
            schedules=self.schedules,
            timezone=self.timezone,
            special_hours=new_special
        )

    def remove_special_hours(self, date: str) -> "OpeningHours":
        """Remove special hours for a date"""
        new_special = tuple(s for s in self.special_hours if s[0] != date)
        return OpeningHours(
            schedules=self.schedules,
            timezone=self.timezone,
            special_hours=new_special
        )

    def get_weekly_open_hours(self) -> dict[DayOfWeek, tuple[time, time]]:
        """Get regular weekly open hours as dict"""
        result = {}
        for schedule in self.schedules:
            if schedule.is_open:
                result[schedule.day] = (schedule.open_time, schedule.close_time)
        return result

    def total_weekly_hours(self) -> float:
        """Total open hours per week"""
        return sum(s.duration_hours for s in self.schedules)

    def to_dict(self) -> dict:
        return {
            "schedules": [s.to_dict() for s in self.schedules],
            "timezone": self.timezone,
            "special_hours": [
                {"date": d, "schedule": s.to_dict()}
                for d, s in self.special_hours
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OpeningHours":
        return cls(
            schedules=tuple(DaySchedule.from_dict(s) for s in data.get("schedules", [])),
            timezone=data.get("timezone", "UTC"),
            special_hours=tuple(
                (d, DaySchedule.from_dict(s))
                for d, s in data.get("special_hours", [])
            ),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "OpeningHours":
        """Create from JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def closed(cls, timezone: str = "UTC") -> "OpeningHours":
        """Create completely closed hours"""
        return cls(
            schedules=tuple(DaySchedule.closed(day) for day in DayOfWeek),
            timezone=timezone
        )

    @classmethod
    def all_day(cls, timezone: str = "UTC") -> "OpeningHours":
        """Create 24/7 hours"""
        return cls(
            schedules=tuple(DaySchedule.all_day(day) for day in DayOfWeek),
            timezone=timezone
        )

    @classmethod
    def business_hours(cls, timezone: str = "UTC") -> "OpeningHours":
        """Create standard business hours (Mon-Fri 9-17)"""
        schedules = []
        for day in DayOfWeek:
            if day <= DayOfWeek.FRIDAY:
                schedules.append(DaySchedule(
                    day=day,
                    open_time=time(9, 0),
                    close_time=time(17, 0)
                ))
            else:
                schedules.append(DaySchedule.closed(day))
        return cls(schedules=tuple(schedules), timezone=timezone)

    def __str__(self) -> str:
        lines = [f"Opening Hours ({self.timezone}):"]
        for schedule in self.schedules:
            lines.append(f"  {schedule}")
        if self.special_hours:
            lines.append("  Special Hours:")
            for date, schedule in self.special_hours:
                lines.append(f"    {date}: {schedule}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"OpeningHours(timezone='{self.timezone}', days_open={sum(1 for s in self.schedules if s.is_open)})"
