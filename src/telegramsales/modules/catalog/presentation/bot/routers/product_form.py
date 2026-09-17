from collections.abc import Awaitable, Callable
from decimal import InvalidOperation
from uuid import UUID

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, InputRichMessage, Message
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.catalog.application.commands.brands import (
    CreateBrand,
    CreateBrandHandler,
)
from telegramsales.modules.catalog.application.commands.media import (
    AttachMedia,
    AttachMediaHandler,
)
from telegramsales.modules.catalog.application.commands.products import (
    CreateProduct,
    CreateProductHandler,
    DescribeProduct,
    DescribeProductHandler,
    RebrandProduct,
    RebrandProductHandler,
    RenameProduct,
    RenameProductHandler,
    RepriceProduct,
    RepriceProductHandler,
)
from telegramsales.modules.catalog.application.commands.variants import (
    AddVariant,
    AddVariantHandler,
    ChangeVariantAxis,
    ChangeVariantAxisHandler,
    RenameVariant,
    RenameVariantHandler,
    RepriceVariant,
    RepriceVariantHandler,
)
from telegramsales.modules.catalog.application.ports import (
    ICatalogQueries,
    IProductQueries,
)
from telegramsales.modules.catalog.contracts import (
    CatalogId,
    CategoryId,
    ProductId,
    VariantId,
)
from telegramsales.modules.catalog.domain.enums import MediaKind
from telegramsales.modules.catalog.domain.pricing import SHOP_CURRENCY
from telegramsales.modules.catalog.domain.values import Description, Title
from telegramsales.modules.catalog.presentation.bot import (
    product_render,
    product_texts,
    product_texts as texts,
    texts as catalog_texts,
)
from telegramsales.modules.catalog.presentation.bot.product_callbacks import (
    ProductAction,
    ProductCallback,
)
from telegramsales.modules.catalog.presentation.bot.product_screens import (
    BRAND_PAGE_SIZE,
)
from telegramsales.modules.catalog.presentation.bot.product_states import ProductForm
from telegramsales.modules.catalog.presentation.bot.routers.drafts import (
    CATALOG_KEY,
    CATEGORY_KEY,
    DESCRIPTION_KEY,
    DRAFT_KEY,
    KIND_KEY,
    PRODUCT_KEY,
    TITLE_KEY,
    VARIANT_KEY,
)
from telegramsales.shared.domain.exceptions import DomainError
from telegramsales.shared.domain.money import Money
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.filters import PlainTextFilter
from telegramsales.shared.presentation.bot.money import parse_amount
from telegramsales.shared.presentation.bot.render import show

router = Router(name="catalog.product_form")


VARIANT_PROMPTS: dict[ProductAction, tuple[State, str]] = {
    ProductAction.RENAME_VARIANT: (
        ProductForm.variant_rename,
        product_texts.ASK_VARIANT_TITLE,
    ),
    ProductAction.REPRICE_VARIANT: (
        ProductForm.variant_price,
        product_texts.ASK_VARIANT_PRICE,
    ),
}

EDIT_PROMPTS: dict[ProductAction, tuple[State, str]] = {
    ProductAction.NAME: (ProductForm.rename, texts.ASK_NEW_TITLE),
    ProductAction.DESC: (ProductForm.redescribe, texts.ASK_NEW_DESCRIPTION),
    ProductAction.PRICE: (ProductForm.reprice, texts.ASK_NEW_PRICE),
    ProductAction.AXIS: (ProductForm.axis, texts.ASK_AXIS),
    ProductAction.ADD_VARIANT: (ProductForm.variant, texts.ASK_VARIANT),
}

MEDIA_PROMPTS: dict[ProductAction, tuple[MediaKind, str]] = {
    ProductAction.ADD_PHOTO: (MediaKind.PHOTO, texts.ASK_PHOTO),
    ProductAction.ADD_VIDEO: (MediaKind.VIDEO, texts.ASK_VIDEO),
}


def _attachment(message: Message) -> tuple[MediaKind, str] | None:
    if message.photo:
        return MediaKind.PHOTO, message.photo[-1].file_id
    if message.video is not None:
        return MediaKind.VIDEO, message.video.file_id
    return None


VARIANT_ACTIONS = frozenset({ProductAction.AXIS, ProductAction.ADD_VARIANT})


def _return_action(action: ProductAction) -> ProductAction:
    if action in VARIANT_ACTIONS:
        return ProductAction.VARIANTS
    return ProductAction.CARD


async def _back_to_list(state: FSMContext) -> ProductCallback:
    stored = await state.get_data()
    return ProductCallback(
        action=ProductAction.LIST,
        catalog_id=stored[CATALOG_KEY],
        category_id=stored.get(CATEGORY_KEY),
    )


