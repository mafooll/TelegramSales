from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Self, override

from telegramsales.shared.domain.exceptions import DomainError
from telegramsales.shared.domain.value_object import DomainValueObject

MINOR_UNIT = Decimal("0.01")


class NegativeMoneyError(DomainError):
    def __init__(self, *, amount: Decimal) -> None:
        super().__init__(
            f"money amount must not be negative, got {amount}",
            details={"amount": str(amount)},
        )


@dataclass(frozen=True)
class Money(DomainValueObject):
    amount: Decimal

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise NegativeMoneyError(amount=self.amount)
        object.__setattr__(
            self, "amount", self.amount.quantize(MINOR_UNIT, rounding=ROUND_HALF_UP)
        )

    @classmethod
    def zero(cls) -> Self:
        return cls(Decimal(0))

    @classmethod
    def from_external(cls, value: Decimal | int | str) -> Self:
        return cls(Decimal(value))

    def __add__(self, other: Self) -> Self:
        return type(self)(self.amount + other.amount)

    def __sub__(self, other: Self) -> Self:
        return type(self)(self.amount - other.amount)

    def __mul__(self, factor: int | Decimal) -> Self:
        return type(self)(self.amount * factor)

    @override
    def __str__(self) -> str:
        return f"{self.amount:.2f}"
