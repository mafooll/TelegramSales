from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.customers.application.ports import ICustomerRepository
from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.customers.domain.entities import Customer
from telegramsales.modules.customers.infrastructure.mappers import CustomerMapper
from telegramsales.modules.customers.infrastructure.models import CustomerORM
from telegramsales.shared.infrastructure.database.repository import Repository


class CustomerRepository(ICustomerRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._models: Repository[CustomerORM, int] = Repository(session, CustomerORM)

    @override
    async def get(self, customer_id: CustomerId) -> Customer | None:
        model = await self._models.get(customer_id)
        return CustomerMapper.to_entity(model) if model is not None else None

    @override
    async def add(self, customer: Customer) -> None:
        await self._models.add(CustomerMapper.to_model(customer))

    @override
    async def save(self, customer: Customer) -> None:
        await self._models.merge(CustomerMapper.to_model(customer))
