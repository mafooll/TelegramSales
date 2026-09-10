from dataclasses import dataclass

import pytest
from structlog.testing import capture_logs

from telegramsales.shared.domain.event import DomainEvent
from telegramsales.shared.infrastructure.events.bus import InProcessEventBus


@dataclass(frozen=True, kw_only=True)
class ProductCreated(DomainEvent):
    product_id: int


@dataclass(frozen=True, kw_only=True)
class ProductArchived(DomainEvent):
    product_id: int


class HandlerBoomError(Exception):
    pass


@pytest.fixture
def bus() -> InProcessEventBus:
    return InProcessEventBus()


async def test_subscribed_handler_receives_the_event(bus: InProcessEventBus) -> None:
    received: list[ProductCreated] = []

    async def remember(event: ProductCreated) -> None:
        received.append(event)

    bus.subscribe(ProductCreated, remember)
    event = ProductCreated(product_id=1)

    await bus.publish(event)

    assert received == [event]


async def test_handler_of_another_type_is_not_called(bus: InProcessEventBus) -> None:
    calls: list[str] = []

    async def on_archived(_event: ProductArchived) -> None:
        calls.append("archived")

    bus.subscribe(ProductArchived, on_archived)

    await bus.publish(ProductCreated(product_id=1))

    assert calls == []


async def test_publish_without_subscribers_does_nothing(
    bus: InProcessEventBus,
) -> None:
    await bus.publish(ProductCreated(product_id=1))


async def test_handlers_run_in_subscription_order(bus: InProcessEventBus) -> None:
    calls: list[str] = []

    async def first(_event: ProductCreated) -> None:
        calls.append("first")

    async def second(_event: ProductCreated) -> None:
        calls.append("second")

    bus.subscribe(ProductCreated, first)
    bus.subscribe(ProductCreated, second)

    await bus.publish(ProductCreated(product_id=1))

    assert calls == ["first", "second"]


async def test_failing_handler_does_not_stop_the_others(
    bus: InProcessEventBus,
) -> None:
    calls: list[str] = []

    async def broken(_event: ProductCreated) -> None:
        raise HandlerBoomError

    async def healthy(_event: ProductCreated) -> None:
        calls.append("healthy")

    bus.subscribe(ProductCreated, broken)
    bus.subscribe(ProductCreated, healthy)

    await bus.publish(ProductCreated(product_id=1))

    assert calls == ["healthy"]


async def test_failing_handler_is_logged_with_its_name(
    bus: InProcessEventBus,
) -> None:
    async def broken(_event: ProductCreated) -> None:
        raise HandlerBoomError

    bus.subscribe(ProductCreated, broken)
    event = ProductCreated(product_id=1)

    with capture_logs() as logs:
        await bus.publish(event)

    assert len(logs) == 1
    assert logs[0]["event"] == "event_handler_failed"
    assert logs[0]["log_level"] == "warning"
    assert logs[0]["event_type"] == "ProductCreated"
    assert logs[0]["event_id"] == str(event.event_id)
    assert logs[0]["handler"].endswith("broken")


async def test_subclass_event_does_not_reach_parent_handler(
    bus: InProcessEventBus,
) -> None:
    @dataclass(frozen=True, kw_only=True)
    class SpecialProductCreated(ProductCreated):
        reason: str

    calls: list[str] = []

    async def on_created(_event: ProductCreated) -> None:
        calls.append("created")

    bus.subscribe(ProductCreated, on_created)

    await bus.publish(SpecialProductCreated(product_id=1, reason="import"))

    assert calls == []


async def test_publish_all_delivers_every_event(bus: InProcessEventBus) -> None:
    received: list[int] = []

    async def remember(event: ProductCreated) -> None:
        received.append(event.product_id)

    bus.subscribe(ProductCreated, remember)

    await bus.publish_all(
        [ProductCreated(product_id=1), ProductCreated(product_id=2)],
    )

    assert received == [1, 2]
