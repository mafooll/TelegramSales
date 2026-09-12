from dataclasses import dataclass
from typing import Self

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.desk.contracts import (
    MessageId,
    RelayId,
    ThreadId,
    TopicId,
)
from telegramsales.modules.desk.domain.enums import TopicKind
from telegramsales.modules.orders.contracts import OrderId
from telegramsales.shared.domain.entity import DomainEntity


@dataclass(eq=False, kw_only=True)
class Topic(DomainEntity[TopicId]):
    kind: TopicKind
    customer_id: CustomerId | None
    thread_id: ThreadId

    @classmethod
    def feed(cls, *, topic_id: TopicId, thread_id: ThreadId) -> Self:
        return cls(
            id=topic_id,
            kind=TopicKind.FEED,
            customer_id=None,
            thread_id=thread_id,
        )

    @classmethod
    def of_customer(
        cls,
        *,
        topic_id: TopicId,
        customer_id: CustomerId,
        thread_id: ThreadId,
    ) -> Self:
        return cls(
            id=topic_id,
            kind=TopicKind.CUSTOMER,
            customer_id=customer_id,
            thread_id=thread_id,
        )

    def rebind(self, thread_id: ThreadId) -> None:
        self.thread_id = thread_id


@dataclass(eq=False, kw_only=True)
class CardLink(DomainEntity[OrderId]):
    feed_message_id: MessageId | None = None
    topic_message_id: MessageId | None = None

    @classmethod
    def of_order(cls, order_id: OrderId) -> Self:
        return cls(id=order_id)

    @property
    def is_published(self) -> bool:
        return self.feed_message_id is not None or self.topic_message_id is not None

    def published_in_feed(self, message_id: MessageId) -> None:
        self.feed_message_id = message_id

    def published_in_topic(self, message_id: MessageId) -> None:
        self.topic_message_id = message_id

    def forget_feed(self) -> None:
        self.feed_message_id = None

    def forget_topic(self) -> None:
        self.topic_message_id = None


@dataclass(eq=False, kw_only=True)
class RelayLink(DomainEntity[RelayId]):
    customer_id: CustomerId
    customer_message_id: MessageId
    topic_message_id: MessageId
