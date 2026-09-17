from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import SendMessage
from aiogram.types import (
    InputMediaPhoto,
    InputRichBlockButtons,
    InputRichBlockCollage,
    InputRichBlockParagraph,
    InputRichBlockPhoto,
    InputRichMessage,
    RichBlockCaption,
    RichMessageButton,
)

from telegramsales.shared.presentation.bot.content import paragraph, without_media
from telegramsales.shared.presentation.bot.render import is_media_rejected

CAPTION = "Пальто оверсайз · 129 $"


def bad_request(message: str) -> TelegramBadRequest:
    return TelegramBadRequest(
        method=SendMessage(chat_id=1, text=""),
        message=message,
    )


def photo_message() -> InputRichMessage:
    return InputRichMessage(
        blocks=[
            paragraph("Витрина"),
            InputRichBlockPhoto(
                photo=InputMediaPhoto(media="file-1"),
                caption=RichBlockCaption(text=CAPTION),
            ),
            InputRichBlockButtons(
                buttons=[RichMessageButton(text="Открыть", callback_data="open")]
            ),
        ]
    )


def test_a_rejected_photo_is_recognised() -> None:
    assert is_media_rejected(bad_request("Bad Request: RICH_MESSAGE_PHOTO_INVALID"))


def test_a_wrong_file_identifier_is_recognised() -> None:
    assert is_media_rejected(bad_request("Bad Request: wrong file identifier"))


def test_an_unrelated_error_is_left_alone() -> None:
    assert not is_media_rejected(bad_request("Bad Request: chat not found"))


def test_media_is_replaced_by_its_caption() -> None:
    stripped = without_media(photo_message())
    blocks = stripped.blocks or []

    assert not any(isinstance(block, InputRichBlockPhoto) for block in blocks)
    assert [
        str(block.text)
        for block in blocks
        if isinstance(block, InputRichBlockParagraph)
    ] == ["Витрина", CAPTION]


def test_the_buttons_survive_the_stripping() -> None:
    stripped = without_media(photo_message())
    blocks = stripped.blocks or []

    assert any(isinstance(block, InputRichBlockButtons) for block in blocks)


def test_a_collage_without_a_caption_just_disappears() -> None:
    message = InputRichMessage(
        blocks=[
            InputRichBlockCollage(
                blocks=[
                    InputRichBlockPhoto(photo=InputMediaPhoto(media="file-1")),
                    InputRichBlockPhoto(photo=InputMediaPhoto(media="file-2")),
                ]
            ),
            paragraph("Описание"),
        ]
    )

    stripped = without_media(message)

    assert [
        str(block.text)
        for block in stripped.blocks or []
        if isinstance(block, InputRichBlockParagraph)
    ] == ["Описание"]
    assert len(stripped.blocks or []) == 1
