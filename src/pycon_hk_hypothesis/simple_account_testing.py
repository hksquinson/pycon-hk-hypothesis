"""Strategies and the contract for the standalone account example.

The strategy is shared by the property test and the demo script so the slide,
the test, and the printed shrink all describe the same inputs.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from hypothesis import strategies as st

from pycon_hk_hypothesis.simple_account import Account

Transfer = Callable[[Account, Account, int, int], None]
Case = tuple[Account, Account, int, int]


@st.composite
def transfers(draw: st.DrawFn) -> Case:
    """Draw two accounts, an amount, and a fee.

    Amounts and fees include negative values so the property also exercises
    the validation branch. The fee bug still shrinks to ``amount=0, fee=1``.
    """
    return (
        Account(0, draw(st.integers(0, 1_000), "src_balance")),
        Account(1, draw(st.integers(0, 1_000), "dst_balance")),
        draw(st.integers(-1_000, 1_000), "amount"),
        draw(st.integers(-100, 100), "fee"),
    )


def check_transfer(fn: Transfer, case: Case) -> None:
    """The contract, independent of the implementation under test."""
    src, dst, amount, fee = case
    old_src, old_dst = src.balance, dst.balance

    if amount < 0 or fee < 0:
        # Invalid input: reject it and leave both balances alone.
        with pytest.raises(ValueError):
            fn(src, dst, amount, fee)
        assert src.balance == old_src
        assert dst.balance == old_dst
    else:
        try:
            fn(src, dst, amount, fee)
        except ValueError:
            # A rejection is only allowed when the sender cannot pay.
            assert src.balance < amount + fee
        else:
            # Accepted: the sender pays the amount and the fee; the receiver
            # gets the amount.
            assert src.balance == old_src - amount - fee
            assert dst.balance == old_dst + amount

    # The property that catches the fee bug: no transfer may overdraw.
    assert src.balance >= 0
    assert dst.balance >= 0
