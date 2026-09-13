from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.notifications.contracts import (
    CallToAction,
    NotificationId,
    RecipientId,
)
from telegramsales.modules.notifications.domain.entities import Notification
from telegramsales.modules.notifications.domain.enums import NotificationStatus
from telegramsales.modules.notifications.infrastructure.repositories import (
    LEASE,
    NotificationOutbox,
    SubscriptionRepository,
)
from tests.notifications.factories import (
    BUYER,
    FRIEND,
    LATER,
    NOW,
    ORDER_MOVED,
    make_subscription,
)

pytestmark = pytest.mark.db

BATCH = 10


async def queue(
    outbox: NotificationOutbox,
    *,
    dedup_key: str | None = None,
    available_at: datetime = NOW,
    action: CallToAction | None = None,
) -> NotificationId:
    notification = Notification(
        id=await outbox.next_id(),
        recipient_id=BUYER,
        key=ORDER_MOVED,
        args={"number": "2026-09-13-0001"},
        action=action,
        dedup_key=dedup_key,
        available_at=available_at,
        created_at=NOW,
    )
    await outbox.add(notification)
    return notification.id


async def test_a_notification_survives_a_round_trip(session: AsyncSession) -> None:
    outbox = NotificationOutbox(session)
    await queue(outbox)

    claimed = await outbox.claim(BATCH, NOW)

    assert len(claimed) == 1
    assert claimed[0].key == ORDER_MOVED
    assert claimed[0].args == {"number": "2026-09-13-0001"}
    assert claimed[0].recipient_id == BUYER


async def test_a_duplicate_is_refused(session: AsyncSession) -> None:
    outbox = NotificationOutbox(session)
    await queue(outbox, dedup_key="new-product:42:1000")
    twin = Notification.queue(
        notification_id=await outbox.next_id(),
        recipient_id=BUYER,
        key=ORDER_MOVED,
        dedup_key="new-product:42:1000",
        now=NOW,
    )

    assert not await outbox.add(twin)
    assert len(await outbox.claim(BATCH, NOW)) == 1


async def test_claiming_leases_the_row(session: AsyncSession) -> None:
    outbox = NotificationOutbox(session)
    await queue(outbox)

    first = await outbox.claim(BATCH, NOW)
    second = await outbox.claim(BATCH, NOW)

    assert len(first) == 1
    assert second == []
    assert first[0].available_at == NOW + LEASE


async def test_a_lease_runs_out(session: AsyncSession) -> None:
    outbox = NotificationOutbox(session)
    await queue(outbox)
    await outbox.claim(BATCH, NOW)

    again = await outbox.claim(BATCH, NOW + LEASE + timedelta(seconds=1))

    assert len(again) == 1


async def test_a_notification_from_the_future_is_not_claimed(
    session: AsyncSession,
) -> None:
    outbox = NotificationOutbox(session)
    await queue(outbox, available_at=LATER)

    assert await outbox.claim(BATCH, NOW) == []


async def test_a_sent_notification_leaves_the_queue(session: AsyncSession) -> None:
    outbox = NotificationOutbox(session)
    await queue(outbox)
    claimed = (await outbox.claim(BATCH, NOW))[0]

    claimed.sent()
    await outbox.save(claimed)

    assert await outbox.claim(BATCH, NOW + LEASE + timedelta(seconds=1)) == []


async def test_a_postponed_notification_comes_back(session: AsyncSession) -> None:
    outbox = NotificationOutbox(session)
    await queue(outbox)
    claimed = (await outbox.claim(BATCH, NOW))[0]

    claimed.postponed(until=NOW + timedelta(seconds=30))
    await outbox.save(claimed)
    again = await outbox.claim(BATCH, NOW + timedelta(seconds=31))

    assert len(again) == 1
    assert again[0].attempts == 1
    assert again[0].status is NotificationStatus.PENDING


async def test_a_subscription_survives_a_round_trip(session: AsyncSession) -> None:
    subscriptions = SubscriptionRepository(session)
    await subscriptions.add(make_subscription())

    loaded = await subscriptions.get(BUYER)

    assert loaded is not None
    assert loaded.is_on
    assert loaded.created_at == NOW


async def test_a_switched_subscription_is_saved(session: AsyncSession) -> None:
    subscriptions = SubscriptionRepository(session)
    await subscriptions.add(make_subscription())
    stored = await subscriptions.get(BUYER)
    assert stored is not None

    stored.switch(enabled=False)
    await subscriptions.save(stored)

    loaded = await subscriptions.get(BUYER)
    assert loaded is not None
    assert not loaded.is_on


async def test_only_the_switched_on_are_recipients(session: AsyncSession) -> None:
    subscriptions = SubscriptionRepository(session)
    await subscriptions.add(make_subscription(BUYER))
    await subscriptions.add(make_subscription(FRIEND, is_on=False))

    assert await subscriptions.recipients() == [BUYER]


async def test_an_unknown_recipient_has_no_subscription(
    session: AsyncSession,
) -> None:
    assert await SubscriptionRepository(session).get(BUYER) is None


async def test_a_call_to_action_survives_a_round_trip(
    session: AsyncSession,
) -> None:
    outbox = NotificationOutbox(session)
    action = CallToAction(key="orders-open-orders-button", data="orders:list")
    stored = await queue(outbox, action=action)

    claimed = await outbox.claim(BATCH, NOW)

    assert [notification.id for notification in claimed] == [stored]
    assert claimed[0].action == action


async def test_a_notification_without_an_action_keeps_none(
    session: AsyncSession,
) -> None:
    outbox = NotificationOutbox(session)
    await queue(outbox)

    claimed = await outbox.claim(BATCH, NOW)

    assert claimed[0].action is None


async def test_a_batch_of_identifiers_is_issued_at_once(
    session: AsyncSession,
) -> None:
    outbox = NotificationOutbox(session)

    issued = await outbox.next_ids(3)

    assert len(set(issued)) == 3
    assert issued == sorted(issued)


async def test_no_identifiers_are_issued_for_an_empty_batch(
    session: AsyncSession,
) -> None:
    assert await NotificationOutbox(session).next_ids(0) == []


async def test_a_batch_insert_skips_the_duplicates(session: AsyncSession) -> None:
    outbox = NotificationOutbox(session)
    await queue(outbox, dedup_key="new-product:coat:1000")
    issued = await outbox.next_ids(2)
    batch = [
        Notification(
            id=notification_id,
            recipient_id=RecipientId(recipient),
            key=ORDER_MOVED,
            dedup_key=f"new-product:coat:{recipient}",
            available_at=NOW,
            created_at=NOW,
        )
        for notification_id, recipient in zip(
            issued, (BUYER, FRIEND), strict=True
        )
    ]

    queued = await outbox.add_all(batch)

    assert queued == 1
    assert len(await outbox.claim(BATCH, NOW)) == 2
