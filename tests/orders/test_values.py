from datetime import date

import pytest

from telegramsales.modules.orders.domain.exceptions import (
    CommentTooLongError,
    InvalidQuantityError,
    MalformedOrderNumberError,
    QuantityTooLargeError,
)
from telegramsales.modules.orders.domain.values import (
    MAX_COMMENT_LENGTH,
    MAX_QUANTITY,
    Comment,
    OrderNumber,
    Quantity,
)


def test_one_is_the_smallest_quantity() -> None:
    assert Quantity.one().value == 1


@pytest.mark.parametrize("value", [0, -1])
def test_a_quantity_below_one_is_rejected(value: int) -> None:
    with pytest.raises(InvalidQuantityError):
        Quantity(value)


def test_a_quantity_above_the_limit_is_rejected() -> None:
    with pytest.raises(QuantityTooLargeError):
        Quantity(MAX_QUANTITY + 1)


def test_quantities_add_up() -> None:
    assert Quantity(2).plus(Quantity(3)) == Quantity(5)


def test_adding_above_the_limit_is_rejected() -> None:
    with pytest.raises(QuantityTooLargeError):
        Quantity(MAX_QUANTITY).plus(Quantity.one())


def test_a_quantity_can_step_up() -> None:
    assert Quantity(2).increased() == Quantity(3)


def test_a_quantity_can_step_down() -> None:
    assert Quantity(2).decreased() == Quantity(1)


def test_stepping_below_one_is_rejected() -> None:
    with pytest.raises(InvalidQuantityError):
        Quantity.one().decreased()


def test_the_lowest_quantity_knows_it() -> None:
    assert Quantity.one().is_lowest


def test_the_highest_quantity_knows_it() -> None:
    assert Quantity(MAX_QUANTITY).is_highest


def test_an_empty_comment_is_allowed() -> None:
    assert Comment("   ").is_empty


def test_a_comment_is_trimmed() -> None:
    assert Comment("  позвоните заранее ").value == "позвоните заранее"


def test_a_long_comment_is_rejected() -> None:
    with pytest.raises(CommentTooLongError):
        Comment("я" * (MAX_COMMENT_LENGTH + 1))


def test_an_order_number_reads_as_date_and_counter() -> None:
    number = OrderNumber(day=date(2026, 9, 11), sequence=7)

    assert number.value == "2026-09-11-0007"


def test_an_order_number_pads_the_counter() -> None:
    assert OrderNumber(day=date(2026, 1, 2), sequence=1234).value == (
        "2026-01-02-1234"
    )


@pytest.mark.parametrize("sequence", [0, 10000])
def test_an_out_of_range_counter_is_rejected(sequence: int) -> None:
    with pytest.raises(MalformedOrderNumberError):
        OrderNumber(day=date(2026, 9, 11), sequence=sequence)
