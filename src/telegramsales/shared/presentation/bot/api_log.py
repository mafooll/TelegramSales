from collections.abc import Awaitable, Callable
import time
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.methods import Response, TelegramMethod
from aiogram.methods.base import TelegramType
from aiogram.types import InputRichMessage
import structlog
from structlog.stdlib import BoundLogger

from telegramsales.shared.presentation.bot.observability import elapsed_ms, shorten

logger: BoundLogger = structlog.get_logger()

TRACKED_ARGUMENTS = (
    "chat_id",
    "message_id",
    "message_thread_id",
    "user_id",
    "name",
    "text",
    "caption",
    "callback_data",
    "photo",
    "video",
    "show_alert",
)
POLLING_METHOD = "GetUpdates"
SLOW_CALL_MS = 1000.0


def _block_types(message: InputRichMessage) -> list[str]:
    return [block.type.value for block in message.blocks or []]


def method_payload(method: TelegramMethod[TelegramType]) -> dict[str, Any]:
    payload: dict[str, Any] = {"method": type(method).__name__}

    for name in TRACKED_ARGUMENTS:
        value: object = getattr(method, name, None)
        if isinstance(value, str):
            payload[name] = shorten(value)
        elif isinstance(value, bool | int):
            payload[name] = value

    rich_message: object = getattr(method, "rich_message", None)
    if isinstance(rich_message, InputRichMessage):
        payload["blocks"] = _block_types(rich_message)
    return payload


class ApiCallLogger:
    async def __call__(
        self,
        make_request: Callable[
            [Bot, TelegramMethod[TelegramType]],
            Awaitable[Response[TelegramType]],
        ],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        if type(method).__name__ == POLLING_METHOD:
            return await make_request(bot, method)

        payload = method_payload(method)
        started = time.perf_counter()
        try:
            response = await make_request(bot, method)
        except TelegramAPIError as error:
            logger.warning(
                "api_call_failed",
                **payload,
                duration_ms=elapsed_ms(started),
                error=str(error),
            )
            raise

        duration = elapsed_ms(started)
        if duration >= SLOW_CALL_MS:
            logger.warning("api_call_slow", **payload, duration_ms=duration)
        else:
            logger.debug("api_call", **payload, duration_ms=duration)
        return response
