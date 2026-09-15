from collections.abc import Callable

from aiogram.enums import ButtonStyle

from telegramsales.modules.catalog.application.queries import (
    CatalogView,
    CategoryView,
    MediaView,
    ProductEntryView,
    ProductView,
    VariantView,
)
from telegramsales.modules.catalog.domain.enums import MediaLayout
from telegramsales.modules.catalog.domain.permissions import CatalogPermission
from telegramsales.modules.catalog.presentation.bot import product_texts, texts
from telegramsales.modules.catalog.presentation.bot.callbacks import (
    CatalogAction,
    CatalogCallback,
    CatalogTarget,
)
from telegramsales.modules.catalog.presentation.bot.product_callbacks import (
    ProductAction,
    ProductCallback,
)
from telegramsales.modules.catalog.presentation.bot.views import (
    BrandPickView,
    CatalogPickView,
    CategoryPickView,
    MoveTargetView,
    ProductListView,
    VariantCardView,
    catalog_products_key,
    media_item_key,
    product_item_key,
    variant_item_key,
)
from telegramsales.shared.presentation.bot.keyboard import Button, label
from telegramsales.shared.presentation.bot.money import money_text

SINGLE_PHOTO = 1

OPEN_PRODUCTS: Button[CategoryView] = Button(
    text=label(product_texts.OPEN_PRODUCTS_BUTTON),
    callback=lambda category: ProductCallback(
        action=ProductAction.LIST,
        catalog_id=category.catalog_id,
        category_id=category.id,
    ),
)

OPEN_CATALOG_PRODUCTS: Button[CatalogView] = Button(
    text=lambda catalog, translate: translate(
        catalog_products_key(catalog),
        count=catalog.uncategorized_product_count,
    ),
    callback=lambda catalog: ProductCallback(
        action=ProductAction.LIST,
        catalog_id=catalog.id,
    ),
    when=lambda catalog: catalog.category_count == 0,
)

PRODUCT_ENTRY: Button[ProductEntryView] = Button(
    text=lambda product, translate: translate(
        product_item_key(product),
        title=product.title,
        price=money_text(product.price),
    ),
    callback=lambda product: ProductCallback(
        action=ProductAction.CARD,
        product_id=product.id,
    ),
)

NEW_PRODUCT: Button[ProductListView] = Button(
    text=label(product_texts.NEW_PRODUCT_BUTTON),
    callback=lambda view: ProductCallback(
        action=ProductAction.NEW,
        catalog_id=view.catalog_id,
        category_id=view.category_id,
    ),
    permission=CatalogPermission.MANAGE,
    style=ButtonStyle.PRIMARY,
)


def _product_button(
    key: str,
    action: ProductAction,
    *,
    style: ButtonStyle | None = None,
    when: Callable[[ProductView], bool] | None = None,
) -> Button[ProductView]:
    return Button(
        text=label(key),
        callback=lambda product: ProductCallback(
            action=action,
            product_id=product.id,
        ),
        permission=CatalogPermission.MANAGE,
        when=when,
        style=style,
    )


EDIT_NAME = _product_button(product_texts.NAME_BUTTON, ProductAction.NAME)
EDIT_DESCRIPTION = _product_button(
    product_texts.DESCRIPTION_BUTTON, ProductAction.DESC
)
EDIT_PRICE = _product_button(product_texts.PRICE_BUTTON, ProductAction.PRICE)
OPEN_MEDIA = _product_button(product_texts.MEDIA_BUTTON, ProductAction.MEDIA)
OPEN_VARIANTS = _product_button(
    product_texts.VARIANTS_BUTTON, ProductAction.VARIANTS
)
PUBLISH = _product_button(
    product_texts.PUBLISH_BUTTON,
    ProductAction.PUBLISH,
    style=ButtonStyle.SUCCESS,
    when=lambda product: not product.is_published,
)
HIDE_PRODUCT = _product_button(
    texts.HIDE_BUTTON,
    ProductAction.HIDE,
    when=lambda product: product.is_published and product.is_visible,
)
SHOW_PRODUCT = _product_button(
    texts.SHOW_BUTTON,
    ProductAction.SHOW,
    style=ButtonStyle.SUCCESS,
    when=lambda product: product.is_published and not product.is_visible,
)
MARK_OUT = _product_button(
    product_texts.OUT_BUTTON,
    ProductAction.OUT,
    when=lambda product: product.is_in_stock,
)
MARK_IN_STOCK = _product_button(
    product_texts.STOCK_BUTTON,
    ProductAction.STOCK,
    when=lambda product: not product.is_in_stock,
)
DELETE_PRODUCT = _product_button(
    texts.DELETE_BUTTON,
    ProductAction.ASK_DELETE,
    style=ButtonStyle.DANGER,
)

