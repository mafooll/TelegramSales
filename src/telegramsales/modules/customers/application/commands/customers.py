from dataclasses import dataclass

from telegramsales.modules.customers.application.ports import ICustomerUnitOfWork
from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.customers.domain.entities import Customer
from telegramsales.modules.customers.domain.values import DisplayName
from telegramsales.shared.application.clock import IClock


@dataclass(frozen=True, slots=True)
class RegisterCustomer:
    customer_id: CustomerId
    name: DisplayName


class RegisterCustomerHandler:
    def __init__(self, uow: ICustomerUnitOfWork, clock: IClock) -> None:
        self._uow: ICustomerUnitOfWork = uow
        self._clock: IClock = clock

    async def handle(self, command: RegisterCustomer) -> None:
        async with self._uow as uow:
            customer = await uow.customers.get(command.customer_id)
            if customer is None:
                await uow.customers.add(
                    Customer.create(
                        customer_id=command.customer_id,
                        name=command.name,
                        now=self._clock.now(),
                    )
                )
                return

            if customer.name != command.name:
                customer.rename(command.name)
                await uow.customers.save(customer)
