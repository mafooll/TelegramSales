from dishka import AsyncContainer, Scope

from telegramsales.modules.desk import (
    PublishOrderCard,
    PublishOrderCardHandler,
    RedrawOrderCard,
    RedrawOrderCardHandler,
)
from telegramsales.modules.orders.domain.events import (
    OrderPlaced,
    OrderStatusChanged,
)
from telegramsales.shared.infrastructure.events.bus import InProcessEventBus


def subscribe_desk(bus: InProcessEventBus, container: AsyncContainer) -> None:
    async def publish_card(event: OrderPlaced) -> None:
        async with container(scope=Scope.REQUEST) as request:
            handler = await request.get(PublishOrderCardHandler)
            await handler.handle(PublishOrderCard(order_id=event.order_id))

    async def redraw_card(event: OrderStatusChanged) -> None:
        async with container(scope=Scope.REQUEST) as request:
            handler = await request.get(RedrawOrderCardHandler)
            await handler.handle(RedrawOrderCard(order_id=event.order_id))

    bus.subscribe(OrderPlaced, publish_card)
    bus.subscribe(OrderStatusChanged, redraw_card)