BACK_TO_CATEGORY: Button[ProductView] = Button(
    text=label(texts.BACK_BUTTON),
    callback=lambda product: ProductCallback(
        action=ProductAction.LIST,
        catalog_id=product.catalog_id,
        category_id=product.category_id,
    ),
)

MEDIA_ENTRY: Button[MediaView] = Button(
    text=lambda media, translate: translate(media_item_key(media)),
    callback=lambda media: ProductCallback(
        action=ProductAction.DROP_MEDIA,
        item_id=media.id,
    ),
    permission=CatalogPermission.MANAGE,
    style=ButtonStyle.DANGER,
)

ADD_PHOTO: Button[ProductView] = Button(
    text=label(product_texts.ADD_PHOTO_BUTTON),
    callback=lambda product: ProductCallback(
        action=ProductAction.ADD_PHOTO,
        product_id=product.id,
    ),
    permission=CatalogPermission.MANAGE,
    style=ButtonStyle.PRIMARY,
)

ADD_VIDEO: Button[ProductView] = Button(
    text=label(product_texts.ADD_VIDEO_BUTTON),
    callback=lambda product: ProductCallback(
        action=ProductAction.ADD_VIDEO,
        product_id=product.id,
    ),
    permission=CatalogPermission.MANAGE,
    when=lambda product: product.video_count == 0,
)

VARIANT_ENTRY: Button[VariantView] = Button(
    text=lambda variant, translate: translate(
        variant_item_key(variant),
        title=variant.title,
        price=money_text(variant.price),
    ),
    callback=lambda variant: ProductCallback(
        action=ProductAction.VARIANT,
        item_id=variant.id,
    ),
    permission=CatalogPermission.MANAGE,
)

SET_AXIS: Button[ProductView] = Button(
    text=label(product_texts.AXIS_BUTTON),
    callback=lambda product: ProductCallback(
        action=ProductAction.AXIS,
        product_id=product.id,
    ),
    permission=CatalogPermission.MANAGE,
)

ADD_VARIANT: Button[ProductView] = Button(
    text=label(product_texts.ADD_VARIANT_BUTTON),
    callback=lambda product: ProductCallback(
        action=ProductAction.ADD_VARIANT,
        product_id=product.id,
    ),
    permission=CatalogPermission.MANAGE,
    when=lambda product: product.variant_label is not None,
    style=ButtonStyle.PRIMARY,
)

BACK_TO_PRODUCT: Button[ProductView] = Button(
    text=label(texts.BACK_BUTTON),
    callback=lambda product: ProductCallback(
        action=ProductAction.CARD,
        product_id=product.id,
    ),
)

DONE_WITH_MEDIA: Button[ProductView] = Button(
    text=label(product_texts.DONE_BUTTON),
    callback=lambda product: ProductCallback(
        action=ProductAction.CARD,
        product_id=product.id,
    ),
    style=ButtonStyle.SUCCESS,
)


def _back_to_catalog_or_category(view: ProductListView) -> CatalogCallback:
    if view.category_id is None:
        return CatalogCallback(
            action=CatalogAction.CARD,
            target=CatalogTarget.CATALOG,
            catalog_id=view.catalog_id,
        )
    return CatalogCallback(
        action=CatalogAction.CARD,
        target=CatalogTarget.CATEGORY,
        category_id=view.category_id,
    )


BACK_TO_CATEGORY_CARD: Button[ProductListView] = Button(
    text=label(texts.BACK_BUTTON),
    callback=_back_to_catalog_or_category,
)


SWITCH_LAYOUT: Button[ProductView] = Button(
    text=lambda product, translate: translate(
        product_texts.LAYOUT_SLIDESHOW_BUTTON
        if product.media_layout is MediaLayout.COLLAGE
        else product_texts.LAYOUT_COLLAGE_BUTTON
    ),
    callback=lambda product: ProductCallback(
        action=ProductAction.LAYOUT,
        product_id=product.id,
    ),
    permission=CatalogPermission.MANAGE,
    when=lambda product: product.photo_count > SINGLE_PHOTO,
)

