from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.types import InputRichMessage, Message

from telegramsales.apps.bot import texts
from telegramsales.shared.application.i18n import ITranslator
from telegramsales.shared.presentation.bot.content import paragraph

router = Router(name="health")


@router.message(CommandStart())
async def start(message: Message, bot: Bot, translate: ITranslator) -> None:
    await bot.send_rich_message(
        chat_id=message.chat.id,
        rich_message=InputRichMessage(blocks=[paragraph(translate(texts.GREETING))]),
    )
