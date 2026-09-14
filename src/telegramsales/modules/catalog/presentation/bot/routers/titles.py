from collections.abc import Awaitable, Callable

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, InputRichMessage, Message
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.catalog.application.commands.brands import (
    CreateBrand,
    CreateBrandHandler,
    RenameBrand,
    RenameBrandHandler,
)
from telegramsales.modules.catalog.application.commands.catalogs import (
    CreateCatalog,
    CreateCatalogHandler,
    RenameCatalog,
    RenameCatalogHandler,
)
from telegramsales.modules.catalog.application.commands.categories import (
    CreateCategory,
    CreateCategoryHandler,
    RenameCategory,
    RenameCategoryHandler,
)
from telegramsales.modules.catalog.application.exceptions import DuplicateTitleError
from telegramsales.modules.catalog.application.ports import ICatalogQueries
from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
)
from telegramsales.modules.catalog.domain.values import Title
from telegramsales.modules.catalog.presentation.bot import render, texts
from telegramsales.modules.catalog.presentation.bot.callbacks import (
    CatalogAction,
    CatalogCallback,
    CatalogTarget,
)
from telegramsales.modules.catalog.presentation.bot.states import TitleForm
from telegramsales.shared.domain.exceptions import DomainError
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.filters import PlainTextFilter
from telegramsales.shared.presentation.bot.render import show

router = Router(name="catalog.titles")

PROMPTS: dict[tuple[CatalogAction, CatalogTarget], tuple[State, str]] = {
    (CatalogAction.ASK_CREATE, CatalogTarget.CATALOG): (
        TitleForm.catalog,
        texts.CATALOG_ASK_TITLE,
    ),
    (CatalogAction.ASK_RENAME, CatalogTarget.CATALOG): (
        TitleForm.catalog_rename,
        texts.CATALOG_ASK_NEW_TITLE,
    ),
    (CatalogAction.ASK_CREATE, CatalogTarget.CATEGORY): (
        TitleForm.category,
        texts.CATEGORY_ASK_TITLE,
    ),
    (CatalogAction.ASK_RENAME, CatalogTarget.CATEGORY): (
        TitleForm.category_rename,
        texts.CATEGORY_ASK_NEW_TITLE,
    ),
    (CatalogAction.ASK_CREATE, CatalogTarget.BRAND): (
        TitleForm.brand,
        texts.BRAND_ASK_TITLE,
    ),
    (CatalogAction.ASK_RENAME, CatalogTarget.BRAND): (
        TitleForm.brand_rename,
        texts.BRAND_ASK_NEW_TITLE,
    ),
}


def _back_to(callback_data: CatalogCallback) -> CatalogCallback:
    if callback_data.target is CatalogTarget.BRAND:
        if callback_data.brand_id is None:
            return CatalogCallback(
                action=CatalogAction.LIST, target=CatalogTarget.BRAND
            )
        return CatalogCallback(
            action=CatalogAction.CARD,
            target=CatalogTarget.BRAND,
            brand_id=callback_data.brand_id,
        )
    if callback_data.category_id is not None:
        return CatalogCallback(
            action=CatalogAction.CARD,
            target=CatalogTarget.CATEGORY,
            catalog_id=callback_data.catalog_id,
            category_id=callback_data.category_id,
        )
    if callback_data.catalog_id is not None:
        return CatalogCallback(
            action=CatalogAction.CARD,
            target=CatalogTarget.CATALOG,
            catalog_id=callback_data.catalog_id,
        )
    return CatalogCallback(action=CatalogAction.LIST, target=CatalogTarget.CATALOG)


@router.callback_query(
    CatalogCallback.filter(
        F.action.in_({CatalogAction.ASK_CREATE, CatalogAction.ASK_RENAME})
    )
)
async def ask_title(
    callback: CallbackQuery,
    callback_data: CatalogCallback,
    context: RenderContext,
    state: FSMContext,
) -> None:
    await callback.answer()
    prompt = PROMPTS.get((callback_data.action, callback_data.target))
    if prompt is None or not isinstance(callback.message, Message):
        return

    form, key = prompt
    await state.set_state(form)
    await state.update_data(
        catalog_id=callback_data.catalog_id,
        category_id=callback_data.category_id,
        brand_id=callback_data.brand_id,
    )
    await show(callback, render.prompt(context, key, _back_to(callback_data)))


