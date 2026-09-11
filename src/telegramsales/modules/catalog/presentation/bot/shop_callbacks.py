from enum import StrEnum

from aiogram.filters.callback_data import CallbackData

from telegramsales.shared.presentation.bot.callbacks import PackedUUID


class ShopAction(StrEnum):
    CATALOGS = "cats"
    CATALOG = "cat"
    CATEGORY = "sub"
    PRODUCTS = "list"
    PRODUCT = "card"


class ShopCallback(CallbackData, prefix="shop"):
    action: ShopAction
    catalog_id: int | None = None
    category_id: int | None = None
    product_id: PackedUUID | None = None
    page: int = 0
