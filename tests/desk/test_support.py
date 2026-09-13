from telegramsales.modules.desk.application.commands.support import (
    CallForSupport,
    CallForSupportHandler,
)
from telegramsales.modules.desk.application.conversations import Conversations
from telegramsales.modules.desk.application.topics import Topics
from tests.desk.factories import BUYER, CUSTOMER_THREAD, customer_topic
from tests.desk.fakes import (
    FakeDeskUnitOfWork,
    FakeOrderPresence,
    FakeTopicRegistry,
    FakeWorkChat,
)
from tests.orders.fakes import FakeCustomerDirectory, blocked_card


def talking(
    uow: FakeDeskUnitOfWork,
    *,
    directory: FakeCustomerDirectory | None = None,
    presence: FakeOrderPresence | None = None,
) -> Conversations:
    return Conversations(
        uow,
        presence or FakeOrderPresence(),
        directory or FakeCustomerDirectory(),
    )


def calling(
    *,
    topics: FakeTopicRegistry | None = None,
    directory: FakeCustomerDirectory | None = None,
    work_chat: FakeWorkChat | None = None,
) -> tuple[CallForSupportHandler, FakeDeskUnitOfWork, FakeWorkChat]:
    uow = FakeDeskUnitOfWork(topics=topics)
    chat = work_chat or FakeWorkChat()
    known = directory or FakeCustomerDirectory()
    handler = CallForSupportHandler(
        Topics(uow, chat, known),
        chat,
        talking(uow, directory=known),
    )
    return handler, uow, chat


async def test_support_opens_a_topic_for_a_customer_without_orders() -> None:
    handler, uow, chat = calling()

    called = await handler.handle(CallForSupport(customer_id=BUYER))

    assert called
    assert len(uow.topic_registry.topics) == 1
    assert len(chat.announced) == 1


async def test_support_reuses_the_topic_of_the_customer() -> None:
    handler, uow, chat = calling(topics=FakeTopicRegistry(customer_topic()))

    await handler.handle(CallForSupport(customer_id=BUYER))

    assert chat.opened == []
    assert chat.announced == [CUSTOMER_THREAD]
    assert len(uow.topic_registry.topics) == 1


async def test_a_blocked_customer_gets_no_manager() -> None:
    handler, uow, chat = calling(
        directory=FakeCustomerDirectory(blocked_card(BUYER))
    )

    called = await handler.handle(CallForSupport(customer_id=BUYER))

    assert not called
    assert uow.topic_registry.topics == {}
    assert chat.announced == []


async def test_an_unusable_work_chat_answers_honestly() -> None:
    handler, _, chat = calling(work_chat=FakeWorkChat(ready=False))

    assert not await handler.handle(CallForSupport(customer_id=BUYER))
    assert chat.announced == []


async def test_a_customer_with_orders_is_already_talking() -> None:
    conversations = talking(
        FakeDeskUnitOfWork(),
        presence=FakeOrderPresence(BUYER),
    )

    assert await conversations.is_open(BUYER)


async def test_a_customer_with_a_topic_is_already_talking() -> None:
    conversations = talking(
        FakeDeskUnitOfWork(topics=FakeTopicRegistry(customer_topic()))
    )

    assert await conversations.is_open(BUYER)


async def test_a_stranger_is_not_talking() -> None:
    conversations = talking(FakeDeskUnitOfWork())

    assert not await conversations.is_open(BUYER)


async def test_a_blocked_customer_is_cut_off_even_with_a_topic() -> None:
    conversations = talking(
        FakeDeskUnitOfWork(topics=FakeTopicRegistry(customer_topic())),
        directory=FakeCustomerDirectory(blocked_card(BUYER)),
        presence=FakeOrderPresence(BUYER),
    )

    assert not await conversations.is_open(BUYER)
