# The realistic example: a recurring-reminder schedule

The talk's running example is abstracted from python-dateutil's recurrence
property tests. dateutil's `rrule` combines a frequency, an interval, a count,
and a weekday filter; its tests draw those fields together with a custom
`@st.composite` strategy and check that cached rules survive pickle and
deepcopy. We keep that shape and drop the time-zone and cache complexity.

The source of the abstraction:

- [`tests/property/test_rrule_prop.py`](https://github.com/dateutil/dateutil/blob/master/tests/property/test_rrule_prop.py)
- [issue #1369](https://github.com/dateutil/dateutil/issues/1369)
- [PR #1600](https://github.com/dateutil/dateutil/pull/1600)

## The model

A `Schedule` has four fields:

| Field | Meaning |
|---|---|
| `start` | The anchor date. |
| `every_days` | The step between candidates, at least 1. |
| `count` | How many occurrences to produce. |
| `weekdays` | ISO weekdays that are allowed (Monday=1 ... Sunday=7). Empty means any day. |

Candidates are `start`, `start + every_days`, `start + 2 * every_days`, and so
on. An occurrence is a candidate whose weekday passes the filter. `start` is
only the anchor; if its weekday is filtered out, the first occurrence is later.

For example, starting on Monday 1 January 2024, every day, Wednesdays only,
three times, gives 3, 10, and 17 January.

## The bug

The intentionally buggy implementation applies `count` to the number of
*candidates examined* rather than the number of *occurrences accepted*:

```python
for _ in range(schedule.count):
    if schedule.allows(day):
        result.append(day)
    day += timedelta(days=schedule.every_days)
```

If a candidate fails the weekday filter, the loop still consumes one of the
`count` iterations, so the schedule comes up short. The fix is to loop until
`len(result) == count`, not until a fixed number of candidates has been seen.

The failing example the talk uses is:

```python
# Two Monday reminders, starting on a Monday.
Schedule(
    start=date(2024, 1, 1),
    every_days=1,
    count=2,
    weekdays=frozenset({1}),
)
```

The first candidate, Monday, is accepted. The second candidate, Tuesday, is
rejected and the loop ends, so the result has one date instead of two.

Hypothesis's shrinker reached `count=2` because the first candidate is accepted
and the second is rejected. A count of 1 can also fail when the anchor itself
is filtered out, but the two-candidate case makes the candidate-versus-
occurrence distinction easier to see.

The buggy version lives in `src/pycon_hk_hypothesis/schedule_buggy.py`. It is
deliberately not imported by `tests/`; the demo script owns the failing
property, so `uv run pytest` stays green.

## The properties

```python
@given(schedules())
def test_returns_exactly_count_occurrences(schedule):
    assert len(schedule.occurrences()) == schedule.count


@given(schedules())
def test_occurrences_are_strictly_increasing(schedule):
    dates = schedule.occurrences()
    assert dates == sorted(set(dates))


@given(schedules())
def test_occurrences_respect_the_weekday_filter(schedule):
    assert all(schedule.allows(day) for day in schedule.occurrences())


@given(schedules())
def test_occurrences_stay_on_the_step_grid(schedule):
    for day in schedule.occurrences():
        assert day >= schedule.start
        assert (day - schedule.start).days % schedule.every_days == 0


@given(schedules())
def test_survives_a_json_round_trip(schedule):
    payload = json.loads(json.dumps(schedule.to_dict()))
    restored = Schedule.from_dict(payload)
    assert restored == schedule
    assert restored.occurrences() == schedule.occurrences()
```

The last property is the LLM/tool-call connection: an assistant creates a
reminder, the payload travels as JSON, and the server rebuilds the same
schedule. The other properties stop a "fix" that pads the result with dates
that are off the grid or on the wrong weekday.

## The custom strategy

`st.builds(Schedule, ...)` would draw the fields independently, which can
produce schedules that are not satisfiable. With a whole-week step
(`every_days` 7 or 14), candidates can only ever land on the start's weekday;
if the filter excludes that weekday, no occurrence exists and `occurrences()`
would raise or loop forever.

The composite strategy encodes that correlation:

```python
@st.composite
def schedules(draw):
    every_days = draw(st.integers(min_value=1, max_value=14))
    weekdays = draw(st.frozensets(st.integers(min_value=1, max_value=7)))

    if weekdays and every_days % 7 == 0:
        weekday = draw(st.sampled_from(sorted(weekdays)))
        start = draw(dates_on_weekday(weekday))
    else:
        start = draw(st.dates(min_value=MIN_DATE, max_value=MAX_DATE))

    count = draw(st.integers(min_value=0, max_value=12))
    return Schedule(start=start, every_days=every_days, count=count, weekdays=weekdays)
```

Any step that is not a multiple of 7 cycles through all seven weekdays (7 is
prime), so an arbitrary start is fine. A multiple-of-7 step needs a start that
the filter allows. This is the case where a custom strategy is genuinely
better than `filter`, which would reject many draws.

## The CrossHair demo

`Schedule.first_offset` scans candidate offsets 0 to 6. That window is enough
because weekday cycles have length 1 or 7, but that is an argument, not a test.
The CrossHair script compares the seven-step scan with a fourteen-step scan for
every step from 1 to 14, and CrossHair explores the branches symbolically. It
also checks a planted six-step version and reports the missed offset.

CrossHair is a bounded symbolic-execution tool, not a proof of the whole
program. Through Hypothesis it searches for counterexamples; it is most useful
when a branch needs a narrow combination of values. The talk places it on a
spectrum: example tests, property-based tests, symbolic execution, formal
verification.

## Run it

```bash
uv run pytest
uv run python scripts/06_realistic_example.py
uv run python scripts/06_realistic_example.py --report  # raw @given report
uv run python scripts/07_crosshair_schedule.py
```
