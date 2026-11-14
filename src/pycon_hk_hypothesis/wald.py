"""The Wald-distribution candidate, abstracted from NumPy PR #29609.

NumPy's ``random_wald`` first computes a candidate ``X`` from a standard normal
draw ``Z``::

    Y = mean * Z * Z
    X = mean + (mean / (2 * scale)) * (Y - sqrt(4 * scale * Y + Y * Y))

When ``Y`` is large compared with ``scale``, the two terms in the parentheses
nearly cancel, and the result can be negative. The PR replaced the formula with
the algebraically equivalent, numerically stable form::

    d = 1 + sqrt(1 + 4 * scale / Y)
    X = mean * (1 - 2 / d)

The property is simple: a Wald sample must never be negative.

Source: https://github.com/numpy/numpy/pull/29609
"""

from __future__ import annotations

import math


def wald_candidate_old(mean: float, scale: float, z: float) -> float:
    """The pre-fix candidate ``X`` for a standard-normal draw ``z``."""
    y = mean * z * z
    if y == 0.0:
        return mean
    return mean + (mean / (2.0 * scale)) * (y - math.sqrt(4.0 * scale * y + y * y))


def wald_candidate_stable(mean: float, scale: float, z: float) -> float:
    """The post-fix candidate ``X`` for a standard-normal draw ``z``."""
    y = mean * z * z
    if y == 0.0:
        return mean
    d = 1.0 + math.sqrt(1.0 + 4.0 * scale / y)
    return mean * (1.0 - 2.0 / d)
