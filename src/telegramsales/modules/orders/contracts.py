from abc import ABC, abstractmethod
from typing import NewType
from uuid import UUID

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.domain.enums import OrderStatus
from telegramsales.shared.application.access import Actor

CartItemId = NewType("CartItemId", int)
OrderId = NewType("OrderId", UUID)
SelectionId = NewType("SelectionId", UUID)

__all__ = [
    "CartItemId",
    "IOrderDesk",
    "IOrderPresence",
    "OrderId",
    "OrderStatus",
    "SelectionId",
]


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
