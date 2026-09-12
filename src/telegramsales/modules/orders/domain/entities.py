from dataclasses import dataclass, field
from datetime import datetime
from typing import Self

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.contracts import (
    CartItemId,
    OrderId,
    SelectionId,
)
from telegramsales.modules.orders.domain.enums import OrderStatus
from telegramsales.modules.orders.domain.events import OrderCancelled, OrderPlaced
from telegramsales.modules.orders.domain.exceptions import (
    EmptyOrderError,
    EmptySelectionError,
    MixedCurrencyOrderError,
    OrderAlreadyTakenError,
)
from telegramsales.modules.orders.domain.values import (
    Comment,
    OrderNumber,
    ProductRef,
    Quantity,
)
from telegramsales.shared.domain.contacts import Contacts
from telegramsales.shared.domain.entity import DomainEntity
from telegramsales.shared.domain.money import Money
from telegramsales.shared.domain.value_object import DomainValueObject


@dataclass(eq=False, kw_only=True)
class CartItem(DomainEntity[CartItemId]):
    customer_id: CustomerId
    reference: ProductRef
    quantity: Quantity
    added_at: datetime

    @classmethod
    def create(
        cls,
        *,
        item_id: CartItemId,
        customer_id: CustomerId,
        reference: ProductRef,
        quantity: Quantity,
        now: datetime,
    ) -> Self:
        return cls(
            id=item_id,
            customer_id=customer_id,
            reference=reference,
            quantity=quantity,
            added_at=now,
        )

    def add_up(self, quantity: Quantity) -> None:
        self.quantity = self.quantity.plus(quantity)

    def set_quantity(self, quantity: Quantity) -> None:
        self.quantity = quantity


@dataclass(frozen=True)
class SelectionLine(DomainValueObject):
    reference: ProductRef
    title: str
    variant_title: str | None
    quantity: Quantity


@dataclass(eq=False, kw_only=True)
class Selection(DomainEntity[SelectionId]):
    author_id: CustomerId
    created_at: datetime
    lines: tuple[SelectionLine, ...] = ()

    @classmethod
    def create(
        cls,
        *,
        selection_id: SelectionId,
        author_id: CustomerId,
        lines: tuple[SelectionLine, ...],
        now: datetime,
    ) -> Self:
        if not lines:
            raise EmptySelectionError
        return cls(
            id=selection_id,
            author_id=author_id,
            lines=lines,
            created_at=now,
        )


@dataclass(frozen=True)
class OrderLine(DomainValueObject):
    reference: ProductRef
    title: str
    article: str
    variant_title: str | None
    price: Money
    old_price: Money | None
    quantity: Quantity

    @property
    def total(self) -> Money:
        return self.price * self.quantity.value


@dataclass(eq=False, kw_only=True)
class Order(DomainEntity[OrderId]):
    number: OrderNumber
    customer_id: CustomerId
    contacts: Contacts
    comment: Comment
    created_at: datetime
    lines: tuple[OrderLine, ...] = ()
    status: OrderStatus = OrderStatus.PLACED
    total: Money = field(init=False)

    def __post_init__(self) -> None:
        if not self.lines:
            raise EmptyOrderError
        self.total = self._sum_up()

    def _sum_up(self) -> Money:
        currencies = {line.price.currency for line in self.lines}
        if len(currencies) > 1:
            raise MixedCurrencyOrderError
        first, *rest = self.lines
        total = first.total
        for line in rest:
            total = total + line.total
        return total

    @classmethod
    def place(  # noqa: PLR0913
        cls,
        *,
        order_id: OrderId,
        number: OrderNumber,
        customer_id: CustomerId,
        contacts: Contacts,
        comment: Comment,
        lines: tuple[OrderLine, ...],
        now: datetime,
    ) -> Self:
        order = cls(
            id=order_id,
            number=number,
            customer_id=customer_id,
            contacts=contacts,
            comment=comment,
            lines=lines,
            created_at=now,
        )
        order.register_event(
            OrderPlaced(
                order_id=order_id,
                number=number.value,
                customer_id=customer_id,
            )
        )
        return order

    @property
    def is_open(self) -> bool:
        return self.status is OrderStatus.PLACED

    def cancel_by_customer(self) -> None:
        if not self.is_open:
            raise OrderAlreadyTakenError(order_id=self.id, status=self.status)

        self.status = OrderStatus.CANCELLED
        self.register_event(
            OrderCancelled(
                order_id=self.id,
                number=self.number.value,
                customer_id=self.customer_id,
            )
        )
