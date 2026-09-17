from typing import override

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.customers.domain.entities import Customer
from telegramsales.modules.customers.domain.values import DisplayName
from telegramsales.modules.customers.infrastructure.models import CustomerORM
from telegramsales.shared.domain.contacts import (
    Address,
    Contacts,
    PersonName,
    Phone,
)
from telegramsales.shared.infrastructure.database.mapper import IEntityMapper


def _contacts(model: CustomerORM) -> Contacts | None:
    if (
        model.contact_name is None
        or model.contact_phone is None
        or model.contact_address is None
    ):
        return None
    return Contacts(
        name=PersonName(model.contact_name),
        phone=Phone(model.contact_phone),
        address=Address(model.contact_address),
    )


class CustomerMapper(IEntityMapper[Customer, CustomerORM]):
    @staticmethod
    @override
    def to_entity(model: CustomerORM) -> Customer:
        return Customer(
            id=CustomerId(model.id),
            name=DisplayName(model.name),
            created_at=model.created_at,
            contacts=_contacts(model),
            is_blocked=model.is_blocked,
        )

    @staticmethod
    @override
    def to_model(entity: Customer) -> CustomerORM:
        contacts = entity.contacts
        return CustomerORM(
            id=entity.id,
            name=entity.name.value,
            contact_name=None if contacts is None else contacts.name.value,
            contact_phone=None if contacts is None else contacts.phone.value,
            contact_address=None if contacts is None else contacts.address.value,
            created_at=entity.created_at,
            is_blocked=entity.is_blocked,
        )
