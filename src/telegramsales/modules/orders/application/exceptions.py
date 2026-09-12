from telegramsales.modules.catalog.contracts import ProductId
from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.contracts import OrderId, SelectionId
from telegramsales.shared.domain.exceptions import ApplicationError


class ProductNotOfferedError(ApplicationError):
    def __init__(self, *, product_id: ProductId) -> None:
        super().__init__(
            f"product {product_id} is not on offer",
            details={"product_id": str(product_id)},
        )


class CartHasUnavailableLinesError(ApplicationError):
    def __init__(self, *, lines: int) -> None:
        super().__init__(
            f"{lines} cart lines are not on offer",
            details={"lines": lines},
        )


class OrderNotFoundError(ApplicationError):
    def __init__(self, *, order_id: OrderId) -> None:
        super().__init__(
            f"order {order_id} does not exist",
            details={"order_id": str(order_id)},
        )


class SelectionNotFoundError(ApplicationError):
    def __init__(self, *, selection_id: SelectionId) -> None:
        super().__init__(
            f"selection {selection_id} does not exist",
            details={"selection_id": str(selection_id)},
        )


class CustomerCannotOrderError(ApplicationError):
    def __init__(self, *, customer_id: CustomerId) -> None:
        super().__init__(
            f"customer {customer_id} is not allowed to place orders",
            details={"customer_id": customer_id},
        )
