"""Use CrossHair to check a bounded search window exhaustively.

Run with:
    uv run python scripts/07_crosshair_schedule.py

``Schedule.first_offset`` scans candidate offsets 0..6. That is enough because
weekday cycles have length 1 or 7, but "enough" is an argument, not a test.
The property below compares the seven-step scan with a fourteen-step scan for
every step from 1 to 14; CrossHair explores the resulting branches
symbolically instead of sampling them.

The second test is a deliberate off-by-one: a six-step scan. CrossHair reports
the counterexample that the shorter window misses.
"""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from pycon_hk_hypothesis.schedule import first_offset

CROSSHAIR = settings(
    backend="crosshair",
    deadline=None,
    max_examples=50,
    database=None,
)


def matches(
    start_weekday: int,
    every_days: int,
    weekdays: frozenset[int],
    offset: int,
) -> bool:
    weekday = ((start_weekday - 1 + offset * every_days) % 7) + 1
    return not weekdays or weekday in weekdays


def expected_offset(
    start_weekday: int,
    every_days: int,
    weekdays: frozenset[int],
) -> int | None:
    """Brute-force the first match over two weeks."""
    return next(
        (offset for offset in range(14) if matches(start_weekday, every_days, weekdays, offset)),
        None,
    )


def first_offset_too_short(
    start_weekday: int,
    every_days: int,
    weekdays: frozenset[int],
) -> int | None:
    """The planted bug: a six-step window misses an offset of six."""
    for offset in range(6):
        if matches(start_weekday, every_days, weekdays, offset):
            return offset
    return None


@CROSSHAIR
@given(
    start_weekday=st.integers(min_value=1, max_value=7),
    every_days=st.integers(min_value=1, max_value=14),
    weekdays=st.frozensets(st.integers(min_value=1, max_value=7)),
)
def test_seven_steps_are_enough(
    start_weekday: int,
    every_days: int,
    weekdays: frozenset[int],
) -> None:
    assert first_offset(start_weekday, every_days, weekdays) == expected_offset(
        start_weekday, every_days, weekdays
    )


@CROSSHAIR
@given(
    start_weekday=st.integers(min_value=1, max_value=7),
    every_days=st.integers(min_value=1, max_value=14),
    weekdays=st.frozensets(st.integers(min_value=1, max_value=7)),
)
def test_planted_off_by_one(
    start_weekday: int,
    every_days: int,
    weekdays: frozenset[int],
) -> None:
    assert first_offset_too_short(start_weekday, every_days, weekdays) == expected_offset(
        start_weekday, every_days, weekdays
    )


def main() -> None:
    test_seven_steps_are_enough()
    print("CrossHair: the seven-step window agrees with a fourteen-step scan.")

    try:
        test_planted_off_by_one()
    except AssertionError as error:
        print("\nCrossHair found the planted six-step off-by-one:\n")
        for note in getattr(error, "__notes__", []):
            print(note)
            print()
    else:
        raise SystemExit("expected the planted off-by-one to fail")


if __name__ == "__main__":
    main()
