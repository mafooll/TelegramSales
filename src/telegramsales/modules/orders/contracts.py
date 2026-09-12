from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import NewType
from uuid import UUID

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.domain.enums import (
    CLOSED_STATUSES,
    NEXT_STATUSES,
    OrderStatus,
)
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.shared.application.access import Actor
from telegramsales.shared.domain.money import Money

CartItemId = NewType("CartItemId", int)
OrderId = NewType("OrderId", UUID)
SelectionId = NewType("SelectionId", UUID)

__all__ = [
    "CLOSED_STATUSES",
    "NEXT_STATUSES",
    "CartItemId",
    "IOrderCards",
    "IOrderDesk",
    "IOrderPresence",
    "OrderCardLine",
    "OrderCardView",
    "OrderId",
    "OrderStatus",
    "SelectionId",
]


@dataclass(frozen=True, slots=True)
class OrderCardLine:
    title: str
    article: str
    variant_title: str | None
    quantity: int
    price: Money
    total: Money


@dataclass(frozen=True, slots=True)
class OrderCardView:
    id: OrderId
    number: str
    status: OrderStatus
    created_at: datetime
    customer_id: CustomerId
    manager_id: StaffId | None
    name: str
    phone: str
    address: str
    comment: str
    lines: tuple[OrderCardLine, ...]
    total: Money

    @property
    def is_taken(self) -> bool:
        return self.manager_id is not None

    @property
    def is_closed(self) -> bool:
        return self.status in CLOSED_STATUSES

    def can_become(self, status: OrderStatus) -> bool:
        return status in NEXT_STATUSES[self.status]


class IOrderCards(ABC):
    @abstractmethod
    async def card(self, order_id: OrderId) -> OrderCardView | None: ...


class IOrderPresence(ABC):
    @abstractmethod
    async def has_orders(self, customer_id: CustomerId) -> bool: ...


class IOrderDesk(ABC):
    @abstractmethod
    async def take_in_work(self, order_id: OrderId, actor: Actor) -> None: ...

    @abstractmethod
    async def change_status(
        self,
        order_id: OrderId,
        status: OrderStatus,
        actor: Actor,
    ) -> None: ...

    @abstractmethod
    async def cancel(self, order_id: OrderId, actor: Actor) -> None: ...