async def _apply(
    message: Message,
    state: FSMContext,
    context: RenderContext,
    apply: Callable[[Title], Awaitable[InputRichMessage | None]],
) -> None:
    if message.text is None:
        return

    try:
        title = Title(message.text)
    except DomainError:
        await message.answer(text=context.translate(texts.TITLE_REJECTED))
        return

    try:
        rendered = await apply(title)
    except DuplicateTitleError:
        await message.answer(text=context.translate(texts.TITLE_TAKEN))
        return

    await state.clear()
    if rendered is not None and message.bot is not None:
        await message.bot.send_rich_message(
            chat_id=message.chat.id,
            rich_message=rendered,
        )


@router.message(TitleForm.catalog, PlainTextFilter())
async def create_catalog(
    message: Message,
    state: FSMContext,
    context: RenderContext,
    handler: FromDishka[CreateCatalogHandler],
    queries: FromDishka[ICatalogQueries],
) -> None:
    async def apply(title: Title) -> InputRichMessage:
        await handler.handle(CreateCatalog(title=title), context.actor)
        return await render.catalog_list(queries, context, 0)

    await _apply(message, state, context, apply)


@router.message(TitleForm.catalog_rename, PlainTextFilter())
async def rename_catalog(
    message: Message,
    state: FSMContext,
    context: RenderContext,
    handler: FromDishka[RenameCatalogHandler],
    queries: FromDishka[ICatalogQueries],
) -> None:
    stored = await state.get_data()
    catalog_id = CatalogId(stored["catalog_id"])

    async def apply(title: Title) -> InputRichMessage | None:
        await handler.handle(
            RenameCatalog(catalog_id=catalog_id, title=title), context.actor
        )
        catalog = await queries.get_catalog(catalog_id)
        if catalog is None:
            return None
        return await render.catalog_card(queries, context, catalog, 0)

    await _apply(message, state, context, apply)


@router.message(TitleForm.category, PlainTextFilter())
async def create_category(
    message: Message,
    state: FSMContext,
    context: RenderContext,
    handler: FromDishka[CreateCategoryHandler],
    queries: FromDishka[ICatalogQueries],
) -> None:
    stored = await state.get_data()
    catalog_id = CatalogId(stored["catalog_id"])
    parent = stored["category_id"]
    parent_id = None if parent is None else CategoryId(parent)

    async def apply(title: Title) -> InputRichMessage | None:
        await handler.handle(
            CreateCategory(catalog_id=catalog_id, title=title, parent_id=parent_id),
            context.actor,
        )
        if parent_id is None:
            catalog = await queries.get_catalog(catalog_id)
            if catalog is None:
                return None
            return await render.catalog_card(queries, context, catalog, 0)
        parent_view = await queries.get_category(parent_id)
        if parent_view is None:
            return None
        return await render.category_card(queries, context, parent_view, 0)

    await _apply(message, state, context, apply)


@router.message(TitleForm.category_rename, PlainTextFilter())
async def rename_category(
    message: Message,
    state: FSMContext,
    context: RenderContext,
    handler: FromDishka[RenameCategoryHandler],
    queries: FromDishka[ICatalogQueries],
) -> None:
    stored = await state.get_data()
    category_id = CategoryId(stored["category_id"])

    async def apply(title: Title) -> InputRichMessage | None:
        await handler.handle(
            RenameCategory(category_id=category_id, title=title), context.actor
        )
        category = await queries.get_category(category_id)
        if category is None:
            return None
        return await render.category_card(queries, context, category, 0)

    await _apply(message, state, context, apply)


@router.message(TitleForm.brand, PlainTextFilter())
async def create_brand(
    message: Message,
    state: FSMContext,
    context: RenderContext,
    handler: FromDishka[CreateBrandHandler],
    queries: FromDishka[ICatalogQueries],
) -> None:
    async def apply(title: Title) -> InputRichMessage:
        await handler.handle(CreateBrand(title=title), context.actor)
        return await render.brand_list(queries, context, 0)

    await _apply(message, state, context, apply)


@router.message(TitleForm.brand_rename, PlainTextFilter())
async def rename_brand(
    message: Message,
    state: FSMContext,
    context: RenderContext,
    handler: FromDishka[RenameBrandHandler],
    queries: FromDishka[ICatalogQueries],
) -> None:
    stored = await state.get_data()
    brand_id = BrandId(stored["brand_id"])

    async def apply(title: Title) -> InputRichMessage | None:
        await handler.handle(
            RenameBrand(brand_id=brand_id, title=title), context.actor
        )
        brand = await queries.get_brand(brand_id)
        if brand is None:
            return None
        return render.brand_card(context, brand)

    await _apply(message, state, context, apply)
