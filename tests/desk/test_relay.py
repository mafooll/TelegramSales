from telegramsales.modules.desk.application.commands.relay import (
    EditFromCustomer,
    EditFromCustomerHandler,
    EditFromTopic,
    EditFromTopicHandler,
    ReactFromCustomer,
    ReactFromCustomerHandler,
    ReactFromTopic,
    ReactFromTopicHandler,
    RelayToCustomer,
    RelayToCustomerHandler,
    RelayToTopic,
    RelayToTopicHandler,
)
from telegramsales.modules.desk.application.topics import Topics
from telegramsales.modules.desk.contracts import MessageId, ThreadId
from tests.desk.factories import (
    BUYER,
    CUSTOMER_THREAD,
    FEED_THREAD,
    customer_topic,
    feed_topic,
    relay_link,
)
from tests.desk.fakes import (
    FakeCustomerChat,
    FakeDeskUnitOfWork,
    FakeRelayRegistry,
    FakeTopicRegistry,
    FakeWorkChat,
)
from tests.orders.fakes import FakeCustomerDirectory

FIRST = MessageId(700)
SECOND = MessageId(701)
LINKED_IN_TOPIC = MessageId(800)
STRANGER_MESSAGE = MessageId(999)


def relaying(
    *,
    topics: FakeTopicRegistry | None = None,
    relays: FakeRelayRegistry | None = None,
    work_chat: FakeWorkChat | None = None,
) -> tuple[FakeDeskUnitOfWork, Topics, FakeWorkChat, FakeCustomerChat]:
    uow = FakeDeskUnitOfWork(topics=topics, relays=relays)
    chat = work_chat or FakeWorkChat()
    return uow, Topics(uow, chat, FakeCustomerDirectory()), chat, FakeCustomerChat()


async def test_a_customer_message_reaches_the_topic() -> None:
    uow, topics, chat, _ = relaying(topics=FakeTopicRegistry(customer_topic()))

    await RelayToTopicHandler(topics, uow, chat).handle(
        RelayToTopic(customer_id=BUYER, message_ids=[FIRST])
    )

    assert chat.copied == [(CUSTOMER_THREAD, BUYER, FIRST)]
    assert uow.relay_registry.links[0].customer_message_id == FIRST


async def test_an_album_is_relayed_message_by_message() -> None:
    uow, topics, chat, _ = relaying(topics=FakeTopicRegistry(customer_topic()))

    await RelayToTopicHandler(topics, uow, chat).handle(
        RelayToTopic(customer_id=BUYER, message_ids=[FIRST, SECOND])
    )

    assert [message_id for _, _, message_id in chat.copied] == [FIRST, SECOND]
    assert len(uow.relay_registry.links) == 2


async def test_a_deleted_topic_does_not_lose_the_message() -> None:
    chat = FakeWorkChat()
    chat.gone = {CUSTOMER_THREAD}
    uow, topics, chat, _ = relaying(
        topics=FakeTopicRegistry(customer_topic()),
        work_chat=chat,
    )

    await RelayToTopicHandler(topics, uow, chat).handle(
        RelayToTopic(customer_id=BUYER, message_ids=[FIRST])
    )

    assert [thread_id for thread_id, _, _ in chat.copied] != [CUSTOMER_THREAD]
    assert len(uow.relay_registry.links) == 1


async def test_a_customer_without_a_work_chat_is_not_relayed() -> None:
    uow, topics, chat, _ = relaying(work_chat=FakeWorkChat(ready=False))

    await RelayToTopicHandler(topics, uow, chat).handle(
        RelayToTopic(customer_id=BUYER, message_ids=[FIRST])
    )

    assert chat.copied == []


async def test_a_topic_message_reaches_the_customer() -> None:
    uow, topics, _, customer_chat = relaying(
        topics=FakeTopicRegistry(customer_topic())
    )

    await RelayToCustomerHandler(topics, uow, customer_chat).handle(
        RelayToCustomer(thread_id=CUSTOMER_THREAD, message_ids=[LINKED_IN_TOPIC])
    )

    assert customer_chat.copied == [(BUYER, LINKED_IN_TOPIC)]
    assert uow.relay_registry.links[0].topic_message_id == LINKED_IN_TOPIC


async def test_the_feed_is_not_a_conversation() -> None:
    uow, topics, _, customer_chat = relaying(topics=FakeTopicRegistry(feed_topic()))

    await RelayToCustomerHandler(topics, uow, customer_chat).handle(
        RelayToCustomer(thread_id=FEED_THREAD, message_ids=[LINKED_IN_TOPIC])
    )

    assert customer_chat.copied == []


async def test_an_unknown_thread_is_ignored() -> None:
    uow, topics, _, customer_chat = relaying()

    await RelayToCustomerHandler(topics, uow, customer_chat).handle(
        RelayToCustomer(thread_id=ThreadId(4242), message_ids=[LINKED_IN_TOPIC])
    )

    assert customer_chat.copied == []


async def test_a_customer_edit_reaches_the_topic() -> None:
    uow, _, chat, _ = relaying(relays=FakeRelayRegistry(relay_link()))

    await EditFromCustomerHandler(uow, chat).handle(
        EditFromCustomer(customer_id=BUYER, message_id=FIRST, text="и поменьше")
    )

    assert chat.edited == [(LINKED_IN_TOPIC, "и поменьше")]


async def test_a_manager_edit_reaches_the_customer() -> None:
    uow, _, _, customer_chat = relaying(relays=FakeRelayRegistry(relay_link()))

    await EditFromTopicHandler(uow, customer_chat).handle(
        EditFromTopic(message_id=LINKED_IN_TOPIC, text="уточняю")
    )

    assert customer_chat.edited == [(BUYER, FIRST, "уточняю")]


async def test_an_edit_without_a_link_goes_nowhere() -> None:
    uow, _, chat, _ = relaying()

    await EditFromCustomerHandler(uow, chat).handle(
        EditFromCustomer(customer_id=BUYER, message_id=STRANGER_MESSAGE, text="эй")
    )

    assert chat.edited == []


async def test_a_customer_reaction_reaches_the_topic() -> None:
    uow, _, chat, _ = relaying(relays=FakeRelayRegistry(relay_link()))

    await ReactFromCustomerHandler(uow, chat).handle(
        ReactFromCustomer(customer_id=BUYER, message_id=FIRST, emoji="👍")
    )

    assert chat.reactions == [(LINKED_IN_TOPIC, "👍")]


async def test_a_removed_reaction_is_removed_too() -> None:
    uow, _, _, customer_chat = relaying(relays=FakeRelayRegistry(relay_link()))

    await ReactFromTopicHandler(uow, customer_chat).handle(
        ReactFromTopic(message_id=LINKED_IN_TOPIC, emoji=None)
    )

    assert customer_chat.reactions == [(BUYER, FIRST, None)]
