from abc import ABC, abstractmethod
from types import TracebackType
from typing import Protocol, Self

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.customers.domain.entities import Customer
from telegramsales.shared.domain.event import DomainEvent, IEventSource


class ICustomerRepository(ABC):
    @abstractmethod
    async def get(self, customer_id: CustomerId) -> Customer | None: ...

    @abstractmethod
    async def add(self, customer: Customer) -> None: ...

    @abstractmethod
    async def save(self, customer: Customer) -> None: ...


class ICustomerUnitOfWork(Protocol):
    @property
    def customers(self) -> ICustomerRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None: ...

    def track(self, entity: IEventSource) -> None: ...

    def collect_events(self) -> list[DomainEvent]: ...
