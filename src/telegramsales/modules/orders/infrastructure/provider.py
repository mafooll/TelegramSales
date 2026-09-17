from typing import final

from dishka import (
    Provider,
    Scope,
    provide,  # pyright: ignore[reportUnknownVariableType]
    provide_all,
)
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.orders.application.commands.cart import (
    AddToCartHandler,
    ClearCartHandler,
    DecreaseCartItemHandler,
    IncreaseCartItemHandler,
    RemoveCartItemHandler,
)
from telegramsales.modules.orders.application.commands.orders import (
    CancelOrderByManagerHandler,
    CancelOrderHandler,
    ChangeOrderStatusHandler,
    PlaceOrderHandler,
    TakeOrderInWorkHandler,
)
from telegramsales.modules.orders.application.commands.selections import (
    AdoptSelectionHandler,
    ShareCartHandler,
)
from telegramsales.modules.orders.application.desk import OrderDesk
from telegramsales.modules.orders.application.ports import (
    ICartQueries,
    IOrderQueries,
    IOrdersUnitOfWork,
    ISelectionQueries,
)
from telegramsales.modules.orders.application.readers import (
    CartReader,
    SelectionReader,
)
from telegramsales.modules.orders.contracts import (
    IOrderCards,
    IOrderDesk,
    IOrderPresence,
)
from telegramsales.modules.orders.infrastructure.queries import (
    CartQueries,
    OrderCards,
    OrderPresence,
    OrderQueries,
    SelectionQueries,
)
from telegramsales.modules.orders.infrastructure.uow import OrdersUnitOfWork
from telegramsales.shared.infrastructure.database.manager import DatabaseManager


@final
class OrdersProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def unit_of_work(self, manager: DatabaseManager) -> IOrdersUnitOfWork:
        return OrdersUnitOfWork(manager.session)

    @provide
    def cart_queries(self, session: AsyncSession) -> ICartQueries:
        return CartQueries(session)

    @provide
    def selection_queries(self, session: AsyncSession) -> ISelectionQueries:
        return SelectionQueries(session)

    @provide
    def order_queries(self, session: AsyncSession) -> IOrderQueries:
        return OrderQueries(session)

    @provide
    def order_cards(self, session: AsyncSession) -> IOrderCards:
        return OrderCards(session)

    @provide
    def order_presence(self, session: AsyncSession) -> IOrderPresence:
        return OrderPresence(session)

    @provide
    def order_desk(
        self,
        take: TakeOrderInWorkHandler,
        change: ChangeOrderStatusHandler,
        cancel: CancelOrderByManagerHandler,
    ) -> IOrderDesk:
        return OrderDesk(take, change, cancel)

    readers = provide_all(CartReader, SelectionReader)

    handlers = provide_all(
        AddToCartHandler,
        IncreaseCartItemHandler,
        DecreaseCartItemHandler,
        RemoveCartItemHandler,
        ClearCartHandler,
        ShareCartHandler,
        AdoptSelectionHandler,
        PlaceOrderHandler,
        CancelOrderHandler,
        TakeOrderInWorkHandler,
        ChangeOrderStatusHandler,
        CancelOrderByManagerHandler,
    )
