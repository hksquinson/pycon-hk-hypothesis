"""Show the heap state machine's counterexample.

Run with:
    uv run python scripts/11_heap_stateful.py

The buggy pop removes the root without rebalancing. Hypothesis shrinks the
failure to a five-step program: push 0, push 1, push 0, pop, pop. The second
pop returns 1 while 0 is still in the heap.

Source: https://hypothesis.works/articles/rule-based-stateful-testing/
"""

from __future__ import annotations

from hypothesis import settings
from hypothesis.stateful import run_state_machine_as_test

from pycon_hk_hypothesis.heap_testing import FixedHeapMachine, HeapMachine

SETTINGS = settings(
    max_examples=50,
    stateful_step_count=20,
    database=None,
    derandomize=True,
)


def main() -> None:
    print("Heap state machine: the buggy pop does not rebalance\n")

    try:
        run_state_machine_as_test(HeapMachine, settings=SETTINGS)
    except AssertionError as exc:
        print("Hypothesis found:\n")
        notes = getattr(exc, "__notes__", None)
        print("\n".join(notes) if notes else str(exc))
    else:
        print("No failure found (unexpected).")

    print("\nFixed pop on the same machine:\n")
    run_state_machine_as_test(FixedHeapMachine, settings=SETTINGS)
    print("PASS")


if __name__ == "__main__":
    main()
