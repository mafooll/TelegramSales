from dataclasses import dataclass, replace

from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.filters.callback_data import CallbackData
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
from telegramsales.modules.notifications import (
    SubscriptionReader,
    SwitchSubscription,
    SwitchSubscriptionHandler,
)
from telegramsales.modules.notifications.contracts import RecipientId
from telegramsales.modules.orders.presentation.bot.buttons import (
    open_cart,
    open_orders,
)
from telegramsales.modules.staff.application.commands.preferences import (
    SwitchCustomerView,
    SwitchCustomerViewHandler,
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


@dataclass(frozen=True, slots=True)
class MenuView:
    is_shopping: bool
    news: bool | None


class ViewModeCallback(CallbackData, prefix="mode"):
    pass


class NewsCallback(CallbackData, prefix="news"):
    pass


OPEN_SHOP: Button[MenuView] = Button(
    text=label(texts.OPEN_SHOP_BUTTON),
    callback=lambda _: ShopCallback(action=ShopAction.CATALOGS),
    for_customers=True,
)

OPEN_STAFF: Button[MenuView] = Button(
    text=label(texts.OPEN_STAFF_BUTTON),
    callback=lambda _: StaffCallback(action=StaffAction.LIST),
    permission=StaffPermission.VIEW_STAFF,
    when=lambda view: not view.is_shopping,
)

OPEN_CATALOG: Button[MenuView] = Button(
    text=label(texts.OPEN_CATALOG_BUTTON),
    callback=lambda _: CatalogCallback(action=CatalogAction.HUB),
    permission=CatalogPermission.MANAGE,
    when=lambda view: not view.is_shopping,
)

SWITCH_NEWS: Button[MenuView] = Button(
    text=lambda view, translate: translate(
        texts.NEWS_ON_BUTTON if view.news else texts.NEWS_OFF_BUTTON
    ),
    callback=lambda _: NewsCallback(),
    for_customers=True,
    when=lambda view: view.news is not None,
)

SWITCH_VIEW: Button[MenuView] = Button(
    text=lambda view, translate: translate(
        texts.HIDE_SHOP_BUTTON if view.is_shopping else texts.SHOW_SHOP_BUTTON
    ),
    callback=lambda _: ViewModeCallback(),
    for_staff=True,
)

MAIN_MENU: Screen[MenuView] = Screen(
    content=label(texts.GREETING),
    buttons=[
        OPEN_SHOP,
        open_cart(for_customers=True),
        open_orders(for_customers=True),
        SWITCH_NEWS,
        OPEN_CATALOG,
        OPEN_STAFF,
        SWITCH_VIEW,
    ],
    layout=(1, 2),
)

router = Router(name="menu")
router.message.filter(HasActorFilter())
router.callback_query.filter(HasActorFilter())


async def _main_menu(
    context: RenderContext,
    news: SubscriptionReader,
) -> InputRichMessage:
    view = MenuView(
        is_shopping=context.actor.is_shopping,
        news=await news.state_of(RecipientId(context.actor.id)),
    )
    return rich_screen(MAIN_MENU, view, context)


@router.message(CommandStart())
async def start(
    message: Message,
    bot: Bot,
    context: RenderContext,
    customers: FromDishka[ICustomerDirectory],
    news: FromDishka[SubscriptionReader],
) -> None:
    if message.from_user is not None:
        await customers.register(
            CustomerId(message.from_user.id),
            message.from_user.full_name,
        )

    await bot.send_rich_message(
        chat_id=message.chat.id,
        rich_message=await _main_menu(context, news),
    )


@router.callback_query(HomeCallback.filter())
async def open_menu(
    callback: CallbackQuery,
    context: RenderContext,
    news: FromDishka[SubscriptionReader],
) -> None:
    await show(callback, await _main_menu(context, news))


@router.callback_query(ViewModeCallback.filter())
async def switch_view(
    callback: CallbackQuery,
    context: RenderContext,
    handler: FromDishka[SwitchCustomerViewHandler],
    news: FromDishka[SubscriptionReader],
) -> None:
    enabled = await handler.handle(
        SwitchCustomerView(enabled=not context.actor.is_shopping),
        context.actor,
    )
    switched = replace(
        context,
        actor=replace(context.actor, is_shopping=enabled),
    )
    await show(callback, await _main_menu(switched, news))


@router.callback_query(NewsCallback.filter())
async def switch_news(
    callback: CallbackQuery,
    context: RenderContext,
    handler: FromDishka[SwitchSubscriptionHandler],
    news: FromDishka[SubscriptionReader],
) -> None:
    recipient_id = RecipientId(context.actor.id)
    state = await news.state_of(recipient_id)
    if state is None:
        return

    await handler.handle(
        SwitchSubscription(recipient_id=recipient_id, enabled=not state)
    )
    await show(callback, await _main_menu(context, news))
