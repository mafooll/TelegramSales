from datetime import UTC, datetime
from uuid import UUID

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.desk.contracts import (
    MessageId,
    RelayId,
    ThreadId,
    TopicId,
)
from telegramsales.modules.desk.domain.entities import RelayLink, Topic
from telegramsales.modules.orders.contracts import (
    OrderCardLine,
    OrderCardView,
    OrderId,
    OrderStatus,
)
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.shared.domain.money import Currency, Money

NOW = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)

BUYER = CustomerId(1000)
FRIEND = CustomerId(2000)
MANAGER = StaffId(3000)

ORDER = OrderId(UUID("33333333-3333-3333-3333-333333333333"))
FEED_THREAD = ThreadId(11)
CUSTOMER_THREAD = ThreadId(22)
FEED_MESSAGE = MessageId(501)
TOPIC_MESSAGE = MessageId(502)


def rub(amount: str) -> Money:
    return Money.from_external(amount, Currency.RUB)


def make_card(
    *,
    status: OrderStatus = OrderStatus.PLACED,
    customer_id: CustomerId = BUYER,
    manager_id: StaffId | None = None,
    comment: str = "",
) -> OrderCardView:
    return OrderCardView(
        id=ORDER,
        number="2026-09-12-0001",
        status=status,
        created_at=NOW,
        customer_id=customer_id,
        manager_id=manager_id,
        name="Иван Петров",
        phone="+79991234567",
        address="Москва, Тверская 1",
        comment=comment,
        lines=(
            OrderCardLine(
                title="Пальто оверсайз",
                article="000042",
                variant_title="M",
                quantity=2,
                price=rub("12900"),
                total=rub("25800"),
            ),
        ),
        total=rub("25800"),
    )


def feed_topic(thread_id: ThreadId = FEED_THREAD) -> Topic:
    return Topic.feed(topic_id=TopicId(1), thread_id=thread_id)


def customer_topic(
    customer_id: CustomerId = BUYER,
    thread_id: ThreadId = CUSTOMER_THREAD,
) -> Topic:
    return Topic.of_customer(
        topic_id=TopicId(2),
        customer_id=customer_id,
        thread_id=thread_id,
    )


def relay_link(
    *,
    customer_id: CustomerId = BUYER,
    customer_message_id: int = 700,
    topic_message_id: int = 800,
) -> RelayLink:
    return RelayLink(
        id=RelayId(1),
        customer_id=customer_id,
        customer_message_id=MessageId(customer_message_id),
        topic_message_id=MessageId(topic_message_id),
    )
