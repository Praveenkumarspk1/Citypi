"""
TimeRange Value Object
"""
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Optional

import pytz


@dataclass(frozen=True, slots=True)
class TimeRange:
    """
    Immutable time range with timezone support.
    Represents a period with start and end datetime.
    """
    start: datetime
    end: datetime
    timezone: str = "UTC"

    def __post_init__(self) -> None:
        """Validate and normalize after initialization"""
        # Ensure timezone awareness
        if self.start.tzinfo is None:
            tz = pytz.timezone(self.timezone)
            object.__setattr__(self, 'start', tz.localize(self.start))
        elif self.start.tzinfo != pytz.timezone(self.timezone):
            object.__setattr__(self, 'start', self.start.astimezone(pytz.timezone(self.timezone)))

        if self.end.tzinfo is None:
            tz = pytz.timezone(self.timezone)
            object.__setattr__(self, 'end', tz.localize(self.end))
        elif self.end.tzinfo != pytz.timezone(self.timezone):
            object.__setattr__(self, 'end', self.end.astimezone(pytz.timezone(self.timezone)))

        if self.start >= self.end:
            raise ValueError("Start time must be before end time")

    @property
    def duration(self) -> timedelta:
        """Duration of the time range"""
        return self.end - self.start

    @property
    def duration_minutes(self) -> int:
        """Duration in minutes"""
        return int(self.duration.total_seconds() / 60)

    @property
    def duration_hours(self) -> float:
        """Duration in hours"""
        return self.duration.total_seconds() / 3600

    def contains(self, dt: datetime) -> bool:
        """Check if a datetime falls within this range"""
        if dt.tzinfo is None:
            dt = pytz.timezone(self.timezone).localize(dt)
        elif dt.tzinfo != pytz.timezone(self.timezone):
            dt = dt.astimezone(pytz.timezone(self.timezone))
        return self.start <= dt < self.end

    def overlaps(self, other: "TimeRange") -> bool:
        """Check if this range overlaps with another"""
        if self.timezone != other.timezone:
            # Convert to same timezone for comparison
            other_start = other.start.astimezone(pytz.timezone(self.timezone))
            other_end = other.end.astimezone(pytz.timezone(self.timezone))
        else:
            other_start = other.start
            other_end = other.end

        return self.start < other_end and other_start < self.end

    def intersection(self, other: "TimeRange") -> Optional["TimeRange"]:
        """Return the intersection of two time ranges"""
        if not self.overlaps(other):
            return None

        if self.timezone != other.timezone:
            other_start = other.start.astimezone(pytz.timezone(self.timezone))
            other_end = other.end.astimezone(pytz.timezone(self.timezone))
        else:
            other_start = other.start
            other_end = other.end

        start = max(self.start, other_start)
        end = min(self.end, other_end)

        return TimeRange(start=start, end=end, timezone=self.timezone)

    def union(self, other: "TimeRange") -> "TimeRange":
        """Return the union of two time ranges (if they overlap or are adjacent)"""
        if not self.overlaps(other) and not self.is_adjacent(other):
            raise ValueError("Cannot union non-overlapping, non-adjacent ranges")

        if self.timezone != other.timezone:
            other_start = other.start.astimezone(pytz.timezone(self.timezone))
            other_end = other.end.astimezone(pytz.timezone(self.timezone))
        else:
            other_start = other.start
            other_end = other.end

        start = min(self.start, other_start)
        end = max(self.end, other_end)

        return TimeRange(start=start, end=end, timezone=self.timezone)

    def is_adjacent(self, other: "TimeRange") -> bool:
        """Check if two ranges are adjacent (end == start)"""
        if self.timezone != other.timezone:
            other_start = other.start.astimezone(pytz.timezone(self.timezone))
            other_end = other.end.astimezone(pytz.timezone(self.timezone))
        else:
            other_start = other.start
            other_end = other.end

        return self.end == other_start or other_end == self.start

    def split(self, duration: timedelta) -> list["TimeRange"]:
        """Split this range into chunks of given duration"""
        chunks = []
        current = self.start
        while current + duration <= self.end:
            chunks.append(TimeRange(start=current, end=current + duration, timezone=self.timezone))
            current += duration
        if current < self.end:
            chunks.append(TimeRange(start=current, end=self.end, timezone=self.timezone))
        return chunks

    def to_dict(self) -> dict:
        """Return as dictionary"""
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "timezone": self.timezone
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TimeRange":
        """Create from dictionary"""
        return cls(
            start=datetime.fromisoformat(data["start"]),
            end=datetime.fromisoformat(data["end"]),
            timezone=data.get("timezone", "UTC")
        )

    @classmethod
    def from_date_time(cls, date: datetime, start_time: time, end_time: time, timezone: str = "UTC") -> "TimeRange":
        """Create from date and time components"""
        tz = pytz.timezone(timezone)
        start = tz.localize(datetime.combine(date.date(), start_time))
        end = tz.localize(datetime.combine(date.date(), end_time))
        if end <= start:
            end += timedelta(days=1)
        return cls(start=start, end=end, timezone=timezone)

    @classmethod
    def now(cls, duration: timedelta, timezone: str = "UTC") -> "TimeRange":
        """Create a range starting now with given duration"""
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        return cls(start=now, end=now + duration, timezone=timezone)

    def __str__(self) -> str:
        return f"{self.start.strftime('%Y-%m-%d %H:%M')} - {self.end.strftime('%H:%M')} ({self.timezone})"

    def __repr__(self) -> str:
        return f"TimeRange(start={self.start.isoformat()}, end={self.end.isoformat()}, timezone='{self.timezone}')"


