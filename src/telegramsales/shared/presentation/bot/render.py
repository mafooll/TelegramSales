from asyncio import gather
from contextvars import ContextVar, Token

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InputRichMessage, Message
import structlog
from structlog.stdlib import BoundLogger

from telegramsales.shared.presentation.bot.content import without_media

logger: BoundLogger = structlog.get_logger()

NOT_MODIFIED = "message is not modified"
_answered: ContextVar[bool] = ContextVar("callback_answered", default=False)
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


async def answer_once(
    callback: CallbackQuery,
    text: str | None = None,
    *,
    alert: bool = False,
) -> None:
    if _answered.get():
        return

    _answered.set(True)
    try:
        await callback.answer(text=text, show_alert=alert)
    except TelegramBadRequest as error:
        logger.debug("callback_answer_skipped", error=str(error))


def start_answering() -> Token[bool]:
    return _answered.set(False)


def stop_answering(token: Token[bool]) -> bool:
    answered = _answered.get()
    _answered.reset(token)
    return answered


async def _draw(callback: CallbackQuery, message: InputRichMessage) -> None:
    if not isinstance(callback.message, Message):
        return

    try:
        await callback.message.edit_text(rich_message=message)
    except TelegramBadRequest as error:
        if NOT_MODIFIED in str(error):
            return
        if callback.message.bot is not None:
            await send(callback.message.bot, callback.message.chat.id, message)


async def show(callback: CallbackQuery, message: InputRichMessage) -> None:
    await gather(answer_once(callback), _draw(callback, message))
