from datetime import datetime
from typing import override

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.customers.application.commands.customers import (
    RegisterCustomerHandler,
)
from telegramsales.modules.customers.application.directory import (
    CustomerDirectory,
)
from telegramsales.modules.customers.contracts import (
    ContactsSnapshot,
    CustomerId,
)
from telegramsales.modules.customers.domain.values import DisplayName
from telegramsales.modules.customers.infrastructure.repositories import (
    CustomerRepository,
)
from telegramsales.modules.customers.infrastructure.uow import (
    CustomerUnitOfWork,
)
from telegramsales.shared.application.clock import IClock
from telegramsales.shared.infrastructure.database.uow import SessionFactory
from tests.customers.test_customers import NOW, make_contacts, make_customer

pytestmark = pytest.mark.db

BUYER = CustomerId(80001)


class FixedClock(IClock):
    @override
    def now(self) -> datetime:
        return NOW


CLOCK = FixedClock()


def directory_with(session_factory: SessionFactory) -> CustomerDirectory:
    uow = CustomerUnitOfWork(session_factory)
    return CustomerDirectory(uow, CLOCK, RegisterCustomerHandler(uow, CLOCK))


def snapshot() -> ContactsSnapshot:
    return ContactsSnapshot(
        name="Иван Петров",
        phone="+79991234567",
        address="Москва, Тверская 1",
    )


async def test_a_customer_survives_a_round_trip(session: AsyncSession) -> None:
    repository = CustomerRepository(session)
    stored = make_customer()
    stored.remember(make_contacts())
    await repository.add(stored)

    loaded = await repository.get(stored.id)

    assert loaded is not None
    assert loaded.name == DisplayName("Иван Петров")
    assert loaded.contacts == make_contacts()


async def test_a_customer_without_contacts_round_trips(
    session: AsyncSession,
) -> None:
    repository = CustomerRepository(session)
    await repository.add(make_customer())

    loaded = await repository.get(make_customer().id)

    assert loaded is not None
    assert loaded.contacts is None


async def test_registering_creates_the_customer(
    session_factory: SessionFactory,
) -> None:
    directory = directory_with(session_factory)

    await directory.register(BUYER, "Иван Петров")
    card = await directory.find(BUYER)

    assert card is not None
    assert card.name == "Иван Петров"
    assert card.contacts is None


async def test_registering_again_refreshes_the_name(
    session_factory: SessionFactory,
) -> None:
    directory = directory_with(session_factory)
    await directory.register(BUYER, "Иван Петров")

    await directory.register(BUYER, "Пётр Иванов")
    card = await directory.find(BUYER)

    assert card is not None
    assert card.name == "Пётр Иванов"


async def test_an_unknown_customer_is_not_found(
    session_factory: SessionFactory,
) -> None:
    directory = directory_with(session_factory)

    assert await directory.find(CustomerId(999999)) is None


async def test_remembering_contacts_creates_the_customer(
    session_factory: SessionFactory,
) -> None:
    directory = directory_with(session_factory)

    await directory.remember(BUYER, snapshot())
    card = await directory.find(BUYER)

    assert card is not None
    assert card.contacts == snapshot()


async def test_remembering_contacts_replaces_the_old_ones(
    session_factory: SessionFactory,
) -> None:
    directory = directory_with(session_factory)
    await directory.remember(BUYER, snapshot())

    moved = ContactsSnapshot(
        name="Иван Петров",
        phone="+79990000000",
        address="Москва, Арбат 2",
    )
    await directory.remember(BUYER, moved)
    card = await directory.find(BUYER)

    assert card is not None
    assert card.contacts == moved


async def test_a_phone_is_normalised_on_the_way_in(
    session_factory: SessionFactory,
) -> None:
    directory = directory_with(session_factory)

    await directory.remember(
        BUYER,
        ContactsSnapshot(
            name="Иван Петров",
            phone="+7 (999) 123-45-67",
            address="Москва, Тверская 1",
        ),
    )
    card = await directory.find(BUYER)

    assert card is not None
    assert card.contacts is not None
    assert card.contacts.phone == "+79991234567"
