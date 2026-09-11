from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class CatalogTarget(StrEnum):
    CATALOG = "catalog"
    CATEGORY = "category"
    BRAND = "brand"


class CatalogAction(StrEnum):
    HUB = "hub"
    LIST = "list"
    CARD = "card"
    ASK_CREATE = "create"
    ASK_RENAME = "rename"
    SHOW = "show"
    HIDE = "hide"
    ASK_DELETE = "ask_del"
    DELETE = "del"


class CatalogCallback(CallbackData, prefix="cat"):
    action: CatalogAction
    target: CatalogTarget = CatalogTarget.CATALOG
    catalog_id: int | None = None
    category_id: int | None = None
    brand_id: int | None = None
    page: int = 0
