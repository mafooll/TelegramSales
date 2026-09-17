from collections.abc import Sequence

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InputRichMessage

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.application.ports import IOrderQueries
from telegramsales.modules.orders.application.queries import (
    CartLineView,
    CartView,
    OrderView,
    SelectionView,
)
from telegramsales.modules.orders.application.readers import CartReader
from telegramsales.modules.orders.presentation.bot.callbacks import (
    CartAction,
    CartCallback,
    OrderAction,
    OrderCallback,
)
from telegramsales.modules.orders.presentation.bot.screens import (
    CART,
    CART_LINE,
    CHECKOUT_CONFIRM,
    ORDER_CARD,
    ORDER_LIST,
    PLACED,
    PROMPT,
    SELECTION,
)
from telegramsales.modules.orders.presentation.bot.views import (
    CheckoutView,
    OrderListView,
    PlacedView,
    PromptView,
)
from telegramsales.shared.application.pagination import DEFAULT_PAGE_SIZE, Page
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.pagination import Pagination
from telegramsales.shared.presentation.bot.rich import rich_paged_screen, rich_screen


def _sliced[ItemType](
    items: Sequence[ItemType],
    number: int,
) -> Page[ItemType]:
    start = number * DEFAULT_PAGE_SIZE
    return Page(
        items=list(items[start : start + DEFAULT_PAGE_SIZE]),
        number=number,
        size=DEFAULT_PAGE_SIZE,
        total=len(items),
    )


def cart(
    context: RenderContext,
    view: CartView,
    number: int = 0,
) -> InputRichMessage:
    pagination = Pagination(
        page=_sliced(view.lines, number),
        callback=lambda value: CartCallback(
            action=CartAction.OPEN,
            page=value,
        ),
    )
    return rich_paged_screen(CART, pagination, view, context)


async def cart_of(
    reader: CartReader,
    context: RenderContext,
    customer_id: CustomerId,
    number: int = 0,
) -> InputRichMessage:
    return cart(context, await reader.read(customer_id), number)


def cart_line(context: RenderContext, line: CartLineView) -> InputRichMessage:
    return rich_screen(CART_LINE, line, context)


def prompt(
    context: RenderContext,
    message_key: str,
    back: CallbackData,
) -> InputRichMessage:
    return rich_screen(
        PROMPT, PromptView(message_key=message_key, back=back), context
    )


def checkout(context: RenderContext, view: CheckoutView) -> InputRichMessage:
    return rich_screen(CHECKOUT_CONFIRM, view, context)


def placed(context: RenderContext, number: str) -> InputRichMessage:
    return rich_screen(PLACED, PlacedView(number=number), context)


async def order_list(
    queries: IOrderQueries,
    context: RenderContext,
    customer_id: CustomerId,
    number: int = 0,
) -> InputRichMessage:
    page = await queries.list_for(customer_id, number, DEFAULT_PAGE_SIZE)
    pagination = Pagination(
        page=page,
        callback=lambda value: OrderCallback(
            action=OrderAction.LIST,
            page=value,
        ),
    )
    return rich_paged_screen(
        ORDER_LIST, pagination, OrderListView(total=page.total), context
    )


def order_card(context: RenderContext, order: OrderView) -> InputRichMessage:
    return rich_screen(ORDER_CARD, order, context)


def selection(context: RenderContext, view: SelectionView) -> InputRichMessage:
    return rich_screen(SELECTION, view, context)
