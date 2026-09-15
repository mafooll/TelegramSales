from datetime import UTC, datetime
from typing import Any

from aiogram.types import CallbackQuery
import pytest

from telegramsales.shared.presentation.bot.middlewares import (
    CallbackAnswerMiddleware,
)
from telegramsales.shared.presentation.bot.render import (
    answer_once,
    start_answering,
    stop_answering,
)

NOW = datetime(2026, 9, 15, 12, 0, tzinfo=UTC)
TEXT = "готово"

type Answers = list[tuple[str | None, bool]]


@pytest.fixture
def callback() -> CallbackQuery:
    return CallbackQuery.model_validate(
        {
            "id": "1",
            "from": {"id": 1, "is_bot": False, "first_name": "Иван"},
            "chat_instance": "instance",
            "data": "probe",
            "message": {
                "message_id": 2,
                "date": NOW,
                "chat": {"id": 3, "type": "private"},
            },
        }
    )


@pytest.fixture
def answers(monkeypatch: pytest.MonkeyPatch) -> Answers:
    recorded: Answers = []

    async def record(
        _self: CallbackQuery,
        text: str | None = None,
        show_alert: bool | None = None,  # noqa: FBT001
        **_kwargs: Any,
    ) -> bool:
        recorded.append((text, bool(show_alert)))
        return True

    monkeypatch.setattr(CallbackQuery, "answer", record)
    return recorded


async def silent(_event: Any, _data: dict[str, Any]) -> None:  # noqa: ANN401
    return None


async def test_an_answer_reaches_telegram_once(
    callback: CallbackQuery,
    answers: Answers,
) -> None:
    token = start_answering()

    await answer_once(callback, TEXT)
    await answer_once(callback, "и ещё раз")
    answered = stop_answering(token)

    assert answers == [(TEXT, False)]
    assert answered


async def test_an_alert_keeps_its_flag(
    callback: CallbackQuery,
    answers: Answers,
) -> None:
    token = start_answering()

    await answer_once(callback, TEXT, alert=True)
    stop_answering(token)

    assert answers == [(TEXT, True)]


async def test_a_silent_handler_is_answered_by_the_middleware(
    callback: CallbackQuery,
    answers: Answers,
) -> None:
    await CallbackAnswerMiddleware()(silent, callback, {})

    assert answers == [(None, False)]


async def test_a_handler_that_answered_is_left_alone(
    callback: CallbackQuery,
    answers: Answers,
) -> None:
    async def talking(_event: Any, _data: dict[str, Any]) -> None:  # noqa: ANN401
        await answer_once(callback, TEXT)

    await CallbackAnswerMiddleware()(talking, callback, {})

    assert answers == [(TEXT, False)]


async def test_a_failing_handler_still_gets_answered(
    callback: CallbackQuery,
    answers: Answers,
) -> None:
    async def failing(_event: Any, _data: dict[str, Any]) -> None:  # noqa: ANN401
        message = "сломалось"
        raise RuntimeError(message)

    with pytest.raises(RuntimeError):
        await CallbackAnswerMiddleware()(failing, callback, {})

    assert answers == [(None, False)]
