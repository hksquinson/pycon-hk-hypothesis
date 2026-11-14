"""The first draft of the schedule generator, kept for the live demo.

The bug is realistic: ``count`` is applied to the number of *candidates*
examined instead of the number of *occurrences* accepted. When the weekday
filter rejects a candidate, the schedule silently comes up short.

The fixed implementation lives in :mod:`pycon_hk_hypothesis.schedule`.
"""

from __future__ import annotations

from datetime import date, timedelta

from pycon_hk_hypothesis.schedule import Schedule


def buggy_occurrences(schedule: Schedule) -> list[date]:
    """Generate at most ``count`` occurrences, examining ``count`` candidates."""
    result: list[date] = []
    day = schedule.start

    for _ in range(schedule.count):
        if schedule.allows(day):
            result.append(day)
        day += timedelta(days=schedule.every_days)

    return result
