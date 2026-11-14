"""Tests for the linear-interpolation example.

The regression test pins the exact pair from NumPy's CI. The property tests
check the scaled tolerance over the same input ranges as NumPy's test.
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given
from numpy.testing import assert_allclose

from pycon_hk_hypothesis.lerp import lerp, scale_aware_atol, symmetric_values
from pycon_hk_hypothesis.lerp_testing import (
    finite_float,
    interpolation_inputs,
    near_power_of_two,
)

# From numpy/lib/tests/test_function_base.py, reported in NumPy PR #32721.
NUMPY_REGRESSION = (0.5, 562949953421314.0, -562949953421310.9)


@given(*interpolation_inputs())
def test_symmetric_with_scaled_tolerance(t: float, a: float, b: float) -> None:
    left, right = symmetric_values(a, b, t)
    assert_allclose(left, right, atol=scale_aware_atol(a, b), rtol=0)


@given(a=finite_float(), b=finite_float())
def test_endpoints_are_exact(a: float, b: float) -> None:
    assert lerp(a, b, 0.0) == a
    assert lerp(a, b, 1.0) == b


@given(near_power_of_two())
def test_boundary_pairs_are_near_opposite(pair: tuple[float, float]) -> None:
    a, b = pair
    assert abs(a + b) < max(abs(a), abs(b))


def test_numpy_regression_needs_scaled_tolerance() -> None:
    t, a, b = NUMPY_REGRESSION
    left, right = symmetric_values(a, b, t)

    # The default tolerance is too tight: the two sides differ by 0.125.
    with pytest.raises(AssertionError):
        assert_allclose(left, right)

    # One ULP of the operands is 0.125; the scaled tolerance allows it.
    assert np.isclose(max(abs(a), abs(b)) * np.finfo(np.float64).eps, 0.125)
    assert_allclose(left, right, atol=scale_aware_atol(a, b), rtol=0)
