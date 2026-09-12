from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InputRichMessage, Message
from dishka.integrations.aiogram import FromDishka

from telegramsales.apps.bot import texts
from telegramsales.modules.catalog.domain.permissions import CatalogPermission
from telegramsales.modules.catalog.presentation.bot.callbacks import (
    CatalogAction,
    CatalogCallback,
)
from telegramsales.modules.catalog.presentation.bot.shop_callbacks import (
    ShopAction,
    ShopCallback,
)
from telegramsales.modules.customers.contracts import (
    CustomerId,
    ICustomerDirectory,
)
from telegramsales.modules.orders.presentation.bot.buttons import (
    open_cart,
    open_orders,
)
from telegramsales.modules.staff.domain.permissions import StaffPermission
from telegramsales.modules.staff.presentation.bot.callbacks import (
    StaffAction,
    StaffCallback,
)
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.filters import HasActorFilter
from telegramsales.shared.presentation.bot.keyboard import Button, Screen, label
from telegramsales.shared.presentation.bot.navigation import HomeCallback
from telegramsales.shared.presentation.bot.render import show
from telegramsales.shared.presentation.bot.rich import rich_screen

OPEN_SHOP: Button[None] = Button(
    text=label(texts.OPEN_SHOP_BUTTON),
    callback=lambda _: ShopCallback(action=ShopAction.CATALOGS),
)

OPEN_STAFF: Button[None] = Button(
    text=label(texts.OPEN_STAFF_BUTTON),
    callback=lambda _: StaffCallback(action=StaffAction.LIST),
    permission=StaffPermission.VIEW_STAFF,
)

OPEN_CATALOG: Button[None] = Button(
    text=label(texts.OPEN_CATALOG_BUTTON),
    callback=lambda _: CatalogCallback(action=CatalogAction.HUB),
    permission=CatalogPermission.MANAGE,
)

MAIN_MENU: Screen[None] = Screen(
    content=label(texts.GREETING),
    buttons=[
        OPEN_SHOP,
        open_cart(),
        open_orders(),
        OPEN_CATALOG,
        OPEN_STAFF,
    ],
    layout=(1, 2),
)

router = Router(name="menu")
router.message.filter(HasActorFilter())
router.callback_query.filter(HasActorFilter())


def _main_menu(context: RenderContext) -> InputRichMessage:
    return rich_screen(MAIN_MENU, None, context)


@router.message(CommandStart())
async def start(
    message: Message,
    bot: Bot,
    context: RenderContext,
    customers: FromDishka[ICustomerDirectory],
) -> None:
    if message.from_user is not None:
        await customers.register(
            CustomerId(message.from_user.id),
            message.from_user.full_name,
        )

    await bot.send_rich_message(
        chat_id=message.chat.id,
        rich_message=_main_menu(context),
    )


@router.callback_query(HomeCallback.filter())
async def open_menu(callback: CallbackQuery, context: RenderContext) -> None:
    await callback.answer()
    await show(callback, _main_menu(context))
