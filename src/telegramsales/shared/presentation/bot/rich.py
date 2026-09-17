from collections.abc import Sequence
from typing import Any

from aiogram.types import (
    DisabledButton,
    InputRichBlockButtons,
    InputRichBlockUnion,
    InputRichMessage,
    RichMessageButton,
)

from telegramsales.shared.presentation.bot import texts
from telegramsales.shared.presentation.bot.content import (
    content_blocks,
    divider,
    footnote,
    paragraph,
    photo,
)
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


def _widths(count: int, row_width: int, layout: Sequence[int]) -> list[int]:
    widths = list(layout)
    placed = sum(widths)
    while placed < count:
        widths.append(row_width)
        placed += row_width
    return widths


def _rows(
    buttons: Sequence[RichMessageButton],
    row_width: int,
    layout: Sequence[int] = (),
) -> list[InputRichBlockUnion]:
    rows: list[InputRichBlockUnion] = []
    start = 0
    for width in _widths(len(buttons), row_width, layout):
        if start >= len(buttons):
            break
        rows.append(
            InputRichBlockButtons(buttons=list(buttons[start : start + width]))
        )
        start += width
    return rows


def button_blocks[ViewType](
    buttons: Sequence[Button[ViewType]],
    row_width: int,
    view: ViewType,
    context: RenderContext,
    layout: Sequence[int] = (),
) -> list[InputRichBlockUnion]:
    allowed = [
        _to_button(button, view, context)
        for button in buttons
        if button.is_allowed(view, context)
    ]
    return _rows(allowed, row_width, layout)


def _step_button(
    key: str,
    number: int,
    pagination: Pagination[Any],
    context: RenderContext,
    *,
    is_available: bool,
) -> RichMessageButton:
    text = context.translate(key)
    if not is_available:
        return RichMessageButton(text=text, disabled=DisabledButton())
    return RichMessageButton(
        text=text,
        callback_data=pagination.callback(number).pack(),
    )


def _navigation_blocks[ItemType](
    pagination: Pagination[ItemType],
    context: RenderContext,
) -> list[InputRichBlockUnion]:
    page = pagination.page
    if page.is_single:
        return []

    return [
        InputRichBlockButtons(
            buttons=[
                _step_button(
                    texts.PREVIOUS,
                    page.number - 1,
                    pagination,
                    context,
                    is_available=page.has_previous,
                ),
                RichMessageButton(
                    text=context.translate(
                        texts.PAGE_POSITION,
                        current=page.number + 1,
                        total=page.total_pages,
                    ),
                    callback_data=pagination.callback(page.number).pack(),
                ),
                _step_button(
                    texts.NEXT,
                    page.number + 1,
                    pagination,
                    context,
                    is_available=page.has_next,
                ),
            ]
        )
    ]


def rich_screen[ViewType](
    screen: Screen[ViewType],
    view: ViewType,
    context: RenderContext,
) -> InputRichMessage:
    return InputRichMessage(
        blocks=[
            *content_blocks(screen.render(view, context)),
            *button_blocks(
                screen.buttons, screen.row_width, view, context, screen.layout
            ),
        ]
    )


def _card_blocks[ItemType, ViewType](
    screen: ListScreen[ItemType, ViewType],
    item: ItemType,
    context: RenderContext,
) -> list[InputRichBlockUnion]:
    caption = (
        None
        if screen.item_caption is None
        else screen.item_caption(item, context.translate)
    )
    file_id = None if screen.item_photo is None else screen.item_photo(item)

    blocks: list[InputRichBlockUnion] = []
    if file_id is not None:
        blocks.append(photo(file_id, caption))
    elif caption is not None:
        blocks.append(paragraph(caption))

    buttons = [_to_button(screen.item, item, context)]
    if screen.item_extra is not None and screen.item_extra.is_allowed(item, context):
        buttons.append(_to_button(screen.item_extra, item, context))
    blocks.append(InputRichBlockButtons(buttons=buttons))
    return blocks


def _item_blocks[ItemType, ViewType](
    screen: ListScreen[ItemType, ViewType],
    items: Sequence[ItemType],
    context: RenderContext,
) -> list[InputRichBlockUnion]:
    if screen.item_photo is None and screen.item_caption is None:
        return _rows(
            [_to_button(screen.item, item, context) for item in items],
            screen.row_width,
        )

    blocks: list[InputRichBlockUnion] = []
    for item in items:
        if blocks:
            blocks.append(divider())
        blocks.extend(_card_blocks(screen, item, context))
    return blocks


def _footnote_blocks[ItemType, ViewType](
    screen: ListScreen[ItemType, ViewType],
    view: ViewType,
    context: RenderContext,
) -> list[InputRichBlockUnion]:
    if screen.footnote is None:
        return []
    return [footnote(screen.footnote(view, context.translate))]


def rich_paged_screen[ItemType, ViewType](
    screen: ListScreen[ItemType, ViewType],
    pagination: Pagination[ItemType],
    view: ViewType,
    context: RenderContext,
) -> InputRichMessage:
    items = [
        item
        for item in pagination.page.items
        if screen.item.is_allowed(item, context)
    ]
    return InputRichMessage(
        blocks=[
            *content_blocks(screen.render(view, context)),
            *_item_blocks(screen, items, context),
            *_navigation_blocks(pagination, context),
            *button_blocks(
                screen.footer,
                screen.footer_row_width,
                view,
                context,
                screen.footer_layout,
            ),
            *_footnote_blocks(screen, view, context),
        ]
    )
