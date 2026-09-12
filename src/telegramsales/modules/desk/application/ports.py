from abc import ABC, abstractmethod
from types import TracebackType
from typing import Protocol, Self

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.desk.contracts import (
    MessageId,
    RelayId,
    ThreadId,
    TopicId,
)
from telegramsales.modules.desk.domain.entities import CardLink, RelayLink, Topic
from telegramsales.modules.orders.contracts import OrderCardView, OrderId


class ITopicRegistry(ABC):
    @abstractmethod
    async def next_id(self) -> TopicId: ...

    @abstractmethod
    async def feed(self) -> Topic | None: ...

    @abstractmethod
    async def of_customer(self, customer_id: CustomerId) -> Topic | None: ...

    @abstractmethod
    async def by_thread(self, thread_id: ThreadId) -> Topic | None: ...

    @abstractmethod
    async def remember(self, topic: Topic) -> Topic: ...

    @abstractmethod
    async def save(self, topic: Topic) -> None: ...


class ICardRegistry(ABC):
    @abstractmethod
    async def get(self, order_id: OrderId) -> CardLink | None: ...

    @abstractmethod
    async def save(self, card: CardLink) -> None: ...


class IRelayRegistry(ABC):
    @abstractmethod
    async def next_id(self) -> RelayId: ...

    @abstractmethod
    async def by_customer_message(
        self,
        customer_id: CustomerId,
        message_id: MessageId,
    ) -> RelayLink | None: ...

    @abstractmethod
    async def by_topic_message(self, message_id: MessageId) -> RelayLink | None: ...

    @abstractmethod
    async def add(self, link: RelayLink) -> None: ...


class IDeskUnitOfWork(Protocol):
    @property
    def topics(self) -> ITopicRegistry: ...

    @property
    def cards(self) -> ICardRegistry: ...

    @property
    def relays(self) -> IRelayRegistry: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None: ...


class IWorkChat(ABC):
    @abstractmethod
    async def is_ready(self) -> bool: ...

    @abstractmethod
    async def open_feed_topic(self) -> ThreadId: ...

    @abstractmethod
    async def open_customer_topic(
        self,
        customer_id: CustomerId,
        name: str,
    ) -> ThreadId: ...

    @abstractmethod
    async def post_card(
        self,
        thread_id: ThreadId,
        card: OrderCardView,
    ) -> MessageId: ...

    @abstractmethod
    async def redraw_card(
        self,
        message_id: MessageId,
        card: OrderCardView,
    ) -> None: ...

    @abstractmethod
    async def copy_into(
        self,
        thread_id: ThreadId,
        customer_id: CustomerId,
        message_id: MessageId,
    ) -> MessageId: ...

    @abstractmethod
    async def edit_message(self, message_id: MessageId, text: str) -> None: ...

    @abstractmethod
    async def react(self, message_id: MessageId, emoji: str | None) -> None: ...


class ICustomerChat(ABC):
    @abstractmethod
    async def copy_from_work_chat(
        self,
        customer_id: CustomerId,
        message_id: MessageId,
    ) -> MessageId: ...

    @abstractmethod
    async def edit_message(
        self,
        customer_id: CustomerId,
        message_id: MessageId,
        text: str,
    ) -> None: ...

    @abstractmethod
    async def react(
        self,
        customer_id: CustomerId,
        message_id: MessageId,
        emoji: str | None,
    ) -> None: ...
