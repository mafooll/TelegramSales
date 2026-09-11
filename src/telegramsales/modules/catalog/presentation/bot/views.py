from dataclasses import dataclass

from telegramsales.modules.catalog.application.queries import (
    BrandView,
    CatalogView,
    CategoryView,
    MediaView,
    ProductEntryView,
    ProductView,
    VariantView,
)
from telegramsales.modules.catalog.contracts import CategoryId
from telegramsales.modules.catalog.domain.enums import MediaKind
from telegramsales.modules.catalog.presentation.bot import product_texts, texts


@dataclass(frozen=True, slots=True)
class CountedView:
    total: int


@dataclass(frozen=True, slots=True)
class PromptView:
    message_key: str


@dataclass(frozen=True, slots=True)
class ProductListView:
    category_id: CategoryId
    total: int


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
