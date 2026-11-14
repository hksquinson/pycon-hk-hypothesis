"""A small recurring-reminder schedule.

This is the realistic example for the talk, abstracted from the recurrence
property tests in python-dateutil. A schedule is an anchor date, a step in
days, a number of occurrences, and an optional weekday filter.

The public API is deliberately small: build a ``Schedule``, ask for its
``occurrences()``, and serialise it with ``to_dict`` / ``from_dict`` when it
travels through a tool call.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import TypedDict

ISO_WEEKDAYS = frozenset(range(1, 8))  # Monday=1 ... Sunday=7


class UnsatisfiableScheduleError(ValueError):
    """Raised when a schedule can never produce the requested occurrences."""


class SchedulePayload(TypedDict):
    """The JSON-shaped form of a schedule."""

    start: str
    every_days: int
    count: int
    weekdays: list[int]


def first_offset(
    start_weekday: int,
    every_days: int,
    weekdays: frozenset[int],
) -> int | None:
    """Return the smallest ``k`` whose candidate is allowed, or ``None``.

    Candidates are ``start + k * every_days``. Their weekdays repeat every
    ``7 / gcd(every_days, 7)`` steps, so if none of the first seven candidates
    is allowed, none ever will be.
    """
    for offset in range(7):
        weekday = ((start_weekday - 1 + offset * every_days) % 7) + 1
        if not weekdays or weekday in weekdays:
            return offset
    return None


@dataclass(frozen=True)
class Schedule:
    """A recurring reminder.

    ``start`` is the anchor, not necessarily the first occurrence: candidates
    are ``start``, ``start + every_days``, ... and the weekday filter decides
    which ones become occurrences. An empty ``weekdays`` means "any day".
    """

    start: date
    every_days: int = 1
    count: int = 1
    weekdays: frozenset[int] = frozenset()

    def __post_init__(self) -> None:
        if self.every_days < 1:
            raise ValueError("every_days must be at least 1")
        if self.count < 0:
            raise ValueError("count must be non-negative")
        unknown = self.weekdays - ISO_WEEKDAYS
        if unknown:
            raise ValueError(f"weekdays must be ISO weekdays 1..7, got {sorted(unknown)}")

    def allows(self, day: date) -> bool:
        """Whether ``day`` passes the weekday filter."""
        return not self.weekdays or day.isoweekday() in self.weekdays

    def first_offset(self) -> int | None:
        """Candidate index of the first allowed occurrence, or ``None``."""
        return first_offset(self.start.isoweekday(), self.every_days, self.weekdays)

    def is_satisfiable(self) -> bool:
        """Whether the schedule can produce ``count`` occurrences."""
        return self.count == 0 or self.first_offset() is not None

    def occurrences(self) -> list[date]:
        """Return exactly ``count`` dates, in increasing order."""
        if self.count == 0:
            return []

        if not self.is_satisfiable():
            raise UnsatisfiableScheduleError(
                f"no candidate of {self!r} falls on an allowed weekday"
            )

        result: list[date] = []
        day = self.start
        while len(result) < self.count:
            if self.allows(day):
                result.append(day)
            day += timedelta(days=self.every_days)
        return result

    def to_dict(self) -> SchedulePayload:
        """Return a JSON-serialisable payload."""
        return {
            "start": self.start.isoformat(),
            "every_days": self.every_days,
            "count": self.count,
            "weekdays": sorted(self.weekdays),
        }

    @classmethod
    def from_dict(cls, payload: SchedulePayload) -> Schedule:
        """Rebuild a schedule from ``to_dict`` output (e.g. parsed JSON)."""
        return cls(
            start=date.fromisoformat(payload["start"]),
            every_days=payload["every_days"],
            count=payload["count"],
            weekdays=frozenset(payload["weekdays"]),
        )
