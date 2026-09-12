from typing import final, override

from telegramsales.modules.orders.application.commands.orders import (
    CancelOrderByManager,
    CancelOrderByManagerHandler,
    ChangeOrderStatus,
    ChangeOrderStatusHandler,
    TakeOrderInWork,
    TakeOrderInWorkHandler,
)
from telegramsales.modules.orders.contracts import IOrderDesk, OrderId, OrderStatus
from telegramsales.shared.application.access import Actor


@final
class OrderDesk(IOrderDesk):
    def __init__(
        self,
        take: TakeOrderInWorkHandler,
        change: ChangeOrderStatusHandler,
        cancel: CancelOrderByManagerHandler,
    ) -> None:
        self._take: TakeOrderInWorkHandler = take
        self._change: ChangeOrderStatusHandler = change
        self._cancel: CancelOrderByManagerHandler = cancel

    @override
    async def take_in_work(self, order_id: OrderId, actor: Actor) -> None:
        await self._take.handle(TakeOrderInWork(order_id=order_id), actor)

    @override
    async def change_status(
        self,
        order_id: OrderId,
        status: OrderStatus,
        actor: Actor,
    ) -> None:
        await self._change.handle(
            ChangeOrderStatus(order_id=order_id, status=status),
            actor,
        )

    @override
    async def cancel(self, order_id: OrderId, actor: Actor) -> None:
        await self._cancel.handle(CancelOrderByManager(order_id=order_id), actor)
