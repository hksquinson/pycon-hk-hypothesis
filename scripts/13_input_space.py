"""Reproduce the samples behind the "Visualizing the Input Space" slide.

Run with:
    uv run python scripts/13_input_space.py

The slide's right-hand panel is a real sample from
``st.floats(min_value=0, max_value=100)``, not hand-placed ticks. The script
prints the sampled values and the SVG x coordinates used in ``slides/talk.md``.
Repeated values (notably ``0.0``) collapse onto one tick in the drawing.
"""

from __future__ import annotations

from hypothesis import given, seed, settings
from hypothesis import strategies as st

X0 = 645.0
SCALE = 3.5


def main() -> None:
    values: list[float] = []

    @seed(11)
    @settings(max_examples=48, database=None)
    @given(
        st.floats(
            min_value=0,
            max_value=100,
            allow_nan=False,
            allow_infinity=False,
        )
    )
    def collect(x: float) -> None:
        values.append(x)

    collect()
    values.sort()

    print(f"{len(values)} samples from st.floats(0, 100), seed 11")
    for value in values:
        print(f"{value:8.2f}  x={X0 + SCALE * value:7.1f}")
    positions = {round(X0 + SCALE * value, 1) for value in values}
    print(f"{len(positions)} distinct x positions")


if __name__ == "__main__":
    main()
