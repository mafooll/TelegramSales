from telegramsales.modules.desk.application.commands.cards import (
    PublishOrderCard,
    PublishOrderCardHandler,
    RedrawOrderCard,
    RedrawOrderCardHandler,
)
from telegramsales.modules.desk.application.topics import Topics
from telegramsales.modules.desk.domain.entities import CardLink
from telegramsales.modules.orders.contracts import OrderCardView, OrderStatus
from tests.desk.factories import (
    FEED_MESSAGE,
    ORDER,
    TOPIC_MESSAGE,
    make_card,
)
from tests.desk.fakes import (
    FakeCardRegistry,
    FakeDeskUnitOfWork,
    FakeOrderCards,
    FakeWorkChat,
)
from tests.orders.fakes import FakeCustomerDirectory


def publishing(
    card: OrderCardView | None = None,
    *,
    cards: FakeCardRegistry | None = None,
    work_chat: FakeWorkChat | None = None,
) -> tuple[PublishOrderCardHandler, FakeDeskUnitOfWork, FakeWorkChat]:
    uow = FakeDeskUnitOfWork(cards=cards)
    chat = work_chat or FakeWorkChat()
    topics = Topics(uow, chat, FakeCustomerDirectory())
    known = FakeOrderCards(card or make_card())
    return PublishOrderCardHandler(known, uow, topics, chat), uow, chat


def redrawing(
    card: OrderCardView,
    link: CardLink,
    *,
    work_chat: FakeWorkChat | None = None,
) -> tuple[RedrawOrderCardHandler, FakeDeskUnitOfWork, FakeWorkChat]:
    registry = FakeCardRegistry(link)
    publish, uow, chat = publishing(card, cards=registry, work_chat=work_chat)
    return (
        RedrawOrderCardHandler(FakeOrderCards(card), uow, chat, publish),
        uow,
        chat,
    )


def published_link() -> CardLink:
    link = CardLink.of_order(ORDER)
    link.published_in_feed(FEED_MESSAGE)
    link.published_in_topic(TOPIC_MESSAGE)
    return link


async def test_a_new_order_reaches_both_points() -> None:
    handler, uow, chat = publishing()

    await handler.handle(PublishOrderCard(order_id=ORDER))
    link = uow.card_registry.cards[ORDER]

    assert len(chat.posted) == 2
    assert link.feed_message_id is not None
    assert link.topic_message_id is not None
    assert link.feed_message_id != link.topic_message_id


async def test_the_card_is_published_once() -> None:
    handler, _, chat = publishing()

    await handler.handle(PublishOrderCard(order_id=ORDER))
    await handler.handle(PublishOrderCard(order_id=ORDER))

    assert len(chat.posted) == 2


async def test_an_unknown_order_is_not_published() -> None:
    uow = FakeDeskUnitOfWork()
    chat = FakeWorkChat()
    handler = PublishOrderCardHandler(
        FakeOrderCards(),
        uow,
        Topics(uow, chat, FakeCustomerDirectory()),
        chat,
    )

    await handler.handle(PublishOrderCard(order_id=ORDER))

    assert chat.posted == []


async def test_an_unusable_work_chat_leaves_no_link() -> None:
    handler, uow, chat = publishing(work_chat=FakeWorkChat(ready=False))

    await handler.handle(PublishOrderCard(order_id=ORDER))

    assert chat.posted == []
    assert not uow.card_registry.cards[ORDER].is_published


async def test_a_status_change_redraws_both_cards() -> None:
    card = make_card(status=OrderStatus.IN_WORK)
    handler, _, chat = redrawing(card, published_link())

    await handler.handle(RedrawOrderCard(order_id=ORDER))

    assert [message_id for message_id, _ in chat.redrawn] == [
        FEED_MESSAGE,
        TOPIC_MESSAGE,
    ]
    assert [drawn.status for _, drawn in chat.redrawn] == [
        OrderStatus.IN_WORK,
        OrderStatus.IN_WORK,
    ]


async def test_an_unpublished_order_is_not_redrawn() -> None:
    card = make_card()
    handler, _, chat = redrawing(card, CardLink.of_order(ORDER))

    await handler.handle(RedrawOrderCard(order_id=ORDER))

    assert chat.redrawn == []


async def test_a_card_lost_with_its_topic_is_published_again() -> None:
    card = make_card(status=OrderStatus.IN_WORK)
    chat = FakeWorkChat()
    chat.gone_messages = {FEED_MESSAGE, TOPIC_MESSAGE}
    handler, uow, _ = redrawing(card, published_link(), work_chat=chat)

    await handler.handle(RedrawOrderCard(order_id=ORDER))
    link = uow.card_registry.cards[ORDER]

    assert len(chat.posted) == 2
    assert link.feed_message_id not in chat.gone_messages
    assert link.topic_message_id not in chat.gone_messages