async def _stored_product(state: FSMContext) -> ProductId:
    stored = await state.get_data()
    return ProductId(UUID(stored[PRODUCT_KEY]))


async def _ask(
    callback: CallbackQuery,
    context: RenderContext,
    message_key: str,
    back: ProductCallback,
) -> None:
    await show(callback, product_render.prompt(context, message_key, back))


async def _apply_text(
    message: Message,
    context: RenderContext,
    apply: Callable[[str], Awaitable[InputRichMessage | None]],
) -> None:
    if message.text is None:
        return

    try:
        rendered = await apply(message.text)
    except DomainError:
        await message.answer(text=context.translate(catalog_texts.TITLE_REJECTED))
        return

    if rendered is not None and message.bot is not None:
        await message.bot.send_rich_message(
            chat_id=message.chat.id, rich_message=rendered
        )


@router.callback_query(ProductCallback.filter(F.action == ProductAction.NEW))
async def start_product(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    state: FSMContext,
    queries: FromDishka[ICatalogQueries],
) -> None:
    catalog_id: CatalogId
    category_id: CategoryId | None
    if callback_data.category_id is not None:
        category = await queries.get_category(CategoryId(callback_data.category_id))
        if category is None:
            await callback.answer()
            return
        catalog_id = category.catalog_id
        category_id = category.id
    elif callback_data.catalog_id is not None:
        catalog = await queries.get_catalog(CatalogId(callback_data.catalog_id))
        if catalog is None:
            await callback.answer()
            return
        catalog_id = catalog.id
        category_id = None
    else:
        await callback.answer()
        return

    await state.set_state(ProductForm.title)
    await state.update_data({CATALOG_KEY: catalog_id, CATEGORY_KEY: category_id})
    await _ask(
        callback,
        context,
        texts.ASK_TITLE,
        ProductCallback(
            action=ProductAction.LIST,
            catalog_id=catalog_id,
            category_id=category_id,
        ),
    )


@router.message(ProductForm.title, PlainTextFilter())
async def take_title(
    message: Message,
    state: FSMContext,
    context: RenderContext,
) -> None:
    back = await _back_to_list(state)

    async def apply(raw: str) -> InputRichMessage:
        await state.update_data({TITLE_KEY: Title(raw).value})
        await state.set_state(ProductForm.description)
        return product_render.prompt(context, texts.ASK_DESCRIPTION, back)

    await _apply_text(message, context, apply)


@router.message(ProductForm.description, PlainTextFilter())
async def take_description(
    message: Message,
    state: FSMContext,
    context: RenderContext,
) -> None:
    back = await _back_to_list(state)

    async def apply(raw: str) -> InputRichMessage:
        await state.update_data({DESCRIPTION_KEY: Description(raw).value})
        await state.set_state(ProductForm.price)
        return product_render.prompt(context, texts.ASK_PRICE, back)

    await _apply_text(message, context, apply)


@router.message(ProductForm.price, PlainTextFilter())
async def take_price(  # noqa: PLR0913, PLR0917
    message: Message,
    state: FSMContext,
    context: RenderContext,
    handler: FromDishka[CreateProductHandler],
    queries: FromDishka[IProductQueries],
    catalog_queries: FromDishka[ICatalogQueries],
) -> None:
    stored = await state.get_data()

    async def apply(raw: str) -> InputRichMessage | None:
        stored_category_id = stored.get(CATEGORY_KEY)
        product_id = await handler.handle(
            CreateProduct(
                catalog_id=CatalogId(stored[CATALOG_KEY]),
                category_id=(
                    None
                    if stored_category_id is None
                    else CategoryId(stored_category_id)
                ),
                title=Title(stored[TITLE_KEY]),
                description=Description(stored[DESCRIPTION_KEY]),
                price=Money(parse_amount(raw), SHOP_CURRENCY),
            ),
            context.actor,
        )
        await state.set_state(ProductForm.brand)
        await state.update_data(
            {
                PRODUCT_KEY: str(product_id),
                KIND_KEY: MediaKind.PHOTO.value,
                DRAFT_KEY: True,
            }
        )
        product = await queries.get_product(product_id)
        if product is None:
            return None
        brands = await catalog_queries.list_brands(0, BRAND_PAGE_SIZE)
        return product_render.brand_picker(context, product, list(brands.items))

    try:
        await _apply_text(message, context, apply)
    except (InvalidOperation, ArithmeticError):
        await message.answer(text=context.translate(texts.PRICE_REJECTED))


