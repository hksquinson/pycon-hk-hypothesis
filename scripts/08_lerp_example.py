"""Reproduce NumPy's lerp symmetry failure on an abstracted lerp.

Run with:
    uv run python scripts/08_lerp_example.py

The pair and the tolerance fix come from NumPy PR #32721:
https://github.com/numpy/numpy/pull/32721

The lesson is deliberately not "NumPy's interpolation is wrong". The
interpolation is fine; the *test's default tolerance* was wrong for inputs
where catastrophic cancellation makes the midpoint tiny.
"""

from __future__ import annotations

import math

import numpy as np
from hypothesis import find, settings
from numpy.testing import assert_allclose

from pycon_hk_hypothesis.lerp import scale_aware_atol, symmetric_values
from pycon_hk_hypothesis.lerp_testing import near_power_of_two

# The exact falsifying example from NumPy's CI, t=0.5.
T, A, B = 0.5, 562949953421314.0, -562949953421310.9


def show_pair(t: float, a: float, b: float) -> None:
    left, right = symmetric_values(a, b, t)
    print(f"  t = {t!r}")
    print(f"  a = {a!r}")
    print(f"  b = {b!r}")
    print(f"  lerp(a, b, 1 - (1 - t)) = {left!r}")
    print(f"  lerp(b, a, 1 - t)       = {right!r}")
    print(f"  difference              = {abs(left - right)!r}")
    ulp = float(max(abs(a), abs(b)) * np.finfo(np.float64).eps)
    print(f"  one ULP at this scale   = {ulp!r}")


def show_default_tolerance_failure() -> None:
    left, right = symmetric_values(A, B, T)
    try:
        assert_allclose(left, right)
    except AssertionError as error:
        print("NumPy's default assert_allclose rejects the pair:\n")
        print(str(error).rstrip())
    else:
        raise SystemExit("expected the default tolerance to fail")


def show_scaled_tolerance_fix() -> None:
    left, right = symmetric_values(A, B, T)
    atol = scale_aware_atol(A, B)
    print(f"Scaled tolerance: max(|a|, |b|) * eps * 100 = {float(atol)!r}\n")
    assert_allclose(left, right, atol=atol, rtol=0)
    print("The same pair passes with the scale-aware tolerance.\n")


def show_hypothesis_search() -> None:
    def is_asymmetric(pair: tuple[float, float]) -> bool:
        a, b = pair
        left, right = symmetric_values(a, b, 0.5)
        return not math.isclose(left, right, rel_tol=1e-7, abs_tol=0.0)

    bad = find(
        near_power_of_two(),
        is_asymmetric,
        settings=settings(max_examples=500, database=None, deadline=None),
    )
    print("A custom strategy for the dangerous region finds another pair:\n")
    show_pair(0.5, *bad)


def main() -> None:
    print("NumPy PR #32721: hypothesis-generated symmetry test\n")
    print("The real failing pair from NumPy's CI:\n")
    show_pair(T, A, B)
    print()
    show_default_tolerance_failure()
    print()
    show_scaled_tolerance_fix()
    show_hypothesis_search()
    print(
        "\nWhat Hypothesis found was a bug in the test, not in lerp:\n"
        "  the property (symmetry) is right, but exact equality is the wrong\n"
        "  specification for floating-point code. The tolerance has to scale\n"
        "  with the inputs."
    )


if __name__ == "__main__":
    main()
