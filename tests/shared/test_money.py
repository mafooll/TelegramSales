from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from telegramsales.shared.domain.money import (
    Currency,
    CurrencyMismatchError,
    Money,
    NegativeMoneyError,
)

RUB = Currency.RUB
USD = Currency.USD


def rub(raw: Decimal | int | str) -> Money:
    return Money.from_external(raw, RUB)


def usd(raw: Decimal | int | str) -> Money:
    return Money.from_external(raw, USD)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("10", "10.00"),
        ("10.0", "10.00"),
        ("10.004", "10.00"),
        ("10.005", "10.01"),
        ("10.994", "10.99"),
        ("0", "0.00"),
    ],
)
def test_amount_is_rounded_to_two_places(raw: str, expected: str) -> None:
    assert str(rub(raw)) == expected


def test_amounts_with_different_scale_are_equal() -> None:
    assert rub("10.0") == rub("10.00")


def test_equal_amounts_share_a_hash() -> None:
    assert len({rub(10), rub("10.00")}) == 1


def test_zero_is_a_zero_amount() -> None:
    assert Money.zero(RUB) == rub(0)


def test_from_external_accepts_str_and_int() -> None:
    assert rub("10.5") == rub("10.50")
    assert rub(10) == rub("10.00")


def test_currency_is_carried_on_the_value() -> None:
    assert rub(10).currency is RUB


def test_negative_amount_is_rejected() -> None:
    with pytest.raises(NegativeMoneyError):
        rub("-0.01")


def test_negative_error_carries_the_amount() -> None:
    with pytest.raises(NegativeMoneyError) as exc_info:
        rub(-5)

    assert exc_info.value.details == {"amount": "-5"}


def test_addition() -> None:
    assert rub("10.50") + rub("0.50") == rub(11)


def test_subtraction() -> None:
    assert rub(10) - rub("2.50") == rub("7.50")


def test_subtraction_below_zero_is_rejected() -> None:
    with pytest.raises(NegativeMoneyError):
        _ = rub(1) - rub(2)


def test_multiplication_by_quantity() -> None:
    assert rub(150) * 3 == rub(450)


def test_multiplication_keeps_the_currency() -> None:
    assert (rub(150) * 3).currency is RUB


def test_multiplication_by_a_rate_applies_a_discount() -> None:
    assert rub(7900) * (Decimal(1) - Decimal("0.15")) == rub(6715)


def test_a_fractional_result_is_rounded_to_two_places() -> None:
    assert rub("99.99") * Decimal("0.85") == rub("84.99")


def test_multiplication_by_a_rate_above_one_raises_the_amount() -> None:
    assert rub(100) * Decimal("1.2") == rub(120)


def test_is_immutable() -> None:
    money = rub(10)

    with pytest.raises(FrozenInstanceError):
        money.amount = Decimal(20)  # pyright: ignore[reportAttributeAccessIssue]


def test_addition_keeps_the_currency() -> None:
    assert (rub("10.50") + rub("0.50")).currency is RUB


def test_subtraction_keeps_the_currency() -> None:
    assert (rub(10) - rub("2.50")).currency is RUB


def test_same_amount_in_another_currency_is_a_different_value() -> None:
    assert rub(10) != usd(10)


def test_addition_across_currencies_is_rejected() -> None:
    with pytest.raises(CurrencyMismatchError):
        _ = rub(10) + usd(10)


def test_subtraction_across_currencies_is_rejected() -> None:
    with pytest.raises(CurrencyMismatchError):
        _ = rub(10) - usd(1)


def test_mismatch_error_names_both_currencies() -> None:
    with pytest.raises(CurrencyMismatchError) as exc_info:
        _ = rub(10) + usd(1)

    assert exc_info.value.details == {"left": "RUB", "right": "USD"}


def test_mismatch_is_checked_before_the_amounts() -> None:
    with pytest.raises(CurrencyMismatchError):
        _ = rub(1) - usd(2)
