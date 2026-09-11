from decimal import Decimal

from telegramsales.shared.domain.money import Currency, Money
from telegramsales.shared.presentation.bot.money import (
    STRIKE,
    money_text,
    parse_amount,
    struck_text,
)


def rub(amount: str) -> Money:
    return Money.from_external(amount, Currency.RUB)


def test_a_round_amount_drops_the_kopecks() -> None:
    assert money_text(rub("12900")) == "12 900 ₽"


def test_kopecks_are_kept_when_they_matter() -> None:
    assert money_text(rub("12900.50")) == "12 900.50 ₽"


def test_thousands_are_grouped() -> None:
    assert money_text(rub("1234567")) == "1 234 567 ₽"


def test_the_currency_picks_the_symbol() -> None:
    assert money_text(Money.from_external("10", Currency.USD)) == "10 $"


def test_a_grouped_amount_is_parsed_back() -> None:
    assert parse_amount("12 900") == Decimal(12900)


def test_a_comma_is_read_as_a_decimal_point() -> None:
    assert parse_amount("12900,50") == Decimal("12900.50")


def test_every_character_of_a_struck_price_is_marked() -> None:
    assert struck_text("10") == f"1{STRIKE}0{STRIKE}"


def test_striking_keeps_the_characters_in_order() -> None:
    assert struck_text("12 900 ₽").replace(STRIKE, "") == "12 900 ₽"


def test_striking_nothing_yields_nothing() -> None:
    assert struck_text("") == ""
