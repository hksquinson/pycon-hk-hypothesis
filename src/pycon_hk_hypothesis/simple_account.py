"""A deliberately small account example for the talk's opening.

This is a standalone teaching example, not the fuller ledger in
:mod:`pycon_hk_hypothesis.account`. It keeps the contract small enough to read
from a slide:

* a deposit or withdrawal changes the balance;
* a transfer moves ``amount`` from the sender to the receiver;
* the fee is burned, so the sender pays ``amount + fee``.

The ``transfer`` function below is the buggy version used in the talk. Its
guard checks ``amount`` but not ``amount + fee``, so a fee larger than the
sender's remaining balance drives the balance negative. ``transfer_fixed`` is
the corrected version.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Account:
    """A cash balance and a small id, for readable counterexamples."""

    id: int
    balance: int = 0

    def deposit(self, funds: int) -> None:
        self.balance += funds

    def withdraw(self, funds: int) -> None:
        if self.balance < funds:
            raise ValueError("Insufficient funds")
        self.balance -= funds


def transfer(src: Account, dst: Account, amount: int, fee: int = 0) -> None:
    """Move ``amount`` from ``src`` to ``dst``, burning ``fee``.

    This is the version shown in the talk. The guard checks ``amount`` but not
    ``amount + fee``; the bug is deliberate.
    """
    if amount < 0 or fee < 0:
        raise ValueError("amount and fee must be non-negative")
    if src.balance < amount:  # bug: the fee is not included
        raise ValueError("Insufficient funds")
    src.balance -= amount + fee
    dst.balance += amount


def transfer_fixed(src: Account, dst: Account, amount: int, fee: int = 0) -> None:
    """The corrected transfer: one guard, one debit, one credit."""
    if amount < 0 or fee < 0:
        raise ValueError("amount and fee must be non-negative")
    src.withdraw(amount + fee)
    dst.deposit(amount)
