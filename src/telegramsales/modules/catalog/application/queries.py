from dataclasses import dataclass

from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
)


@dataclass(frozen=True, slots=True)
class CatalogView:
    id: CatalogId
    title: str
    is_active: bool
    category_count: int


@dataclass(frozen=True, slots=True)
class CategoryView:
    id: CategoryId
    catalog_id: CatalogId
    parent_id: CategoryId | None
    title: str
    is_active: bool
    child_count: int


@dataclass(frozen=True, slots=True)
class BrandView:
    id: BrandId
    title: str
    is_active: bool
