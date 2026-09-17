from telegramsales.modules.notifications.application.commands.announce import (
    Announce,
    AnnounceHandler,
)
from telegramsales.modules.notifications.application.commands.dispatch import (
    DispatchOutbox,
    DispatchOutboxHandler,
)
from telegramsales.modules.notifications.application.commands.subscriptions import (
    OpenSubscription,
    OpenSubscriptionHandler,
    SwitchSubscription,
    SwitchSubscriptionHandler,
)
from telegramsales.modules.notifications.application.ports import (
    Delivered,
    Refused,
)
from telegramsales.modules.notifications.application.readers import (
    SubscriptionReader,
)
from tests.notifications.factories import (
    BUYER,
    FRIEND,
    NEW_PRODUCT,
    NOW,
    STRANGER,
    make_notification,
    make_subscription,
)
from tests.notifications.fakes import (
    FakeNotificationsUnitOfWork,
    FakeOutbox,
    FakeSender,
    FakeSubscriptions,
)
from tests.orders.fakes import FixedClock

CLOCK = FixedClock(NOW)
TOPIC = "new-product:coat"
BLOCKED = "Forbidden: bot was blocked by the user"


async def test_the_first_order_opens_a_subscription() -> None:
    uow = FakeNotificationsUnitOfWork()

    opened = await OpenSubscriptionHandler(uow, CLOCK).handle(
        OpenSubscription(recipient_id=BUYER)
    )

    assert opened
    assert await uow.subscribers.recipients() == [BUYER]


async def test_the_second_order_changes_nothing() -> None:
    uow = FakeNotificationsUnitOfWork(None, FakeSubscriptions(make_subscription()))

    opened = await OpenSubscriptionHandler(uow, CLOCK).handle(
        OpenSubscription(recipient_id=BUYER)
    )

    assert not opened


async def test_a_reopened_subscription_keeps_being_off() -> None:
    uow = FakeNotificationsUnitOfWork(
        None,
        FakeSubscriptions(make_subscription(is_on=False)),
    )

    await OpenSubscriptionHandler(uow, CLOCK).handle(
        OpenSubscription(recipient_id=BUYER)
    )

    assert await uow.subscribers.recipients() == []


async def test_the_switch_turns_the_news_off_and_on() -> None:
    uow = FakeNotificationsUnitOfWork(None, FakeSubscriptions(make_subscription()))
    handler = SwitchSubscriptionHandler(uow)

    assert not await handler.handle(
        SwitchSubscription(recipient_id=BUYER, enabled=False)
    )
    assert await handler.handle(
        SwitchSubscription(recipient_id=BUYER, enabled=True)
    )


async def test_a_stranger_has_nothing_to_switch() -> None:
    uow = FakeNotificationsUnitOfWork()

    assert not await SwitchSubscriptionHandler(uow).handle(
        SwitchSubscription(recipient_id=BUYER, enabled=True)
    )


async def test_the_reader_tells_the_three_states() -> None:
    uow = FakeNotificationsUnitOfWork(
        None,
        FakeSubscriptions(
            make_subscription(BUYER),
            make_subscription(FRIEND, is_on=False),
        ),
    )
    reader = SubscriptionReader(uow)

    assert await reader.state_of(BUYER) is True
    assert await reader.state_of(FRIEND) is False
    assert await reader.state_of(STRANGER) is None


async def test_an_announcement_reaches_every_subscriber() -> None:
    uow = FakeNotificationsUnitOfWork(
        None,
        FakeSubscriptions(make_subscription(BUYER), make_subscription(FRIEND)),
    )

    queued = await AnnounceHandler(uow, CLOCK).handle(
        Announce(key=NEW_PRODUCT, topic=TOPIC)
    )

    assert queued == 2
    assert {
        notification.recipient_id
        for notification in uow.queue.notifications.values()
    } == {BUYER, FRIEND}


async def test_an_announcement_skips_the_unsubscribed() -> None:
    uow = FakeNotificationsUnitOfWork(
        None,
        FakeSubscriptions(
            make_subscription(BUYER),
            make_subscription(FRIEND, is_on=False),
        ),
    )

    queued = await AnnounceHandler(uow, CLOCK).handle(
        Announce(key=NEW_PRODUCT, topic=TOPIC)
    )

    assert queued == 1


async def test_the_same_product_is_announced_once() -> None:
    uow = FakeNotificationsUnitOfWork(
        None,
        FakeSubscriptions(make_subscription(BUYER)),
    )
    handler = AnnounceHandler(uow, CLOCK)

    assert await handler.handle(Announce(key=NEW_PRODUCT, topic=TOPIC)) == 1
    assert await handler.handle(Announce(key=NEW_PRODUCT, topic=TOPIC)) == 0


async def test_a_blocked_recipient_stops_getting_the_news() -> None:
    outbox = FakeOutbox(make_notification())
    uow = FakeNotificationsUnitOfWork(
        outbox,
        FakeSubscriptions(make_subscription(BUYER)),
    )
    sender = FakeSender(Refused(reason=BLOCKED))

    await DispatchOutboxHandler(uow, sender, CLOCK).handle(DispatchOutbox())

    assert await uow.subscribers.recipients() == []


async def test_a_delivered_notification_keeps_the_subscription() -> None:
    outbox = FakeOutbox(make_notification())
    uow = FakeNotificationsUnitOfWork(
        outbox,
        FakeSubscriptions(make_subscription(BUYER)),
    )
    sender = FakeSender(Delivered())

    await DispatchOutboxHandler(uow, sender, CLOCK).handle(DispatchOutbox())

    assert await uow.subscribers.recipients() == [BUYER]
