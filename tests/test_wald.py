"""Tests for the Wald-distribution example.

The stable formula passes the non-negativity property. The regression test
pins the pre-fix formula's failure for a 1-sigma draw.

Run this test with:
    uv run pytest tests/test_wald.py --runxfail -q --tb=short
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st
from numpy.random import MT19937, Generator

from pycon_hk_hypothesis.wald import wald_candidate_old, wald_candidate_stable
from pycon_hk_hypothesis.wald_testing import cancellation_prone, wald_inputs

moderate_inputs = st.tuples(
    st.floats(min_value=1.0, max_value=100.0),
    st.floats(min_value=0.1, max_value=10.0),
    st.floats(min_value=-2.0, max_value=2.0),
)


@given(case=wald_inputs())
def test_stable_candidate_is_nonnegative(case: tuple[float, float, float]) -> None:
    mean, scale, z = case
    assert wald_candidate_stable(mean, scale, z) >= 0.0


@given(case=cancellation_prone())
def test_stable_candidate_is_nonnegative_in_dangerous_region(
    case: tuple[float, float, float],
) -> None:
    mean, scale, z = case
    assert wald_candidate_stable(mean, scale, z) >= 0.0


def test_old_formula_goes_negative_for_a_one_sigma_draw() -> None:
    # mean=1e8, scale=0.1, z=1.0 gives Y=1e8, so Y >> scale.
    mean, scale, z = 1e8, 0.1, 1.0
    old = wald_candidate_old(mean, scale, z)
    stable = wald_candidate_stable(mean, scale, z)

    assert old < 0.0
    assert stable >= 0.0
    # The values documented in docs/wald-example.md.
    assert math.isclose(old, -1.4901161193847656, rel_tol=1e-12)
    assert math.isclose(stable, 0.1000000082740371, rel_tol=1e-12)


def test_zero_draw_returns_mean() -> None:
    # Both formulas special-case Y == 0; keep that branch honest.
    assert wald_candidate_old(2.0, 1.0, 0.0) == 2.0
    assert wald_candidate_stable(2.0, 1.0, 0.0) == 2.0


def test_numpy_wald_snippet_is_nonnegative() -> None:
    # The real `Generator.wald` call from the slide; current NumPy is post-fix.
    random = Generator(MT19937(1234567890))
    samples = random.wald(mean=1e8, scale=2.25, size=1000)
    assert np.all(samples >= 0.0)


@given(wald_inputs())
def test_wald_inputs_use_the_pr_ranges(case: tuple[float, float, float]) -> None:
    mean, scale, _z = case
    assert 1e8 <= mean <= 1e15
    assert 0.1 <= scale <= 10.0


@given(cancellation_prone())
def test_cancellation_prone_is_in_the_dangerous_region(
    case: tuple[float, float, float],
) -> None:
    mean, scale, z = case
    assert mean * z * z > scale


@given(moderate_inputs)
def test_formulas_agree_for_moderate_values(
    case: tuple[float, float, float],
) -> None:
    mean, scale, z = case
    old = wald_candidate_old(mean, scale, z)
    stable = wald_candidate_stable(mean, scale, z)
    assert math.isclose(old, stable, rel_tol=1e-9, abs_tol=1e-9)


@pytest.mark.xfail(strict=True, reason="deliberate bug: the old formula cancels")
@given(cancellation_prone())
def test_old_formula_is_nonnegative(case: tuple[float, float, float]) -> None:
    mean, scale, z = case
    assert wald_candidate_old(mean, scale, z) >= 0.0
