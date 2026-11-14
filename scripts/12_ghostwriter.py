"""Run ``hypothesis write`` on the demo module and return the generated test.

Run with:
    uv run python scripts/12_ghostwriter.py

The generated test is printed and saved to
``scratchpad/ghostwriter_generated_test.py`` so it can be inspected or copied
into the test suite after review.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

TARGETS = [
    "pycon_hk_hypothesis.ghostwriter_demo.encode",
    "pycon_hk_hypothesis.ghostwriter_demo.decode",
]
OUTPUT = Path("scratchpad/ghostwriter_generated_test.py")


def main() -> None:
    command = ["hypothesis", "write", *TARGETS, "--roundtrip"]
    print("$", " ".join(command), "\n")

    result = subprocess.run(command, capture_output=True, text=True, check=True)
    print(result.stdout)

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(result.stdout)
    print(f"Saved to {OUTPUT}")


if __name__ == "__main__":
    main()
