from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from telegramsales.shared.domain.money import Money, NegativeMoneyError


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
    assert str(Money(Decimal(raw))) == expected


def test_amounts_with_different_scale_are_equal() -> None:
    assert Money(Decimal("10.0")) == Money(Decimal("10.00"))


def test_equal_amounts_share_a_hash() -> None:
    assert len({Money(Decimal(10)), Money(Decimal("10.00"))}) == 1


def test_zero_is_a_zero_amount() -> None:
    assert Money.zero() == Money(Decimal(0))


def test_from_external_accepts_str_and_int() -> None:
    assert Money.from_external("10.5") == Money(Decimal("10.50"))
    assert Money.from_external(10) == Money(Decimal("10.00"))


def test_negative_amount_is_rejected() -> None:
    with pytest.raises(NegativeMoneyError):
        Money(Decimal("-0.01"))


def test_negative_error_carries_the_amount() -> None:
    with pytest.raises(NegativeMoneyError) as exc_info:
        Money(Decimal(-5))

    assert exc_info.value.details == {"amount": "-5"}


def test_addition() -> None:
    assert Money(Decimal("10.50")) + Money(Decimal("0.50")) == Money(Decimal(11))


def test_subtraction() -> None:
    assert Money(Decimal(10)) - Money(Decimal("2.50")) == Money(Decimal("7.50"))


def test_subtraction_below_zero_is_rejected() -> None:
    with pytest.raises(NegativeMoneyError):
        _ = Money(Decimal(1)) - Money(Decimal(2))


def test_multiplication_by_quantity() -> None:
    assert Money(Decimal(150)) * 3 == Money(Decimal(450))


def test_multiplication_by_a_rate_applies_a_discount() -> None:
    assert Money(Decimal(7900)) * (Decimal(1) - Decimal("0.15")) == Money(
        Decimal(6715)
    )


def test_a_fractional_result_is_rounded_to_two_places() -> None:
    assert Money(Decimal("99.99")) * Decimal("0.85") == Money(Decimal("84.99"))


def test_multiplication_by_a_rate_above_one_raises_the_amount() -> None:
    assert Money(Decimal(100)) * Decimal("1.2") == Money(Decimal(120))


def test_is_immutable() -> None:
    money = Money(Decimal(10))

    with pytest.raises(FrozenInstanceError):
        money.amount = Decimal(20)  # pyright: ignore[reportAttributeAccessIssue]
