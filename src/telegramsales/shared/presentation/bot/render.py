from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InputRichMessage, Message

NOT_MODIFIED = "message is not modified"


async def show(callback: CallbackQuery, message: InputRichMessage) -> None:
    if not isinstance(callback.message, Message):
        return

    try:
        await callback.message.edit_text(rich_message=message)
    except TelegramBadRequest as error:
        if NOT_MODIFIED in str(error):
            return
        if callback.message.bot is not None:
            await callback.message.bot.send_rich_message(
                chat_id=callback.message.chat.id,
                rich_message=message,
            )
