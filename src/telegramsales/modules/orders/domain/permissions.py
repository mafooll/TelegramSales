from enum import StrEnum


class OrdersPermission(StrEnum):
    VIEW_ORDERS = "orders.view"
    MANAGE_ORDERS = "orders.manage"
