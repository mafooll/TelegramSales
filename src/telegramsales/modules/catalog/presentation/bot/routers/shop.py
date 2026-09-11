from aiogram import F, Router
from aiogram.types import CallbackQuery, InputRichMessage
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.catalog.application.ports import IShopQueries
from telegramsales.modules.catalog.application.queries import ShopCategoryView
from telegramsales.modules.catalog.contracts import (
    CatalogId,
    CategoryId,
    ProductId,
)
from telegramsales.modules.catalog.presentation.bot import shop_render, shop_texts
from telegramsales.modules.catalog.presentation.bot.shop_callbacks import (
    ShopAction,
    ShopCallback,
)
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.render import show

router = Router(name="catalog.shop")


async def _gone(callback: CallbackQuery, context: RenderContext) -> None:
    await callback.answer(context.translate(shop_texts.GONE), show_alert=True)


@router.callback_query(ShopCallback.filter(F.action == ShopAction.CATALOGS))
async def show_catalogs(
    callback: CallbackQuery,
    callback_data: ShopCallback,
    context: RenderContext,
    queries: FromDishka[IShopQueries],
) -> None:
    await callback.answer()
    await show(
        callback,
        await shop_render.catalog_list(queries, context, callback_data.page),
    )


@router.callback_query(ShopCallback.filter(F.action == ShopAction.CATALOG))
async def show_catalog(
    callback: CallbackQuery,
    callback_data: ShopCallback,
    context: RenderContext,
    queries: FromDishka[IShopQueries],
) -> None:
    catalog = (
        None
        if callback_data.catalog_id is None
        else await queries.get_catalog(CatalogId(callback_data.catalog_id))
    )
    if catalog is None:
        await _gone(callback, context)
        return

    await callback.answer()
    await show(
        callback,
        await shop_render.catalog_card(
            queries, context, catalog, callback_data.page
        ),
    )


@router.callback_query(ShopCallback.filter(F.action == ShopAction.CATEGORY))
async def show_category(
    callback: CallbackQuery,
    callback_data: ShopCallback,
    context: RenderContext,
    queries: FromDishka[IShopQueries],
) -> None:
    category = await _category(queries, callback_data.category_id)
    if category is None:
        await _gone(callback, context)
        return

    await callback.answer()
    await show(
        callback,
        await _below_category(queries, context, category, callback_data.page),
    )


@router.callback_query(ShopCallback.filter(F.action == ShopAction.PRODUCTS))
async def show_products(
    callback: CallbackQuery,
    callback_data: ShopCallback,
    context: RenderContext,
    queries: FromDishka[IShopQueries],
) -> None:
    category = await _category(queries, callback_data.category_id)
    if category is None:
        await _gone(callback, context)
        return

    await callback.answer()
    await show(
        callback,
        await shop_render.product_list(
            queries, context, category, callback_data.page
        ),
    )


@router.callback_query(ShopCallback.filter(F.action == ShopAction.PRODUCT))
async def show_product(
    callback: CallbackQuery,
    callback_data: ShopCallback,
    context: RenderContext,
    queries: FromDishka[IShopQueries],
) -> None:
    product = (
        None
        if callback_data.product_id is None
        else await queries.get_product(ProductId(callback_data.product_id))
    )
    if product is None:
        await _gone(callback, context)
        return

    await callback.answer()
    await show(callback, shop_render.product_card(context, product))


async def _category(
    queries: IShopQueries,
    category_id: int | None,
) -> ShopCategoryView | None:
    if category_id is None:
        return None
    return await queries.get_category(CategoryId(category_id))


async def _below_category(
    queries: IShopQueries,
    context: RenderContext,
    category: ShopCategoryView,
    number: int,
) -> InputRichMessage:
    if category.child_count == 0:
        return await shop_render.product_list(queries, context, category, number)
    return await shop_render.category_card(queries, context, category, number)
