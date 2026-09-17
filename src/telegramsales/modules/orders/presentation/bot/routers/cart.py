from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.application.commands.cart import (
    ClearCart,
    ClearCartHandler,
    DecreaseCartItem,
    DecreaseCartItemHandler,
    IncreaseCartItem,
    IncreaseCartItemHandler,
    RemoveCartItem,
    RemoveCartItemHandler,
)
from telegramsales.modules.orders.application.commands.selections import (
    ShareCart,
    ShareCartHandler,
)
from telegramsales.modules.orders.application.queries import CartLineView
from telegramsales.modules.orders.application.readers import CartReader
from telegramsales.modules.orders.contracts import CartItemId
from telegramsales.modules.orders.presentation.bot import render, texts
from telegramsales.modules.orders.presentation.bot.callbacks import (
    CartAction,
    CartCallback,
)
from telegramsales.shared.presentation.bot.callbacks import pack_uuid
from telegramsales.shared.presentation.bot.confirmation import (
    CONFIRMATION_SCREEN,
    ConfirmationView,
)
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.render import send, show
from telegramsales.shared.presentation.bot.rich import rich_screen

router = Router(name="orders.cart")

SELECTION_PREFIX = "c"
LINK_TEMPLATE = "https://t.me/{username}?start={payload}"


def _customer(context: RenderContext) -> CustomerId:
    return CustomerId(context.actor.id)


async def _line(
    reader: CartReader,
    context: RenderContext,
    item_id: int | None,
) -> CartLineView | None:
    if item_id is None:
        return None
    view = await reader.read(_customer(context))
    return next((line for line in view.lines if line.item_id == item_id), None)


async def _show_cart(
    callback: CallbackQuery,
    context: RenderContext,
    reader: CartReader,
    page: int = 0,
) -> None:
    await show(
        callback,
        await render.cart_of(reader, context, _customer(context), page),
    )


CART_COMMAND = "cart"


@router.message(Command(CART_COMMAND))
async def open_cart_by_command(
    message: Message,
    context: RenderContext,
    reader: FromDishka[CartReader],
    state: FSMContext,
) -> None:
    if message.bot is None:
        return

    await state.set_state(None)

    await send(
        message.bot,
        message.chat.id,
        await render.cart_of(reader, context, _customer(context)),
    )


@router.callback_query(CartCallback.filter(F.action == CartAction.OPEN))
async def open_cart(
    callback: CallbackQuery,
    callback_data: CartCallback,
    context: RenderContext,
    reader: FromDishka[CartReader],
) -> None:
    await _show_cart(callback, context, reader, callback_data.page)


@router.callback_query(CartCallback.filter(F.action == CartAction.LINE))
async def open_line(
    callback: CallbackQuery,
    callback_data: CartCallback,
    context: RenderContext,
    reader: FromDishka[CartReader],
) -> None:
    line = await _line(reader, context, callback_data.item_id)
    if line is None:
        await _show_cart(callback, context, reader)
        return

    await show(callback, render.cart_line(context, line))


@router.callback_query(CartCallback.filter(F.action == CartAction.MORE))
async def take_more(
    callback: CallbackQuery,
    callback_data: CartCallback,
    context: RenderContext,
    reader: FromDishka[CartReader],
    handler: FromDishka[IncreaseCartItemHandler],
) -> None:
    if callback_data.item_id is None:
        return

    await handler.handle(
        IncreaseCartItem(
            customer_id=_customer(context),
            item_id=CartItemId(callback_data.item_id),
        )
    )
    await open_line(callback, callback_data, context, reader)


@router.callback_query(CartCallback.filter(F.action == CartAction.LESS))
async def take_less(
    callback: CallbackQuery,
    callback_data: CartCallback,
    context: RenderContext,
    reader: FromDishka[CartReader],
    handler: FromDishka[DecreaseCartItemHandler],
) -> None:
    if callback_data.item_id is None:
        return

    await handler.handle(
        DecreaseCartItem(
            customer_id=_customer(context),
            item_id=CartItemId(callback_data.item_id),
        )
    )
    await open_line(callback, callback_data, context, reader)


@router.callback_query(CartCallback.filter(F.action == CartAction.DROP))
async def drop_line(
    callback: CallbackQuery,
    callback_data: CartCallback,
    context: RenderContext,
    reader: FromDishka[CartReader],
    handler: FromDishka[RemoveCartItemHandler],
) -> None:
    if callback_data.item_id is None:
        return

    await handler.handle(
        RemoveCartItem(
            customer_id=_customer(context),
            item_id=CartItemId(callback_data.item_id),
        )
    )
    await _show_cart(callback, context, reader)


@router.callback_query(CartCallback.filter(F.action == CartAction.ASK_CLEAR))
async def ask_to_clear(callback: CallbackQuery, context: RenderContext) -> None:
    view = ConfirmationView(
        question_key=texts.CLEAR_QUESTION,
        confirm=CartCallback(action=CartAction.CLEAR),
        cancel=CartCallback(action=CartAction.OPEN),
    )
    await show(callback, rich_screen(CONFIRMATION_SCREEN, view, context))


@router.callback_query(CartCallback.filter(F.action == CartAction.CLEAR))
async def clear_cart(
    callback: CallbackQuery,
    context: RenderContext,
    reader: FromDishka[CartReader],
    handler: FromDishka[ClearCartHandler],
) -> None:
    await handler.handle(ClearCart(customer_id=_customer(context)))
    await _show_cart(callback, context, reader)


@router.callback_query(CartCallback.filter(F.action == CartAction.SHARE))
async def share_cart(
    callback: CallbackQuery,
    context: RenderContext,
    bot: Bot,
    handler: FromDishka[ShareCartHandler],
) -> None:
    await callback.answer()
    selection_id = await handler.handle(ShareCart(customer_id=_customer(context)))
    me = await bot.me()
    link = LINK_TEMPLATE.format(
        username=me.username,
        payload=f"{SELECTION_PREFIX}{pack_uuid(selection_id)}",
    )
    if callback.message is not None:
        await bot.send_message(
            chat_id=callback.message.chat.id,
            text=context.translate(texts.SHARE_MESSAGE, link=link),
        )
