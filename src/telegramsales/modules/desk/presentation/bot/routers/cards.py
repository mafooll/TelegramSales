from aiogram import F, Router
from aiogram.types import CallbackQuery
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.desk.presentation.bot import texts
from telegramsales.modules.desk.presentation.bot.callbacks import (
    DeskAction,
    DeskCallback,
)
from telegramsales.modules.desk.presentation.bot.screens import ORDER_CARD
from telegramsales.modules.orders.contracts import (
    IOrderCards,
    IOrderDesk,
    OrderCardView,
    OrderId,
    OrderStatus,
)
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.shared.presentation.bot.confirmation import (
    CONFIRMATION_SCREEN,
    ConfirmationView,
)
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.render import answer_once, show
from telegramsales.shared.presentation.bot.rich import rich_screen

router = Router(name="desk.cards")

MOVES = {
    DeskAction.PAID: OrderStatus.PAID,
    DeskAction.SHIPPED: OrderStatus.SHIPPED,
    DeskAction.DONE: OrderStatus.DONE,
}


async def _card(
    cards: IOrderCards,
    callback_data: DeskCallback,
) -> OrderCardView | None:
    return await cards.card(OrderId(callback_data.order_id))


async def _answer_gone(callback: CallbackQuery, context: RenderContext) -> None:
    await answer_once(callback, context.translate(texts.ORDER_GONE), alert=True)


@router.callback_query(DeskCallback.filter(F.action == DeskAction.CARD))
async def show_card(
    callback: CallbackQuery,
    callback_data: DeskCallback,
    context: RenderContext,
    cards: FromDishka[IOrderCards],
) -> None:
    card = await _card(cards, callback_data)
    if card is None:
        await _answer_gone(callback, context)
        return

    await show(callback, rich_screen(ORDER_CARD, card, context))


@router.callback_query(DeskCallback.filter(F.action == DeskAction.TAKE))
async def take_in_work(
    callback: CallbackQuery,
    callback_data: DeskCallback,
    context: RenderContext,
    cards: FromDishka[IOrderCards],
    desk: FromDishka[IOrderDesk],
) -> None:
    card = await _card(cards, callback_data)
    if card is None:
        await _answer_gone(callback, context)
        return
    if card.is_run_by(StaffId(context.actor.id)):
        await answer_once(callback, context.translate(texts.ALREADY_YOURS))
        return

    await desk.take_in_work(card.id, context.actor)
    await answer_once(callback, context.translate(texts.TAKEN))


@router.callback_query(DeskCallback.filter(F.action.in_(MOVES)))
async def change_status(
    callback: CallbackQuery,
    callback_data: DeskCallback,
    context: RenderContext,
    desk: FromDishka[IOrderDesk],
) -> None:
    await desk.change_status(
        OrderId(callback_data.order_id),
        MOVES[callback_data.action],
        context.actor,
    )
    await answer_once(callback, context.translate(texts.STATUS_CHANGED))


@router.callback_query(DeskCallback.filter(F.action == DeskAction.ASK_CANCEL))
async def ask_to_cancel(
    callback: CallbackQuery,
    callback_data: DeskCallback,
    context: RenderContext,
    cards: FromDishka[IOrderCards],
) -> None:
    card = await _card(cards, callback_data)
    if card is None:
        await _answer_gone(callback, context)
        return

    view = ConfirmationView(
        question_key=texts.CANCEL_QUESTION,
        question_args={"number": card.number},
        confirm=DeskCallback(action=DeskAction.CANCEL, order_id=card.id),
        cancel=DeskCallback(action=DeskAction.CARD, order_id=card.id),
    )
    await show(callback, rich_screen(CONFIRMATION_SCREEN, view, context))


@router.callback_query(DeskCallback.filter(F.action == DeskAction.CANCEL))
async def cancel_order(
    callback: CallbackQuery,
    callback_data: DeskCallback,
    context: RenderContext,
    desk: FromDishka[IOrderDesk],
) -> None:
    await desk.cancel(OrderId(callback_data.order_id), context.actor)
    await answer_once(callback, context.translate(texts.STATUS_CHANGED))
