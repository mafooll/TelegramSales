from aiogram.types import InputRichBlockUnion

from telegramsales.modules.catalog.application.queries import (
    MediaView,
    ProductEntryView,
    ProductView,
    VariantView,
)
from telegramsales.modules.catalog.domain.enums import MediaLayout
from telegramsales.modules.catalog.presentation.bot import product_texts
from telegramsales.modules.catalog.presentation.bot.product_buttons import (
    ADD_PHOTO,
    ADD_VARIANT,
    ADD_VIDEO,
    BACK_TO_CATEGORY,
    BACK_TO_CATEGORY_CARD,
    BACK_TO_MOVE,
    BACK_TO_PRODUCT,
    BACK_TO_VARIANTS,
    BRAND_PICK,
    DELETE_PRODUCT,
    DONE_WITH_MEDIA,
    DROP_VARIANT,
    EDIT_DESCRIPTION,
    EDIT_NAME,
    EDIT_PRICE,
    HIDE_PRODUCT,
    MARK_IN_STOCK,
    MARK_OUT,
    MEDIA_ENTRY,
    MOVE_CATALOG_PICK,
    MOVE_CATEGORY_PICK,
    MOVE_INTO_CATALOG,
    MOVE_PRODUCT,
    NEW_BRAND,
    NEW_PRODUCT,
    OPEN_MEDIA,
    OPEN_VARIANTS,
    PICK_BRAND,
    PRODUCT_ENTRY,
    PUBLISH,
    RENAME_VARIANT,
    REPRICE_VARIANT,
    SELL_VARIANT,
    SET_AXIS,
    SHOW_PRODUCT,
    STOP_VARIANT,
    SWITCH_LAYOUT,
    VARIANT_ENTRY,
)
from telegramsales.modules.catalog.presentation.bot.views import (
    BrandPickView,
    CatalogPickView,
    CategoryPickView,
    MoveTargetView,
    ProductListView,
    VariantCardView,
    product_card_key,
    variant_screen_key,
)
from telegramsales.shared.application.i18n import ITranslator
from telegramsales.shared.presentation.bot.content import (
    Content,
    gallery,
    paragraph,
    slideshow,
    video,
)
from telegramsales.shared.presentation.bot.keyboard import ListScreen, Screen
from telegramsales.shared.presentation.bot.money import money_text

PRODUCT_LIST: ListScreen[ProductEntryView, ProductListView] = ListScreen(
    content=lambda view, translate: translate(
        product_texts.PRODUCT_LIST_EMPTY
        if view.total == 0
        else product_texts.PRODUCT_LIST,
        total=view.total,
    ),
    item=PRODUCT_ENTRY,
    footer=[NEW_PRODUCT, BACK_TO_CATEGORY_CARD],
)


def _card_content(product: ProductView, translate: ITranslator) -> Content:
    return [
        paragraph(_card_text(product, translate)),
        *_photos(product),
        *([] if product.video_id is None else [video(product.video_id)]),
    ]


def _photos(product: ProductView) -> list[InputRichBlockUnion]:
    if product.media_layout is MediaLayout.SLIDESHOW:
        return slideshow(product.photo_ids)
    return gallery(product.photo_ids)


def _card_text(product: ProductView, translate: ITranslator) -> str:
    return translate(
        product_card_key(product),
        title=product.title,
        article=product.article,
        description=product.description,
        price=money_text(product.price),
        old_price=(
            "" if product.old_price is None else money_text(product.old_price)
        ),
        brand=product.brand_title or "",
        photos=product.photo_count,
        videos=product.video_count,
        variants=product.variant_count,
    )


PRODUCT_CARD: Screen[ProductView] = Screen(
    content=_card_content,
    buttons=[
        EDIT_NAME,
        EDIT_DESCRIPTION,
        EDIT_PRICE,
        OPEN_MEDIA,
        OPEN_VARIANTS,
        PICK_BRAND,
        MOVE_PRODUCT,
        PUBLISH,
        HIDE_PRODUCT,
        SHOW_PRODUCT,
        MARK_OUT,
        MARK_IN_STOCK,
        DELETE_PRODUCT,
        BACK_TO_CATEGORY,
    ],
    row_width=2,
    layout=(2, 2, 2, 2),
)

MEDIA_BOARD: ListScreen[MediaView, ProductView] = ListScreen(
    content=lambda product, translate: [
        paragraph(
            translate(
                product_texts.MEDIA_SCREEN,
                title=product.title,
                photos=product.photo_count,
                videos=product.video_count,
            )
        ),
        *_photos(product),
    ],
    item=MEDIA_ENTRY,
    footer=[ADD_PHOTO, ADD_VIDEO, SWITCH_LAYOUT, DONE_WITH_MEDIA],
    footer_layout=(2, 1, 1),
)

VARIANT_BOARD: ListScreen[VariantView, ProductView] = ListScreen(
    content=lambda product, translate: translate(
        variant_screen_key(product),
        title=product.title,
        label=product.variant_label or "",
        total=product.variant_count,
    ),
    item=VARIANT_ENTRY,
    footer=[SET_AXIS, ADD_VARIANT, BACK_TO_PRODUCT],
)


BRAND_PAGE_SIZE = 50
MOVE_PAGE_SIZE = 50

BRAND_PICKER: ListScreen[BrandPickView, ProductView] = ListScreen(
    content=lambda product, translate: translate(
        product_texts.BRAND_PICKER,
        title=product.title,
        brand=product.brand_title or translate(product_texts.BRAND_UNKNOWN),
    ),
    item=BRAND_PICK,
    footer=[NEW_BRAND, BACK_TO_PRODUCT],
    footer_layout=(2,),
)


VARIANT_CARD: Screen[VariantCardView] = Screen(
    content=lambda card, translate: translate(
        product_texts.VARIANT_CARD,
        product=card.product.title,
        label=card.product.variant_label or "",
        title=card.variant.title,
        price=money_text(card.variant.price),
    ),
    buttons=[
        RENAME_VARIANT,
        REPRICE_VARIANT,
        SELL_VARIANT,
        STOP_VARIANT,
        DROP_VARIANT,
        BACK_TO_VARIANTS,
    ],
    layout=(2, 1),
)


MOVE_CATALOG_PICKER: ListScreen[CatalogPickView, ProductView] = ListScreen(
    content=lambda product, translate: translate(
        product_texts.MOVE_CATALOG_PICKER, title=product.title
    ),
    item=MOVE_CATALOG_PICK,
    footer=[BACK_TO_PRODUCT],
)

MOVE_CATEGORY_PICKER: ListScreen[CategoryPickView, MoveTargetView] = ListScreen(
    content=lambda view, translate: translate(
        product_texts.MOVE_CATEGORY_PICKER,
        title=view.product.title,
        catalog=view.catalog.title,
    ),
    item=MOVE_CATEGORY_PICK,
    footer=[MOVE_INTO_CATALOG, BACK_TO_MOVE],
    footer_layout=(2,),
)
