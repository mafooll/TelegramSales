from decimal import Decimal

from telegramsales.modules.catalog.domain.exceptions import (
    NonPositivePriceError,
    PriceNotDiscountedError,
)
from telegramsales.shared.domain.money import Currency, Money

FREE = Decimal(0)
SHOP_CURRENCY = Currency.USD


def ensure_positive_price(price: Money) -> None:
    if price.amount <= FREE:
        raise NonPositivePriceError


def ensure_sellable_price(price: Money, old_price: Money | None) -> None:
    ensure_positive_price(price)
    if old_price is not None and old_price.amount <= price.amount:
        raise PriceNotDiscountedError(price=price, old_price=old_price)
