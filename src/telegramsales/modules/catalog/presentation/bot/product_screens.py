from telegramsales.modules.catalog.application.queries import (
    MediaView,
    ProductEntryView,
    ProductView,
    VariantView,
)
from telegramsales.modules.catalog.presentation.bot import product_texts
from telegramsales.modules.catalog.presentation.bot.product_buttons import (
    ADD_PHOTO,
    ADD_VARIANT,
    ADD_VIDEO,
    BACK_TO_CATEGORY,
    BACK_TO_CATEGORY_CARD,
    BACK_TO_PRODUCT,
    DELETE_PRODUCT,
    DONE_WITH_MEDIA,
    EDIT_DESCRIPTION,
    EDIT_NAME,
    EDIT_PRICE,
    HIDE_PRODUCT,
    MARK_IN_STOCK,
    MARK_OUT,
    MEDIA_ENTRY,
    NEW_PRODUCT,
    OPEN_MEDIA,
    OPEN_VARIANTS,
    PRODUCT_ENTRY,
    PUBLISH,
    SET_AXIS,
    SHOW_PRODUCT,
    VARIANT_ENTRY,
)
from telegramsales.modules.catalog.presentation.bot.views import (
    ProductListView,
    product_card_key,
    variant_screen_key,
)
from telegramsales.shared.application.i18n import ITranslator
from telegramsales.shared.presentation.bot.content import (
    Content,
    gallery,
    paragraph,
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
        *gallery(product.photo_ids),
        *([] if product.video_id is None else [video(product.video_id)]),
    ]


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
        PUBLISH,
        HIDE_PRODUCT,
        SHOW_PRODUCT,
        MARK_OUT,
        MARK_IN_STOCK,
        DELETE_PRODUCT,
        BACK_TO_CATEGORY,
    ],
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
        *gallery(product.photo_ids),
    ],
    item=MEDIA_ENTRY,
    footer=[ADD_PHOTO, ADD_VIDEO, DONE_WITH_MEDIA],
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
