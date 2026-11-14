"""Property tests for the account ledger.

The fixed implementation must pass. The deliberately buggy transfer is marked
``xfail(strict=True)``: it fails, the marker keeps the suite green, and the
counterexample stays runnable as the demo.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pycon_hk_hypothesis.account import Account, InsufficientFunds, transfer_balance
from pycon_hk_hypothesis.account_buggy import transfer_balance as buggy_transfer

Transfer = Callable[[Account, Account, int, int], int]
Case = tuple[Account, Account, int, int]


@st.composite
def account(draw: st.DrawFn, ident: str) -> Account:
    """Draw an account with a non-negative balance and the given identifier."""
    return Account(account_id=ident, balance=draw(st.integers(0, 1_000), ident))


@st.composite
def transfers(draw: st.DrawFn) -> Case:
    """Draw a transfer: two accounts, an amount, and a fee."""
    return (
        draw(account("src")),
        draw(account("dst")),
        draw(st.integers(0, 1_000), "amt"),
        draw(st.integers(0, 100), "fee"),
    )


def check_transfer(transfer: Transfer, case: Case) -> None:
    """The contract, independent of the implementation under test."""
    src, dst, amt, fee = case
    old_src, old_dst = src.balance, dst.balance

    try:
        transfer(src, dst, amt, fee)
    except InsufficientFunds:
        # Rejected: nothing moved.
        assert src.balance == old_src
        assert dst.balance == old_dst
    else:
        # Accepted: the fee is burned and nothing is created.
        assert src.balance + dst.balance + fee == old_src + old_dst

    # True on both paths.
    assert src.balance >= 0
    assert dst.balance >= 0


@given(transfers())
def test_transfer(case: Case) -> None:
    check_transfer(transfer_balance, case)


@pytest.mark.xfail(strict=True, reason="deliberate bug: the fee is not checked")
@given(transfers())
def test_buggy_transfer_is_caught(case: Case) -> None:
    check_transfer(buggy_transfer, case)
