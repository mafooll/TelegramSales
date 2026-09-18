from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputRichMessage, Message
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.catalog.application.ports import IShopQueries
from telegramsales.modules.catalog.application.queries import (
    ShopCatalogView,
    ShopCategoryView,
)
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
from telegramsales.modules.catalog.presentation.bot.states import SearchForm
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.filters import PlainTextFilter
from telegramsales.shared.presentation.bot.render import answer_once, send, show

router = Router(name="catalog.shop")


async def _gone(callback: CallbackQuery, context: RenderContext) -> None:
    await answer_once(callback, context.translate(shop_texts.GONE), alert=True)


SHOP_COMMAND = "shop"


@router.message(Command(SHOP_COMMAND))
async def show_catalogs_by_command(
    message: Message,
    context: RenderContext,
    queries: FromDishka[IShopQueries],
    state: FSMContext,
) -> None:
    if message.bot is None:
        return

    await state.set_state(None)

    await send(
        message.bot,
        message.chat.id,
        await shop_render.catalog_list(queries, context, 0),
    )


@router.callback_query(ShopCallback.filter(F.action == ShopAction.CATALOGS))
async def show_catalogs(
    callback: CallbackQuery,
    callback_data: ShopCallback,
    context: RenderContext,
    queries: FromDishka[IShopQueries],
) -> None:
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
    category: ShopCategoryView | None = None
    if callback_data.category_id is not None:
        category = await _category(queries, callback_data.category_id)
        if category is None:
            await _gone(callback, context)
            return
        catalog = ShopCatalogView(
            id=category.catalog_id, title=category.catalog_title
        )
    else:
        catalog = await _catalog(queries, callback_data.catalog_id)
        if catalog is None:
            await _gone(callback, context)
            return

    await show(
        callback,
        await shop_render.product_list(
            queries, context, catalog, category, callback_data.page
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

    await show(
        callback,
        shop_render.product_card(context, product),
        keep=callback_data.keep,
    )


async def _category(
    queries: IShopQueries,
    category_id: int | None,
) -> ShopCategoryView | None:
    if category_id is None:
        return None
    return await queries.get_category(CategoryId(category_id))


async def _catalog(
    queries: IShopQueries,
    catalog_id: int | None,
) -> ShopCatalogView | None:
    if catalog_id is None:
        return None
    return await queries.get_catalog(CatalogId(catalog_id))


async def _below_category(
    queries: IShopQueries,
    context: RenderContext,
    category: ShopCategoryView,
    number: int,
) -> InputRichMessage:
    if category.child_count == 0:
        catalog = ShopCatalogView(
            id=category.catalog_id, title=category.catalog_title
        )
        return await shop_render.product_list(
            queries, context, catalog, category, number
        )
    return await shop_render.category_card(queries, context, category, number)


@router.callback_query(ShopCallback.filter(F.action == ShopAction.VARIANTS))
async def show_variants(
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

    await show(callback, shop_render.variant_picker(context, product))


FIND_COMMAND = "find"
NEEDLE_KEY = "needle"
LEAST_NEEDLE_LENGTH = 2
MAX_NEEDLE_LENGTH = 64


async def _search(
    message: Message,
    state: FSMContext,
    context: RenderContext,
    queries: IShopQueries,
    needle: str,
) -> None:
    if message.bot is None:
        return

    if len(needle) < LEAST_NEEDLE_LENGTH:
        await message.answer(
            text=context.translate(
                shop_texts.SEARCH_TOO_SHORT, least=LEAST_NEEDLE_LENGTH
            )
        )
        return

    await state.set_state(None)
    await state.update_data({NEEDLE_KEY: needle})
    await send(
        message.bot,
        message.chat.id,
        await shop_render.found_products(queries, context, needle, 0),
    )


@router.message(Command(FIND_COMMAND))
async def search_by_command(
    message: Message,
    command: CommandObject,
    context: RenderContext,
    queries: FromDishka[IShopQueries],
    state: FSMContext,
) -> None:
    if message.bot is None:
        return

    needle = (command.args or "").strip()[:MAX_NEEDLE_LENGTH]
    if not needle:
        await state.set_state(SearchForm.needle)
        await send(
            message.bot,
            message.chat.id,
            shop_render.search_prompt(context),
        )
        return

    await _search(message, state, context, queries, needle)


@router.message(SearchForm.needle, PlainTextFilter())
async def search_by_text(
    message: Message,
    context: RenderContext,
    queries: FromDishka[IShopQueries],
    state: FSMContext,
) -> None:
    needle = (message.text or "").strip()[:MAX_NEEDLE_LENGTH]
    await _search(message, state, context, queries, needle)


@router.callback_query(ShopCallback.filter(F.action == ShopAction.SEARCH))
async def ask_needle(
    callback: CallbackQuery,
    context: RenderContext,
    state: FSMContext,
) -> None:
    await state.set_state(SearchForm.needle)
    await show(callback, shop_render.search_prompt(context))


@router.callback_query(ShopCallback.filter(F.action == ShopAction.FOUND))
async def show_found(
    callback: CallbackQuery,
    callback_data: ShopCallback,
    context: RenderContext,
    queries: FromDishka[IShopQueries],
    state: FSMContext,
) -> None:
    stored = await state.get_data()
    needle = stored.get(NEEDLE_KEY)
    if not isinstance(needle, str):
        await answer_once(
            callback, context.translate(shop_texts.SEARCH_LOST), alert=True
        )
        return

    await show(
        callback,
        await shop_render.found_products(
            queries, context, needle, callback_data.page
        ),
    )
