from dataclasses import dataclass
from datetime import date
from typing import Self, override

from telegramsales.modules.catalog.contracts import ProductId, VariantId
from telegramsales.modules.orders.domain.exceptions import (
    CommentTooLongError,
    InvalidQuantityError,
    MalformedOrderNumberError,
    QuantityTooLargeError,
)
from telegramsales.shared.domain.value_object import DomainValueObject

MIN_QUANTITY = 1
MAX_QUANTITY = 99
MAX_COMMENT_LENGTH = 512
SEQUENCE_DIGITS = 4
MAX_SEQUENCE = 9999


@dataclass(frozen=True)
class Quantity(DomainValueObject):
    value: int

    def __post_init__(self) -> None:
        if self.value < MIN_QUANTITY:
            raise InvalidQuantityError(value=self.value)
        if self.value > MAX_QUANTITY:
            raise QuantityTooLargeError(value=self.value, limit=MAX_QUANTITY)

    @classmethod
    def one(cls) -> Self:
        return cls(MIN_QUANTITY)

    def plus(self, other: Self) -> Self:
        return type(self)(self.value + other.value)

    def increased(self) -> Self:
        return type(self)(self.value + MIN_QUANTITY)

    def decreased(self) -> Self:
        return type(self)(self.value - MIN_QUANTITY)

    @property
    def is_lowest(self) -> bool:
        return self.value == MIN_QUANTITY

    @property
    def is_highest(self) -> bool:
        return self.value == MAX_QUANTITY

    @override
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Comment(DomainValueObject):
    value: str

    def __post_init__(self) -> None:
        trimmed = self.value.strip()
        if len(trimmed) > MAX_COMMENT_LENGTH:
            raise CommentTooLongError(
                length=len(trimmed),
                limit=MAX_COMMENT_LENGTH,
            )
        object.__setattr__(self, "value", trimmed)

    @property
    def is_empty(self) -> bool:
        return not self.value

    @override
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ProductRef(DomainValueObject):
    product_id: ProductId
    variant_id: VariantId | None = None


@dataclass(frozen=True)
class OrderNumber(DomainValueObject):
    day: date
    sequence: int

    def __post_init__(self) -> None:
        if not MIN_QUANTITY <= self.sequence <= MAX_SEQUENCE:
            raise MalformedOrderNumberError(sequence=self.sequence)

    @property
    def value(self) -> str:
        return f"{self.day:%Y-%m-%d}-{self.sequence:0{SEQUENCE_DIGITS}d}"

    @override
    def __str__(self) -> str:
        return self.value
