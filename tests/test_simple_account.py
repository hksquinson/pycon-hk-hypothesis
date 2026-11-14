"""Tests for the standalone account example used in the talk's opening.

The fixed transfer passes. The deliberately buggy transfer is marked
``xfail(strict=True)``: the property fails, the marker keeps the suite green,
and the counterexample stays runnable as the demo.
"""

from __future__ import annotations

import copy

import pytest
from hypothesis import find, given, settings

from pycon_hk_hypothesis.simple_account import Account, transfer, transfer_fixed
from pycon_hk_hypothesis.simple_account_testing import Case, check_transfer, transfers


def test_slide_example_transfer() -> None:
    """The hand-written example test from the "Testing" slide."""
    a = Account(1, 100)
    b = Account(2)
    transfer(a, b, 50)
    assert a.balance == 50
    assert b.balance == 50


def test_deposit_and_withdraw() -> None:
    account = Account(7)
    account.deposit(10)
    assert account.balance == 10
    account.withdraw(4)
    assert account.balance == 6
    with pytest.raises(ValueError, match="Insufficient funds"):
        account.withdraw(7)
    assert account.balance == 6


@pytest.mark.parametrize(
    ("start", "amount", "expected"),
    [
        (0, 0, 0),  # withdraw zero
        (10, 0, 10),  # withdraw zero from a funded account
        (10, 10, 0),  # withdraw the full balance
        (10, 11, None),  # withdraw more than the balance
    ],
)
def test_withdraw_boundaries(start: int, amount: int, expected: int | None) -> None:
    """A short table of known cases is clearer than a property."""
    account = Account(1, start)
    if expected is None:
        with pytest.raises(ValueError, match="Insufficient funds"):
            account.withdraw(amount)
        assert account.balance == start
    else:
        account.withdraw(amount)
        assert account.balance == expected


def test_fixed_transfer_rejects_the_shrunk_case() -> None:
    src, dst = Account(0), Account(1)
    with pytest.raises(ValueError, match="Insufficient funds"):
        transfer_fixed(src, dst, 0, 1)
    assert (src.balance, dst.balance) == (0, 0)


def test_buggy_transfer_on_the_slide_case_goes_negative() -> None:
    src, dst = Account(0), Account(1)
    transfer(src, dst, 0, 1)
    assert (src.balance, dst.balance) == (-1, 0)


@given(transfers())
def test_fixed_transfer(case: Case) -> None:
    check_transfer(transfer_fixed, case)


@pytest.mark.xfail(strict=True, reason="deliberate bug: the fee is not checked")
@given(transfers())
def test_transfer(case: Case) -> None:
    check_transfer(transfer, case)


def violates(case: Case) -> bool:
    """Return True when the buggy transfer produces a negative balance."""
    src, dst, amount, fee = copy.deepcopy(case)
    try:
        transfer(src, dst, amount, fee)
    except ValueError:
        return False
    return src.balance < 0 or dst.balance < 0


def test_buggy_transfer_shrinks_to_the_slide_counterexample() -> None:
    case = find(
        transfers(),
        violates,
        settings=settings(max_examples=2_000, database=None, derandomize=True),
    )
    src, dst, amount, fee = case
    assert (src.balance, dst.balance, amount, fee) == (0, 0, 0, 1)
