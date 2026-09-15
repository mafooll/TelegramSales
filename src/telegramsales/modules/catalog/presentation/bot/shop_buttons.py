from aiogram.enums import ButtonStyle

from telegramsales.modules.catalog.application.queries import (
    ShopCatalogView,
    ShopCategoryView,
    ShopProductEntryView,
    ShopProductView,
)
from telegramsales.modules.catalog.presentation.bot import shop_texts
from telegramsales.modules.catalog.presentation.bot.shop_callbacks import (
    ShopAction,
    ShopCallback,
)
from telegramsales.modules.catalog.presentation.bot.views import (
    ShopProductsView,
    ShopVariantPickView,
    shop_product_item_key,
)
from telegramsales.shared.application.i18n import ITranslator
from telegramsales.shared.presentation.bot.keyboard import Button, label
from telegramsales.shared.presentation.bot.money import money_text

CATALOG_ENTRY: Button[ShopCatalogView] = Button(
    text=lambda catalog, translate: translate(
        shop_texts.CATALOG_ENTRY, title=catalog.title
    ),
    callback=lambda catalog: ShopCallback(
        action=ShopAction.CATALOG,
        catalog_id=catalog.id,
    ),
)

CATEGORY_ENTRY: Button[ShopCategoryView] = Button(
    text=lambda category, translate: translate(
        shop_texts.CATEGORY_ENTRY, title=category.title
    ),
    callback=lambda category: ShopCallback(
        action=ShopAction.CATEGORY,
        catalog_id=category.catalog_id,
        category_id=category.id,
    ),
)

OPEN_PRODUCTS: Button[ShopCategoryView] = Button(
    text=lambda category, translate: translate(
        shop_texts.OPEN_PRODUCTS_BUTTON, count=category.product_count
    ),
    callback=lambda category: ShopCallback(
        action=ShopAction.PRODUCTS,
        catalog_id=category.catalog_id,
        category_id=category.id,
    ),
    when=lambda category: category.product_count > 0,
)

PRODUCT_ENTRY: Button[ShopProductEntryView] = Button(
    text=label(shop_texts.OPEN_PRODUCT_BUTTON),
    callback=lambda product: ShopCallback(
        action=ShopAction.PRODUCT,
        product_id=product.id,
    ),
)

ADD_ENTRY_TO_CART: Button[ShopProductEntryView] = Button(
    text=label(shop_texts.ADD_TO_CART_BUTTON),
    callback=lambda product: ShopCallback(
        action=ShopAction.ADD,
        product_id=product.id,
    ),
    when=lambda product: product.is_in_stock and not product.has_variants,
    style=ButtonStyle.PRIMARY,
)


def product_caption(
    product: ShopProductEntryView,
    translate: ITranslator,
) -> str:
    return translate(
        shop_product_item_key(product),
        title=product.title,
        price=money_text(product.price),
    )


def back_to_catalogs[ViewType]() -> Button[ViewType]:
    return Button(
        text=label(shop_texts.BACK_BUTTON),
        callback=lambda _: ShopCallback(action=ShopAction.CATALOGS),
    )


BACK_TO_CATALOG: Button[ShopCategoryView] = Button(
    text=label(shop_texts.BACK_BUTTON),
    callback=lambda category: ShopCallback(
        action=ShopAction.CATALOG,
        catalog_id=category.catalog_id,
    ),
    when=lambda category: category.parent_id is None,
)

BACK_TO_PARENT: Button[ShopCategoryView] = Button(
    text=label(shop_texts.BACK_BUTTON),
    callback=lambda category: ShopCallback(
        action=ShopAction.CATEGORY,
        catalog_id=category.catalog_id,
        category_id=category.parent_id,
    ),
    when=lambda category: category.parent_id is not None,
)


def _is_leaf(view: ShopProductsView) -> bool:
    return view.category is None or view.category.child_count == 0


PRODUCTS_BACK_TO_CATEGORY: Button[ShopProductsView] = Button(
    text=label(shop_texts.BACK_BUTTON),
    callback=lambda view: ShopCallback(
        action=ShopAction.CATEGORY,
        catalog_id=view.catalog.id,
        category_id=None if view.category is None else view.category.id,
    ),
    when=lambda view: not _is_leaf(view),
)

PRODUCTS_BACK_TO_PARENT: Button[ShopProductsView] = Button(
    text=label(shop_texts.BACK_BUTTON),
    callback=lambda view: ShopCallback(
        action=ShopAction.CATEGORY,
        catalog_id=view.catalog.id,
        category_id=None if view.category is None else view.category.parent_id,
    ),
    when=lambda view: (
        view.category is not None
        and _is_leaf(view)
        and view.category.parent_id is not None
    ),
)

PRODUCTS_BACK_TO_CATALOG: Button[ShopProductsView] = Button(
    text=label(shop_texts.BACK_BUTTON),
    callback=lambda view: ShopCallback(
        action=ShopAction.CATALOG,
        catalog_id=view.catalog.id,
    ),
    when=lambda view: (
        view.category is not None
        and _is_leaf(view)
        and view.category.parent_id is None
    ),
)

PRODUCTS_BACK_TO_CATALOGS: Button[ShopProductsView] = Button(
    text=label(shop_texts.BACK_BUTTON),
    callback=lambda _: ShopCallback(action=ShopAction.CATALOGS),
    when=lambda view: view.category is None,
)

BACK_TO_PRODUCTS: Button[ShopProductView] = Button(
    text=label(shop_texts.BACK_BUTTON),
    callback=lambda product: ShopCallback(
        action=ShopAction.PRODUCTS,
        catalog_id=product.catalog_id,
        category_id=product.category_id,
    ),
)


ADD_TO_CART: Button[ShopProductView] = Button(
    text=label(shop_texts.ADD_TO_CART_BUTTON),
    callback=lambda product: ShopCallback(
        action=ShopAction.ADD,
        product_id=product.id,
    ),
    when=lambda product: product.is_in_stock and not product.variants,
    style=ButtonStyle.PRIMARY,
)

PICK_VARIANT: Button[ShopProductView] = Button(
    text=label(shop_texts.PICK_VARIANT_BUTTON),
    callback=lambda product: ShopCallback(
        action=ShopAction.VARIANTS,
        product_id=product.id,
    ),
    when=lambda product: product.is_in_stock and bool(product.variants),
    style=ButtonStyle.PRIMARY,
)

VARIANT_PICK: Button[ShopVariantPickView] = Button(
    text=lambda pick, translate: translate(
        shop_texts.VARIANT_ENTRY,
        title=pick.title,
        price=money_text(pick.price),
    ),
    callback=lambda pick: ShopCallback(
        action=ShopAction.ADD,
        product_id=pick.product_id,
        variant_id=pick.variant_id,
    ),
)


def open_cart[ViewType]() -> Button[ViewType]:
    return Button(
        text=label(shop_texts.OPEN_CART_BUTTON),
        callback=lambda _: ShopCallback(action=ShopAction.CART),
    )


BACK_TO_PRODUCT: Button[ShopProductView] = Button(
    text=label(shop_texts.BACK_BUTTON),
    callback=lambda product: ShopCallback(
        action=ShopAction.PRODUCT,
        product_id=product.id,
    ),
)
