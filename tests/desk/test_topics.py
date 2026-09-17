from typing import override

from telegramsales.modules.desk.application.topics import Topics
from telegramsales.modules.desk.contracts import ThreadId
from telegramsales.modules.desk.domain.entities import Topic
from tests.desk.factories import (
    BUYER,
    CUSTOMER_THREAD,
    FEED_THREAD,
    customer_topic,
    feed_topic,
)
from tests.desk.fakes import FakeDeskUnitOfWork, FakeTopicRegistry, FakeWorkChat
from tests.orders.fakes import FakeCustomerDirectory


def topics_of(
    registry: FakeTopicRegistry | None = None,
    work_chat: FakeWorkChat | None = None,
    directory: FakeCustomerDirectory | None = None,
) -> tuple[Topics, FakeDeskUnitOfWork, FakeWorkChat]:
    uow = FakeDeskUnitOfWork(topics=registry)
    chat = work_chat or FakeWorkChat()
    return Topics(uow, chat, directory or FakeCustomerDirectory()), uow, chat


async def test_the_feed_topic_is_opened_once() -> None:
    topics, uow, chat = topics_of()

    first = await topics.feed()
    second = await topics.feed()

    assert first == second
    assert len(chat.opened) == 1
    assert len(uow.topic_registry.topics) == 1


async def test_a_known_feed_topic_is_reused() -> None:
    topics, _, chat = topics_of(FakeTopicRegistry(feed_topic()))

    assert await topics.feed() == FEED_THREAD
    assert chat.opened == []


async def test_a_customer_topic_is_named_after_the_customer() -> None:
    directory = FakeCustomerDirectory()
    await directory.register(BUYER, "Иван Петров")
    topics, _, chat = topics_of(directory=directory)

    await topics.of_customer(BUYER)

    assert chat.opened == ["Иван Петров"]


async def test_a_known_customer_topic_is_reused() -> None:
    topics, _, chat = topics_of(FakeTopicRegistry(customer_topic()))

    assert await topics.of_customer(BUYER) == CUSTOMER_THREAD
    assert chat.opened == []


class RacingTopicRegistry(FakeTopicRegistry):
    def __init__(self, winner: Topic) -> None:
        super().__init__()
        self._winner: Topic = winner

    @override
    async def remember(self, topic: Topic) -> Topic:
        await self.save(self._winner)
        return await super().remember(topic)


async def test_a_topic_lost_to_a_race_is_not_duplicated() -> None:
    theirs = customer_topic(thread_id=ThreadId(777))
    topics, uow, _ = topics_of(RacingTopicRegistry(theirs))

    assert await topics.of_customer(BUYER) == theirs.thread_id
    assert len(uow.topic_registry.topics) == 1


async def test_an_unusable_work_chat_gives_no_topic() -> None:
    topics, _, _ = topics_of(work_chat=FakeWorkChat(ready=False))

    assert await topics.feed() is None
    assert await topics.of_customer(BUYER) is None


async def test_a_deleted_topic_is_opened_again() -> None:
    registry = FakeTopicRegistry(customer_topic())
    topics, _, _ = topics_of(registry)

    reopened = await topics.reopen(CUSTOMER_THREAD)

    assert reopened is not None
    assert reopened != CUSTOMER_THREAD
    assert await topics.of_customer(BUYER) == reopened


async def test_an_unknown_thread_is_not_reopened() -> None:
    topics, _, chat = topics_of()

    assert await topics.reopen(ThreadId(999)) is None
    assert chat.opened == []


async def test_a_thread_points_back_to_its_customer() -> None:
    topics, _, _ = topics_of(FakeTopicRegistry(customer_topic(), feed_topic()))

    assert await topics.customer_of(CUSTOMER_THREAD) == BUYER
    assert await topics.customer_of(FEED_THREAD) is None
