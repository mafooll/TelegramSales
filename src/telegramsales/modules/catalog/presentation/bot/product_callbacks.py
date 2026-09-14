from enum import StrEnum

from aiogram.filters.callback_data import CallbackData

from telegramsales.shared.presentation.bot.callbacks import PackedUUID


class ProductAction(StrEnum):
    LIST = "list"
    CARD = "card"
    NEW = "new"
    NAME = "name"
    DESC = "desc"
    PRICE = "price"
    PUBLISH = "pub"
    SHOW = "show"
    HIDE = "hide"
    STOCK = "stock"
    OUT = "out"
    ASK_DELETE = "askdel"
    DELETE = "del"
    MEDIA = "media"
    ADD_PHOTO = "addpic"
    ADD_VIDEO = "addvid"
    DROP_MEDIA = "delpic"
    LAYOUT = "layout"
    BRAND = "brand"
    SET_BRAND = "setbrn"
    VARIANTS = "vars"
    AXIS = "axis"
    ADD_VARIANT = "addvar"
    DROP_VARIANT = "delvar"
    VARIANT_ON = "varon"
    VARIANT_OFF = "varoff"


class ProductCallback(CallbackData, prefix="prd"):
    action: ProductAction
    product_id: PackedUUID | None = None
    catalog_id: int | None = None
    category_id: int | None = None
    item_id: int | None = None
    page: int = 0
