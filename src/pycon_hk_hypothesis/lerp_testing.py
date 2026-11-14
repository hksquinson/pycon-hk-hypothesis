"""Hypothesis strategies for the lerp example.

The original NumPy test used plain ``st.floats``. That found the failure in
2025, but the general float distribution does not reliably produce the
near-power-of-two pair on every Hypothesis version. The composite strategy
below encodes the dangerous region directly, which is also the point of a
custom strategy: describe the inputs that matter instead of hoping a generic
generator stumbles into them.
"""

from __future__ import annotations

from hypothesis import strategies as st


@st.composite
def near_power_of_two(draw: st.DrawFn) -> tuple[float, float]:
    """Draw ``(a, b)`` straddling a power-of-two boundary.

    For ``a ~ 2**e`` and ``b ~ -2**e``, ``b - a`` crosses a binade boundary and
    is rounded. The midpoint is then tiny compared with the operands, so the
    two symmetry calculations can disagree by about one ULP.
    """
    exponent = draw(st.integers(min_value=40, max_value=52))
    magnitude = 2.0**exponent
    a = magnitude + draw(st.floats(min_value=-1, max_value=1))
    b = -magnitude + draw(st.floats(min_value=-1, max_value=1))
    return a, b


def finite_float() -> st.SearchStrategy[float]:
    """A finite float in the range used by NumPy's lerp test."""
    return st.floats(min_value=-1e300, max_value=1e300, allow_nan=False, allow_infinity=False)


def interpolation_inputs() -> tuple[st.SearchStrategy[float], ...]:
    """General finite inputs, matching the ranges in NumPy's test."""
    return (
        st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
        finite_float(),
        finite_float(),
    )
