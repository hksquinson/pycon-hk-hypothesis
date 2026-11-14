"""Show shrinking without pytest.

Run with:
    uv run python scripts/14_shrink_demo.py

The script calls the property test directly, so Hypothesis prints the minimal
failing case without pytest's report. The same test lives in
``tests/test_slide_examples.py`` as ``test_sum_below_100``.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st


@given(st.lists(st.integers()))
def test_sum_below_100(xs: list[int]) -> None:
    assert sum(xs) < 100


if __name__ == "__main__":
    test_sum_below_100()
