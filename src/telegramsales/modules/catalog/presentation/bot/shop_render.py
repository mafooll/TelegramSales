from aiogram.types import InputRichMessage

from telegramsales.modules.catalog.application.ports import IShopQueries
from telegramsales.modules.catalog.application.queries import (
    ShopCatalogView,
    ShopCategoryView,
    ShopProductView,
)
from telegramsales.modules.catalog.presentation.bot.shop_callbacks import (
    ShopAction,
    ShopCallback,
)
from telegramsales.modules.catalog.presentation.bot.shop_screens import (
    CATALOG,
    CATALOGS,
    CATEGORY,
    PRODUCT_CARD,
    PRODUCT_LIST,
    VARIANT_PICKER,
)
from telegramsales.modules.catalog.presentation.bot.views import (
    CountedView,
    ShopCatalogPageView,
    ShopProductsView,
    ShopVariantPickView,
)
from telegramsales.shared.application.pagination import DEFAULT_PAGE_SIZE, Page
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.pagination import Pagination
from telegramsales.shared.presentation.bot.rich import rich_paged_screen, rich_screen


async def catalog_list(
    queries: IShopQueries,
    context: RenderContext,
    number: int,
) -> InputRichMessage:
    page = await queries.list_catalogs(number, DEFAULT_PAGE_SIZE)
    pagination = Pagination(
        page=page,
        callback=lambda value: ShopCallback(
            action=ShopAction.CATALOGS,
            page=value,
        ),
    )
    return rich_paged_screen(
        CATALOGS, pagination, CountedView(total=page.total), context
    )


async def catalog_card(
    queries: IShopQueries,
    context: RenderContext,
    catalog: ShopCatalogView,
    number: int,
) -> InputRichMessage:
    page = await queries.list_categories(catalog.id, None, number, DEFAULT_PAGE_SIZE)
    pagination = Pagination(
        page=page,
        callback=lambda value: ShopCallback(
            action=ShopAction.CATALOG,
            catalog_id=catalog.id,
            page=value,
        ),
    )
    view = ShopCatalogPageView(catalog=catalog, total=page.total)
    return rich_paged_screen(CATALOG, pagination, view, context)


async def category_card(
    queries: IShopQueries,
    context: RenderContext,
    category: ShopCategoryView,
    number: int,
) -> InputRichMessage:
    page = await queries.list_categories(
        category.catalog_id, category.id, number, DEFAULT_PAGE_SIZE
    )
    pagination = Pagination(
        page=page,
        callback=lambda value: ShopCallback(
            action=ShopAction.CATEGORY,
            catalog_id=category.catalog_id,
            category_id=category.id,
            page=value,
        ),
    )
    return rich_paged_screen(CATEGORY, pagination, category, context)


async def product_list(
    queries: IShopQueries,
    context: RenderContext,
    category: ShopCategoryView,
    number: int,
) -> InputRichMessage:
    page = await queries.list_products(category.id, number, DEFAULT_PAGE_SIZE)
    pagination = Pagination(
        page=page,
        callback=lambda value: ShopCallback(
            action=ShopAction.PRODUCTS,
            category_id=category.id,
            page=value,
        ),
    )
    view = ShopProductsView(category=category, total=page.total)
    return rich_paged_screen(PRODUCT_LIST, pagination, view, context)


def product_card(
    context: RenderContext,
    product: ShopProductView,
) -> InputRichMessage:
    return rich_screen(PRODUCT_CARD, product, context)


def variant_picker(
    context: RenderContext,
    product: ShopProductView,
) -> InputRichMessage:
    picks = [
        ShopVariantPickView(
            product_id=product.id,
            variant_id=variant.id,
            title=variant.title,
            price=variant.price,
        )
        for variant in product.variants
    ]
    pagination = Pagination(
        page=Page(items=picks, number=0, size=len(picks) or 1, total=len(picks)),
        callback=lambda value: ShopCallback(
            action=ShopAction.VARIANTS,
            product_id=product.id,
            page=value,
        ),
    )
    return rich_paged_screen(VARIANT_PICKER, pagination, product, context)
