from types import TracebackType
from typing import Self, override

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.desk.application.exceptions import TopicGoneError
from telegramsales.modules.desk.application.ports import (
    ICardRegistry,
    ICustomerChat,
    IRelayRegistry,
    ITopicRegistry,
    IWorkChat,
)
from telegramsales.modules.desk.contracts import (
    MessageId,
    RelayId,
    ThreadId,
    TopicId,
)
from telegramsales.modules.desk.domain.entities import CardLink, RelayLink, Topic
from telegramsales.modules.desk.domain.enums import TopicKind
from telegramsales.modules.orders.contracts import (
    IOrderCards,
    OrderCardView,
    OrderId,
)

FIRST_THREAD = 100
FIRST_MESSAGE = 1000


class FakeTopicRegistry(ITopicRegistry):
    def __init__(self, *topics: Topic) -> None:
        self.topics: dict[TopicId, Topic] = {topic.id: topic for topic in topics}
        self._next: int = max((topic.id for topic in topics), default=0) + 1

    @override
    async def next_id(self) -> TopicId:
        issued = TopicId(self._next)
        self._next += 1
        return issued

    @override
    async def feed(self) -> Topic | None:
        return self._find(TopicKind.FEED, None)

    @override
    async def of_customer(self, customer_id: CustomerId) -> Topic | None:
        return self._find(TopicKind.CUSTOMER, customer_id)

    @override
    async def by_thread(self, thread_id: ThreadId) -> Topic | None:
        return next(
            (
                topic
                for topic in self.topics.values()
                if topic.thread_id == thread_id
            ),
            None,
        )

    @override
    async def remember(self, topic: Topic) -> Topic:
        stored = self._find(topic.kind, topic.customer_id)
        if stored is not None:
            return stored
        self.topics[topic.id] = topic
        return topic

    @override
    async def save(self, topic: Topic) -> None:
        self.topics[topic.id] = topic

    def _find(self, kind: TopicKind, customer_id: CustomerId | None) -> Topic | None:
        return next(
            (
                topic
                for topic in self.topics.values()
                if topic.kind is kind and topic.customer_id == customer_id
            ),
            None,
        )


class FakeCardRegistry(ICardRegistry):
    def __init__(self, *cards: CardLink) -> None:
        self.cards: dict[OrderId, CardLink] = {card.id: card for card in cards}

    @override
    async def get(self, order_id: OrderId) -> CardLink | None:
        return self.cards.get(order_id)

    @override
    async def save(self, card: CardLink) -> None:
        self.cards[card.id] = card


class FakeRelayRegistry(IRelayRegistry):
    def __init__(self, *links: RelayLink) -> None:
        self.links: list[RelayLink] = list(links)
        self._next: int = len(self.links) + 1

    @override
    async def next_id(self) -> RelayId:
        issued = RelayId(self._next)
        self._next += 1
        return issued

    @override
    async def by_customer_message(
        self,
        customer_id: CustomerId,
        message_id: MessageId,
    ) -> RelayLink | None:
        return next(
            (
                link
                for link in self.links
                if link.customer_id == customer_id
                and link.customer_message_id == message_id
            ),
            None,
        )

    @override
    async def by_topic_message(self, message_id: MessageId) -> RelayLink | None:
        return next(
            (link for link in self.links if link.topic_message_id == message_id),
            None,
        )

    @override
    async def add(self, link: RelayLink) -> None:
        self.links.append(link)


class FakeDeskUnitOfWork:
    def __init__(
        self,
        *,
        topics: FakeTopicRegistry | None = None,
        cards: FakeCardRegistry | None = None,
        relays: FakeRelayRegistry | None = None,
    ) -> None:
        self.topic_registry: FakeTopicRegistry = topics or FakeTopicRegistry()
        self.card_registry: FakeCardRegistry = cards or FakeCardRegistry()
        self.relay_registry: FakeRelayRegistry = relays or FakeRelayRegistry()
        self.entered: int = 0

    @property
    def topics(self) -> ITopicRegistry:
        return self.topic_registry

    @property
    def cards(self) -> ICardRegistry:
        return self.card_registry

    @property
    def relays(self) -> IRelayRegistry:
        return self.relay_registry

    async def __aenter__(self) -> Self:
        self.entered += 1
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return None


