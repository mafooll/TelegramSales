from uuid import UUID

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.application.commands.orders import (
    CancelOrder,
    CancelOrderHandler,
)
from telegramsales.modules.orders.application.ports import IOrderQueries
from telegramsales.modules.orders.application.queries import OrderView
from telegramsales.modules.orders.contracts import OrderId
from telegramsales.modules.orders.presentation.bot import render, texts
from telegramsales.modules.orders.presentation.bot.callbacks import (
    OrderAction,
    OrderCallback,
)
from telegramsales.shared.presentation.bot.confirmation import (
    CONFIRMATION_SCREEN,
    ConfirmationView,
)
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.render import send, show
from telegramsales.shared.presentation.bot.rich import rich_screen

router = Router(name="orders.orders")


def _customer(context: RenderContext) -> CustomerId:
    return CustomerId(context.actor.id)


async def _order(
    queries: IOrderQueries,
    context: RenderContext,
    order_id: UUID | None,
) -> OrderView | None:
    if order_id is None:
        return None
    return await queries.get_for(OrderId(order_id), _customer(context))


ORDERS_COMMAND = "orders"


@router.message(Command(ORDERS_COMMAND))
async def show_orders_by_command(
    message: Message,
    context: RenderContext,
    queries: FromDishka[IOrderQueries],
    state: FSMContext,
) -> None:
    if message.bot is None:
        return

    await state.set_state(None)

    await send(
        message.bot,
        message.chat.id,
        await render.order_list(queries, context, _customer(context)),
    )


@router.callback_query(OrderCallback.filter(F.action == OrderAction.LIST))
async def show_orders(
    callback: CallbackQuery,
    callback_data: OrderCallback,
    context: RenderContext,
    queries: FromDishka[IOrderQueries],
) -> None:
    await callback.answer()
    await show(
        callback,
        await render.order_list(
            queries, context, _customer(context), callback_data.page
        ),
    )


@router.callback_query(OrderCallback.filter(F.action == OrderAction.CARD))
async def show_order(
    callback: CallbackQuery,
    callback_data: OrderCallback,
    context: RenderContext,
    queries: FromDishka[IOrderQueries],
) -> None:
    order = await _order(queries, context, callback_data.order_id)
    if order is None:
        await callback.answer(context.translate(texts.ORDER_GONE), show_alert=True)
        return

    await callback.answer()
    await show(callback, render.order_card(context, order))


@router.callback_query(OrderCallback.filter(F.action == OrderAction.ASK_CANCEL))
async def ask_to_cancel(
    callback: CallbackQuery,
    callback_data: OrderCallback,
    context: RenderContext,
    queries: FromDishka[IOrderQueries],
) -> None:
    order = await _order(queries, context, callback_data.order_id)
    if order is None:
        await callback.answer(context.translate(texts.ORDER_GONE), show_alert=True)
        return

    await callback.answer()
    view = ConfirmationView(
        question_key=texts.CANCEL_QUESTION,
        question_args={"number": order.number},
        confirm=OrderCallback(action=OrderAction.CANCEL, order_id=order.id),
        cancel=OrderCallback(action=OrderAction.CARD, order_id=order.id),
    )
    await show(callback, rich_screen(CONFIRMATION_SCREEN, view, context))


@router.callback_query(OrderCallback.filter(F.action == OrderAction.CANCEL))
async def cancel_order(
    callback: CallbackQuery,
    callback_data: OrderCallback,
    context: RenderContext,
    queries: FromDishka[IOrderQueries],
    handler: FromDishka[CancelOrderHandler],
) -> None:
    await callback.answer()
    if callback_data.order_id is None:
        return

    await handler.handle(
        CancelOrder(
            customer_id=_customer(context),
            order_id=OrderId(callback_data.order_id),
        )
    )
    await show_order(callback, callback_data, context, queries)
