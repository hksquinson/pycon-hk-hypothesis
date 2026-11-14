"""Rule-based state machine for the heap example from the Hypothesis blog.

Source: https://hypothesis.works/articles/rule-based-stateful-testing/

``HeapMachine`` uses the blog post's buggy pop; ``FixedHeapMachine`` swaps in
the rebalancing implementation. The state machine is shared by the test and
the demo script.
"""

from __future__ import annotations

from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, precondition, rule

from pycon_hk_hypothesis.heap import heappop_buggy, heappop_fixed, heappush


class HeapMachine(RuleBasedStateMachine):
    """Push and pop, checking every pop against the true minimum."""

    pop_impl = staticmethod(heappop_buggy)

    def __init__(self) -> None:
        super().__init__()
        self.heap: list[int] = []

    @rule(value=st.integers())
    def push(self, value: int) -> None:
        heappush(self.heap, value)

    @precondition(lambda self: self.heap)
    @rule()
    def pop(self) -> None:
        correct = min(self.heap)
        result = self.pop_impl(self.heap)
        assert correct == result


class FixedHeapMachine(HeapMachine):
    """The same machine with the rebalancing pop."""

    pop_impl = staticmethod(heappop_fixed)
