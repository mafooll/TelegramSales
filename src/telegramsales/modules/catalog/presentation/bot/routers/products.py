from uuid import UUID

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.catalog.application.commands.media import (
    DetachMedia,
    DetachMediaHandler,
)
from telegramsales.modules.catalog.application.commands.products import (
    ChangeMediaLayout,
    ChangeMediaLayoutHandler,
    ChangeProductStock,
    ChangeProductStockHandler,
    ChangeProductVisibility,
    ChangeProductVisibilityHandler,
    DeleteProduct,
    DeleteProductHandler,
    MoveProduct,
    MoveProductHandler,
    PublishProduct,
    PublishProductHandler,
    RebrandProduct,
    RebrandProductHandler,
)
from telegramsales.modules.catalog.application.commands.variants import (
    ChangeVariantAvailability,
    ChangeVariantAvailabilityHandler,
    DeleteVariant,
    DeleteVariantHandler,
)
from telegramsales.modules.catalog.application.ports import (
    ICatalogQueries,
    IProductQueries,
)
from telegramsales.modules.catalog.application.queries import ProductView
from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
    MediaId,
    ProductId,
    VariantId,
)
from telegramsales.modules.catalog.domain.enums import MediaLayout
from telegramsales.modules.catalog.presentation.bot import (
    product_render,
    product_texts,
    texts,
)
from telegramsales.modules.catalog.presentation.bot.product_callbacks import (
    ProductAction,
    ProductCallback,
)
from telegramsales.modules.catalog.presentation.bot.product_screens import (
    BRAND_PAGE_SIZE,
    MOVE_PAGE_SIZE,
    VARIANT_CARD,
)
from telegramsales.modules.catalog.presentation.bot.product_states import (
    ProductForm,
)
from telegramsales.modules.catalog.presentation.bot.views import (
    VariantCardView,
)
from telegramsales.shared.presentation.bot.confirmation import (
    CONFIRMATION_SCREEN,
    ConfirmationView,
)
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.render import answer_once, show
from telegramsales.shared.presentation.bot.rich import rich_screen

router = Router(name="catalog.products")

VISIBILITY = F.action.in_({ProductAction.HIDE, ProductAction.SHOW})
STOCK = F.action.in_({ProductAction.OUT, ProductAction.STOCK})
AVAILABILITY = F.action.in_({ProductAction.VARIANT_ON, ProductAction.VARIANT_OFF})


async def _view(
    queries: IProductQueries,
    product_id: UUID | None,
) -> ProductView | None:
    if product_id is None:
        return None
    return await queries.get_product(ProductId(product_id))


async def _brand_target(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    queries: IProductQueries,
) -> tuple[ProductView, BrandId | None] | None:
    if callback_data.item_id is not None:
        brand_id = BrandId(callback_data.item_id)
        product_id = callback_data.product_id
    else:
        brand_id = None
        product_id = callback_data.product_id
    product = await _view(queries, product_id)
    if product is None:
        await callback.answer()
        return None
    return product, brand_id


async def _show_card(
    callback: CallbackQuery,
    context: RenderContext,
    product: ProductView,
) -> None:
    await show(callback, product_render.product_card(context, product))


@router.callback_query(ProductCallback.filter(F.action == ProductAction.LIST))
async def show_products(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    queries: FromDishka[IProductQueries],
) -> None:
    if callback_data.catalog_id is None:
        return

    await show(
        callback,
        await product_render.product_list(
            queries,
            context,
            CatalogId(callback_data.catalog_id),
            (
                None
                if callback_data.category_id is None
                else CategoryId(callback_data.category_id)
            ),
            callback_data.page,
        ),
    )


@router.callback_query(ProductCallback.filter(F.action == ProductAction.CARD))
async def show_product(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    queries: FromDishka[IProductQueries],
) -> None:
    product = await _view(queries, callback_data.product_id)
    if product is not None:
        await _show_card(callback, context, product)


