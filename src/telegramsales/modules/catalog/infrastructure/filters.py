from sqlalchemy import ColumnElement

from telegramsales.modules.catalog.contracts import CategoryId
from telegramsales.modules.catalog.infrastructure.models import (
    CategoryORM,
    ProductORM,
)


def parent_filter(parent_id: CategoryId | None) -> ColumnElement[bool]:
    if parent_id is None:
        return CategoryORM.parent_id.is_(None)
    return CategoryORM.parent_id == parent_id


def category_filter(category_id: CategoryId | None) -> ColumnElement[bool]:
    if category_id is None:
        return ProductORM.category_id.is_(None)
    return ProductORM.category_id == category_id
