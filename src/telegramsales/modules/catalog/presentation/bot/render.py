from aiogram.types import InputRichMessage

from telegramsales.modules.catalog.application.ports import ICatalogQueries
from telegramsales.modules.catalog.application.queries import (
    BrandView,
    CatalogView,
    CategoryView,
)
from telegramsales.modules.catalog.presentation.bot.callbacks import (
    CatalogAction,
    CatalogCallback,
    CatalogTarget,
)
from telegramsales.modules.catalog.presentation.bot.screens import (
    BRAND_CARD,
    BRAND_LIST,
    CATALOG_CARD,
    CATALOG_LIST,
    CATEGORY_CARD,
    HUB,
    PROMPT,
)
from telegramsales.modules.catalog.presentation.bot.views import (
    CountedView,
    PromptView,
)
from telegramsales.shared.application.pagination import DEFAULT_PAGE_SIZE
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.pagination import Pagination
from telegramsales.shared.presentation.bot.rich import rich_paged_screen, rich_screen


def hub(context: RenderContext) -> InputRichMessage:
    return rich_screen(HUB, None, context)


def prompt(context: RenderContext, message_key: str) -> InputRichMessage:
    return rich_screen(PROMPT, PromptView(message_key=message_key), context)


async def catalog_list(
    queries: ICatalogQueries,
    context: RenderContext,
    number: int,
) -> InputRichMessage:
    page = await queries.list_catalogs(number, DEFAULT_PAGE_SIZE)
    pagination = Pagination(
        page=page,
        callback=lambda value: CatalogCallback(
            action=CatalogAction.LIST,
            target=CatalogTarget.CATALOG,
            page=value,
        ),
    )
    return rich_paged_screen(
        CATALOG_LIST, pagination, CountedView(total=page.total), context
    )


async def catalog_card(
    queries: ICatalogQueries,
    context: RenderContext,
    catalog: CatalogView,
    number: int,
) -> InputRichMessage:
    page = await queries.list_categories(catalog.id, None, number, DEFAULT_PAGE_SIZE)
    pagination = Pagination(
        page=page,
        callback=lambda value: CatalogCallback(
            action=CatalogAction.CARD,
            target=CatalogTarget.CATALOG,
            catalog_id=catalog.id,
            page=value,
        ),
    )
    return rich_paged_screen(CATALOG_CARD, pagination, catalog, context)


async def category_card(
    queries: ICatalogQueries,
    context: RenderContext,
    category: CategoryView,
    number: int,
) -> InputRichMessage:
    page = await queries.list_categories(
        category.catalog_id, category.id, number, DEFAULT_PAGE_SIZE
    )
    pagination = Pagination(
        page=page,
        callback=lambda value: CatalogCallback(
            action=CatalogAction.CARD,
            target=CatalogTarget.CATEGORY,
            catalog_id=category.catalog_id,
            category_id=category.id,
            page=value,
        ),
    )
    return rich_paged_screen(CATEGORY_CARD, pagination, category, context)


async def brand_list(
    queries: ICatalogQueries,
    context: RenderContext,
    number: int,
) -> InputRichMessage:
    page = await queries.list_brands(number, DEFAULT_PAGE_SIZE)
    pagination = Pagination(
        page=page,
        callback=lambda value: CatalogCallback(
            action=CatalogAction.LIST,
            target=CatalogTarget.BRAND,
            page=value,
        ),
    )
    return rich_paged_screen(
        BRAND_LIST, pagination, CountedView(total=page.total), context
    )


def brand_card(context: RenderContext, brand: BrandView) -> InputRichMessage:
    return rich_screen(BRAND_CARD, brand, context)
