from enum import StrEnum

from aiogram.filters.callback_data import CallbackData

from telegramsales.shared.presentation.bot.callbacks import PackedUUID


class CartAction(StrEnum):
    OPEN = "open"
    LINE = "line"
    MORE = "more"
    LESS = "less"
    DROP = "drop"
    ASK_CLEAR = "askclr"
    CLEAR = "clear"
    SHARE = "share"
    CHECKOUT = "check"
    CONTACTS = "contacts"
    COMMENT = "comment"
    PLACE = "place"


class CartCallback(CallbackData, prefix="crt"):
    action: CartAction
    item_id: int | None = None
    page: int = 0


class OrderAction(StrEnum):
    LIST = "list"
    CARD = "card"
    ASK_CANCEL = "askcan"
    CANCEL = "cancel"


class OrderCallback(CallbackData, prefix="ord"):
    action: OrderAction
    order_id: PackedUUID | None = None
    page: int = 0
    keep: bool = False


class SelectionAction(StrEnum):
    VIEW = "view"
    ADOPT = "adopt"


class SelectionCallback(CallbackData, prefix="sel"):
    action: SelectionAction
    selection_id: PackedUUID
