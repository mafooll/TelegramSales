from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InputRichMessage, Message
import structlog
from structlog.stdlib import BoundLogger

from telegramsales.shared.presentation.bot.content import without_media

logger: BoundLogger = structlog.get_logger()

NOT_MODIFIED = "message is not modified"
REJECTED_MEDIA = (
    "RICH_MESSAGE_PHOTO_INVALID",
    "RICH_MESSAGE_VIDEO_INVALID",
    "RICH_MESSAGE_MEDIA_INVALID",
    "wrong file identifier",
)


def is_media_rejected(error: TelegramBadRequest) -> bool:
    return any(reason in str(error) for reason in REJECTED_MEDIA)


async def send(
    bot: Bot,
    chat_id: int,
    message: InputRichMessage,
) -> None:
    try:
        await bot.send_rich_message(chat_id=chat_id, rich_message=message)
    except TelegramBadRequest as error:
        if not is_media_rejected(error):
            raise
        logger.warning("rich_media_rejected", chat_id=chat_id, error=str(error))
        await bot.send_rich_message(
            chat_id=chat_id,
            rich_message=without_media(message),
        )


async def show(callback: CallbackQuery, message: InputRichMessage) -> None:
    if not isinstance(callback.message, Message):
        return

    try:
        await callback.message.edit_text(rich_message=message)
    except TelegramBadRequest as error:
        if NOT_MODIFIED in str(error):
            return
        if callback.message.bot is not None:
            await send(callback.message.bot, callback.message.chat.id, message)
