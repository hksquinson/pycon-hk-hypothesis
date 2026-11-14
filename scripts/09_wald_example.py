"""Reproduce NumPy's negative-Wald-sample bug on an abstracted formula.

Run with:
    uv run python scripts/09_wald_example.py

The property, the old formula, and the stable replacement come from NumPy PR
#29609: https://github.com/numpy/numpy/pull/29609

The PR's Hypothesis test asserted that ``random.wald(mean, scale, size=1000)``
never returns a negative sample. It failed for large ``mean`` and small
``scale``. This script isolates the numerical core: the candidate computed from
one standard-normal draw, before the acceptance step.
"""

from __future__ import annotations

from hypothesis import find, settings

from pycon_hk_hypothesis.wald import wald_candidate_old, wald_candidate_stable
from pycon_hk_hypothesis.wald_testing import wald_inputs

# A 1-sigma draw with a large mean and a small scale: Y = mean * z**2 = 1e8,
# so Y >> scale and the subtraction in the old formula cancels.
MEAN, SCALE, Z = 1e8, 0.1, 1.0


def show_case(mean: float, scale: float, z: float) -> None:
    y = mean * z * z
    old = wald_candidate_old(mean, scale, z)
    stable = wald_candidate_stable(mean, scale, z)
    print(f"  mean  = {mean!r}")
    print(f"  scale = {scale!r}")
    print(f"  z     = {z!r}   (Y = mean * z**2 = {y!r})")
    print(f"  old formula    = {old!r}")
    print(f"  stable formula = {stable!r}")


def main() -> None:
    print("NumPy PR #29609: Hypothesis found negative Wald samples\n")
    print("The pre-fix formula (NumPy's random_wald, before acceptance):\n")
    print("  Y = mean * z**2")
    print("  X = mean + (mean / (2 * scale)) * (Y - sqrt(4 * scale * Y + Y * Y))\n")

    print("A simple failing case:\n")
    show_case(MEAN, SCALE, Z)
    print()

    bad = find(
        wald_inputs(),
        lambda case: wald_candidate_old(*case) < 0.0,
        settings=settings(max_examples=5000, database=None, deadline=None, derandomize=True),
    )
    print("Hypothesis shrinks the old formula's failure to:\n")
    show_case(*bad)
    print()

    print("The stable formula from the PR:\n")
    print("  d = 1 + sqrt(1 + 4 * scale / Y)")
    print("  X = mean * (1 - 2 / d)\n")
    print("For the same three cases, the stable candidate is non-negative.\n")

    # The property that failed in NumPy, restricted to the candidate formula.
    for case in [(MEAN, SCALE, Z), bad]:
        mean, scale, z = case
        assert wald_candidate_stable(mean, scale, z) >= 0.0
    print("Property on the stable formula: all candidates >= 0. PASS")
    print(
        "\nThis is a code bug, not a test-tolerance bug: the old formula loses\n"
        "precision when Y >> scale, and the fix changes the computation itself."
    )


if __name__ == "__main__":
    main()
