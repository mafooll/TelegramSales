from aiogram.enums import ButtonStyle

from telegramsales.modules.desk.presentation.bot import texts
from telegramsales.modules.desk.presentation.bot.callbacks import (
    DeskAction,
    DeskCallback,
)
from telegramsales.modules.desk.presentation.bot.views import (
    can_cancel,
    can_finish,
    can_pay,
    can_ship,
    can_take,
)
from telegramsales.modules.orders.contracts import OrderCardView
from telegramsales.shared.presentation.bot.keyboard import Button, label

TAKE: Button[OrderCardView] = Button(
    text=lambda card, translate: translate(
        texts.REASSIGN_BUTTON if card.is_taken else texts.TAKE_BUTTON
    ),
    callback=lambda card: DeskCallback(action=DeskAction.TAKE, order_id=card.id),
    when=can_take,
    style=ButtonStyle.PRIMARY,
)

PAID: Button[OrderCardView] = Button(
    text=label(texts.PAID_BUTTON),
    callback=lambda card: DeskCallback(action=DeskAction.PAID, order_id=card.id),
    when=can_pay,
)

SHIPPED: Button[OrderCardView] = Button(
    text=label(texts.SHIPPED_BUTTON),
    callback=lambda card: DeskCallback(action=DeskAction.SHIPPED, order_id=card.id),
    when=can_ship,
)

DONE: Button[OrderCardView] = Button(
    text=label(texts.DONE_BUTTON),
    callback=lambda card: DeskCallback(action=DeskAction.DONE, order_id=card.id),
    when=can_finish,
    style=ButtonStyle.SUCCESS,
)

CANCEL: Button[OrderCardView] = Button(
    text=label(texts.CANCEL_BUTTON),
    callback=lambda card: DeskCallback(
        action=DeskAction.ASK_CANCEL,
        order_id=card.id,
    ),
    when=can_cancel,
    style=ButtonStyle.DANGER,
)
