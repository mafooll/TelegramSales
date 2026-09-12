from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.desk.contracts import (
    MessageId,
    RelayId,
    ThreadId,
    TopicId,
)
from telegramsales.modules.desk.domain.entities import CardLink, RelayLink, Topic
from telegramsales.modules.desk.domain.enums import TopicKind
from telegramsales.modules.desk.infrastructure.models import (
    CardORM,
    RelayORM,
    TopicORM,
)
from telegramsales.modules.orders.contracts import OrderId


def _message(value: int | None) -> MessageId | None:
    return None if value is None else MessageId(value)


def topic_to_entity(model: TopicORM) -> Topic:
    return Topic(
        id=TopicId(model.id),
        kind=TopicKind(model.kind),
        customer_id=(
            None if model.customer_id is None else CustomerId(model.customer_id)
        ),
        thread_id=ThreadId(model.thread_id),
    )


def topic_to_model(entity: Topic) -> TopicORM:
    return TopicORM(
        id=entity.id,
        kind=entity.kind.value,
        customer_id=entity.customer_id,
        thread_id=entity.thread_id,
    )


def card_to_entity(model: CardORM) -> CardLink:
    return CardLink(
        id=OrderId(model.order_id),
        feed_message_id=_message(model.feed_message_id),
        topic_message_id=_message(model.topic_message_id),
    )


def card_to_model(entity: CardLink) -> CardORM:
    return CardORM(
        order_id=entity.id,
        feed_message_id=entity.feed_message_id,
        topic_message_id=entity.topic_message_id,
    )


def relay_to_entity(model: RelayORM) -> RelayLink:
    return RelayLink(
        id=RelayId(model.id),
        customer_id=CustomerId(model.customer_id),
        customer_message_id=MessageId(model.customer_message_id),
        topic_message_id=MessageId(model.topic_message_id),
    )


def relay_to_model(entity: RelayLink) -> RelayORM:
    return RelayORM(
        id=entity.id,
        customer_id=entity.customer_id,
        customer_message_id=entity.customer_message_id,
        topic_message_id=entity.topic_message_id,
    )
