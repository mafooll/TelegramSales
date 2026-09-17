from aiogram import F, Router
from aiogram.types import CallbackQuery
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.catalog.application.commands.brands import (
    ChangeBrandVisibility,
    ChangeBrandVisibilityHandler,
    DeleteBrand,
    DeleteBrandHandler,
)
from telegramsales.modules.catalog.application.commands.catalogs import (
    ChangeCatalogVisibility,
    ChangeCatalogVisibilityHandler,
    DeleteCatalog,
    DeleteCatalogHandler,
)
from telegramsales.modules.catalog.application.commands.categories import (
    ChangeCategoryVisibility,
    ChangeCategoryVisibilityHandler,
    DeleteCategory,
    DeleteCategoryHandler,
)
from telegramsales.modules.catalog.application.ports import ICatalogQueries
from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
)
from telegramsales.modules.catalog.presentation.bot import render, texts
from telegramsales.modules.catalog.presentation.bot.callbacks import (
    CatalogAction,
    CatalogCallback,
    CatalogTarget,
)
from telegramsales.shared.presentation.bot.confirmation import (
    CONFIRMATION_SCREEN,
    ConfirmationView,
)
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.render import answer_once, show
from telegramsales.shared.presentation.bot.rich import rich_screen

router = Router(name="catalog.edit")

VISIBILITY = F.action.in_({CatalogAction.HIDE, CatalogAction.SHOW})


def _is_visible(callback_data: CatalogCallback) -> bool:
    return callback_data.action is CatalogAction.SHOW


@router.callback_query(
    CatalogCallback.filter(VISIBILITY & (F.target == CatalogTarget.CATALOG))
)
async def set_catalog_visibility(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    context: RenderContext,
    handler: FromDishka[ChangeCatalogVisibilityHandler],
    queries: FromDishka[ICatalogQueries],
) -> None:
    if callback_data.catalog_id is None:
        await callback.answer()
        return

    catalog_id = CatalogId(callback_data.catalog_id)
    await handler.handle(
        ChangeCatalogVisibility(
            catalog_id=catalog_id, is_visible=_is_visible(callback_data)
        ),
        context.actor,
    )

    catalog = await queries.get_catalog(catalog_id)
    if catalog is not None:
        await show(callback, await render.catalog_card(queries, context, catalog, 0))


@router.callback_query(
    CatalogCallback.filter(VISIBILITY & (F.target == CatalogTarget.CATEGORY))
)
async def set_category_visibility(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    context: RenderContext,
    handler: FromDishka[ChangeCategoryVisibilityHandler],
    queries: FromDishka[ICatalogQueries],
) -> None:
    if callback_data.category_id is None:
        await callback.answer()
        return

    category_id = CategoryId(callback_data.category_id)
    await handler.handle(
        ChangeCategoryVisibility(
            category_id=category_id, is_visible=_is_visible(callback_data)
        ),
        context.actor,
    )

    category = await queries.get_category(category_id)
    if category is not None:
        await show(
            callback, await render.category_card(queries, context, category, 0)
        )


@router.callback_query(
    CatalogCallback.filter(VISIBILITY & (F.target == CatalogTarget.BRAND))
)
async def set_brand_visibility(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    context: RenderContext,
    handler: FromDishka[ChangeBrandVisibilityHandler],
    queries: FromDishka[ICatalogQueries],
) -> None:
    if callback_data.brand_id is None:
        await callback.answer()
        return

    brand_id = BrandId(callback_data.brand_id)
    await handler.handle(
        ChangeBrandVisibility(
            brand_id=brand_id, is_visible=_is_visible(callback_data)
        ),
        context.actor,
    )

    brand = await queries.get_brand(brand_id)
    if brand is not None:
        await show(callback, render.brand_card(context, brand))


async def _title_of(
    callback_data: CatalogCallback,
    queries: ICatalogQueries,
) -> str | None:
    if callback_data.target is CatalogTarget.CATALOG:
        if callback_data.catalog_id is None:
            return None
        catalog = await queries.get_catalog(CatalogId(callback_data.catalog_id))
        return None if catalog is None else catalog.title
    if callback_data.target is CatalogTarget.CATEGORY:
        if callback_data.category_id is None:
            return None
        category = await queries.get_category(CategoryId(callback_data.category_id))
        return None if category is None else category.title
    if callback_data.brand_id is None:
        return None
    brand = await queries.get_brand(BrandId(callback_data.brand_id))
    return None if brand is None else brand.title


@router.callback_query(CatalogCallback.filter(F.action == CatalogAction.ASK_DELETE))
async def ask_delete(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    context: RenderContext,
    queries: FromDishka[ICatalogQueries],
) -> None:
    title = await _title_of(callback_data, queries)
    if title is None:
        return

    view = ConfirmationView(
        question_key=texts.DELETE_QUESTION,
        question_args={"title": title},
        confirm=callback_data.model_copy(update={"action": CatalogAction.DELETE}),
        cancel=callback_data.model_copy(update={"action": CatalogAction.CARD}),
    )
    await show(callback, rich_screen(CONFIRMATION_SCREEN, view, context))


@router.callback_query(
    CatalogCallback.filter(
        (F.action == CatalogAction.DELETE) & (F.target == CatalogTarget.CATALOG)
    )
)
async def delete_catalog(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    context: RenderContext,
    handler: FromDishka[DeleteCatalogHandler],
    queries: FromDishka[ICatalogQueries],
) -> None:
    if callback_data.catalog_id is None:
        await callback.answer()
        return

    await handler.handle(
        DeleteCatalog(catalog_id=CatalogId(callback_data.catalog_id)), context.actor
    )
    await answer_once(callback, context.translate(texts.DELETED))
    await show(callback, await render.catalog_list(queries, context, 0))


@router.callback_query(
    CatalogCallback.filter(
        (F.action == CatalogAction.DELETE) & (F.target == CatalogTarget.CATEGORY)
    )
)
async def delete_category(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    context: RenderContext,
    handler: FromDishka[DeleteCategoryHandler],
    queries: FromDishka[ICatalogQueries],
) -> None:
    if callback_data.category_id is None or callback_data.catalog_id is None:
        await callback.answer()
        return

    await handler.handle(
        DeleteCategory(category_id=CategoryId(callback_data.category_id)),
        context.actor,
    )
    await answer_once(callback, context.translate(texts.DELETED))

    catalog = await queries.get_catalog(CatalogId(callback_data.catalog_id))
    if catalog is not None:
        await show(callback, await render.catalog_card(queries, context, catalog, 0))


@router.callback_query(
    CatalogCallback.filter(
        (F.action == CatalogAction.DELETE) & (F.target == CatalogTarget.BRAND)
    )
)
async def delete_brand(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    context: RenderContext,
    handler: FromDishka[DeleteBrandHandler],
    queries: FromDishka[ICatalogQueries],
) -> None:
    if callback_data.brand_id is None:
        await callback.answer()
        return

    await handler.handle(
        DeleteBrand(brand_id=BrandId(callback_data.brand_id)), context.actor
    )
    await answer_once(callback, context.translate(texts.DELETED))
    await show(callback, await render.brand_list(queries, context, 0))
