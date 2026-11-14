"""Tests for the Ghostwriter demo module.

The generated test from `scripts/12_ghostwriter.py` is the same property:
decode(encode(text)) == text.
"""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from pycon_hk_hypothesis.ghostwriter_demo import decode, encode


@given(st.text())
def test_decode_inverts_encode(text: str) -> None:
    assert decode(encode(text)) == text
