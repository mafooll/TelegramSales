from collections.abc import Sequence

from aiogram.types import (
    InputRichBlockButtons,
    InputRichBlockUnion,
    InputRichMessage,
    RichMessageButton,
)

from telegramsales.shared.application.access import Actor
from telegramsales.shared.presentation.bot import texts
from telegramsales.shared.presentation.bot.content import Content, content_blocks
from telegramsales.shared.presentation.bot.keyboard import Button, ListScreen, Screen
from telegramsales.shared.presentation.bot.pagination import Pagination


def _to_button[ViewType](
    button: Button[ViewType], view: ViewType
) -> RichMessageButton:
    return RichMessageButton(
        text=button.render(view),
        callback_data=button.callback(view).pack(),
        style=button.style,
    )


def _rows(
    buttons: Sequence[RichMessageButton],
    row_width: int,
) -> list[InputRichBlockUnion]:
    return [
        InputRichBlockButtons(buttons=list(buttons[start : start + row_width]))
        for start in range(0, len(buttons), row_width)
    ]


def screen_blocks[ViewType](
    screen: Screen[ViewType],
    view: ViewType,
    actor: Actor,
) -> list[InputRichBlockUnion]:
    allowed = [
        _to_button(button, view)
        for button in screen.buttons
        if button.is_allowed(view, actor)
    ]
    return _rows(allowed, screen.row_width)


def _navigation_blocks[ItemType](
    pagination: Pagination[ItemType],
) -> list[InputRichBlockUnion]:
    page, make_callback = pagination.page, pagination.callback
    if page.is_single:
        return []

    buttons: list[RichMessageButton] = []
    if page.has_previous:
        buttons.append(
            RichMessageButton(
                text=texts.PREVIOUS,
                callback_data=make_callback(page.number - 1).pack(),
            )
        )
    buttons.append(
        RichMessageButton(
            text=f"{page.number + 1}/{page.total_pages}",
            callback_data=make_callback(page.number).pack(),
        )
    )
    if page.has_next:
        buttons.append(
            RichMessageButton(
                text=texts.NEXT,
                callback_data=make_callback(page.number + 1).pack(),
            )
        )
    return [InputRichBlockButtons(buttons=buttons)]


def rich_screen[ViewType](
    content: Content,
    screen: Screen[ViewType],
    view: ViewType,
    actor: Actor,
) -> InputRichMessage:
    return InputRichMessage(
        blocks=[
            *content_blocks(content),
            *screen_blocks(screen, view, actor),
        ]
    )


def rich_paged_screen[ItemType, ViewType](
    content: Content,
    screen: ListScreen[ItemType, ViewType],
    pagination: Pagination[ItemType],
    view: ViewType,
    actor: Actor,
) -> InputRichMessage:
    items = [
        _to_button(screen.item, item)
        for item in pagination.page.items
        if screen.item.is_allowed(item, actor)
    ]
    return InputRichMessage(
        blocks=[
            *content_blocks(content),
            *_rows(items, screen.row_width),
            *_navigation_blocks(pagination),
            *screen_blocks(screen.footer, view, actor),
        ]
    )
