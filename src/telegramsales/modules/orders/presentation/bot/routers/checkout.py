from collections.abc import Awaitable, Callable

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InputRichMessage, Message
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.customers.contracts import (
    CustomerId,
    ICustomerDirectory,
)
from telegramsales.modules.orders.application.commands.orders import (
    PlaceOrder,
    PlaceOrderHandler,
)
from telegramsales.modules.orders.application.readers import CartReader
from telegramsales.modules.orders.domain.values import Comment
from telegramsales.modules.orders.presentation.bot import render, texts
from telegramsales.modules.orders.presentation.bot.callbacks import (
    CartAction,
    CartCallback,
)
from telegramsales.modules.orders.presentation.bot.states import Checkout
from telegramsales.modules.orders.presentation.bot.views import CheckoutView
from telegramsales.shared.domain.contacts import (
    Address,
    Contacts,
    PersonName,
    Phone,
)
from telegramsales.shared.domain.exceptions import DomainError
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.filters import PlainTextFilter
from telegramsales.shared.presentation.bot.money import money_text
from telegramsales.shared.presentation.bot.render import show

router = Router(name="orders.checkout")

NAME_KEY = "contact_name"
PHONE_KEY = "contact_phone"
ADDRESS_KEY = "contact_address"
COMMENT_KEY = "order_comment"

BACK_TO_CART = CartCallback(action=CartAction.OPEN)


def _customer(context: RenderContext) -> CustomerId:
    return CustomerId(context.actor.id)


async def _view(
    state: FSMContext,
    reader: CartReader,
    context: RenderContext,
) -> CheckoutView | None:
    stored = await state.get_data()
    cart = await reader.read(_customer(context))
    if cart.is_empty or cart.has_unavailable:
        return None

    name = stored.get(NAME_KEY)
    phone = stored.get(PHONE_KEY)
    address = stored.get(ADDRESS_KEY)
    if name is None or phone is None or address is None:
        return None

    return CheckoutView(
        name=name,
        phone=phone,
        address=address,
        comment=stored.get(COMMENT_KEY, ""),
        lines=len(cart.lines),
        total=money_text(cart.total),
    )


async def _ask_name(
    callback: CallbackQuery,
    context: RenderContext,
    state: FSMContext,
) -> None:
    await state.set_state(Checkout.name)
    await show(callback, render.prompt(context, texts.ASK_NAME, BACK_TO_CART))


async def _take(
    message: Message,
    context: RenderContext,
    rejection_key: str,
    apply: Callable[[str], Awaitable[InputRichMessage]],
) -> None:
    if message.text is None:
        return

    try:
        rendered = await apply(message.text)
    except DomainError:
        await message.answer(text=context.translate(rejection_key))
        return

    if message.bot is not None:
        await message.bot.send_rich_message(
            chat_id=message.chat.id, rich_message=rendered
        )


@router.callback_query(CartCallback.filter(F.action == CartAction.CHECKOUT))
async def start_checkout(
    callback: CallbackQuery,
    context: RenderContext,
    state: FSMContext,
    reader: FromDishka[CartReader],
    directory: FromDishka[ICustomerDirectory],
) -> None:
    await callback.answer()
    cart = await reader.read(_customer(context))
    if cart.is_empty or cart.has_unavailable:
        await show(callback, render.cart(context, cart))
        return

    card = await directory.find(_customer(context))
    if card is None or card.contacts is None:
        await _ask_name(callback, context, state)
        return

    await state.update_data(
        {
            NAME_KEY: card.contacts.name,
            PHONE_KEY: card.contacts.phone,
            ADDRESS_KEY: card.contacts.address,
            COMMENT_KEY: "",
        }
    )
    view = await _view(state, reader, context)
    if view is None:
        await _ask_name(callback, context, state)
        return

    await show(callback, render.checkout(context, view))


@router.callback_query(CartCallback.filter(F.action == CartAction.CONTACTS))
async def change_contacts(
    callback: CallbackQuery,
    context: RenderContext,
    state: FSMContext,
) -> None:
    await callback.answer()
    await _ask_name(callback, context, state)


@router.message(Checkout.name, PlainTextFilter())
async def take_name(
    message: Message,
    context: RenderContext,
    state: FSMContext,
) -> None:
    async def apply(raw: str) -> InputRichMessage:
        await state.update_data({NAME_KEY: PersonName(raw).value})
        await state.set_state(Checkout.phone)
        return render.prompt(context, texts.ASK_PHONE, BACK_TO_CART)

    await _take(message, context, texts.NAME_REJECTED, apply)


@router.message(Checkout.phone, PlainTextFilter())
async def take_phone(
    message: Message,
    context: RenderContext,
    state: FSMContext,
) -> None:
    async def apply(raw: str) -> InputRichMessage:
        await state.update_data({PHONE_KEY: Phone(raw).value})
        await state.set_state(Checkout.address)
        return render.prompt(context, texts.ASK_ADDRESS, BACK_TO_CART)

    await _take(message, context, texts.PHONE_REJECTED, apply)


@router.message(Checkout.address, PlainTextFilter())
async def take_address(
    message: Message,
    context: RenderContext,
    state: FSMContext,
    reader: FromDishka[CartReader],
) -> None:
    async def apply(raw: str) -> InputRichMessage:
        await state.update_data({ADDRESS_KEY: Address(raw).value})
        await state.set_state(None)
        view = await _view(state, reader, context)
        if view is None:
            return render.cart(context, await reader.read(_customer(context)))
        return render.checkout(context, view)

    await _take(message, context, texts.ADDRESS_REJECTED, apply)


@router.callback_query(CartCallback.filter(F.action == CartAction.COMMENT))
async def ask_comment(
    callback: CallbackQuery,
    context: RenderContext,
    state: FSMContext,
) -> None:
    await callback.answer()
    await state.set_state(Checkout.comment)
    await show(callback, render.prompt(context, texts.ASK_COMMENT, BACK_TO_CART))


@router.message(Checkout.comment, PlainTextFilter())
async def take_comment(
    message: Message,
    context: RenderContext,
    state: FSMContext,
    reader: FromDishka[CartReader],
) -> None:
    async def apply(raw: str) -> InputRichMessage:
        await state.update_data({COMMENT_KEY: Comment(raw).value})
        await state.set_state(None)
        view = await _view(state, reader, context)
        if view is None:
            return render.cart(context, await reader.read(_customer(context)))
        return render.checkout(context, view)

    await _take(message, context, texts.COMMENT_REJECTED, apply)


@router.callback_query(CartCallback.filter(F.action == CartAction.PLACE))
async def place_order(
    callback: CallbackQuery,
    context: RenderContext,
    state: FSMContext,
    reader: FromDishka[CartReader],
    handler: FromDishka[PlaceOrderHandler],
) -> None:
    await callback.answer()
    view = await _view(state, reader, context)
    if view is None:
        await show(
            callback,
            await render.cart_of(reader, context, _customer(context)),
        )
        return

    number = await handler.handle(
        PlaceOrder(
            customer_id=_customer(context),
            contacts=Contacts(
                name=PersonName(view.name),
                phone=Phone(view.phone),
                address=Address(view.address),
            ),
            comment=Comment(view.comment),
        )
    )
    await state.clear()
    await show(callback, render.placed(context, number))
