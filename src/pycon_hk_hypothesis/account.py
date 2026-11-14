"""A small account ledger: the talk's hands-on example.

Money is an integer number of cents. ``Account`` is mutable, so every property
test should build a fresh account inside the test body.

The specification lives here, because the tests are the contract:

* Every operation either completes or raises without changing any account.
* ``buy`` and ``sell`` require a positive quantity and a non-negative price.
* A transfer fee is **burned**: the sender pays ``amount + fee``, the receiver
  receives ``amount``, and the total across accounts drops by ``fee``.
* Balances and asset holdings never go negative.
* A zero holding is stored as no entry, so two accounts with the same balance
  and holdings compare equal.
"""

from __future__ import annotations

from dataclasses import dataclass, field

Money = int
Asset = str


class BankError(Exception):
    """Base class for ledger errors."""


class InvalidAmount(BankError):
    """An amount, price, quantity, or fee is outside its allowed range."""


class InsufficientFunds(BankError):
    """The account cannot cover the requested debit."""


class InsufficientAssets(BankError):
    """The account does not hold enough of the requested asset."""


def _require_non_negative(value: int, name: str) -> None:
    if value < 0:
        raise InvalidAmount(f"{name} must be non-negative, got {value}")


def _require_positive(value: int, name: str) -> None:
    if value <= 0:
        raise InvalidAmount(f"{name} must be positive, got {value}")


@dataclass
class Account:
    """A cash balance plus a holding per asset."""

    account_id: str
    balance: Money = 0
    assets: dict[Asset, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Reject invalid initial state and canonicalise zero holdings."""
        _require_non_negative(self.balance, "balance")
        for asset, qty in self.assets.items():
            _require_non_negative(qty, f"holding of {asset}")
        self.assets = {asset: qty for asset, qty in self.assets.items() if qty != 0}

    def add_balance(self, amt: Money) -> None:
        """Credit ``amt`` cents."""
        _require_non_negative(amt, "amount")
        self.balance += amt

    def subtract_balance(self, amt: Money) -> None:
        """Debit ``amt`` cents, or raise without touching the account."""
        _require_non_negative(amt, "amount")
        if amt > self.balance:
            raise InsufficientFunds(f"{self.account_id} has {self.balance}, needs {amt}")
        self.balance -= amt

    def add_asset(self, asset: Asset, qty: int) -> None:
        """Add ``qty`` units of ``asset``; adding zero changes nothing."""
        _require_non_negative(qty, "quantity")
        if qty == 0:
            return
        self.assets[asset] = self.assets.get(asset, 0) + qty

    def subtract_asset(self, asset: Asset, qty: int) -> None:
        """Remove ``qty`` units of ``asset``, or raise without touching it."""
        _require_non_negative(qty, "quantity")
        if qty == 0:
            return
        held = self.assets.get(asset, 0)
        if held < qty:
            raise InsufficientAssets(f"{self.account_id} holds {held} {asset}, needs {qty}")
        remaining = held - qty
        if remaining == 0:
            self.assets.pop(asset, None)
        else:
            self.assets[asset] = remaining

    def buy(self, asset: Asset, price: Money, qty: int) -> Money:
        """Buy ``qty`` units at ``price`` cents each and return the new balance."""
        _require_positive(qty, "quantity")
        _require_non_negative(price, "price")
        self.subtract_balance(price * qty)
        self.add_asset(asset, qty)
        return self.balance

    def sell(self, asset: Asset, price: Money, qty: int) -> Money:
        """Sell ``qty`` units at ``price`` cents each and return the new balance."""
        _require_positive(qty, "quantity")
        _require_non_negative(price, "price")
        self.subtract_asset(asset, qty)
        self.add_balance(price * qty)
        return self.balance


def transfer_balance(src: Account, dest: Account, amt: Money, fee: Money = 0) -> Money:
    """Move ``amt`` cents from ``src`` to ``dest``, burning ``fee``.

    The debit happens first, so a rejected transfer leaves both accounts
    untouched. Returns the sender's new balance.
    """
    _require_non_negative(amt, "amount")
    _require_non_negative(fee, "fee")
    src.subtract_balance(amt + fee)
    dest.add_balance(amt)
    return src.balance


def transfer_assets(
    src: Account,
    dest: Account,
    asset: Asset,
    qty: int,
    fee: Money = 0,
) -> Money:
    """Move ``qty`` units of ``asset`` from ``src`` to ``dest``, burning ``fee``.

    Both preconditions are checked before either account is touched. Returns
    the sender's new cash balance.
    """
    _require_positive(qty, "quantity")
    _require_non_negative(fee, "fee")
    # Check before moving anything: subtract_balance() below must never be the
    # call that fails after the asset has already changed hands.
    if fee > src.balance:
        raise InsufficientFunds(f"{src.account_id} has {src.balance}, needs {fee}")
    src.subtract_asset(asset, qty)
    dest.add_asset(asset, qty)
    src.subtract_balance(fee)
    return src.balance
