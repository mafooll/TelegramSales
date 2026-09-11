from telegramsales.modules.catalog.contracts import CatalogId
from telegramsales.modules.catalog.domain.entities import Category
from telegramsales.modules.catalog.domain.exceptions import (
    CatalogNotEmptyError,
    CategoryNotEmptyError,
    ForeignCatalogError,
    NestingTooDeepError,
)

EMPTY = 0


def ensure_can_hold_children(parent: Category, catalog_id: CatalogId) -> None:
    if parent.catalog_id != catalog_id:
        raise ForeignCatalogError(category_id=parent.id, catalog_id=catalog_id)
    if not parent.is_root:
        raise NestingTooDeepError(category_id=parent.id)


def ensure_catalog_is_empty(catalog_id: CatalogId, category_count: int) -> None:
    if category_count > EMPTY:
        raise CatalogNotEmptyError(
            catalog_id=catalog_id,
            category_count=category_count,
        )


def ensure_category_is_empty(category: Category, child_count: int) -> None:
    if child_count > EMPTY:
        raise CategoryNotEmptyError(
            category_id=category.id,
            child_count=child_count,
        )
