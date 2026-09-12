from aiogram.types import InputRichBlockUnion

from telegramsales.modules.catalog.application.queries import (
    ShopCatalogView,
    ShopCategoryView,
    ShopProductEntryView,
    ShopProductView,
)
from telegramsales.modules.catalog.domain.enums import MediaLayout
from telegramsales.modules.catalog.presentation.bot import shop_texts
from telegramsales.modules.catalog.presentation.bot.shop_buttons import (
    ADD_TO_CART,
    BACK_TO_CATALOG,
    BACK_TO_PARENT,
    BACK_TO_PRODUCT,
    BACK_TO_PRODUCTS,
    CATALOG_ENTRY,
    CATEGORY_ENTRY,
    OPEN_PRODUCTS,
    PICK_VARIANT,
    PRODUCT_ENTRY,
    PRODUCTS_BACK_TO_CATALOG,
    PRODUCTS_BACK_TO_CATEGORY,
    PRODUCTS_BACK_TO_PARENT,
    VARIANT_PICK,
    back_to_catalogs,
    open_cart,
)
from telegramsales.modules.catalog.presentation.bot.views import (
    CountedView,
    ShopCatalogPageView,
    ShopProductsView,
    ShopVariantPickView,
    shop_product_card_key,
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
from telegramsales.shared.presentation.bot.money import money_text, struck_text
from telegramsales.shared.presentation.bot.navigation import home_button

CATALOGS: ListScreen[ShopCatalogView, CountedView] = ListScreen(
    content=lambda view, translate: translate(
        shop_texts.CATALOGS_EMPTY if view.total == 0 else shop_texts.CATALOGS
    ),
    item=CATALOG_ENTRY,
    footer=[home_button()],
)

CATALOG: ListScreen[ShopCategoryView, ShopCatalogPageView] = ListScreen(
    content=lambda view, translate: translate(
        shop_texts.CATALOG_EMPTY if view.total == 0 else shop_texts.CATALOG,
        title=view.catalog.title,
    ),
    item=CATEGORY_ENTRY,
    footer=[back_to_catalogs()],
)

CATEGORY: ListScreen[ShopCategoryView, ShopCategoryView] = ListScreen(
    content=lambda category, translate: translate(
        shop_texts.CATEGORY, title=category.title
    ),
    item=CATEGORY_ENTRY,
    footer=[OPEN_PRODUCTS, BACK_TO_CATALOG, BACK_TO_PARENT],
)

PRODUCT_LIST: ListScreen[ShopProductEntryView, ShopProductsView] = ListScreen(
    content=lambda view, translate: translate(
        shop_texts.PRODUCT_LIST_EMPTY
        if view.total == 0
        else shop_texts.PRODUCT_LIST,
        title=view.category.title,
        total=view.total,
    ),
    item=PRODUCT_ENTRY,
    footer=[
        PRODUCTS_BACK_TO_CATEGORY,
        PRODUCTS_BACK_TO_PARENT,
        PRODUCTS_BACK_TO_CATALOG,
    ],
)


def _photos(product: ShopProductView) -> list[InputRichBlockUnion]:
    if product.media_layout is MediaLayout.SLIDESHOW:
        return slideshow(product.photo_ids)
    return gallery(product.photo_ids)


def _header(product: ShopProductView, translate: ITranslator) -> str:
    return translate(
        shop_product_card_key(product),
        title=product.title,
        article=product.article,
        price=money_text(product.price),
        old_price=(
            ""
            if product.old_price is None
            else struck_text(money_text(product.old_price))
        ),
    )


def _variants(product: ShopProductView, translate: ITranslator) -> str:
    items = "\n".join(
        translate(
            shop_texts.PRODUCT_VARIANT_ITEM,
            title=variant.title,
            price=money_text(variant.price),
        )
        for variant in product.variants
    )
    return translate(
        shop_texts.PRODUCT_VARIANTS,
        label=product.variant_label or "",
        items=items,
    )


def _card_content(product: ShopProductView, translate: ITranslator) -> Content:
    blocks: list[InputRichBlockUnion] = [paragraph(_header(product, translate))]
    if product.brand_title is not None:
        blocks.append(
            paragraph(translate(shop_texts.PRODUCT_BRAND, brand=product.brand_title))
        )
    blocks.append(paragraph(product.description))
    if product.variants:
        blocks.append(paragraph(_variants(product, translate)))
    if not product.is_in_stock:
        blocks.append(paragraph(translate(shop_texts.PRODUCT_OUT)))
    blocks.extend(_photos(product))
    if product.video_id is not None:
        blocks.append(video(product.video_id))
    return blocks


PRODUCT_CARD: Screen[ShopProductView] = Screen(
    content=_card_content,
    buttons=[ADD_TO_CART, PICK_VARIANT, open_cart(), BACK_TO_PRODUCTS],
    layout=(2, 1),
)

VARIANT_PICKER: ListScreen[ShopVariantPickView, ShopProductView] = ListScreen(
    content=lambda product, translate: translate(
        shop_texts.VARIANT_PICKER,
        title=product.title,
        label=product.variant_label or "",
    ),
    item=VARIANT_PICK,
    footer=[BACK_TO_PRODUCT],
)
