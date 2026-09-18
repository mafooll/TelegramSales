from dataclasses import dataclass

from aiogram.filters.callback_data import CallbackData

from telegramsales.modules.catalog.application.queries import (
    BrandView,
    CatalogView,
    CategoryView,
    MediaView,
    ProductEntryView,
    ProductView,
    ShopCatalogView,
    ShopCategoryView,
    ShopProductEntryView,
    VariantView,
)
from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
    ProductId,
    VariantId,
)
from telegramsales.modules.catalog.domain.enums import MediaKind
from telegramsales.modules.catalog.presentation.bot import (
    product_texts,
    shop_texts,
    texts,
)
from telegramsales.shared.application.i18n import ITranslator
from telegramsales.shared.domain.money import Money


@dataclass(frozen=True, slots=True)
class CountedView:
    total: int


@dataclass(frozen=True, slots=True)
class SearchView:
    needle: str
    total: int


@dataclass(frozen=True, slots=True)
class PromptView:
    message_key: str
    back: CallbackData


@dataclass(frozen=True, slots=True)
class ProductListView:
    catalog_id: CatalogId
    category_id: CategoryId | None
    total: int


@dataclass(frozen=True, slots=True)
class ShopCatalogPageView:
    catalog: ShopCatalogView
    total: int


@dataclass(frozen=True, slots=True)
class ShopVariantPickView:
    product_id: ProductId
    variant_id: VariantId
    title: str
    price: Money


@dataclass(frozen=True, slots=True)
class ShopProductsView:
    catalog: ShopCatalogView
    category: ShopCategoryView | None
    total: int


@dataclass(frozen=True, slots=True)
class CatalogPickView:
    product_id: ProductId
    catalog_id: CatalogId
    title: str


@dataclass(frozen=True, slots=True)
class CategoryPickView:
    product_id: ProductId
    catalog_id: CatalogId
    category_id: CategoryId
    title: str


@dataclass(frozen=True, slots=True)
class MoveTargetView:
    product: ProductView
    catalog: CatalogView
    takes_products: bool


@dataclass(frozen=True, slots=True)
class VariantCardView:
    product: ProductView
    variant: VariantView


@dataclass(frozen=True, slots=True)
class BrandPickView:
    product_id: ProductId
    brand_id: BrandId
    title: str


def catalog_item_key(catalog: CatalogView) -> str:
    return texts.CATALOG_ITEM if catalog.is_active else texts.CATALOG_ITEM_HIDDEN


def category_item_key(category: CategoryView) -> str:
    return texts.CATEGORY_ITEM if category.is_active else texts.CATEGORY_ITEM_HIDDEN


def brand_item_key(brand: BrandView) -> str:
    return texts.BRAND_ITEM if brand.is_active else texts.BRAND_ITEM_HIDDEN


def product_item_key(product: ProductEntryView) -> str:
    if not product.is_published:
        return product_texts.PRODUCT_ITEM_DRAFT
    if not product.is_visible:
        return product_texts.PRODUCT_ITEM_HIDDEN
    return product_texts.PRODUCT_ITEM


def product_card_key(product: ProductView) -> str:
    if product.old_price is not None:
        return product_texts.PRODUCT_CARD_SALE
    return product_texts.PRODUCT_CARD


def media_item_key(media: MediaView) -> str:
    if media.kind is MediaKind.VIDEO:
        return product_texts.MEDIA_VIDEO_ITEM
    return product_texts.MEDIA_ITEM


def variant_item_key(variant: VariantView) -> str:
    if variant.is_available:
        return product_texts.VARIANT_ITEM
    return product_texts.VARIANT_ITEM_OUT


def variant_screen_key(product: ProductView) -> str:
    if product.variant_label is None:
        return product_texts.VARIANT_SCREEN_CLOSED
    return product_texts.VARIANT_SCREEN


def shop_product_item_key(product: ShopProductEntryView) -> str:
    if product.is_in_stock:
        return shop_texts.PRODUCT_ENTRY
    return shop_texts.PRODUCT_ENTRY_OUT


def catalog_products_key(catalog: CatalogView) -> str:
    if catalog.uncategorized_product_count == 0:
        return product_texts.OPEN_CATALOG_PRODUCTS_EMPTY_BUTTON
    return product_texts.OPEN_CATALOG_PRODUCTS_BUTTON


def breadcrumbs(view: ShopProductsView, translate: ITranslator) -> str:
    category = view.category
    trail = [translate(shop_texts.BREADCRUMB_ROOT), view.catalog.title]
    if category is not None:
        if category.parent_title is not None:
            trail.append(category.parent_title)
        trail.append(category.title)
    return translate(shop_texts.BREADCRUMB_SEPARATOR).join(trail)