@dataclass(frozen=True, slots=True)
class RecurringTimeRange:
    """
    Recurring time range (e.g., "every Monday 9-17").
    """
    days_of_week: tuple[int, ...]  # 0=Monday, 6=Sunday
    start_time: time
    end_time: time
    timezone: str = "UTC"
    start_date: datetime | None = None
    end_date: datetime | None = None

    def __post_init__(self) -> None:
        """Validate after initialization"""
        if not self.days_of_week:
            raise ValueError("At least one day of week required")
        if any(d < 0 or d > 6 for d in self.days_of_week):
            raise ValueError("Days of week must be 0-6 (Monday=0)")
        if self.start_time >= self.end_time:
            raise ValueError("Start time must be before end time")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date must be before end date")

    def occurs_on(self, dt: datetime) -> bool:
        """Check if this recurring range occurs on a given datetime"""
        if dt.tzinfo is None:
            dt = pytz.timezone(self.timezone).localize(dt)
        elif dt.tzinfo != pytz.timezone(self.timezone):
            dt = dt.astimezone(pytz.timezone(self.timezone))

        if self.start_date and dt < self.start_date:
            return False
        if self.end_date and dt > self.end_date:
            return False

        if dt.weekday() not in self.days_of_week:
            return False

        current_time = dt.time()
        return self.start_time <= current_time < self.end_time

    def get_occurrences(self, start: datetime, end: datetime) -> list[TimeRange]:
        """Get all occurrences within a date range"""
        occurrences = []
        current = start
        while current <= end:
            if current.weekday() in self.days_of_week:
                tz = pytz.timezone(self.timezone)
                occurrence_start = tz.localize(datetime.combine(current.date(), self.start_time))
                occurrence_end = tz.localize(datetime.combine(current.date(), self.end_time))
                if occurrence_end <= occurrence_start:
                    occurrence_end += timedelta(days=1)
                occurrences.append(TimeRange(start=occurrence_start, end=occurrence_end, timezone=self.timezone))
            current += timedelta(days=1)
        return occurrences

    def to_dict(self) -> dict:
        return {
            "days_of_week": list(self.days_of_week),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "timezone": self.timezone,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecurringTimeRange":
        return cls(
            days_of_week=tuple(data["days_of_week"]),
            start_time=time.fromisoformat(data["start_time"]),
            end_time=time.fromisoformat(data["end_time"]),
            timezone=data.get("timezone", "UTC"),
            start_date=datetime.fromisoformat(data["start_date"]) if data.get("start_date") else None,
            end_date=datetime.fromisoformat(data["end_date"]) if data.get("end_date") else None,
        )
