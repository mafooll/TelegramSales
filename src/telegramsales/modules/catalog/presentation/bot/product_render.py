from aiogram.filters.callback_data import CallbackData
from aiogram.types import InputRichMessage

from telegramsales.modules.catalog.application.ports import IProductQueries
from telegramsales.modules.catalog.application.queries import (
    BrandView,
    CatalogView,
    CategoryView,
    MediaView,
    ProductView,
    VariantView,
)
from telegramsales.modules.catalog.contracts import CatalogId, CategoryId
from telegramsales.modules.catalog.presentation.bot.product_callbacks import (
    ProductAction,
    ProductCallback,
)
from telegramsales.modules.catalog.presentation.bot.product_screens import (
    BRAND_PICKER,
    MEDIA_BOARD,
    MOVE_CATALOG_PICKER,
    MOVE_CATEGORY_PICKER,
    PRODUCT_CARD,
    PRODUCT_LIST,
    VARIANT_BOARD,
    VARIANT_CARD,
)
from telegramsales.modules.catalog.presentation.bot.screens import PROMPT
from telegramsales.modules.catalog.presentation.bot.views import (
    BrandPickView,
    CatalogPickView,
    CategoryPickView,
    MoveTargetView,
    ProductListView,
    PromptView,
    VariantCardView,
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
    catalog_id: CatalogId,
    category_id: CategoryId | None,
    number: int = 0,
) -> InputRichMessage:
    page = await queries.list_products(
        catalog_id, category_id, number, DEFAULT_PAGE_SIZE
    )
    pagination = Pagination(
        page=page,
        callback=lambda value: ProductCallback(
            action=ProductAction.LIST,
            catalog_id=catalog_id,
            category_id=category_id,
            page=value,
        ),
    )
    view = ProductListView(
        catalog_id=catalog_id, category_id=category_id, total=page.total
    )
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


def brand_picker(
    context: RenderContext,
    product: ProductView,
    brands: list[BrandView],
) -> InputRichMessage:
    picks = [
        BrandPickView(product_id=product.id, brand_id=brand.id, title=brand.title)
        for brand in brands
    ]
    return rich_paged_screen(BRAND_PICKER, _whole(picks), product, context)


def variant_card(
    context: RenderContext,
    product: ProductView,
    variant: VariantView,
) -> InputRichMessage:
    view = VariantCardView(product=product, variant=variant)
    return rich_screen(VARIANT_CARD, view, context)


def move_catalog_picker(
    context: RenderContext,
    product: ProductView,
    catalogs: list[CatalogView],
) -> InputRichMessage:
    picks = [
        CatalogPickView(
            product_id=product.id,
            catalog_id=catalog.id,
            title=catalog.title,
        )
        for catalog in catalogs
    ]
    return rich_paged_screen(MOVE_CATALOG_PICKER, _whole(picks), product, context)


def move_category_picker(
    context: RenderContext,
    product: ProductView,
    catalog: CatalogView,
    categories: list[CategoryView],
) -> InputRichMessage:
    picks = [
        CategoryPickView(
            product_id=product.id,
            catalog_id=catalog.id,
            category_id=category.id,
            title=category.title,
        )
        for category in categories
    ]
    view = MoveTargetView(
        product=product,
        catalog=catalog,
        takes_products=not categories,
    )
    return rich_paged_screen(MOVE_CATEGORY_PICKER, _whole(picks), view, context)
