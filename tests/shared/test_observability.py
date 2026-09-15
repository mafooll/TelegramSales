from datetime import UTC, datetime
from typing import Any

from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.methods import SendMessage, SendRichMessage
from aiogram.types import (
    CallbackQuery,
    Chat,
    InputRichBlockButtons,
    InputRichMessage,
    Message,
    Update,
    User,
)
import pytest
import structlog

from telegramsales.shared.application.access import Actor
from telegramsales.shared.domain.exceptions import DomainError
from telegramsales.shared.presentation.bot.api_log import (
    POLLING_METHOD,
    method_payload,
)
from telegramsales.shared.presentation.bot.content import paragraph
from telegramsales.shared.presentation.bot.observability import (
    MAX_TEXT_LENGTH,
    UpdateLogMiddleware,
    actor_payload,
    shorten,
    update_payload,
)

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
CHAT_ID = 500
USER_ID = 100


def user() -> User:
    return User(id=USER_ID, is_bot=False, first_name="Иван", username="ivan")


def chat() -> Chat:
    return Chat(id=CHAT_ID, type="private")


def message(text: str = "/cart") -> Message:
    return Message(message_id=7, date=NOW, chat=chat(), from_user=user(), text=text)


def callback() -> CallbackQuery:
    return CallbackQuery(
        id="1",
        from_user=user(),
        chat_instance="instance",
        data="shop:card:::abc::0",
        message=message("экран"),
    )


async def handler(_event: Any, _data: dict[str, Any]) -> str:  # noqa: ANN401
    return "handled"


def test_a_long_text_is_cut_to_the_limit() -> None:
    cut = shorten("a" * (MAX_TEXT_LENGTH + 10))

    assert len(cut) == MAX_TEXT_LENGTH + 1
    assert cut.endswith("…")


def test_a_message_update_carries_its_text() -> None:
    payload = update_payload(Update(update_id=1, message=message()))

    assert payload["update_id"] == 1
    assert payload["event_type"] == "message"
    assert payload["text"] == "/cart"
    assert payload["chat_id"] == CHAT_ID
    assert payload["content_type"] == "text"


def test_a_callback_update_carries_its_data() -> None:
    payload = update_payload(Update(update_id=2, callback_query=callback()))

    assert payload["callback_data"] == "shop:card:::abc::0"
    assert payload["message_id"] == 7


def test_the_actor_adds_its_rights() -> None:
    payload = actor_payload(
        {
            "event_from_user": user(),
            "actor": Actor(id=USER_ID, permissions=frozenset({"catalog.manage"})),
        }
    )

    assert payload["user_id"] == USER_ID
    assert payload["username"] == "ivan"
    assert payload["is_staff"]
    assert payload["permissions"] == ["catalog.manage"]


def test_an_anonymous_update_adds_nothing() -> None:
    assert actor_payload({}) == {}


async def test_a_handled_update_is_logged_with_its_duration() -> None:
    update = Update(update_id=3, message=message())

    with structlog.testing.capture_logs() as entries:
        await UpdateLogMiddleware()(handler, update, {})

    events = [entry["event"] for entry in entries]
    finished = entries[-1]

    assert events == ["update_received", "update_handled"]
    assert finished["is_handled"]
    assert finished["duration_ms"] >= 0


async def test_a_quiet_update_keeps_its_payload_out() -> None:
    update = Update(update_id=4, message=message("секрет"))

    with structlog.testing.capture_logs() as entries:
        await UpdateLogMiddleware(with_payload=False)(handler, update, {})

    assert entries[0]["event"] == "update_received"


def test_an_api_call_names_its_method_and_arguments() -> None:
    payload = method_payload(SendMessage(chat_id=CHAT_ID, text="привет"))

    assert payload["method"] == "SendMessage"
    assert payload["chat_id"] == CHAT_ID
    assert payload["text"] == "привет"


def test_a_rich_message_call_lists_its_blocks() -> None:
    method = SendRichMessage(
        chat_id=CHAT_ID,
        rich_message=InputRichMessage(
            blocks=[paragraph("текст"), InputRichBlockButtons(buttons=[])]
        ),
    )
    payload = method_payload(method)

    assert payload["method"] == "SendRichMessage"
    assert payload["blocks"] == ["paragraph", "buttons"]


async def unhandled(_event: Any, _data: dict[str, Any]) -> Any:  # noqa: ANN401
    return UNHANDLED


async def failing(_event: Any, _data: dict[str, Any]) -> Any:  # noqa: ANN401
    message = "база недоступна"
    raise RuntimeError(message)


async def test_an_unhandled_update_says_so() -> None:
    update = Update(update_id=5, message=message())

    with structlog.testing.capture_logs() as entries:
        await UpdateLogMiddleware()(unhandled, update, {})

    assert not entries[-1]["is_handled"]


async def test_a_failed_update_is_logged_and_reraised() -> None:
    update = Update(update_id=6, message=message())

    with (
        structlog.testing.capture_logs() as entries,
        pytest.raises(RuntimeError),
    ):
        await UpdateLogMiddleware()(failing, update, {})

    failure = entries[-1]

    assert failure["event"] == "update_failed"
    assert failure["log_level"] == "error"
    assert failure["duration_ms"] >= 0


def test_polling_is_not_an_api_call_worth_logging() -> None:
    assert POLLING_METHOD == "GetUpdates"


REFUSAL = "нужна фотография"


async def refusing(_event: Any, _data: dict[str, Any]) -> Any:  # noqa: ANN401
    raise DomainError(REFUSAL, details={"product_id": "42"})


async def test_a_refused_update_is_a_warning_without_a_traceback() -> None:
    update = Update(update_id=7, message=message())

    with (
        structlog.testing.capture_logs() as entries,
        pytest.raises(DomainError),
    ):
        await UpdateLogMiddleware()(refusing, update, {})

    refusal = entries[-1]

    assert refusal["event"] == "update_rejected"
    assert refusal["log_level"] == "warning"
    assert refusal["reason"] == "DomainError"
    assert refusal["details"] == {"product_id": "42"}
