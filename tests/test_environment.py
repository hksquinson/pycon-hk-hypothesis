"""Minimal checks that the talk environment is installed and working."""

from hypothesis import given
from hypothesis import strategies as st


def reverse_twice(xs: list[int]) -> list[int]:
    return list(reversed(list(reversed(xs))))


@given(st.lists(st.integers()))
def test_reverse_twice_is_identity(xs: list[int]) -> None:
    assert reverse_twice(xs) == xs
