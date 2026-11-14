"""Tests for the small examples shown on the talk slides.

Each test mirrors a slide snippet. The point is to keep the deck honest: if a
snippet stops working, the test suite catches it before the talk does.
"""

from __future__ import annotations

import json
import math
import re
from bisect import bisect_left
from decimal import Decimal
from fractions import Fraction

import pytest
from hypothesis import assume, example, find, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

# --- Writing a property-based test -----------------------------------------


@given(st.lists(st.integers()))
def test_reverse_twice(xs: list[int]) -> None:
    assert list(reversed(list(reversed(xs)))) == xs


# --- Strategies: numerical values ------------------------------------------


@given(st.integers())
def test_any_integer(x: int) -> None:
    assert isinstance(x, int)


@given(st.integers(min_value=0, max_value=100))
def test_bounded_integer(x: int) -> None:
    assert 0 <= x <= 100


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_finite_floats_are_finite(x: float) -> None:
    assert math.isfinite(x)


def test_default_floats_include_special_values() -> None:
    search = settings(max_examples=2_000, database=None, derandomize=True)
    assert math.isnan(find(st.floats(), math.isnan, settings=search))
    assert math.isinf(find(st.floats(), math.isinf, settings=search))
    negative_zero = find(
        st.floats(),
        lambda x: x == 0.0 and math.copysign(1.0, x) < 0,
        settings=search,
    )
    assert negative_zero == 0.0


@given(st.fractions())
def test_fractions_are_fractions(x: Fraction) -> None:
    assert isinstance(x, Fraction)


@given(st.decimals())
def test_decimals_are_decimals(x: Decimal) -> None:
    assert isinstance(x, Decimal)


# --- Strategies: lists and containers --------------------------------------


@given(
    st.lists(st.integers()),
    st.tuples(st.integers(), st.text()),
    st.sets(st.integers()),
    st.dictionaries(st.text(), st.integers()),
)
def test_container_strategies_produce_the_right_types(
    xs: list[int],
    pair: tuple[int, str],
    values: set[int],
    mapping: dict[str, int],
) -> None:
    assert isinstance(xs, list)
    assert isinstance(pair, tuple) and len(pair) == 2
    assert isinstance(values, set)
    assert isinstance(mapping, dict)


@given(st.lists(st.text(), min_size=1, max_size=5))
def test_list_size_bounds(xs: list[str]) -> None:
    assert 1 <= len(xs) <= 5


@given(st.lists(st.integers(), unique=True))
def test_unique_list_has_no_duplicates(xs: list[int]) -> None:
    assert len(xs) == len(set(xs))


# --- Strategies: strings ----------------------------------------------------


@given(st.text())
def test_text_is_a_string(s: str) -> None:
    assert isinstance(s, str)


@given(st.text(alphabet="abc", max_size=5), st.binary(max_size=5))
def test_string_and_binary_strategies(s: str, b: bytes) -> None:
    assert set(s) <= set("abc")
    assert isinstance(b, bytes)


@given(st.text(min_size=1, max_size=10))
def test_text_size_bounds(s: str) -> None:
    assert 1 <= len(s) <= 10


@given(st.characters())
def test_characters_are_single_code_points(c: str) -> None:
    assert isinstance(c, str)
    assert len(c) == 1


def test_from_regex_generates_a_matching_string() -> None:
    pattern = r"[a-z]+@[a-z]+\.[a-z]{2,3}"
    value = find(
        st.from_regex(pattern),
        lambda _: True,
        settings=settings(max_examples=10, database=None, derandomize=True),
    )
    assert re.search(pattern, value)


# --- Modifying and filtering -------------------------------------------------


@given(st.integers().map(lambda x: x * 2))
def test_map_produces_even_numbers(x: int) -> None:
    assert x % 2 == 0


@given(st.integers().filter(lambda x: x % 2 == 0))
def test_filter_keeps_even_numbers(x: int) -> None:
    assert x % 2 == 0


