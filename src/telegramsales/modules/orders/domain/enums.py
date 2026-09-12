from enum import StrEnum


class OrderStatus(StrEnum):
    PLACED = "placed"
    IN_WORK = "in_work"
    PAID = "paid"
    SHIPPED = "shipped"
    DONE = "done"
    CANCELLED = "cancelled"
