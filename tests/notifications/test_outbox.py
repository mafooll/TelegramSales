from datetime import timedelta

import pytest

from telegramsales.modules.notifications.application.commands.dispatch import (
    DispatchOutbox,
    DispatchOutboxHandler,
)
from telegramsales.modules.notifications.application.commands.enqueue import (
    EnqueueNotification,
    EnqueueNotificationHandler,
)
from telegramsales.modules.notifications.application.ports import (
    Delivered,
    Postponed,
    Refused,
)
from telegramsales.modules.notifications.contracts import NotificationId
from telegramsales.modules.notifications.domain.enums import NotificationStatus
from telegramsales.modules.notifications.domain.exceptions import (
    NotificationAlreadyClosedError,
)
from tests.notifications.factories import (
    BUYER,
    LATER,
    NOW,
    ORDER_MOVED,
    make_notification,
)
from tests.notifications.fakes import (
    FakeNotificationsUnitOfWork,
    FakeOutbox,
    FakeSender,
)
from tests.orders.fakes import FixedClock

CLOCK = FixedClock(NOW)


def enqueueing(
    outbox: FakeOutbox | None = None,
) -> tuple[EnqueueNotificationHandler, FakeNotificationsUnitOfWork]:
    uow = FakeNotificationsUnitOfWork(outbox)
    return EnqueueNotificationHandler(uow, CLOCK), uow


def dispatching(
    outbox: FakeOutbox,
    sender: FakeSender | None = None,
) -> tuple[DispatchOutboxHandler, FakeNotificationsUnitOfWork, FakeSender]:
    uow = FakeNotificationsUnitOfWork(outbox)
    posting = sender or FakeSender()
    return DispatchOutboxHandler(uow, posting, CLOCK), uow, posting


async def test_a_queued_notification_waits_in_the_outbox() -> None:
    handler, uow = enqueueing()

    queued = await handler.handle(
        EnqueueNotification(recipient_id=BUYER, key=ORDER_MOVED)
    )
    stored = next(iter(uow.queue.notifications.values()))

    assert queued
    assert stored.status is NotificationStatus.PENDING
    assert stored.available_at == NOW
    assert stored.attempts == 0


async def test_the_same_notification_is_queued_once() -> None:
    handler, uow = enqueueing()
    command = EnqueueNotification(
        recipient_id=BUYER,
        key=ORDER_MOVED,
        dedup_key="new-product:42:1000",
    )

    assert await handler.handle(command)
    assert not await handler.handle(command)
    assert len(uow.queue.notifications) == 1


async def test_dispatching_sends_what_is_due() -> None:
    outbox = FakeOutbox(make_notification(1), make_notification(2))
    handler, uow, sender = dispatching(outbox)

    dispatched = await handler.handle(DispatchOutbox())

    assert dispatched == 2
    assert len(sender.sent) == 2
    assert all(
        notification.status is NotificationStatus.SENT
        for notification in uow.queue.notifications.values()
    )


async def test_a_notification_from_the_future_waits() -> None:
    outbox = FakeOutbox(make_notification(1, available_at=LATER))
    handler, _, sender = dispatching(outbox)

    assert await handler.handle(DispatchOutbox()) == 0
    assert sender.sent == []


async def test_a_batch_is_limited() -> None:
    outbox = FakeOutbox(*(make_notification(number) for number in range(1, 6)))
    handler, _, sender = dispatching(outbox)

    assert await handler.handle(DispatchOutbox(limit=2)) == 2
    assert len(sender.sent) == 2


async def test_a_rate_limit_postpones_the_notification() -> None:
    outbox = FakeOutbox(make_notification(1))
    handler, uow, _ = dispatching(outbox, FakeSender(Postponed(seconds=30)))

    await handler.handle(DispatchOutbox())
    stored = uow.queue.notifications[NotificationId(1)]

    assert stored.status is NotificationStatus.PENDING
    assert stored.available_at == NOW + timedelta(seconds=30)
    assert stored.attempts == 1


async def test_a_refused_notification_is_not_retried() -> None:
    outbox = FakeOutbox(make_notification(1))
    handler, uow, _ = dispatching(outbox, FakeSender(Refused(reason="bot blocked")))

    await handler.handle(DispatchOutbox())
    stored = uow.queue.notifications[NotificationId(1)]

    assert stored.status is NotificationStatus.REJECTED
    assert stored.reason == "bot blocked"
    assert await handler.handle(DispatchOutbox()) == 0


async def test_the_outcome_is_written_after_the_send() -> None:
    outbox = FakeOutbox(make_notification(1))
    handler, uow, sender = dispatching(outbox, FakeSender(Delivered()))

    await handler.handle(DispatchOutbox())

    stored = uow.queue.notifications[NotificationId(1)]

    assert sender.statuses == [NotificationStatus.PENDING]
    assert stored.status is NotificationStatus.SENT


async def test_a_closed_notification_is_not_touched_again() -> None:
    notification = make_notification(1)
    notification.sent()

    with pytest.raises(NotificationAlreadyClosedError):
        notification.rejected(reason="too late")
