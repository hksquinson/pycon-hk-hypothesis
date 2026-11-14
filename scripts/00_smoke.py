"""Smoke-test the talk environment, including the CrossHair backend.

Run with:
    uv run python scripts/00_smoke.py
"""

from hypothesis import given, settings
from hypothesis import strategies as st


@given(st.text())
def test_utf8_roundtrip(value: str) -> None:
    assert value.encode("utf-8").decode("utf-8") == value


@settings(backend="crosshair", max_examples=10, deadline=None)
@given(st.integers(min_value=-(10**6), max_value=10**6))
def test_absolute_value_is_non_negative(value: int) -> None:
    assert abs(value) >= 0


if __name__ == "__main__":
    test_utf8_roundtrip()
    test_absolute_value_is_non_negative()
    print("Environment OK: Hypothesis and the CrossHair backend both ran.")