@router.callback_query(ProductCallback.filter(F.action == ProductAction.PUBLISH))
async def publish(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    handler: FromDishka[PublishProductHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    if callback_data.product_id is None:
        await callback.answer()
        return

    product_id = ProductId(callback_data.product_id)
    await handler.handle(PublishProduct(product_id=product_id), context.actor)

    product = await queries.get_product(product_id)
    if product is not None:
        await _show_card(callback, context, product)


@router.callback_query(ProductCallback.filter(VISIBILITY))
async def set_visibility(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    handler: FromDishka[ChangeProductVisibilityHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    if callback_data.product_id is None:
        await callback.answer()
        return

    product_id = ProductId(callback_data.product_id)
    await handler.handle(
        ChangeProductVisibility(
            product_id=product_id,
            is_visible=callback_data.action is ProductAction.SHOW,
        ),
        context.actor,
    )

    product = await queries.get_product(product_id)
    if product is not None:
        await _show_card(callback, context, product)


@router.callback_query(ProductCallback.filter(STOCK))
async def set_stock(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    handler: FromDishka[ChangeProductStockHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    if callback_data.product_id is None:
        await callback.answer()
        return

    product_id = ProductId(callback_data.product_id)
    await handler.handle(
        ChangeProductStock(
            product_id=product_id,
            is_in_stock=callback_data.action is ProductAction.STOCK,
        ),
        context.actor,
    )

    product = await queries.get_product(product_id)
    if product is not None:
        await _show_card(callback, context, product)


@router.callback_query(ProductCallback.filter(F.action == ProductAction.ASK_DELETE))
async def ask_delete(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    queries: FromDishka[IProductQueries],
) -> None:
    product = await _view(queries, callback_data.product_id)
    if product is None:
        return

    view = ConfirmationView(
        question_key=texts.DELETE_QUESTION,
        question_args={"title": product.title},
        confirm=ProductCallback(
            action=ProductAction.DELETE,
            product_id=product.id,
            catalog_id=product.catalog_id,
            category_id=product.category_id,
        ),
        cancel=ProductCallback(action=ProductAction.CARD, product_id=product.id),
    )
    await show(callback, rich_screen(CONFIRMATION_SCREEN, view, context))


@router.callback_query(ProductCallback.filter(F.action == ProductAction.DELETE))
async def delete(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    handler: FromDishka[DeleteProductHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    if callback_data.product_id is None or callback_data.catalog_id is None:
        await callback.answer()
        return

    await handler.handle(
        DeleteProduct(product_id=ProductId(callback_data.product_id)), context.actor
    )
    await answer_once(callback, context.translate(texts.DELETED))
    await show(
        callback,
        await product_render.product_list(
            queries,
            context,
            CatalogId(callback_data.catalog_id),
            (
                None
                if callback_data.category_id is None
                else CategoryId(callback_data.category_id)
            ),
        ),
    )


@router.callback_query(ProductCallback.filter(F.action == ProductAction.MEDIA))
async def show_media(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    queries: FromDishka[IProductQueries],
) -> None:
    product = await _view(queries, callback_data.product_id)
    if product is None:
        return

    media = await queries.list_media(product.id)
    await show(callback, product_render.media_board(context, product, media))


@router.callback_query(ProductCallback.filter(F.action == ProductAction.DROP_MEDIA))
async def drop_media(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    handler: FromDishka[DetachMediaHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    if callback_data.item_id is None:
        await callback.answer()
        return

    media_id = MediaId(callback_data.item_id)
    product_id = await queries.product_of_media(media_id)
    await handler.handle(DetachMedia(media_id=media_id), context.actor)

    product = await _view(queries, product_id)
    if product is None:
        return

    media = await queries.list_media(product.id)
    await show(callback, product_render.media_board(context, product, media))


@router.callback_query(ProductCallback.filter(F.action == ProductAction.VARIANTS))
async def show_variants(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    queries: FromDishka[IProductQueries],
) -> None:
    product = await _view(queries, callback_data.product_id)
    if product is None:
        return

    variants = await queries.list_variants(product.id)
    await show(callback, product_render.variant_board(context, product, variants))


@router.callback_query(ProductCallback.filter(AVAILABILITY))
async def set_availability(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    handler: FromDishka[ChangeVariantAvailabilityHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    if callback_data.item_id is None:
        await callback.answer()
        return

    variant_id = VariantId(callback_data.item_id)
    await handler.handle(
        ChangeVariantAvailability(
            variant_id=variant_id,
            is_available=callback_data.action is ProductAction.VARIANT_ON,
        ),
        context.actor,
    )

    await _show_variant(callback, context, queries, variant_id)


@router.callback_query(ProductCallback.filter(F.action == ProductAction.LAYOUT))
async def switch_layout(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    handler: FromDishka[ChangeMediaLayoutHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    product = await _view(queries, callback_data.product_id)
    if product is None:
        return

    flipped = (
        MediaLayout.SLIDESHOW
        if product.media_layout is MediaLayout.COLLAGE
        else MediaLayout.COLLAGE
    )
    await handler.handle(
        ChangeMediaLayout(product_id=product.id, layout=flipped), context.actor
    )

    updated = await queries.get_product(product.id)
    if updated is None:
        return
    media = await queries.list_media(product.id)
    await show(callback, product_render.media_board(context, updated, media))


@router.callback_query(ProductCallback.filter(F.action == ProductAction.BRAND))
async def pick_brand(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    queries: FromDishka[IProductQueries],
    catalog_queries: FromDishka[ICatalogQueries],
) -> None:
    product = await _view(queries, callback_data.product_id)
    if product is None:
        return

    brands = await catalog_queries.list_brands(0, BRAND_PAGE_SIZE)
    await show(
        callback,
        product_render.brand_picker(context, product, list(brands.items)),
    )


@router.callback_query(ProductCallback.filter(F.action == ProductAction.SET_BRAND))
async def set_brand(  # noqa: PLR0913, PLR0917
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    state: FSMContext,
    handler: FromDishka[RebrandProductHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    target = await _brand_target(callback, callback_data, queries)
    if target is None:
        return

    product, brand_id = target
    await handler.handle(
        RebrandProduct(product_id=product.id, brand_id=brand_id), context.actor
    )

    updated = await queries.get_product(product.id)
    if updated is None:
        return

    if await state.get_state() == ProductForm.brand.state:
        await state.set_state(ProductForm.photos)
        await show(callback, product_render.media_board(context, updated, []))
        return

    await _show_card(callback, context, updated)


async def _variant_card(
    queries: IProductQueries,
    variant_id: VariantId,
) -> VariantCardView | None:
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
    return VariantCardView(product=product, variant=found)


async def _show_variant(
    callback: CallbackQuery,
    context: RenderContext,
    queries: IProductQueries,
    variant_id: VariantId,
) -> None:
    card = await _variant_card(queries, variant_id)
    if card is None:
        return
    await show(callback, rich_screen(VARIANT_CARD, card, context))


@router.callback_query(ProductCallback.filter(F.action == ProductAction.VARIANT))
async def show_variant(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    queries: FromDishka[IProductQueries],
) -> None:
    if callback_data.item_id is None:
        return
    await _show_variant(callback, context, queries, VariantId(callback_data.item_id))


@router.callback_query(
    ProductCallback.filter(F.action == ProductAction.ASK_DROP_VARIANT)
)
async def ask_drop_variant(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    queries: FromDishka[IProductQueries],
) -> None:
    if callback_data.item_id is None:
        return

    variant_id = VariantId(callback_data.item_id)
    card = await _variant_card(queries, variant_id)
    if card is None:
        return

    view = ConfirmationView(
        question_key=product_texts.VARIANT_DROP_QUESTION,
        question_args={"title": card.variant.title},
        confirm=ProductCallback(
            action=ProductAction.DROP_VARIANT,
            product_id=card.product.id,
            item_id=variant_id,
        ),
        cancel=ProductCallback(action=ProductAction.VARIANT, item_id=variant_id),
    )
    await show(callback, rich_screen(CONFIRMATION_SCREEN, view, context))


@router.callback_query(
    ProductCallback.filter(F.action == ProductAction.DROP_VARIANT)
)
async def drop_variant(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    handler: FromDishka[DeleteVariantHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    if callback_data.item_id is None:
        return

    variant_id = VariantId(callback_data.item_id)
    product_id = await queries.product_of_variant(variant_id)
    await handler.handle(DeleteVariant(variant_id=variant_id), context.actor)

    product = await _view(queries, product_id)
    if product is None:
        return

    variants = await queries.list_variants(product.id)
    await show(callback, product_render.variant_board(context, product, variants))


@router.callback_query(ProductCallback.filter(F.action == ProductAction.MOVE))
async def pick_move_catalog(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    queries: FromDishka[IProductQueries],
    catalog_queries: FromDishka[ICatalogQueries],
) -> None:
    product = await _view(queries, callback_data.product_id)
    if product is None:
        return

    catalogs = await catalog_queries.list_catalogs(0, MOVE_PAGE_SIZE)
    await show(
        callback,
        product_render.move_catalog_picker(context, product, list(catalogs.items)),
    )


@router.callback_query(
    ProductCallback.filter(F.action == ProductAction.MOVE_TO_CATALOG)
)
async def pick_move_category(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    queries: FromDishka[IProductQueries],
    catalog_queries: FromDishka[ICatalogQueries],
) -> None:
    product = await _view(queries, callback_data.product_id)
    if product is None or callback_data.catalog_id is None:
        return

    catalog = await catalog_queries.get_catalog(CatalogId(callback_data.catalog_id))
    if catalog is None:
        return

    categories = await catalog_queries.list_categories(
        catalog.id, None, 0, MOVE_PAGE_SIZE
    )
    await show(
        callback,
        product_render.move_category_picker(
            context, product, catalog, list(categories.items)
        ),
    )


@router.callback_query(ProductCallback.filter(F.action == ProductAction.MOVE_TO))
async def move_product(
    callback: CallbackQuery,
    callback_data: ProductCallback,
    context: RenderContext,
    handler: FromDishka[MoveProductHandler],
    queries: FromDishka[IProductQueries],
) -> None:
    product = await _view(queries, callback_data.product_id)
    if product is None or callback_data.catalog_id is None:
        return

    await handler.handle(
        MoveProduct(
            product_id=product.id,
            catalog_id=CatalogId(callback_data.catalog_id),
            category_id=(
                None
                if callback_data.category_id is None
                else CategoryId(callback_data.category_id)
            ),
        ),
        context.actor,
    )
    await answer_once(callback, context.translate(product_texts.MOVED))

    moved = await queries.get_product(product.id)
    if moved is not None:
        await _show_card(callback, context, moved)