PICK_BRAND: Button[ProductView] = Button(
    text=label(product_texts.BRAND_BUTTON),
    callback=lambda product: ProductCallback(
        action=ProductAction.BRAND,
        product_id=product.id,
    ),
    permission=CatalogPermission.MANAGE,
)

BRAND_PICK: Button[BrandPickView] = Button(
    text=lambda pick, translate: translate(
        product_texts.BRAND_ENTRY, title=pick.title
    ),
    callback=lambda pick: ProductCallback(
        action=ProductAction.SET_BRAND,
        product_id=pick.product_id,
        item_id=pick.brand_id,
    ),
    permission=CatalogPermission.MANAGE,
)

NEW_BRAND: Button[ProductView] = Button(
    text=label(product_texts.NEW_BRAND_BUTTON),
    callback=lambda _: CatalogCallback(
        action=CatalogAction.ASK_CREATE,
        target=CatalogTarget.BRAND,
    ),
    permission=CatalogPermission.MANAGE,
)


def _variant_button(
    key: str,
    action: ProductAction,
    *,
    style: ButtonStyle | None = None,
    when: Callable[[VariantCardView], bool] | None = None,
) -> Button[VariantCardView]:
    return Button(
        text=label(key),
        callback=lambda card: ProductCallback(
            action=action,
            product_id=card.product.id,
            item_id=card.variant.id,
        ),
        permission=CatalogPermission.MANAGE,
        when=when,
        style=style,
    )


RENAME_VARIANT = _variant_button(
    product_texts.VARIANT_RENAME_BUTTON, ProductAction.RENAME_VARIANT
)

REPRICE_VARIANT = _variant_button(
    product_texts.VARIANT_PRICE_BUTTON, ProductAction.REPRICE_VARIANT
)

SELL_VARIANT = _variant_button(
    product_texts.VARIANT_ON_BUTTON,
    ProductAction.VARIANT_ON,
    when=lambda card: not card.variant.is_available,
    style=ButtonStyle.SUCCESS,
)

STOP_VARIANT = _variant_button(
    product_texts.VARIANT_OFF_BUTTON,
    ProductAction.VARIANT_OFF,
    when=lambda card: card.variant.is_available,
)

DROP_VARIANT = _variant_button(
    product_texts.VARIANT_DROP_BUTTON,
    ProductAction.ASK_DROP_VARIANT,
    style=ButtonStyle.DANGER,
)

BACK_TO_VARIANTS: Button[VariantCardView] = Button(
    text=label(product_texts.BACK_TO_VARIANTS_BUTTON),
    callback=lambda card: ProductCallback(
        action=ProductAction.VARIANTS,
        product_id=card.product.id,
    ),
)


MOVE_PRODUCT = _product_button(
    product_texts.MOVE_BUTTON, ProductAction.MOVE
)

MOVE_CATALOG_PICK: Button[CatalogPickView] = Button(
    text=lambda pick, translate: translate(
        product_texts.MOVE_CATALOG_ENTRY, title=pick.title
    ),
    callback=lambda pick: ProductCallback(
        action=ProductAction.MOVE_TO_CATALOG,
        product_id=pick.product_id,
        catalog_id=pick.catalog_id,
    ),
    permission=CatalogPermission.MANAGE,
)

MOVE_CATEGORY_PICK: Button[CategoryPickView] = Button(
    text=lambda pick, translate: translate(
        product_texts.MOVE_CATEGORY_ENTRY, title=pick.title
    ),
    callback=lambda pick: ProductCallback(
        action=ProductAction.MOVE_TO,
        product_id=pick.product_id,
        catalog_id=pick.catalog_id,
        category_id=pick.category_id,
    ),
    permission=CatalogPermission.MANAGE,
)

MOVE_INTO_CATALOG: Button[MoveTargetView] = Button(
    text=label(product_texts.MOVE_INTO_CATALOG_BUTTON),
    callback=lambda view: ProductCallback(
        action=ProductAction.MOVE_TO,
        product_id=view.product.id,
        catalog_id=view.catalog.id,
    ),
    permission=CatalogPermission.MANAGE,
    when=lambda view: view.takes_products,
    style=ButtonStyle.PRIMARY,
)

BACK_TO_MOVE: Button[MoveTargetView] = Button(
    text=label(texts.BACK_BUTTON),
    callback=lambda view: ProductCallback(
        action=ProductAction.MOVE,
        product_id=view.product.id,
    ),
)
