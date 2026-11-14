"""Hypothesis discovers, shrinks, and explains a realistic schedule bug.

Run with:
    uv run python scripts/06_realistic_example.py
    uv run python scripts/06_realistic_example.py --report   # raw @given output

The schedule is abstracted from python-dateutil's recurrence property tests:
an anchor date, a step, a count, and a weekday filter. The buggy
implementation applies ``count`` to candidates examined rather than
occurrences accepted, so a weekday filter silently truncates the schedule.
"""

from __future__ import annotations

import sys
from datetime import date

from hypothesis import HealthCheck, find, given, settings

from pycon_hk_hypothesis.schedule import Schedule
from pycon_hk_hypothesis.schedule_buggy import buggy_occurrences
from pycon_hk_hypothesis.testing import schedules

DEMO_SETTINGS = settings(
    max_examples=500,
    deadline=None,
    database=None,
    suppress_health_check=[HealthCheck.too_slow],
)


def describe(schedule: Schedule) -> str:
    weekdays = sorted(schedule.weekdays)
    return (
        f"Schedule(start={schedule.start.isoformat()}, "
        f"every_days={schedule.every_days}, count={schedule.count}, "
        f"weekdays={weekdays})"
    )


@DEMO_SETTINGS
@given(schedules())
def test_exactly_count_occurrences(schedule: Schedule) -> None:
    result = buggy_occurrences(schedule)
    assert len(result) == schedule.count, (
        f"expected {schedule.count} occurrence(s), got {len(result)}"
    )


def show_search() -> Schedule:
    bad = find(
        schedules(),
        lambda schedule: len(buggy_occurrences(schedule)) != schedule.count,
        settings=DEMO_SETTINGS,
    )
    print("Hypothesis found a failing schedule and shrank it:")
    print("    len(occurrences(schedule)) == schedule.count\n")
    print(f"  shrunk counterexample: {describe(bad)}")
    print(f"  buggy result: {[day.isoformat() for day in buggy_occurrences(bad)]}")
    print(f"  fixed result: {[day.isoformat() for day in bad.occurrences()]}")
    print(
        "\nWhy this is a small, clear counterexample:\n"
        "  one accepted candidate (Monday) is followed by one rejected candidate\n"
        "  (Tuesday), so a one-day step and a single weekday are enough to expose\n"
        "  the bug, and the start date shrank to the first Monday in the range.\n"
    )
    return bad


def show_report() -> None:
    print("The same property as a normal @given test (raw Hypothesis report):\n")
    try:
        test_exactly_count_occurrences()
    except AssertionError as error:
        for note in getattr(error, "__notes__", []):
            print(note)
            print()
    else:
        raise SystemExit("expected the buggy implementation to fail")


def main() -> None:
    sample = Schedule(
        start=date(2024, 1, 1),  # Monday
        every_days=1,
        count=3,
        weekdays=frozenset({3}),  # Wednesday
    )
    print("A reminder every day, Wednesdays only, starting Monday 1 Jan 2024:\n")
    print(f"  {describe(sample)}")
    print(f"  expected: {[day.isoformat() for day in sample.occurrences()]}")
    print(f"  buggy:    {[day.isoformat() for day in buggy_occurrences(sample)]}")
    print()

    bad = show_search()
    print(f"  restored from JSON: {Schedule.from_dict(bad.to_dict()) == bad}\n")

    if "--report" in sys.argv:
        show_report()


if __name__ == "__main__":
    main()
