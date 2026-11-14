"""Stateful test for the heap example from the Hypothesis blog post.

The blog post's counterexample is:

    Step #1: push(value=1)
    Step #2: push(value=0)
    Step #3: push(value=0)
    Step #4: pop()
    Step #5: pop()

The second pop returns 1, but the heap still contains 0.

Source: https://hypothesis.works/articles/rule-based-stateful-testing/
"""

from __future__ import annotations

import pytest
from hypothesis import settings
from hypothesis.stateful import run_state_machine_as_test

from pycon_hk_hypothesis.heap import heapnew, heappop_buggy, heappop_fixed, heappush
from pycon_hk_hypothesis.heap_testing import FixedHeapMachine, HeapMachine

STATE_MACHINE_SETTINGS = settings(
    max_examples=50,
    stateful_step_count=20,
    database=None,
    derandomize=True,
)


def test_blog_counterexample_is_a_program() -> None:
    """The exact sequence from the blog post still fails on the buggy pop."""
    heap = heapnew()
    heappush(heap, 1)
    heappush(heap, 0)
    heappush(heap, 0)

    assert heappop_buggy(heap) == 0
    assert min(heap) == 0
    assert heappop_buggy(heap) == 1  # the bug: the next minimum is still 0


def test_fixed_heap_pops_in_sorted_order() -> None:
    heap = heapnew()
    for value in [1, 0, 0]:
        heappush(heap, value)

    popped = [heappop_fixed(heap), heappop_fixed(heap), heappop_fixed(heap)]
    assert popped == [0, 0, 1]


@pytest.mark.xfail(strict=True, reason="deliberate bug: heappop does not rebalance")
def test_buggy_heap_is_caught() -> None:
    run_state_machine_as_test(HeapMachine, settings=STATE_MACHINE_SETTINGS)


def test_fixed_heap_passes() -> None:
    run_state_machine_as_test(FixedHeapMachine, settings=STATE_MACHINE_SETTINGS)
