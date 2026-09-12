from abc import ABC, abstractmethod
from datetime import date
from types import TracebackType
from typing import Protocol, Self

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.application.queries import (
    CartRow,
    OrderEntryView,
    OrderView,
    SelectionRow,
)
from telegramsales.modules.orders.contracts import (
    CartItemId,
    OrderId,
    SelectionId,
)
from telegramsales.modules.orders.domain.entities import (
    CartItem,
    Order,
    Selection,
)
from telegramsales.modules.orders.domain.values import ProductRef
from telegramsales.shared.application.pagination import Page
from telegramsales.shared.domain.event import DomainEvent, IEventSource


class ICartRepository(ABC):
    @abstractmethod
    async def next_id(self) -> CartItemId: ...

    @abstractmethod
    async def get(self, item_id: CartItemId) -> CartItem | None: ...

    @abstractmethod
    async def find(
        self,
        customer_id: CustomerId,
        reference: ProductRef,
    ) -> CartItem | None: ...

    @abstractmethod
    async def items_of(self, customer_id: CustomerId) -> list[CartItem]: ...

    @abstractmethod
    async def add(self, item: CartItem) -> None: ...

    @abstractmethod
    async def save(self, item: CartItem) -> None: ...

    @abstractmethod
    async def delete(self, item: CartItem) -> None: ...

    @abstractmethod
    async def clear(self, customer_id: CustomerId) -> None: ...


class ISelectionRepository(ABC):
    @abstractmethod
    async def next_id(self) -> SelectionId: ...

    @abstractmethod
    async def get(self, selection_id: SelectionId) -> Selection | None: ...

    @abstractmethod
    async def add(self, selection: Selection) -> None: ...


class IOrderRepository(ABC):
    @abstractmethod
    async def next_id(self) -> OrderId: ...

    @abstractmethod
    async def next_sequence(self, day: date) -> int: ...

    @abstractmethod
    async def get(self, order_id: OrderId) -> Order | None: ...

    @abstractmethod
    async def add(self, order: Order) -> None: ...

    @abstractmethod
    async def save(self, order: Order) -> None: ...


class IOrdersUnitOfWork(Protocol):
    @property
    def carts(self) -> ICartRepository: ...

    @property
    def selections(self) -> ISelectionRepository: ...

    @property
    def orders(self) -> IOrderRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None: ...

    def track(self, entity: IEventSource) -> None: ...

    def collect_events(self) -> list[DomainEvent]: ...


class ICartQueries(ABC):
    @abstractmethod
    async def rows_of(self, customer_id: CustomerId) -> list[CartRow]: ...

    @abstractmethod
    async def count(self, customer_id: CustomerId) -> int: ...


class ISelectionQueries(ABC):
    @abstractmethod
    async def author_of(self, selection_id: SelectionId) -> CustomerId | None: ...

    @abstractmethod
    async def rows_of(self, selection_id: SelectionId) -> list[SelectionRow]: ...


class IOrderQueries(ABC):
    @abstractmethod
    async def list_for(
        self,
        customer_id: CustomerId,
        number: int,
        size: int,
    ) -> Page[OrderEntryView]: ...

    @abstractmethod
    async def get_for(
        self,
        order_id: OrderId,
        customer_id: CustomerId,
    ) -> OrderView | None: ...
