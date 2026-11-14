"""A deliberately buggy binary heap, from the Hypothesis blog post.

Source: https://hypothesis.works/articles/rule-based-stateful-testing/

The bug is in ``heappop_buggy``: it pops the root but does not rebalance the
heap, so the next pop can return a larger value than the true minimum.
``heappop_fixed`` sifts the last element down after removing the root.
"""

from __future__ import annotations


def heapnew() -> list[int]:
    """Return a new empty heap."""
    return []


def heapempty(heap: list[int]) -> bool:
    """Return True when the heap has no elements."""
    return not heap


def heappush(heap: list[int], value: int) -> None:
    """Push ``value`` and bubble it up until the heap property holds."""
    heap.append(value)
    index = len(heap) - 1
    while index > 0:
        parent = (index - 1) // 2
        if heap[parent] > heap[index]:
            heap[parent], heap[index] = heap[index], heap[parent]
            index = parent
        else:
            break


def heappop_buggy(heap: list[int]) -> int:
    """The blog post's bug: pop the root without rebalancing."""
    return heap.pop(0)


def heappop_fixed(heap: list[int]) -> int:
    """Pop the root, then sift the last element down into place."""
    if not heap:
        raise ValueError("Empty heap")
    if len(heap) == 1:
        return heap.pop()

    result = heap[0]
    heap[0] = heap.pop()
    index = 0
    while index * 2 + 1 < len(heap):
        children = [index * 2 + 1, index * 2 + 2]
        children = [child for child in children if child < len(heap)]
        children.sort(key=lambda child: heap[child])
        for child in children:
            if heap[index] > heap[child]:
                heap[index], heap[child] = heap[child], heap[index]
                index = child
                break
        else:
            break
    return result
