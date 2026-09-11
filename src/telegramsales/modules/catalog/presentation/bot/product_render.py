from aiogram.filters.callback_data import CallbackData
from aiogram.types import InputRichMessage

from telegramsales.modules.catalog.application.ports import IProductQueries
from telegramsales.modules.catalog.application.queries import (
    MediaView,
    ProductView,
    VariantView,
)
from telegramsales.modules.catalog.contracts import CategoryId
from telegramsales.modules.catalog.presentation.bot.product_callbacks import (
    ProductAction,
    ProductCallback,
)
from telegramsales.modules.catalog.presentation.bot.product_screens import (
    MEDIA_BOARD,
    PRODUCT_CARD,
    PRODUCT_LIST,
    VARIANT_BOARD,
)
from telegramsales.modules.catalog.presentation.bot.screens import PROMPT
from telegramsales.modules.catalog.presentation.bot.views import (
    ProductListView,
    PromptView,
)
from telegramsales.shared.application.pagination import DEFAULT_PAGE_SIZE, Page
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.pagination import Pagination
from telegramsales.shared.presentation.bot.rich import rich_paged_screen, rich_screen

UNPAGED = 100


def _whole[ItemType](items: list[ItemType]) -> Pagination[ItemType]:
    return Pagination(
        page=Page(items=items, number=0, size=UNPAGED, total=len(items)),
        callback=lambda value: ProductCallback(
            action=ProductAction.CARD, page=value
        ),
    )


async def product_list(
    queries: IProductQueries,
    context: RenderContext,
    category_id: CategoryId,
    number: int = 0,
) -> InputRichMessage:
    page = await queries.list_products(category_id, number, DEFAULT_PAGE_SIZE)
    pagination = Pagination(
        page=page,
        callback=lambda value: ProductCallback(
            action=ProductAction.LIST,
            category_id=category_id,
            page=value,
        ),
    )
    view = ProductListView(category_id=category_id, total=page.total)
    return rich_paged_screen(PRODUCT_LIST, pagination, view, context)


def product_card(context: RenderContext, product: ProductView) -> InputRichMessage:
    return rich_screen(PRODUCT_CARD, product, context)


def media_board(
    context: RenderContext,
    product: ProductView,
    media: list[MediaView],
) -> InputRichMessage:
    return rich_paged_screen(MEDIA_BOARD, _whole(media), product, context)


def variant_board(
    context: RenderContext,
    product: ProductView,
    variants: list[VariantView],
) -> InputRichMessage:
    return rich_paged_screen(VARIANT_BOARD, _whole(variants), product, context)


def prompt(
    context: RenderContext,
    message_key: str,
    back: CallbackData,
) -> InputRichMessage:
    view = PromptView(message_key=message_key, back=back)
    return rich_screen(PROMPT, view, context)
