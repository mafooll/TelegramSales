from datetime import UTC, datetime, timedelta

from telegramsales.modules.notifications.contracts import (
    NotificationArgs,
    NotificationId,
    RecipientId,
)
from telegramsales.modules.notifications.domain.entities import (
    NO_ARGS,
    Notification,
    Subscription,
)

NOW = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)
LATER = NOW + timedelta(minutes=5)

BUYER = RecipientId(1000)
FRIEND = RecipientId(2000)
STRANGER = RecipientId(3000)

ORDER_MOVED = "notifications-order-moved"
NEW_PRODUCT = "shop-new-product"


def make_subscription(
    recipient_id: RecipientId = BUYER,
    *,
    is_on: bool = True,
) -> Subscription:
    subscription = Subscription.open(recipient_id=recipient_id, now=NOW)
    subscription.switch(enabled=is_on)
    return subscription


def make_notification(  # noqa: PLR0913
    notification_id: int = 1,
    *,
    recipient_id: RecipientId = BUYER,
    key: str = ORDER_MOVED,
    args: NotificationArgs = NO_ARGS,
    dedup_key: str | None = None,
    available_at: datetime = NOW,
) -> Notification:
    notification = Notification.queue(
        notification_id=NotificationId(notification_id),
        recipient_id=recipient_id,
        key=key,
        args=args,
        dedup_key=dedup_key,
        now=NOW,
    )
    notification.available_at = available_at
    return notification
