"""The first draft of the ledger transfer, kept for the live demo.

This module deliberately does not satisfy the contract in
:mod:`pycon_hk_hypothesis.account`. The property suite is supposed to find
where it diverges. Same signature as the fixed version, so one property can be
run against both.
"""

from __future__ import annotations

from pycon_hk_hypothesis.account import (
    Account,
    InsufficientFunds,
    InvalidAmount,
    Money,
)


def transfer_balance(src: Account, dest: Account, amt: Money, fee: Money = 0) -> Money:
    """Move ``amt`` cents from ``src`` to ``dest``, burning ``fee``."""
    if amt < 0:
        raise InvalidAmount(f"amount must be non-negative, got {amt}")
    if fee < 0:
        raise InvalidAmount(f"fee must be non-negative, got {fee}")
    if amt > src.balance:
        raise InsufficientFunds(f"{src.account_id} has {src.balance}, needs {amt}")
    src.balance -= amt + fee
    dest.balance += amt
    return src.balance
