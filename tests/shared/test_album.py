import asyncio
from datetime import UTC, datetime
from typing import Any

from aiogram.types import Chat, Message, TelegramObject
import pytest

from telegramsales.shared.presentation.bot.album import ALBUM_KEY, AlbumMiddleware

NO_DELAY = 0.01
CHAT = Chat(id=1, type="private")


def message(message_id: int, group: str | None = None) -> Message:
    return Message(
        message_id=message_id,
        date=datetime.now(UTC),
        chat=CHAT,
        media_group_id=group,
    )


class Collector:
    def __init__(self) -> None:
        self.calls: list[list[int]] = []

    async def __call__(self, _event: TelegramObject, data: dict[str, Any]) -> None:
        self.calls.append([item.message_id for item in data[ALBUM_KEY]])


async def test_a_lone_message_passes_through() -> None:
    collector = Collector()
    middleware = AlbumMiddleware(NO_DELAY)

    await middleware(collector, message(1), {})

    assert collector.calls == [[1]]


async def test_an_album_reaches_the_handler_once() -> None:
    collector = Collector()
    middleware = AlbumMiddleware(NO_DELAY)

    await asyncio.gather(
        *[middleware(collector, message(index, "group"), {}) for index in (1, 2, 3)]
    )

    assert collector.calls == [[1, 2, 3]]


async def test_an_album_arrives_in_order() -> None:
    collector = Collector()
    middleware = AlbumMiddleware(NO_DELAY)

    await asyncio.gather(
        *[middleware(collector, message(index, "group"), {}) for index in (3, 1, 2)]
    )

    assert collector.calls == [[1, 2, 3]]


async def test_two_albums_do_not_mix() -> None:
    collector = Collector()
    middleware = AlbumMiddleware(NO_DELAY)

    await asyncio.gather(
        middleware(collector, message(1, "first"), {}),
        middleware(collector, message(2, "second"), {}),
    )

    assert sorted(collector.calls) == [[1], [2]]


@pytest.mark.parametrize("size", [1, 2, 10])
async def test_every_album_size_is_delivered_whole(size: int) -> None:
    collector = Collector()
    middleware = AlbumMiddleware(NO_DELAY)

    await asyncio.gather(
        *[
            middleware(collector, message(index, "group"), {})
            for index in range(1, size + 1)
        ]
    )

    assert collector.calls == [list(range(1, size + 1))]
