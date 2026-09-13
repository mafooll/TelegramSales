from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from dishka.integrations.aiogram import FromDishka

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.desk.application.commands.support import (
    CallForSupport,
    CallForSupportHandler,
)
from telegramsales.modules.desk.presentation.bot import texts
from telegramsales.modules.desk.presentation.bot.filters import InCustomerChatFilter
from telegramsales.shared.presentation.bot.context import RenderContext

router = Router(name="desk.support")

SUPPORT_COMMAND = "support"


@router.message(Command(SUPPORT_COMMAND), InCustomerChatFilter())
async def call_for_support(
    message: Message,
    context: RenderContext,
    handler: FromDishka[CallForSupportHandler],
) -> None:
    if message.from_user is None:
        return

    called = await handler.handle(
        CallForSupport(customer_id=CustomerId(message.from_user.id))
    )
    answer = texts.SUPPORT_OPENED if called else texts.SUPPORT_REFUSED
    await message.answer(context.translate(answer))
