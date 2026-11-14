"""Linear interpolation, abstracted from NumPy's lerp symmetry test.

NumPy computes ``_lerp(a, b, t)`` with a branch that reduces cancellation::

    diff = b - a
    a + diff * t          if t < 0.5
    b - diff * (1 - t)    otherwise

The property test ``test_linear_interpolation_formula_symmetric`` asserts that
interpolating from ``a`` to ``b`` at ``t`` equals interpolating from ``b`` to
``a`` at ``1 - t``. For huge, nearly opposite values the two sides differ by
about one ULP of the inputs: the midpoint is small relative to the operands, so
the low bits are lost.

NumPy PR #32721 fixed the *test*, not the interpolation: it scaled the absolute
tolerance by ``max(|a|, |b|) * eps * 100``. This module keeps the same shape so
the failure and the fix can be reproduced without NumPy internals.
"""

from __future__ import annotations

import sys

FLOAT_EPS = sys.float_info.epsilon


def lerp(a: float, b: float, t: float) -> float:
    """Interpolate between ``a`` and ``b`` by ``t`` in ``[0, 1]``.

    This mirrors the branch in NumPy's ``_lerp``: compute from the nearer
    endpoint so the subtraction stays small.
    """
    diff = b - a
    if t < 0.5:
        return a + diff * t
    return b - diff * (1 - t)


def symmetric_values(a: float, b: float, t: float) -> tuple[float, float]:
    """Return the two sides of the symmetry property.

    The ``1 - (1 - t)`` form is intentional: it is the form NumPy's test uses
    to avoid giving ``t < 0.5`` extra precision through the subtraction.
    """
    return lerp(a, b, 1 - (1 - t)), lerp(b, a, 1 - t)


def scale_aware_atol(a: float, b: float) -> float:
    """Absolute tolerance scaled to the input magnitude.

    One ULP of the larger input is the natural size of the rounding error in
    the midpoint. The factor of 100 is the margin NumPy chose in PR #32721.
    """
    return max(abs(a), abs(b)) * FLOAT_EPS * 100
