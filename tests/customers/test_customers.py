from datetime import UTC, datetime

import pytest

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.customers.domain.entities import Customer
from telegramsales.modules.customers.domain.exceptions import (
    CustomerBlockedError,
)
from telegramsales.modules.customers.domain.values import (
    MAX_DISPLAY_NAME_LENGTH,
    UNKNOWN_NAME,
    DisplayName,
)
from telegramsales.shared.domain.contacts import (
    Address,
    Contacts,
    PersonName,
    Phone,
)

NOW = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
BUYER = CustomerId(1000)


def make_customer(name: str = "Иван Петров") -> Customer:
    return Customer.create(
        customer_id=BUYER,
        name=DisplayName(name),
        now=NOW,
    )


def make_contacts() -> Contacts:
    return Contacts(
        name=PersonName("Иван Петров"),
        phone=Phone("+79991234567"),
        address=Address("Москва, Тверская 1"),
    )


def test_a_display_name_collapses_spaces() -> None:
    assert DisplayName("  Иван   Петров ").value == "Иван Петров"


def test_a_nameless_profile_gets_a_stand_in() -> None:
    assert DisplayName("   ").value == UNKNOWN_NAME


def test_a_long_display_name_is_cut_instead_of_rejected() -> None:
    name = DisplayName("я" * (MAX_DISPLAY_NAME_LENGTH + 10))

    assert len(name.value) == MAX_DISPLAY_NAME_LENGTH


def test_a_new_customer_has_no_contacts() -> None:
    assert make_customer().contacts is None


def test_a_new_customer_is_not_blocked() -> None:
    assert not make_customer().is_blocked


def test_a_customer_can_be_renamed() -> None:
    customer = make_customer()

    customer.rename(DisplayName("Пётр"))

    assert customer.name == DisplayName("Пётр")


def test_contacts_are_remembered() -> None:
    customer = make_customer()

    customer.remember(make_contacts())

    assert customer.contacts == make_contacts()


def test_a_customer_may_order_by_default() -> None:
    make_customer().ensure_can_order()


def test_a_blocked_customer_may_not_order() -> None:
    customer = make_customer()
    customer.block()

    with pytest.raises(CustomerBlockedError):
        customer.ensure_can_order()


def test_a_block_can_be_lifted() -> None:
    customer = make_customer()
    customer.block()

    customer.unblock()

    customer.ensure_can_order()