@given(st.integers(), st.integers())
def test_division_with_assume(x: int, y: int) -> None:
    assume(y != 0)
    assert x == (x // y) * y + x % y


@given(st.integers(), st.integers(min_value=1, max_value=10))
def test_floor_division_lossless(a: int, b: int) -> None:
    assume(a % b == 0)
    assert (a // b) * b == a


# --- Custom strategies: recursive data --------------------------------------


json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(),
    lambda children: st.lists(children) | st.dictionaries(st.text(), children),
    max_leaves=5,
)


@given(json_values)
def test_json_round_trip(value: object) -> None:
    assert json.loads(json.dumps(value)) == value


# --- Custom strategies: @st.composite --------------------------------------


@st.composite
def ordered_pairs(draw: st.DrawFn) -> tuple[int, int]:
    n1 = draw(st.integers())
    n2 = draw(st.integers(min_value=n1))
    return n1, n2


@given(ordered_pairs())
def test_pairs_are_ordered(pair: tuple[int, int]) -> None:
    n1, n2 = pair
    assert n1 <= n2


# --- Custom strategies: st.data() -------------------------------------------


@given(st.data())
def test_binary_search_finds_value(data: st.DataObject) -> None:
    values = sorted(data.draw(st.lists(st.integers(), min_size=1)))
    index = data.draw(st.integers(min_value=0, max_value=len(values) - 1))
    found = bisect_left(values, values[index])
    assert values[found] == values[index]


# --- Where to use property-based testing ------------------------------------


@given(st.lists(st.integers()))
def test_sorted_is_ordered_and_permutation(xs: list[int]) -> None:
    result = sorted(xs)
    assert all(a <= b for a, b in zip(result, result[1:], strict=False))
    assert sorted(result) == sorted(xs)


def format_source(source: str) -> str:
    """A tiny stand-in for a code formatter."""
    lines = [line.rstrip() for line in source.splitlines()]
    return "\n".join(line for line in lines if line).strip()


@given(st.text())
def test_formatter_is_idempotent(source: str) -> None:
    once = format_source(source)
    assert format_source(once) == once


@given(st.lists(st.integers()), st.integers(min_value=-10, max_value=10))
def test_scaling_scales_sum(xs: list[int], factor: int) -> None:
    assert sum(factor * x for x in xs) == factor * sum(xs)


def old_sum(xs: list[int]) -> int:
    total = 0
    for x in xs:
        total += x
    return total


@given(st.lists(st.integers()))
def test_old_and_new_sum_agree(xs: list[int]) -> None:
    assert old_sum(xs) == sum(xs)


# --- Shrinking --------------------------------------------------------------


@pytest.mark.xfail(strict=True, reason="illustrates shrinking to [100]")
@given(st.lists(st.integers()))
def test_sum_below_100(xs: list[int]) -> None:
    assert sum(xs) < 100


# --- Settings and examples --------------------------------------------------


@settings(max_examples=10, deadline=None)
@given(st.integers())
def test_settings_are_applied(x: int) -> None:
    assert abs(x) >= 0


def test_profile_registration_and_loading() -> None:
    previous = settings.default
    assert previous is not None
    settings.register_profile("slide_demo", max_examples=5, deadline=None)
    settings.register_profile("slide_restore", parent=previous)
    try:
        settings.load_profile("slide_demo")
        current = settings.default
        assert current is not None
        assert current.max_examples == 5
        assert current.deadline is None
    finally:
        settings.load_profile("slide_restore")


def test_ci_profile_is_ci_ready() -> None:
    ci = settings.get_profile("ci")
    assert ci.max_examples == 1000
    assert ci.derandomize is True
    assert ci.deadline is None
    assert ci.database is None
    assert ci.print_blob is True


@given(st.integers())
@settings(max_examples=100, derandomize=True)
def test_without_example_passes(x: int) -> None:
    # Random sampling does not find this specific value.
    assert x != 123_456_789


@pytest.mark.xfail(strict=True, reason="pinned example triggers the failure")
@given(st.integers())
@example(123_456_789)
def test_with_example_fails(x: int) -> None:
    assert x != 123_456_789


# --- Limitations ------------------------------------------------------------


def add(a: int, b: int) -> int:
    """Deliberately wrong: a too-general property still passes."""
    return a - b


@given(st.integers(), st.integers())
def test_type_only_property_misses_a_wrong_add(a: int, b: int) -> None:
    # True even though add() subtracts; the property only checks the type.
    assert isinstance(add(a, b), int)


# --- CrossHair --------------------------------------------------------------


@pytest.mark.crosshair
def test_crosshair_finds_the_branch() -> None:
    @settings(backend="crosshair", max_examples=10, deadline=None, database=None)
    @given(st.integers())
    def prop(x: int) -> None:
        assert x != 123456789

    with pytest.raises(AssertionError):
        prop()


# --- Stateful testing -------------------------------------------------------


class BankMachine(RuleBasedStateMachine):
    def __init__(self) -> None:
        super().__init__()
        self.balance = 0

    @rule(amount=st.integers(min_value=0, max_value=100))
    def deposit(self, amount: int) -> None:
        self.balance += amount

    @invariant()
    def balance_non_negative(self) -> None:
        assert self.balance >= 0


def test_bank_machine() -> None:
    BankMachine.TestCase().runTest()
