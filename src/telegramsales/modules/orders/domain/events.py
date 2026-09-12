from dataclasses import dataclass

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.contracts import OrderId
from telegramsales.modules.orders.domain.enums import OrderStatus
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.shared.domain.event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class OrderPlaced(DomainEvent):
    order_id: OrderId
    number: str
    customer_id: CustomerId


@dataclass(frozen=True, kw_only=True)
class OrderTaken(DomainEvent):
    order_id: OrderId
    number: str
    customer_id: CustomerId
    manager_id: StaffId


@dataclass(frozen=True, kw_only=True)
class OrderStatusChanged(DomainEvent):
    order_id: OrderId
    number: str
    customer_id: CustomerId
    previous: OrderStatus
    status: OrderStatus


@dataclass(frozen=True, kw_only=True)
class OrderCancelled(DomainEvent):
    order_id: OrderId
    number: str
    customer_id: CustomerId
    manager_id: StaffId | None
