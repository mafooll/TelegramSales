from typing import Any, cast

from telegramsales.modules.notifications.contracts import (
    NotificationArgs,
    NotificationId,
    RecipientId,
)
from telegramsales.modules.notifications.domain.entities import (
    Notification,
    Subscription,
)
from telegramsales.modules.notifications.domain.enums import NotificationStatus
from telegramsales.modules.notifications.infrastructure.models import (
    NotificationORM,
    SubscriptionORM,
)


def subscription_to_entity(model: SubscriptionORM) -> Subscription:
    return Subscription(
        id=RecipientId(model.id),
        is_on=model.is_on,
        created_at=model.created_at,
    )


def subscription_to_model(entity: Subscription) -> SubscriptionORM:
    return SubscriptionORM(
        id=entity.id,
        is_on=entity.is_on,
        created_at=entity.created_at,
    )


def notification_to_entity(model: NotificationORM) -> Notification:
    return Notification(
        id=NotificationId(model.id),
        recipient_id=RecipientId(model.recipient_id),
        key=model.key,
        args=cast("NotificationArgs", model.args),
        dedup_key=model.dedup_key,
        status=NotificationStatus(model.status),
        attempts=model.attempts,
        available_at=model.available_at,
        created_at=model.created_at,
        reason=model.reason,
    )


def notification_to_model(entity: Notification) -> NotificationORM:
    return NotificationORM(
        id=entity.id,
        recipient_id=entity.recipient_id,
        key=entity.key,
        args=cast("dict[str, Any]", dict(entity.args)),
        dedup_key=entity.dedup_key,
        status=entity.status.value,
        attempts=entity.attempts,
        available_at=entity.available_at,
        created_at=entity.created_at,
        reason=entity.reason,
    )
