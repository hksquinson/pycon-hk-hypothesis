"""Hypothesis strategies for the Wald-distribution example.

The real NumPy test draws only ``mean`` and ``scale`` and lets a fixed-seed
generator produce 1000 samples. The abstraction draws the standard-normal
value directly so the numerical failure is deterministic and the shrink is
readable.
"""

from __future__ import annotations

from hypothesis import strategies as st


@st.composite
def wald_inputs(draw: st.DrawFn) -> tuple[float, float, float]:
    """Draw ``(mean, scale, z)`` over the ranges that expose the cancellation."""
    mean = draw(st.floats(min_value=1e8, max_value=1e15, allow_nan=False, allow_infinity=False))
    scale = draw(st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False))
    z = draw(st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False))
    return mean, scale, z


@st.composite
def cancellation_prone(draw: st.DrawFn) -> tuple[float, float, float]:
    """Bias the draw toward ``Y >> scale``, where the old formula cancels.

    This is the custom-strategy lesson: when you know the dangerous region,
    encode it instead of relying on a generic float distribution to find it.
    """
    mean = draw(st.floats(min_value=1e8, max_value=1e15, allow_nan=False, allow_infinity=False))
    scale = draw(st.floats(min_value=0.1, max_value=1.0, allow_nan=False, allow_infinity=False))
    z = draw(st.floats(min_value=0.5, max_value=3.0, allow_nan=False, allow_infinity=False))
    return mean, scale, z
