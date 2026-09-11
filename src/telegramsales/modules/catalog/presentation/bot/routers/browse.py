from aiogram import F, Router
from aiogram.types import CallbackQuery
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.catalog.application.ports import ICatalogQueries
from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
)
from telegramsales.modules.catalog.presentation.bot import render
from telegramsales.modules.catalog.presentation.bot.callbacks import (
    CatalogAction,
    CatalogCallback,
    CatalogTarget,
)
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.render import show

router = Router(name="catalog.browse")


@router.callback_query(CatalogCallback.filter(F.action == CatalogAction.HUB))
async def open_hub(callback: CallbackQuery, context: RenderContext) -> None:
    await callback.answer()
    await show(callback, render.hub(context))


@router.callback_query(
    CatalogCallback.filter(
        (F.action == CatalogAction.LIST) & (F.target == CatalogTarget.CATALOG)
    )
)
async def show_catalogs(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    context: RenderContext,
    queries: FromDishka[ICatalogQueries],
) -> None:
    await callback.answer()
    await show(
        callback,
        await render.catalog_list(queries, context, callback_data.page),
    )


@router.callback_query(
    CatalogCallback.filter(
        (F.action == CatalogAction.CARD) & (F.target == CatalogTarget.CATALOG)
    )
)
async def show_catalog(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    context: RenderContext,
    queries: FromDishka[ICatalogQueries],
) -> None:
    await callback.answer()
    if callback_data.catalog_id is None:
        return

    catalog = await queries.get_catalog(CatalogId(callback_data.catalog_id))
    if catalog is None:
        return

    await show(
        callback,
        await render.catalog_card(queries, context, catalog, callback_data.page),
    )


@router.callback_query(
    CatalogCallback.filter(
        (F.action == CatalogAction.CARD) & (F.target == CatalogTarget.CATEGORY)
    )
)
async def show_category(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    context: RenderContext,
    queries: FromDishka[ICatalogQueries],
) -> None:
    await callback.answer()
    if callback_data.category_id is None:
        return

    category = await queries.get_category(CategoryId(callback_data.category_id))
    if category is None:
        return

    await show(
        callback,
        await render.category_card(queries, context, category, callback_data.page),
    )


@router.callback_query(
    CatalogCallback.filter(
        (F.action == CatalogAction.LIST) & (F.target == CatalogTarget.BRAND)
    )
)
async def show_brands(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    context: RenderContext,
    queries: FromDishka[ICatalogQueries],
) -> None:
    await callback.answer()
    await show(
        callback,
        await render.brand_list(queries, context, callback_data.page),
    )


@router.callback_query(
    CatalogCallback.filter(
        (F.action == CatalogAction.CARD) & (F.target == CatalogTarget.BRAND)
    )
)
async def show_brand(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    context: RenderContext,
    queries: FromDishka[ICatalogQueries],
) -> None:
    await callback.answer()
    if callback_data.brand_id is None:
        return

    brand = await queries.get_brand(BrandId(callback_data.brand_id))
    if brand is None:
        return

    await show(callback, render.brand_card(context, brand))
