from collections.abc import Sequence

from aiogram.types import (
    InputRichBlockButtons,
    InputRichBlockUnion,
    InputRichMessage,
    RichMessageButton,
)

from telegramsales.shared.presentation.bot import texts
from telegramsales.shared.presentation.bot.content import content_blocks
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.keyboard import Button, ListScreen, Screen
from telegramsales.shared.presentation.bot.pagination import Pagination


def _to_button[ViewType](
    button: Button[ViewType],
    view: ViewType,
    context: RenderContext,
) -> RichMessageButton:
    return RichMessageButton(
        text=button.render(view, context),
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


def button_blocks[ViewType](
    buttons: Sequence[Button[ViewType]],
    row_width: int,
    view: ViewType,
    context: RenderContext,
) -> list[InputRichBlockUnion]:
    allowed = [
        _to_button(button, view, context)
        for button in buttons
        if button.is_allowed(view, context)
    ]
    return _rows(allowed, row_width)


def _navigation_blocks[ItemType](
    pagination: Pagination[ItemType],
    context: RenderContext,
) -> list[InputRichBlockUnion]:
    page, make_callback = pagination.page, pagination.callback
    if page.is_single:
        return []

    buttons: list[RichMessageButton] = []
    if page.has_previous:
        buttons.append(
            RichMessageButton(
                text=context.translate(texts.PREVIOUS),
                callback_data=make_callback(page.number - 1).pack(),
            )
        )
    buttons.append(
        RichMessageButton(
            text=context.translate(
                texts.PAGE_POSITION,
                current=page.number + 1,
                total=page.total_pages,
            ),
            callback_data=make_callback(page.number).pack(),
        )
    )
    if page.has_next:
        buttons.append(
            RichMessageButton(
                text=context.translate(texts.NEXT),
                callback_data=make_callback(page.number + 1).pack(),
            )
        )
    return [InputRichBlockButtons(buttons=buttons)]


def rich_screen[ViewType](
    screen: Screen[ViewType],
    view: ViewType,
    context: RenderContext,
) -> InputRichMessage:
    return InputRichMessage(
        blocks=[
            *content_blocks(screen.render(view, context)),
            *button_blocks(screen.buttons, screen.row_width, view, context),
        ]
    )


def rich_paged_screen[ItemType, ViewType](
    screen: ListScreen[ItemType, ViewType],
    pagination: Pagination[ItemType],
    view: ViewType,
    context: RenderContext,
) -> InputRichMessage:
    items = [
        _to_button(screen.item, item, context)
        for item in pagination.page.items
        if screen.item.is_allowed(item, context)
    ]
    return InputRichMessage(
        blocks=[
            *content_blocks(screen.render(view, context)),
            *_rows(items, screen.row_width),
            *_navigation_blocks(pagination, context),
            *button_blocks(screen.footer, screen.footer_row_width, view, context),
        ]
    )
