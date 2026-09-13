from telegramsales.modules.orders.contracts import CartItemId, OrderId
from telegramsales.modules.orders.domain.enums import OrderStatus
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.shared.domain.exceptions import DomainError


class InvalidQuantityError(DomainError):
    def __init__(self, *, value: int) -> None:
        super().__init__(
            f"quantity must be at least 1, got {value}",
            details={"value": value},
        )


class QuantityTooLargeError(DomainError):
    def __init__(self, *, value: int, limit: int) -> None:
        super().__init__(
            f"quantity {value} is above the limit of {limit}",
            details={"value": value, "limit": limit},
        )


class CommentTooLongError(DomainError):
    def __init__(self, *, length: int, limit: int) -> None:
        super().__init__(
            f"comment is {length} characters long, limit is {limit}",
            details={"length": length, "limit": limit},
        )


class MalformedOrderNumberError(DomainError):
    def __init__(self, *, sequence: int) -> None:
        super().__init__(
            f"order sequence {sequence} is out of range",
            details={"sequence": sequence},
        )


class ItemNotInCartError(DomainError):
    def __init__(self, *, item_id: CartItemId) -> None:
        super().__init__(
            f"cart item {item_id} does not exist",
            details={"item_id": item_id},
        )


class EmptyCartError(DomainError):
    def __init__(self) -> None:
        super().__init__("an empty cart cannot be ordered")


class EmptyOrderError(DomainError):
    def __init__(self) -> None:
        super().__init__("an order must have at least one line")


class EmptySelectionError(DomainError):
    def __init__(self) -> None:
        super().__init__("a shared cart must have at least one line")


class MixedCurrencyOrderError(DomainError):
    def __init__(self) -> None:
        super().__init__("all order lines must share one currency")


class OrderIsClosedError(DomainError):
    def __init__(self, *, order_id: OrderId, status: OrderStatus) -> None:
        super().__init__(
            f"order {order_id} is {status} and accepts no further changes",
            details={"order_id": str(order_id), "status": status},
        )


class OrderAlreadyYoursError(DomainError):
    def __init__(self, *, order_id: OrderId, manager_id: StaffId) -> None:
        super().__init__(
            f"order {order_id} already belongs to manager {manager_id}",
            details={"order_id": str(order_id), "manager_id": manager_id},
        )


class ForbiddenStatusChangeError(DomainError):
    def __init__(
        self,
        *,
        order_id: OrderId,
        status: OrderStatus,
        requested: OrderStatus,
    ) -> None:
        super().__init__(
            f"order {order_id} cannot go from {status} to {requested}",
            details={
                "order_id": str(order_id),
                "status": status,
                "requested": requested,
            },
        )


class OrderAlreadyTakenError(DomainError):
    def __init__(self, *, order_id: OrderId, status: OrderStatus) -> None:
        super().__init__(
            f"order {order_id} is {status} and cannot be cancelled by the customer",
            details={"order_id": str(order_id), "status": status},
        )
