from dataclasses import dataclass

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.contracts import OrderId
from telegramsales.shared.domain.event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class OrderPlaced(DomainEvent):
    order_id: OrderId
    number: str
    customer_id: CustomerId


@dataclass(frozen=True, kw_only=True)
class OrderCancelled(DomainEvent):
    order_id: OrderId
    number: str
    customer_id: CustomerId
