from typing import override

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.desk.application.ports import (
    ICardRegistry,
    IRelayRegistry,
    ITopicRegistry,
)
from telegramsales.modules.desk.contracts import (
    MessageId,
    RelayId,
    ThreadId,
    TopicId,
)
from telegramsales.modules.desk.domain.entities import CardLink, RelayLink, Topic
from telegramsales.modules.desk.domain.enums import TopicKind
from telegramsales.modules.desk.infrastructure.mappers import (
    card_to_entity,
    card_to_model,
    relay_to_entity,
    relay_to_model,
    topic_to_entity,
    topic_to_model,
)
from telegramsales.modules.desk.infrastructure.models import (
    CardORM,
    RelayORM,
    TopicORM,
)
from telegramsales.modules.orders.contracts import OrderId
from telegramsales.shared.infrastructure.database.repository import Repository

ID_COLUMN = "id"
TOPIC_CONFLICT = ("kind", "customer_id")


async def _next_id(session: AsyncSession, table: str) -> int:
    sequence = func.pg_get_serial_sequence(table, ID_COLUMN)
    return (await session.execute(select(func.nextval(sequence)))).scalar_one()


class TopicRegistry(ITopicRegistry):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._models: Repository[TopicORM, int] = Repository(session, TopicORM)

    @override
    async def next_id(self) -> TopicId:
        return TopicId(await _next_id(self._session, TopicORM.__tablename__))

    @override
    async def feed(self) -> Topic | None:
        return await self._find(TopicKind.FEED, None)

    @override
    async def of_customer(self, customer_id: CustomerId) -> Topic | None:
        return await self._find(TopicKind.CUSTOMER, customer_id)

    @override
    async def by_thread(self, thread_id: ThreadId) -> Topic | None:
        query = select(TopicORM).where(TopicORM.thread_id == thread_id)
        model = (await self._session.execute(query)).scalar_one_or_none()
        return None if model is None else topic_to_entity(model)

    @override
    async def remember(self, topic: Topic) -> Topic:
        statement = (
            insert(TopicORM)
            .values(
                id=topic.id,
                kind=topic.kind.value,
                customer_id=topic.customer_id,
                thread_id=topic.thread_id,
            )
            .on_conflict_do_nothing(index_elements=TOPIC_CONFLICT)
        )
        await self._session.execute(statement)
        await self._session.flush()

        stored = await self._find(topic.kind, topic.customer_id)
        return topic if stored is None else stored

    @override
    async def save(self, topic: Topic) -> None:
        await self._models.merge(topic_to_model(topic))

    async def _find(
        self,
        kind: TopicKind,
        customer_id: CustomerId | None,
    ) -> Topic | None:
        query = select(TopicORM).where(
            TopicORM.kind == kind.value,
            TopicORM.customer_id.is_(None)
            if customer_id is None
            else TopicORM.customer_id == customer_id,
        )
        model = (await self._session.execute(query)).scalar_one_or_none()
        return None if model is None else topic_to_entity(model)


class CardRegistry(ICardRegistry):
    def __init__(self, session: AsyncSession) -> None:
        self._models: Repository[CardORM, OrderId] = Repository(session, CardORM)

    @override
    async def get(self, order_id: OrderId) -> CardLink | None:
        model = await self._models.get(order_id)
        return None if model is None else card_to_entity(model)

    @override
    async def save(self, card: CardLink) -> None:
        await self._models.merge(card_to_model(card))


class RelayRegistry(IRelayRegistry):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._models: Repository[RelayORM, int] = Repository(session, RelayORM)

    @override
    async def next_id(self) -> RelayId:
        return RelayId(await _next_id(self._session, RelayORM.__tablename__))

    @override
    async def by_customer_message(
        self,
        customer_id: CustomerId,
        message_id: MessageId,
    ) -> RelayLink | None:
        query = select(RelayORM).where(
            RelayORM.customer_id == customer_id,
            RelayORM.customer_message_id == message_id,
        )
        return await self._one(query)

    @override
    async def by_topic_message(self, message_id: MessageId) -> RelayLink | None:
        return await self._one(
            select(RelayORM).where(RelayORM.topic_message_id == message_id)
        )

    @override
    async def add(self, link: RelayLink) -> None:
        await self._models.add(relay_to_model(link))

    async def _one(self, query: Select[tuple[RelayORM]]) -> RelayLink | None:
        model = (await self._session.execute(query)).scalar_one_or_none()
        return None if model is None else relay_to_entity(model)
