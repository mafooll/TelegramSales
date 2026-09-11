from dataclasses import dataclass

from telegramsales.modules.catalog.application.queries import (
    BrandView,
    CatalogView,
    CategoryView,
)
from telegramsales.modules.catalog.presentation.bot import texts


@dataclass(frozen=True, slots=True)
class CountedView:
    total: int


@dataclass(frozen=True, slots=True)
class PromptView:
    message_key: str


def catalog_item_key(catalog: CatalogView) -> str:
    return texts.CATALOG_ITEM if catalog.is_active else texts.CATALOG_ITEM_HIDDEN


def category_item_key(category: CategoryView) -> str:
    return texts.CATEGORY_ITEM if category.is_active else texts.CATEGORY_ITEM_HIDDEN


def brand_item_key(brand: BrandView) -> str:
    return texts.BRAND_ITEM if brand.is_active else texts.BRAND_ITEM_HIDDEN
