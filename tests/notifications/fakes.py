from collections.abc import Sequence
from datetime import datetime
from types import TracebackType
from typing import TYPE_CHECKING, Self, override

from telegramsales.modules.notifications.application.ports import (
    Delivered,
    Delivery,
    INotificationOutbox,
    INotificationSender,
    ISubscriptionRepository,
)
from telegramsales.modules.notifications.contracts import (
    NotificationId,
    RecipientId,
)
from telegramsales.modules.notifications.domain.entities import (
    Notification,
    Subscription,
)

if TYPE_CHECKING:
    from telegramsales.modules.notifications.domain.enums import NotificationStatus


class FakeOutbox(INotificationOutbox):
    def __init__(self, *notifications: Notification) -> None:
        self.notifications: dict[NotificationId, Notification] = {
            notification.id: notification for notification in notifications
        }
        self.claimed: list[NotificationId] = []
        self._next: int = len(self.notifications) + 1

    @override
    async def next_id(self) -> NotificationId:
        issued = NotificationId(self._next)
        self._next += 1
        return issued

    @override
    async def next_ids(self, count: int) -> list[NotificationId]:
        return [await self.next_id() for _ in range(count)]

    @override
    async def add(self, notification: Notification) -> bool:
        taken = {
            stored.dedup_key
            for stored in self.notifications.values()
            if stored.dedup_key is not None
        }
        if notification.dedup_key is not None and notification.dedup_key in taken:
            return False

        self.notifications[notification.id] = notification
        return True

    @override
    async def add_all(self, notifications: Sequence[Notification]) -> int:
        queued = 0
        for notification in notifications:
            queued += await self.add(notification)
        return queued

    @override
    async def claim(self, limit: int, now: datetime) -> list[Notification]:
        due = [
            notification
            for notification in self.notifications.values()
            if notification.is_pending and notification.available_at <= now
        ]
        claimed = sorted(due, key=lambda item: (item.available_at, item.id))[:limit]
        self.claimed.extend(notification.id for notification in claimed)
        return claimed

    @override
    async def save(self, notification: Notification) -> None:
        self.notifications[notification.id] = notification


class FakeSubscriptions(ISubscriptionRepository):
    def __init__(self, *subscriptions: Subscription) -> None:
        self.items: dict[RecipientId, Subscription] = {
            subscription.id: subscription for subscription in subscriptions
        }

    @override
    async def get(self, recipient_id: RecipientId) -> Subscription | None:
        return self.items.get(recipient_id)

    @override
    async def add(self, subscription: Subscription) -> None:
        self.items[subscription.id] = subscription

    @override
    async def save(self, subscription: Subscription) -> None:
        self.items[subscription.id] = subscription

    @override
    async def recipients(self) -> list[RecipientId]:
        return sorted(
            recipient_id
            for recipient_id, subscription in self.items.items()
            if subscription.is_on
        )


class FakeNotificationsUnitOfWork:
    def __init__(
        self,
        outbox: FakeOutbox | None = None,
        subscriptions: FakeSubscriptions | None = None,
    ) -> None:
        self.queue: FakeOutbox = outbox or FakeOutbox()
        self.subscribers: FakeSubscriptions = subscriptions or FakeSubscriptions()

    @property
    def outbox(self) -> INotificationOutbox:
        return self.queue

    @property
    def subscriptions(self) -> ISubscriptionRepository:
        return self.subscribers

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return None


class FakeSender(INotificationSender):
    def __init__(self, *deliveries: Delivery) -> None:
        self.deliveries: list[Delivery] = list(deliveries)
        self.sent: list[Notification] = []
        self.statuses: list[NotificationStatus] = []

    @override
    async def send(self, notification: Notification) -> Delivery:
        self.sent.append(notification)
        self.statuses.append(notification.status)
        if not self.deliveries:
            return Delivered()
        return self.deliveries.pop(0)
