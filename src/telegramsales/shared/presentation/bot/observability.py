from collections.abc import Awaitable, Callable
import time
from typing import TYPE_CHECKING, Any, override

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.types import CallbackQuery, Message, TelegramObject, Update, User
import structlog
from structlog.stdlib import BoundLogger

if TYPE_CHECKING:
    from telegramsales.shared.application.access import Actor

logger: BoundLogger = structlog.get_logger()

MAX_TEXT_LENGTH = 512
ELLIPSIS = "…"
MILLISECONDS = 1000


def shorten(text: str, limit: int = MAX_TEXT_LENGTH) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + ELLIPSIS


def elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * MILLISECONDS, 1)


def message_payload(message: Message) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "message_id": message.message_id,
        "content_type": message.content_type,
        "chat_id": message.chat.id,
        "chat_type": message.chat.type,
    }
    if message.message_thread_id is not None:
        payload["thread_id"] = message.message_thread_id
    text = message.text or message.caption
    if text is not None:
        payload["text"] = shorten(text)
        payload["text_length"] = len(text)
    if message.photo:
        payload["photo_id"] = message.photo[-1].file_id
    if message.video is not None:
        payload["video_id"] = message.video.file_id
    if message.media_group_id is not None:
        payload["media_group_id"] = message.media_group_id
    return payload


def callback_payload(callback: CallbackQuery) -> dict[str, Any]:
    payload: dict[str, Any] = {"callback_data": callback.data}
    if isinstance(callback.message, Message):
        payload["message_id"] = callback.message.message_id
        payload["chat_id"] = callback.message.chat.id
    return payload


def event_payload(event: TelegramObject) -> dict[str, Any]:
    if isinstance(event, Message):
        return message_payload(event)
    if isinstance(event, CallbackQuery):
        return callback_payload(event)
    return {}


def update_payload(update: Update) -> dict[str, Any]:
    event = update.event
    return {
        "update_id": update.update_id,
        "event_type": update.event_type,
        **event_payload(event),
    }


def actor_payload(data: dict[str, Any]) -> dict[str, Any]:
    user: User | None = data.get("event_from_user")
    actor: Actor | None = data.get("actor")
    payload: dict[str, Any] = {}
    if user is not None:
        payload["user_id"] = user.id
        payload["username"] = user.username
    if actor is not None:
        payload["is_staff"] = actor.is_staff
        payload["permissions"] = sorted(actor.permissions)
    return payload


class UpdateLogMiddleware(BaseMiddleware):
    def __init__(self, *, with_payload: bool = True) -> None:
        self._with_payload: bool = with_payload

    @override
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Update):
            return await handler(event, data)

        structlog.contextvars.clear_contextvars()
        payload = update_payload(event) if self._with_payload else {
            "update_id": event.update_id,
            "event_type": event.event_type,
        }
        structlog.contextvars.bind_contextvars(**payload)

        logger.info("update_received")
        started = time.perf_counter()
        try:
            result = await handler(event, data)
        except Exception:
            logger.exception("update_failed", duration_ms=elapsed_ms(started))
            raise

        logger.info(
            "update_handled",
            duration_ms=elapsed_ms(started),
            is_handled=result is not UNHANDLED,
        )
        return result


class HandlerLogMiddleware(BaseMiddleware):
    @override
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        structlog.contextvars.bind_contextvars(**actor_payload(data))
        return await handler(event, data)
