from sqlalchemy import ColumnElement

from telegramsales.modules.catalog.contracts import CategoryId
from telegramsales.modules.catalog.infrastructure.models import CategoryORM


def parent_filter(parent_id: CategoryId | None) -> ColumnElement[bool]:
    if parent_id is None:
        return CategoryORM.parent_id.is_(None)
    return CategoryORM.parent_id == parent_id
