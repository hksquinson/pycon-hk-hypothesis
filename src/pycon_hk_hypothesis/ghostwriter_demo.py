"""A tiny module for the Ghostwriter demo.

The functions are deliberately simple: ``hypothesis write --roundtrip`` can
infer that ``decode`` inverts ``encode`` and generate the property test.
"""

from __future__ import annotations


def encode(text: str) -> bytes:
    """Encode text as UTF-8 bytes."""
    return text.encode("utf-8")


def decode(data: bytes) -> str:
    """Decode UTF-8 bytes back to text."""
    return data.decode("utf-8")
