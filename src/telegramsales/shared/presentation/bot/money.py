from collections.abc import Mapping
from decimal import Decimal

from telegramsales.shared.domain.money import Currency, Money

SYMBOLS: Mapping[Currency, str] = {Currency.RUB: "₽", Currency.USD: "$"}
GROUP_SEPARATOR = " "


def money_text(money: Money) -> str:
    rounded = money.amount.to_integral_value()
    digits = 0 if money.amount == rounded else 2
    grouped = f"{money.amount:,.{digits}f}".replace(",", GROUP_SEPARATOR)
    return f"{grouped} {SYMBOLS[money.currency]}"


def parse_amount(raw: str) -> Decimal:
    return Decimal(
        raw.replace(GROUP_SEPARATOR, "").replace(" ", "").replace(",", ".")
    )
