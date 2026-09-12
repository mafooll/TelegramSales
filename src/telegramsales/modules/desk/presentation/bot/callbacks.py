from enum import StrEnum

from aiogram.filters.callback_data import CallbackData

from telegramsales.shared.presentation.bot.callbacks import PackedUUID


class DeskAction(StrEnum):
    CARD = "card"
    TAKE = "take"
    PAID = "paid"
    SHIPPED = "shipped"
    DONE = "done"
    ASK_CANCEL = "askcan"
    CANCEL = "cancel"


class DeskCallback(CallbackData, prefix="dsk"):
    action: DeskAction
    order_id: PackedUUID
