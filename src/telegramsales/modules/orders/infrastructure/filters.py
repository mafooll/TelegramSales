from sqlalchemy import ColumnElement

from telegramsales.modules.catalog.contracts import VariantId
from telegramsales.modules.orders.infrastructure.models import CartItemORM


def variant_filter(variant_id: VariantId | None) -> ColumnElement[bool]:
    if variant_id is None:
        return CartItemORM.variant_id.is_(None)
    return CartItemORM.variant_id == variant_id
