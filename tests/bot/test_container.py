from dishka import Scope
import pytest

from telegramsales.apps.bot.container import container_context
from telegramsales.modules.catalog.application.ports import (
    ICatalogQueries,
    IProductQueries,
    IShopQueries,
)
from telegramsales.modules.catalog.contracts import ICatalogOffers
from telegramsales.modules.customers.contracts import ICustomerDirectory
from telegramsales.modules.desk.application.commands.cards import (
    PublishOrderCardHandler,
    RedrawOrderCardHandler,
)
from telegramsales.modules.desk.application.commands.relay import (
    EditFromCustomerHandler,
    EditFromTopicHandler,
    ReactFromCustomerHandler,
    ReactFromTopicHandler,
    RelayToCustomerHandler,
    RelayToTopicHandler,
)
from telegramsales.modules.desk.application.ports import ICustomerChat, IWorkChat
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
from telegramsales.modules.orders.application.ports import IOrderQueries
from telegramsales.modules.orders.application.readers import (
    CartReader,
    SelectionReader,
)
from telegramsales.modules.orders.contracts import (
    IOrderCards,
    IOrderDesk,
    IOrderPresence,
)
from telegramsales.modules.staff.application.commands.preferences import (
    SwitchCustomerViewHandler,
)
from telegramsales.modules.staff.application.ports import IStaffQueries

REQUESTED = [
    ICatalogQueries,
    IProductQueries,
    IShopQueries,
    ICatalogOffers,
    ICustomerDirectory,
    IStaffQueries,
    IOrderQueries,
    IOrderCards,
    IOrderDesk,
    IOrderPresence,
    CartReader,
    SelectionReader,
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
    SwitchCustomerViewHandler,
    IWorkChat,
    ICustomerChat,
    PublishOrderCardHandler,
    RedrawOrderCardHandler,
    RelayToTopicHandler,
    RelayToCustomerHandler,
    EditFromCustomerHandler,
    EditFromTopicHandler,
    ReactFromCustomerHandler,
    ReactFromTopicHandler,
]


@pytest.mark.parametrize("requested", REQUESTED, ids=lambda kind: kind.__name__)
async def test_every_entry_point_is_resolvable(requested: type) -> None:
    async with (
        container_context() as container,
        container(scope=Scope.REQUEST) as request,
    ):
        assert await request.get(requested) is not None
