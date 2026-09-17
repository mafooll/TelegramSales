from telegramsales.modules.orders.domain.exceptions import EmptyCartError
from telegramsales.modules.orders.domain.values import MAX_QUANTITY, Quantity


def ensure_cart_is_not_empty(lines: int) -> None:
    if lines == 0:
        raise EmptyCartError


def capped_quantity(current: Quantity, added: Quantity) -> Quantity:
    return Quantity(min(current.value + added.value, MAX_QUANTITY))
