import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.customers.domain.entities import Customer
from telegramsales.modules.customers.domain.values import DisplayName
from telegramsales.modules.customers.infrastructure.repositories import (
    CustomerRepository,
)
from telegramsales.modules.desk.contracts import MessageId, ThreadId
from telegramsales.modules.desk.domain.entities import CardLink, RelayLink, Topic
from telegramsales.modules.desk.infrastructure.repositories import (
    CardRegistry,
    RelayRegistry,
    TopicRegistry,
)
from telegramsales.modules.orders.contracts import OrderId
from tests.desk.factories import NOW
from tests.orders.test_persistence import make_order, store_customer

pytestmark = pytest.mark.db

BUYER = CustomerId(80001)
FRIEND = CustomerId(80002)
FEED_THREAD = ThreadId(11)
CUSTOMER_THREAD = ThreadId(22)


async def store_buyer(
    session: AsyncSession,
    customer_id: CustomerId = BUYER,
) -> None:
    await CustomerRepository(session).add(
        Customer.create(
            customer_id=customer_id,
            name=DisplayName("Иван Петров"),
            now=NOW,
        )
    )


async def make_topic(
    registry: TopicRegistry,
    *,
    customer_id: CustomerId | None = None,
    thread_id: ThreadId,
) -> Topic:
    topic_id = await registry.next_id()
    if customer_id is None:
        return await registry.remember(
            Topic.feed(topic_id=topic_id, thread_id=thread_id)
        )
    return await registry.remember(
        Topic.of_customer(
            topic_id=topic_id,
            customer_id=customer_id,
            thread_id=thread_id,
        )
    )


async def test_the_feed_topic_survives_a_round_trip(session: AsyncSession) -> None:
    registry = TopicRegistry(session)
    await make_topic(registry, thread_id=FEED_THREAD)

    stored = await registry.feed()

    assert stored is not None
    assert stored.thread_id == FEED_THREAD
    assert stored.customer_id is None


async def test_a_customer_topic_is_found_both_ways(session: AsyncSession) -> None:
    await store_buyer(session)
    registry = TopicRegistry(session)
    await make_topic(registry, customer_id=BUYER, thread_id=CUSTOMER_THREAD)

    by_customer = await registry.of_customer(BUYER)
    by_thread = await registry.by_thread(CUSTOMER_THREAD)

    assert by_customer is not None
    assert by_thread is not None
    assert by_customer.id == by_thread.id


async def test_two_customers_keep_separate_topics(session: AsyncSession) -> None:
    await store_buyer(session)
    await store_buyer(session, FRIEND)
    registry = TopicRegistry(session)
    await make_topic(registry, customer_id=BUYER, thread_id=CUSTOMER_THREAD)
    await make_topic(registry, customer_id=FRIEND, thread_id=ThreadId(33))

    mine = await registry.of_customer(BUYER)

    assert mine is not None
    assert mine.thread_id == CUSTOMER_THREAD


async def test_the_second_topic_of_a_customer_is_refused(
    session: AsyncSession,
) -> None:
    await store_buyer(session)
    registry = TopicRegistry(session)
    first = await make_topic(registry, customer_id=BUYER, thread_id=CUSTOMER_THREAD)

    second = await make_topic(registry, customer_id=BUYER, thread_id=ThreadId(44))

    assert second.id == first.id
    assert second.thread_id == CUSTOMER_THREAD


async def test_a_reopened_topic_keeps_its_row(session: AsyncSession) -> None:
    await store_buyer(session)
    registry = TopicRegistry(session)
    topic = await make_topic(
        registry,
        customer_id=BUYER,
        thread_id=CUSTOMER_THREAD,
    )

    topic.rebind(ThreadId(55))
    await registry.save(topic)
    stored = await registry.of_customer(BUYER)

    assert stored is not None
    assert stored.id == topic.id
    assert stored.thread_id == ThreadId(55)


async def store_order(session: AsyncSession) -> OrderId:
    await store_customer(session)
    order = await make_order(session)
    return order.id


async def test_a_card_link_survives_a_round_trip(session: AsyncSession) -> None:
    order_id = await store_order(session)
    registry = CardRegistry(session)
    link = CardLink.of_order(order_id)
    link.published_in_feed(MessageId(501))
    link.published_in_topic(MessageId(502))

    await registry.save(link)
    stored = await registry.get(order_id)

    assert stored is not None
    assert stored.feed_message_id == MessageId(501)
    assert stored.topic_message_id == MessageId(502)


async def test_a_forgotten_card_is_stored_empty(session: AsyncSession) -> None:
    order_id = await store_order(session)
    registry = CardRegistry(session)
    link = CardLink.of_order(order_id)
    link.published_in_feed(MessageId(501))
    await registry.save(link)

    link.forget_feed()
    await registry.save(link)
    stored = await registry.get(order_id)

    assert stored is not None
    assert not stored.is_published


async def test_a_relay_link_is_found_from_both_sides(session: AsyncSession) -> None:
    await store_buyer(session)
    registry = RelayRegistry(session)
    await registry.add(
        RelayLink(
            id=await registry.next_id(),
            customer_id=BUYER,
            customer_message_id=MessageId(700),
            topic_message_id=MessageId(800),
        )
    )

    from_customer = await registry.by_customer_message(BUYER, MessageId(700))
    from_topic = await registry.by_topic_message(MessageId(800))

    assert from_customer is not None
    assert from_topic is not None
    assert from_customer.id == from_topic.id


async def test_an_unlinked_message_is_not_found(session: AsyncSession) -> None:
    await store_buyer(session)
    registry = RelayRegistry(session)

    assert await registry.by_topic_message(MessageId(999)) is None
