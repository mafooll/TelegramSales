from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Self, override

from telegramsales.shared.domain.exceptions import DomainError
from telegramsales.shared.domain.value_object import DomainValueObject

MINOR_UNIT = Decimal("0.01")


class Currency(StrEnum):
    RUB = "RUB"
    USD = "USD"


class NegativeMoneyError(DomainError):
    def __init__(self, *, amount: Decimal) -> None:
        super().__init__(
            f"money amount must not be negative, got {amount}",
            details={"amount": str(amount)},
        )


class CurrencyMismatchError(DomainError):
    def __init__(self, *, left: Currency, right: Currency) -> None:
        super().__init__(
            f"cannot combine money in {left} with money in {right}",
            details={"left": left.value, "right": right.value},
        )


@dataclass(frozen=True)
class Money(DomainValueObject):
    amount: Decimal
    currency: Currency

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise NegativeMoneyError(amount=self.amount)
        object.__setattr__(
            self, "amount", self.amount.quantize(MINOR_UNIT, rounding=ROUND_HALF_UP)
        )

    @classmethod
    def zero(cls, currency: Currency) -> Self:
        return cls(Decimal(0), currency)

    @classmethod
    def from_external(cls, value: Decimal | int | str, currency: Currency) -> Self:
        return cls(Decimal(value), currency)

    def _ensure_same_currency(self, other: Self) -> None:
        if self.currency is not other.currency:
            raise CurrencyMismatchError(left=self.currency, right=other.currency)

    def __add__(self, other: Self) -> Self:
        self._ensure_same_currency(other)
        return type(self)(self.amount + other.amount, self.currency)

    def __sub__(self, other: Self) -> Self:
        self._ensure_same_currency(other)
        return type(self)(self.amount - other.amount, self.currency)

    def __mul__(self, factor: int | Decimal) -> Self:
        return type(self)(self.amount * factor, self.currency)

    @override
    def __str__(self) -> str:
        return f"{self.amount:.2f}"
