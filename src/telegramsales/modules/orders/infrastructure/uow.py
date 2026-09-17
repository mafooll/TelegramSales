from telegramsales.modules.orders.application.ports import (
    ICartRepository,
    IOrderRepository,
    ISelectionRepository,
)
from telegramsales.modules.orders.infrastructure.repositories import (
    CartRepository,
    OrderRepository,
    SelectionRepository,
)
from telegramsales.shared.infrastructure.database.uow import UnitOfWork


class OrdersUnitOfWork(UnitOfWork):
    @property
    def carts(self) -> ICartRepository:
        return CartRepository(self.session)

    @property
    def selections(self) -> ISelectionRepository:
        return SelectionRepository(self.session)

    @property
    def orders(self) -> IOrderRepository:
        return OrderRepository(self.session)
