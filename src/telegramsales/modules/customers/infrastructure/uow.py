from telegramsales.modules.customers.application.ports import ICustomerRepository
from telegramsales.modules.customers.infrastructure.repositories import (
    CustomerRepository,
)
from telegramsales.shared.infrastructure.database.uow import UnitOfWork


class CustomerUnitOfWork(UnitOfWork):
    @property
    def customers(self) -> ICustomerRepository:
        return CustomerRepository(self.session)
