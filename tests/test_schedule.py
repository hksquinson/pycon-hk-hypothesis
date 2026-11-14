"""Property tests for the recurring-reminder schedule.

Run with ``uv run pytest``. These tests pass against the fixed implementation;
the demo script runs the same properties against the intentionally buggy one.
"""

from __future__ import annotations

import json
from datetime import date

import pytest
from hypothesis import given

from pycon_hk_hypothesis.schedule import (
    Schedule,
    UnsatisfiableScheduleError,
    first_offset,
)
from pycon_hk_hypothesis.testing import schedules


@given(schedules())
def test_returns_exactly_count_occurrences(schedule: Schedule) -> None:
    assert len(schedule.occurrences()) == schedule.count


@given(schedules())
def test_occurrences_are_strictly_increasing(schedule: Schedule) -> None:
    dates = schedule.occurrences()
    assert dates == sorted(set(dates))


@given(schedules())
def test_occurrences_respect_the_weekday_filter(schedule: Schedule) -> None:
    assert all(schedule.allows(day) for day in schedule.occurrences())


@given(schedules())
def test_occurrences_stay_on_the_step_grid(schedule: Schedule) -> None:
    for day in schedule.occurrences():
        assert day >= schedule.start
        assert (day - schedule.start).days % schedule.every_days == 0


@given(schedules())
def test_survives_a_json_round_trip(schedule: Schedule) -> None:
    payload = json.loads(json.dumps(schedule.to_dict()))
    restored = Schedule.from_dict(payload)

    assert restored == schedule
    assert restored.occurrences() == schedule.occurrences()


def test_zero_count_means_no_reminders() -> None:
    schedule = Schedule(start=date(2024, 1, 1), every_days=3, count=0)
    assert schedule.occurrences() == []


def test_impossible_schedule_is_reported_not_hung() -> None:
    # A whole-week step can only ever land on the start's weekday.
    schedule = Schedule(
        start=date(2024, 1, 1),  # Monday
        every_days=7,
        count=2,
        weekdays=frozenset({2}),  # Tuesday
    )

    assert not schedule.is_satisfiable()
    with pytest.raises(UnsatisfiableScheduleError):
        schedule.occurrences()


def test_first_offset_skips_rejected_candidates() -> None:
    assert first_offset(1, 1, frozenset({1})) == 0
    assert first_offset(1, 1, frozenset({2})) == 1
    assert first_offset(1, 7, frozenset({2})) is None