class FakeWorkChat(IWorkChat):
    def __init__(self, *, ready: bool = True) -> None:
        self.ready: bool = ready
        self.opened: list[str] = []
        self.posted: list[tuple[ThreadId, OrderCardView]] = []
        self.redrawn: list[tuple[MessageId, OrderCardView]] = []
        self.copied: list[tuple[ThreadId, CustomerId, MessageId]] = []
        self.edited: list[tuple[MessageId, str]] = []
        self.reactions: list[tuple[MessageId, str | None]] = []
        self.gone: set[ThreadId] = set()
        self.gone_messages: set[MessageId] = set()
        self._next_thread: int = FIRST_THREAD
        self._next_message: int = FIRST_MESSAGE

    @override
    async def is_ready(self) -> bool:
        return self.ready

    @override
    async def open_feed_topic(self) -> ThreadId:
        self.opened.append(TopicKind.FEED.value)
        return self._thread()

    @override
    async def open_customer_topic(
        self,
        customer_id: CustomerId,
        name: str,
    ) -> ThreadId:
        self.opened.append(name)
        return self._thread()

    @override
    async def post_card(
        self,
        thread_id: ThreadId,
        card: OrderCardView,
    ) -> MessageId:
        self._ensure_alive(thread_id)
        self.posted.append((thread_id, card))
        return self._message()

    @override
    async def redraw_card(
        self,
        message_id: MessageId,
        card: OrderCardView,
    ) -> None:
        if message_id in self.gone_messages:
            raise TopicGoneError(thread_id=None)
        self.redrawn.append((message_id, card))

    @override
    async def copy_into(
        self,
        thread_id: ThreadId,
        customer_id: CustomerId,
        message_id: MessageId,
    ) -> MessageId:
        self._ensure_alive(thread_id)
        self.copied.append((thread_id, customer_id, message_id))
        return self._message()

    @override
    async def edit_message(self, message_id: MessageId, text: str) -> None:
        self.edited.append((message_id, text))

    @override
    async def react(self, message_id: MessageId, emoji: str | None) -> None:
        self.reactions.append((message_id, emoji))

    def _ensure_alive(self, thread_id: ThreadId) -> None:
        if thread_id in self.gone:
            raise TopicGoneError(thread_id=thread_id)

    def _thread(self) -> ThreadId:
        issued = ThreadId(self._next_thread)
        self._next_thread += 1
        return issued

    def _message(self) -> MessageId:
        issued = MessageId(self._next_message)
        self._next_message += 1
        return issued


class FakeCustomerChat(ICustomerChat):
    def __init__(self) -> None:
        self.copied: list[tuple[CustomerId, MessageId]] = []
        self.edited: list[tuple[CustomerId, MessageId, str]] = []
        self.reactions: list[tuple[CustomerId, MessageId, str | None]] = []
        self._next_message: int = FIRST_MESSAGE

    @override
    async def copy_from_work_chat(
        self,
        customer_id: CustomerId,
        message_id: MessageId,
    ) -> MessageId:
        self.copied.append((customer_id, message_id))
        issued = MessageId(self._next_message)
        self._next_message += 1
        return issued

    @override
    async def edit_message(
        self,
        customer_id: CustomerId,
        message_id: MessageId,
        text: str,
    ) -> None:
        self.edited.append((customer_id, message_id, text))

    @override
    async def react(
        self,
        customer_id: CustomerId,
        message_id: MessageId,
        emoji: str | None,
    ) -> None:
        self.reactions.append((customer_id, message_id, emoji))


class FakeOrderCards(IOrderCards):
    def __init__(self, *cards: OrderCardView) -> None:
        self.cards: dict[OrderId, OrderCardView] = {card.id: card for card in cards}

    @override
    async def card(self, order_id: OrderId) -> OrderCardView | None:
        return self.cards.get(order_id)
