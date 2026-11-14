"""Show the account counterexample by running the property test.

Run with:
    uv run python scripts/10_simple_account.py

The buggy transfer checks ``amount`` but not ``amount + fee``. The property
test fails on ``amount=0, fee=1`` with two empty accounts: the sender ends at
``-1`` and the fee is burned, so conservation and the exact balances still
hold; only non-negativity fails.

The script runs pytest rather than calling ``find`` directly, so the output is
the same failure the audience sees when they run the test suite.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BUGGY = "tests/test_simple_account.py::test_transfer"
FIXED = "tests/test_simple_account.py::test_fixed_transfer"


def run(*args: str) -> int:
    """Run pytest with the given arguments and return its exit code."""
    command = [sys.executable, "-m", "pytest", *args]
    print(f"$ pytest {' '.join(args)}\n", flush=True)
    return subprocess.run(command, cwd=REPO_ROOT, text=True).returncode


def main() -> None:
    print("Simple account: the fee is not checked\n", flush=True)

    print("The buggy transfer fails the property:\n", flush=True)
    # --runxfail ignores the xfail marker, so pytest does not swallow the
    # failure and Hypothesis prints the counterexample it found.
    if run(BUGGY, "--runxfail", "-q", "--tb=short", "--hypothesis-seed=0") == 0:
        raise SystemExit("expected the buggy transfer to fail")

    print("\nThe fixed transfer passes the same property:\n", flush=True)
    if run(FIXED, "-q", "--hypothesis-seed=0") != 0:
        raise SystemExit("expected the fixed transfer to pass")

    print("\nBuggy: FAIL (expected). Fixed: PASS.", flush=True)


if __name__ == "__main__":
    main()
