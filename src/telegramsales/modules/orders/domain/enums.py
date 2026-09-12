from collections.abc import Mapping
from enum import StrEnum


class OrderStatus(StrEnum):
    PLACED = "placed"
    IN_WORK = "in_work"
    PAID = "paid"
    SHIPPED = "shipped"
    DONE = "done"
    CANCELLED = "cancelled"


CLOSED_STATUSES = frozenset({OrderStatus.DONE, OrderStatus.CANCELLED})

NEXT_STATUSES: Mapping[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.PLACED: frozenset(),
    OrderStatus.IN_WORK: frozenset(
        {OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DONE}
    ),
    OrderStatus.PAID: frozenset({OrderStatus.SHIPPED, OrderStatus.DONE}),
    OrderStatus.SHIPPED: frozenset({OrderStatus.DONE}),
    OrderStatus.DONE: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}
