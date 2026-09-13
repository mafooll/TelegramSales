import asyncio
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress
from dataclasses import dataclass
from functools import partial

from dishka import AsyncContainer, Scope
import structlog
from structlog.stdlib import BoundLogger

from telegramsales.modules.catalog.domain.events import ProductPublished
from telegramsales.modules.catalog.presentation.bot import shop_texts
from telegramsales.modules.notifications import (
    Announce,
    AnnounceHandler,
    DispatchOutbox,
    DispatchOutboxHandler,
    OpenSubscription,
    OpenSubscriptionHandler,
)
from telegramsales.modules.notifications.contracts import (
    INotifications,
    NotificationArgs,
    RecipientId,
)
from telegramsales.modules.orders import notice_key
from telegramsales.modules.orders.domain.enums import OrderStatus
from telegramsales.modules.orders.domain.events import (
    OrderCancelled,
    OrderPlaced,
    OrderStatusChanged,
)
from telegramsales.shared.infrastructure.events.bus import InProcessEventBus

logger: BoundLogger = structlog.get_logger()

IDLE_PAUSE = 1.0
FAILURE_PAUSE = 5.0

type Tick = Callable[[], Awaitable[int]]

NUMBER_ARGUMENT = "number"
TITLE_ARGUMENT = "title"
ARTICLE_ARGUMENT = "article"
NEW_PRODUCT_TOPIC = "new-product"


@dataclass(frozen=True, slots=True)
class Notice:
    recipient_id: RecipientId
    key: str
    args: NotificationArgs
    dedup_key: str


def status_notice(event: OrderStatusChanged) -> Notice | None:
    if event.status is OrderStatus.CANCELLED:
        return None

    key = notice_key(event.status)
    if key is None:
        return None

    return Notice(
        recipient_id=RecipientId(event.customer_id),
        key=key,
        args={NUMBER_ARGUMENT: event.number},
        dedup_key=f"order-status:{event.order_id}:{event.status.value}",
    )


def cancellation_notice(event: OrderCancelled) -> Notice | None:
    if event.manager_id is None:
        return None

    key = notice_key(OrderStatus.CANCELLED)
    if key is None:
        return None

    return Notice(
        recipient_id=RecipientId(event.customer_id),
        key=key,
        args={NUMBER_ARGUMENT: event.number},
        dedup_key=f"order-cancelled:{event.order_id}",
    )


def new_product_announcement(event: ProductPublished) -> Announce:
    return Announce(
        key=shop_texts.NEW_PRODUCT,
        args={
            TITLE_ARGUMENT: event.title,
            ARTICLE_ARGUMENT: event.article,
        },
        topic=f"{NEW_PRODUCT_TOPIC}:{event.product_id}",
    )


def subscribe_notifications(
    bus: InProcessEventBus,
    container: AsyncContainer,
) -> None:
    async def enqueue(notice: Notice | None) -> None:
        if notice is None:
            return

        async with container(scope=Scope.REQUEST) as request:
            notifications = await request.get(INotifications)
            await notifications.enqueue(
                notice.recipient_id,
                notice.key,
                notice.args,
                notice.dedup_key,
            )

    async def notify_about_status(event: OrderStatusChanged) -> None:
        await enqueue(status_notice(event))

    async def notify_about_cancellation(event: OrderCancelled) -> None:
        await enqueue(cancellation_notice(event))

    async def open_subscription(event: OrderPlaced) -> None:
        async with container(scope=Scope.REQUEST) as request:
            handler = await request.get(OpenSubscriptionHandler)
            await handler.handle(
                OpenSubscription(recipient_id=RecipientId(event.customer_id))
            )

    async def announce_product(event: ProductPublished) -> None:
        async with container(scope=Scope.REQUEST) as request:
            handler = await request.get(AnnounceHandler)
            await handler.handle(new_product_announcement(event))

    bus.subscribe(OrderStatusChanged, notify_about_status)
    bus.subscribe(OrderCancelled, notify_about_cancellation)
    bus.subscribe(OrderPlaced, open_subscription)
    bus.subscribe(ProductPublished, announce_product)


async def dispatch_once(container: AsyncContainer) -> int:
    async with container(scope=Scope.REQUEST) as request:
        handler = await request.get(DispatchOutboxHandler)
        return await handler.handle(DispatchOutbox())


async def run_outbox(
    tick: Tick,
    *,
    idle_pause: float = IDLE_PAUSE,
    failure_pause: float = FAILURE_PAUSE,
) -> None:
    while True:
        try:
            dispatched = await tick()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("outbox_tick_failed")
            await asyncio.sleep(failure_pause)
            continue

        if not dispatched:
            await asyncio.sleep(idle_pause)


@asynccontextmanager
async def outbox_worker(container: AsyncContainer) -> AsyncGenerator[None]:
    worker = asyncio.create_task(run_outbox(partial(dispatch_once, container)))
    try:
        yield
    finally:
        worker.cancel()
        with suppress(asyncio.CancelledError):
            await worker