@router.message(ProductForm.photos)
async def take_media(  # noqa: PLR0913
    message: Message,
    *,
    album: list[Message],
    state: FSMContext,
    context: RenderContext,
    handler: FromDishka[AttachMediaHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    product_id = await _stored_product(state)

    attached = 0
    for item in album:
        attachment = _attachment(item)
        if attachment is None:
            continue
        kind, file_id = attachment
        await handler.handle(
            AttachMedia(product_id=product_id, kind=kind, file_id=file_id),
            context.actor,
        )
        attached += 1

    if attached == 0:
        rejected = (
            texts.MEDIA_AS_FILE
            if any(item.document is not None for item in album)
            else texts.MEDIA_REJECTED
        )
        await message.answer(text=context.translate(rejected))
        return

    product = await queries.get_product(product_id)
    if product is None or message.bot is None:
        return

    media = await queries.list_media(product_id)
    await message.bot.send_rich_message(
        chat_id=message.chat.id,
        rich_message=product_render.media_board(context, product, media),
    )


@router.callback_query(
    ProductCallback.filter(
        F.action.in_({ProductAction.ADD_PHOTO, ProductAction.ADD_VIDEO})
    )
)
async def ask_media(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    state: FSMContext,
) -> None:
    prompt = MEDIA_PROMPTS.get(callback_data.action)
    if prompt is None or callback_data.product_id is None:
        await callback.answer()
        return

    kind, message_key = prompt
    await state.set_state(ProductForm.photos)
    await state.update_data(
        {PRODUCT_KEY: str(callback_data.product_id), KIND_KEY: kind.value}
    )
    await _ask(
        callback,
        context,
        message_key,
        ProductCallback(
            action=ProductAction.MEDIA, product_id=callback_data.product_id
        ),
    )


@router.callback_query(ProductCallback.filter(F.action.in_(set(EDIT_PROMPTS))))
async def ask_edit(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    state: FSMContext,
) -> None:
    prompt = EDIT_PROMPTS.get(callback_data.action)
    if prompt is None or callback_data.product_id is None:
        await callback.answer()
        return

    form, message_key = prompt
    await state.set_state(form)
    await state.update_data({PRODUCT_KEY: str(callback_data.product_id)})
    await _ask(
        callback,
        context,
        message_key,
        ProductCallback(
            action=_return_action(callback_data.action),
            product_id=callback_data.product_id,
        ),
    )


@router.message(ProductForm.rename, PlainTextFilter())
async def take_new_title(
    message: Message,
    state: FSMContext,
    context: RenderContext,
    handler: FromDishka[RenameProductHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    product_id = await _stored_product(state)

    async def apply(raw: str) -> InputRichMessage | None:
        await handler.handle(
            RenameProduct(product_id=product_id, title=Title(raw)), context.actor
        )
        await state.clear()
        product = await queries.get_product(product_id)
        return (
            None
            if product is None
            else product_render.product_card(context, product)
        )

    await _apply_text(message, context, apply)


@router.message(ProductForm.redescribe, PlainTextFilter())
async def take_new_description(
    message: Message,
    state: FSMContext,
    context: RenderContext,
    handler: FromDishka[DescribeProductHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    product_id = await _stored_product(state)

    async def apply(raw: str) -> InputRichMessage | None:
        await handler.handle(
            DescribeProduct(product_id=product_id, description=Description(raw)),
            context.actor,
        )
        await state.clear()
        product = await queries.get_product(product_id)
        return (
            None
            if product is None
            else product_render.product_card(context, product)
        )

    await _apply_text(message, context, apply)


@router.message(ProductForm.reprice, PlainTextFilter())
async def take_new_price(
    message: Message,
    state: FSMContext,
    context: RenderContext,
    handler: FromDishka[RepriceProductHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    product_id = await _stored_product(state)

    async def apply(raw: str) -> InputRichMessage | None:
        await handler.handle(
            RepriceProduct(
                product_id=product_id, price=Money(parse_amount(raw), SHOP_CURRENCY)
            ),
            context.actor,
        )
        await state.clear()
        product = await queries.get_product(product_id)
        return (
            None
            if product is None
            else product_render.product_card(context, product)
        )

    try:
        await _apply_text(message, context, apply)
    except (InvalidOperation, ArithmeticError):
        await message.answer(text=context.translate(texts.PRICE_REJECTED))


@router.message(ProductForm.axis, PlainTextFilter())
async def take_axis(
    message: Message,
    state: FSMContext,
    context: RenderContext,
    handler: FromDishka[ChangeVariantAxisHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    product_id = await _stored_product(state)

    async def apply(raw: str) -> InputRichMessage | None:
        await handler.handle(
            ChangeVariantAxis(product_id=product_id, label=Title(raw)), context.actor
        )
        await state.clear()
        product = await queries.get_product(product_id)
        if product is None:
            return None
        variants = await queries.list_variants(product_id)
        return product_render.variant_board(context, product, variants)

    await _apply_text(message, context, apply)


@router.message(ProductForm.variant, PlainTextFilter())
async def take_variant(
    message: Message,
    state: FSMContext,
    context: RenderContext,
    handler: FromDishka[AddVariantHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    product_id = await _stored_product(state)

    async def apply(raw: str) -> InputRichMessage | None:
        await handler.handle(
            AddVariant(product_id=product_id, title=Title(raw)), context.actor
        )
        await state.clear()
        product = await queries.get_product(product_id)
        if product is None:
            return None
        variants = await queries.list_variants(product_id)
        return product_render.variant_board(context, product, variants)

    await _apply_text(message, context, apply)


async def _stored_variant(state: FSMContext) -> VariantId:
    stored = await state.get_data()
    return VariantId(int(stored[VARIANT_KEY]))


async def _show_variant_card(
    context: RenderContext,
    queries: IProductQueries,
    variant_id: VariantId,
) -> InputRichMessage | None:
    product_id = await queries.product_of_variant(variant_id)
    if product_id is None:
        return None

    product = await queries.get_product(product_id)
    if product is None:
        return None

    variants = await queries.list_variants(product_id)
    found = next((item for item in variants if item.id == variant_id), None)
    if found is None:
        return None
    return product_render.variant_card(context, product, found)


@router.callback_query(ProductCallback.filter(F.action.in_(set(VARIANT_PROMPTS))))
async def ask_variant_edit(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    state: FSMContext,
) -> None:
    prompt = VARIANT_PROMPTS.get(callback_data.action)
    if prompt is None or callback_data.item_id is None:
        await callback.answer()
        return

    form, message_key = prompt
    await state.set_state(form)
    await state.update_data({VARIANT_KEY: callback_data.item_id})
    await _ask(
        callback,
        context,
        message_key,
        ProductCallback(
            action=ProductAction.VARIANT,
            item_id=callback_data.item_id,
        ),
    )


@router.message(ProductForm.variant_rename, PlainTextFilter())
async def take_variant_title(
    message: Message,
    state: FSMContext,
    context: RenderContext,
    handler: FromDishka[RenameVariantHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    variant_id = await _stored_variant(state)

    async def apply(raw: str) -> InputRichMessage | None:
        await handler.handle(
            RenameVariant(variant_id=variant_id, title=Title(raw)), context.actor
        )
        await state.clear()
        return await _show_variant_card(context, queries, variant_id)

    await _apply_text(message, context, apply)


@router.message(ProductForm.variant_price, PlainTextFilter())
async def take_variant_price(
    message: Message,
    state: FSMContext,
    context: RenderContext,
    handler: FromDishka[RepriceVariantHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    variant_id = await _stored_variant(state)

    async def apply(raw: str) -> InputRichMessage | None:
        await handler.handle(
            RepriceVariant(
                variant_id=variant_id,
                price_override=Money(parse_amount(raw), SHOP_CURRENCY),
            ),
            context.actor,
        )
        await state.clear()
        return await _show_variant_card(context, queries, variant_id)

    try:
        await _apply_text(message, context, apply)
    except (InvalidOperation, ArithmeticError):
        await message.answer(text=context.translate(texts.PRICE_REJECTED))


@router.callback_query(ProductCallback.filter(F.action == ProductAction.NEW_BRAND))
async def ask_brand_title(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    state: FSMContext,
) -> None:
    if callback_data.product_id is None:
        await callback.answer()
        return

    await state.set_state(ProductForm.brand_title)
    await state.update_data({PRODUCT_KEY: str(callback_data.product_id)})
    await _ask(
        callback,
        context,
        product_texts.ASK_BRAND_TITLE,
        ProductCallback(
            action=ProductAction.BRAND,
            product_id=callback_data.product_id,
        ),
    )


@router.message(ProductForm.brand_title, PlainTextFilter())
async def take_brand_title(  # noqa: PLR0913, PLR0917
    message: Message,
    state: FSMContext,
    context: RenderContext,
    creator: FromDishka[CreateBrandHandler],
    rebrander: FromDishka[RebrandProductHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    product_id = await _stored_product(state)
    stored = await state.get_data()

    async def apply(raw: str) -> InputRichMessage | None:
        brand_id = await creator.handle(CreateBrand(title=Title(raw)), context.actor)
        await rebrander.handle(
            RebrandProduct(product_id=product_id, brand_id=brand_id), context.actor
        )

        product = await queries.get_product(product_id)
        if product is None:
            return None

        if not stored.get(DRAFT_KEY):
            await state.clear()
            return product_render.product_card(context, product)

        await state.set_state(ProductForm.photos)
        return product_render.media_board(context, product, [])

    await _apply_text(message, context, apply)
