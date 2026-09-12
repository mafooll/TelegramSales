from typing import final, override

from telegramsales.modules.customers.application.commands.customers import (
    RegisterCustomer,
    RegisterCustomerHandler,
)
from telegramsales.modules.customers.application.ports import ICustomerUnitOfWork
from telegramsales.modules.customers.contracts import (
    ContactsSnapshot,
    CustomerCard,
    CustomerId,
    ICustomerDirectory,
)
from telegramsales.modules.customers.domain.entities import Customer
from telegramsales.modules.customers.domain.values import DisplayName
from telegramsales.shared.application.clock import IClock
from telegramsales.shared.domain.contacts import (
    Address,
    Contacts,
    PersonName,
    Phone,
)


def _snapshot(contacts: Contacts | None) -> ContactsSnapshot | None:
    if contacts is None:
        return None
    return ContactsSnapshot(
        name=contacts.name.value,
        phone=contacts.phone.value,
        address=contacts.address.value,
    )


def _contacts(snapshot: ContactsSnapshot) -> Contacts:
    return Contacts(
        name=PersonName(snapshot.name),
        phone=Phone(snapshot.phone),
        address=Address(snapshot.address),
    )


@final
class CustomerDirectory(ICustomerDirectory):
    def __init__(
        self,
        uow: ICustomerUnitOfWork,
        clock: IClock,
        register: RegisterCustomerHandler,
    ) -> None:
        self._uow: ICustomerUnitOfWork = uow
        self._clock: IClock = clock
        self._register: RegisterCustomerHandler = register

    @override
    async def register(self, customer_id: CustomerId, name: str) -> None:
        await self._register.handle(
            RegisterCustomer(customer_id=customer_id, name=DisplayName(name))
        )

    @override
    async def find(self, customer_id: CustomerId) -> CustomerCard | None:
        async with self._uow as uow:
            customer = await uow.customers.get(customer_id)
            if customer is None:
                return None
            return CustomerCard(
                id=customer.id,
                name=customer.name.value,
                contacts=_snapshot(customer.contacts),
                is_blocked=customer.is_blocked,
            )

    @override
    async def remember(
        self,
        customer_id: CustomerId,
        contacts: ContactsSnapshot,
    ) -> None:
        async with self._uow as uow:
            customer = await uow.customers.get(customer_id)
            if customer is None:
                customer = Customer.create(
                    customer_id=customer_id,
                    name=DisplayName(contacts.name),
                    now=self._clock.now(),
                )
                customer.remember(_contacts(contacts))
                await uow.customers.add(customer)
                return

            customer.remember(_contacts(contacts))
            await uow.customers.save(customer)
