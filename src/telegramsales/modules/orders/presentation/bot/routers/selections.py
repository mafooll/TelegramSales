from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.customers.contracts import (
    CustomerId,
    ICustomerDirectory,
)
from telegramsales.modules.orders.application.commands.selections import (
    AdoptSelection,
    AdoptSelectionHandler,
)
from telegramsales.modules.orders.application.readers import (
    CartReader,
    SelectionReader,
)
from telegramsales.modules.orders.contracts import SelectionId
from telegramsales.modules.orders.presentation.bot import render, texts
from telegramsales.modules.orders.presentation.bot.callbacks import (
    SelectionAction,
    SelectionCallback,
)
from telegramsales.shared.presentation.bot.callbacks import unpack_uuid
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.render import answer_once, show

router = Router(name="orders.selections")

SELECTION_PREFIX = "c"


def _selection_id(payload: str | None) -> SelectionId | None:
    if payload is None or not payload.startswith(SELECTION_PREFIX):
        return None
    unpacked = unpack_uuid(payload[len(SELECTION_PREFIX) :])
    return None if unpacked is None else SelectionId(unpacked)


def _customer(context: RenderContext) -> CustomerId:
    return CustomerId(context.actor.id)


@router.message(CommandStart(deep_link=True))
async def open_shared_cart(
    message: Message,
    command: CommandObject,
    context: RenderContext,
    reader: FromDishka[SelectionReader],
    customers: FromDishka[ICustomerDirectory],
) -> None:
    selection_id = _selection_id(command.args)
    if selection_id is None or message.bot is None:
        return

    if message.from_user is not None:
        await customers.register(
            CustomerId(message.from_user.id),
            message.from_user.full_name,
        )

    view = await reader.read(selection_id)
    if view is None:
        await message.answer(text=context.translate(texts.SELECTION_GONE))
        return

    await message.bot.send_rich_message(
        chat_id=message.chat.id,
        rich_message=render.selection(context, view),
    )


@router.callback_query(SelectionCallback.filter(F.action == SelectionAction.VIEW))
async def show_selection(
    callback: CallbackQuery,
    callback_data: SelectionCallback,
    context: RenderContext,
    reader: FromDishka[SelectionReader],
) -> None:
    view = await reader.read(SelectionId(callback_data.selection_id))
    if view is None:
        await answer_once(
            callback,
            context.translate(texts.SELECTION_GONE),
            alert=True,
        )
        return

    await show(callback, render.selection(context, view))


@router.callback_query(SelectionCallback.filter(F.action == SelectionAction.ADOPT))
async def adopt_selection(
    callback: CallbackQuery,
    callback_data: SelectionCallback,
    context: RenderContext,
    cart: FromDishka[CartReader],
    handler: FromDishka[AdoptSelectionHandler],
) -> None:
    adoption = await handler.handle(
        AdoptSelection(
            customer_id=_customer(context),
            selection_id=SelectionId(callback_data.selection_id),
        )
    )
    await answer_once(
        callback,
        _adoption_text(context, adoption.added, adoption.skipped),
    )
    await show(
        callback,
        await render.cart_of(cart, context, _customer(context)),
    )


def _adoption_text(context: RenderContext, added: int, skipped: int) -> str:
    if added == 0:
        return context.translate(texts.ADOPTED_NOTHING)
    if skipped == 0:
        return context.translate(texts.ADOPTED, added=added)
    return context.translate(texts.ADOPTED_PARTLY, added=added, skipped=skipped)
