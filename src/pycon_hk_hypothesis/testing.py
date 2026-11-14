"""Hypothesis strategies for the schedule example.

In a real project this module would live under ``tests/``. It is importable
here so both the pytest suite and the demo scripts share one definition.
"""

from __future__ import annotations

from datetime import date, timedelta

from hypothesis import strategies as st

from pycon_hk_hypothesis.schedule import Schedule

MIN_DATE = date(2024, 1, 1)
MAX_DATE = date(2030, 12, 31)


@st.composite
def dates_on_weekday(
    draw: st.DrawFn,
    weekday: int,
    min_value: date = MIN_DATE,
    max_value: date = MAX_DATE,
) -> date:
    """Draw a date in the range whose ISO weekday is ``weekday``."""
    first = min_value + timedelta(days=(weekday - min_value.isoweekday()) % 7)
    weeks = (max_value - first).days // 7
    return first + timedelta(days=7 * draw(st.integers(min_value=0, max_value=weeks)))


@st.composite
def schedules(draw: st.DrawFn) -> Schedule:
    """Draw a valid, satisfiable schedule.

    The fields are correlated, which is the point of a custom strategy:

    * With a whole-week step (``every_days`` 7 or 14) only the start's weekday
      is ever a candidate, so the start must satisfy the filter.
    * Any other step cycles through all seven weekdays, so every start is fine.
    """
    every_days = draw(st.integers(min_value=1, max_value=14))
    weekdays = draw(st.frozensets(st.integers(min_value=1, max_value=7)))

    if weekdays and every_days % 7 == 0:
        weekday = draw(st.sampled_from(sorted(weekdays)))
        start = draw(dates_on_weekday(weekday))
    else:
        start = draw(st.dates(min_value=MIN_DATE, max_value=MAX_DATE))

    count = draw(st.integers(min_value=0, max_value=12))
    return Schedule(start=start, every_days=every_days, count=count, weekdays=weekdays)
