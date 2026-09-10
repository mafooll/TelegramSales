from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from aiogram.enums import ButtonStyle
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InputRichBlockButtons,
    InputRichBlockParagraph,
    InputRichMessage,
)
import pytest

from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.pagination import Page
from telegramsales.shared.presentation.bot.keyboard import (
    MAX_BUTTONS_PER_ROW,
    Button,
    ListScreen,
    RowWidthError,
    Screen,
)
from telegramsales.shared.presentation.bot.pagination import Pagination
from telegramsales.shared.presentation.bot.rich import rich_paged_screen, rich_screen


class ProbePermission(StrEnum):
    MANAGE = "probe.manage"


class ProbeCallback(CallbackData, prefix="probe"):
    value: str


@dataclass(frozen=True, slots=True)
class ProbeView:
    label: str
    editable: bool


VIEW = ProbeView(label="Товар", editable=True)


def actor_with(*permissions: StrEnum) -> Actor:
    return Actor(id=1, permissions=frozenset(p.value for p in permissions))


ANYONE = actor_with()
MANAGER = actor_with(ProbePermission.MANAGE)


def rows_of(message: InputRichMessage) -> list[list[str]]:
    blocks = message.blocks or []
    return [
        [str(button.text) for button in block.buttons]
        for block in blocks
        if isinstance(block, InputRichBlockButtons)
    ]


def texts_of(message: InputRichMessage) -> list[str]:
    return [text for row in rows_of(message) for text in row]


def paragraphs_of(message: InputRichMessage) -> list[str]:
    blocks = message.blocks or []
    return [
        str(block.text)
        for block in blocks
        if isinstance(block, InputRichBlockParagraph)
    ]


def button(
    text: str,
    permission: StrEnum | None = None,
    when: Callable[[ProbeView], bool] | None = None,
    style: ButtonStyle | None = None,
) -> Button[ProbeView]:
    return Button(
        text=text,
        callback=lambda _: ProbeCallback(value=text),
        permission=permission,
        when=when,
        style=style,
    )


def test_message_starts_with_the_text_paragraph() -> None:
    screen = Screen(buttons=[button("Назад")])

    message = rich_screen("Заголовок", screen, VIEW, ANYONE)

    assert paragraphs_of(message) == ["Заголовок"]


def test_button_without_permission_is_visible_to_anyone() -> None:
    screen = Screen(buttons=[button("Назад")])

    assert texts_of(rich_screen("t", screen, VIEW, ANYONE)) == ["Назад"]


def test_button_with_permission_is_hidden_without_it() -> None:
    screen = Screen(buttons=[button("Удалить", ProbePermission.MANAGE)])

    assert texts_of(rich_screen("t", screen, VIEW, ANYONE)) == []


def test_button_with_permission_is_shown_with_it() -> None:
    screen = Screen(buttons=[button("Удалить", ProbePermission.MANAGE)])

    assert texts_of(rich_screen("t", screen, VIEW, MANAGER)) == ["Удалить"]


def test_when_hides_the_button_even_with_permission() -> None:
    screen = Screen(
        buttons=[
            button(
                "Изменить", ProbePermission.MANAGE, lambda view: not view.editable
            )
        ]
    )

    assert texts_of(rich_screen("t", screen, VIEW, MANAGER)) == []


def test_declaration_order_is_preserved() -> None:
    screen = Screen(buttons=[button("Раз"), button("Два"), button("Три")])

    assert texts_of(rich_screen("t", screen, VIEW, ANYONE)) == ["Раз", "Два", "Три"]


def test_row_width_groups_buttons_into_blocks() -> None:
    screen = Screen(
        buttons=[button("Раз"), button("Два"), button("Три")], row_width=2
    )

    assert rows_of(rich_screen("t", screen, VIEW, ANYONE)) == [
        ["Раз", "Два"],
        ["Три"],
    ]


def test_row_width_at_the_api_limit_is_accepted() -> None:
    screen = Screen(buttons=[button("Раз")], row_width=MAX_BUTTONS_PER_ROW)

    assert screen.row_width == MAX_BUTTONS_PER_ROW


@pytest.mark.parametrize("row_width", [0, -1, MAX_BUTTONS_PER_ROW + 1])
def test_row_width_outside_the_api_limit_is_rejected(row_width: int) -> None:
    with pytest.raises(RowWidthError):
        Screen(buttons=[button("Раз")], row_width=row_width)


def test_style_reaches_the_button() -> None:
    screen = Screen(buttons=[button("Отозвать", style=ButtonStyle.DANGER)])

    message = rich_screen("t", screen, VIEW, ANYONE)
    blocks = message.blocks or []
    block = next(b for b in blocks if isinstance(b, InputRichBlockButtons))

    assert block.buttons[0].style == ButtonStyle.DANGER


def test_callback_data_is_packed() -> None:
    screen = Screen(buttons=[button("Назад")])

    message = rich_screen("t", screen, VIEW, ANYONE)
    blocks = message.blocks or []
    block = next(b for b in blocks if isinstance(b, InputRichBlockButtons))

    assert block.buttons[0].callback_data == "probe:Назад"


def test_text_may_be_computed_from_the_view() -> None:
    screen: Screen[ProbeView] = Screen(
        buttons=[
            Button(
                text=lambda view: f"Открыть {view.label}",
                callback=lambda _: ProbeCallback(value="open"),
            )
        ]
    )

    assert texts_of(rich_screen("t", screen, VIEW, ANYONE)) == ["Открыть Товар"]


LIST_SCREEN: ListScreen[str, ProbeView] = ListScreen(
    item=Button(
        text=lambda item: item, callback=lambda item: ProbeCallback(value=item)
    ),
    footer=Screen(
        buttons=[button("Добавить", ProbePermission.MANAGE), button("Назад")]
    ),
)


def page(number: int, total: int, size: int = 3) -> Page[str]:
    start = number * size
    return Page(
        items=[f"item{index}" for index in range(start, min(start + size, total))],
        number=number,
        size=size,
        total=total,
    )


def pagination(number: int, total: int, size: int = 3) -> Pagination[str]:
    return Pagination(
        page=page(number, total, size),
        callback=lambda value: ProbeCallback(value=str(value)),
    )


def test_single_page_has_no_navigation() -> None:
    message = rich_paged_screen("t", LIST_SCREEN, pagination(0, 2), VIEW, MANAGER)

    assert rows_of(message) == [["item0"], ["item1"], ["Добавить"], ["Назад"]]


def test_first_page_has_no_back_arrow() -> None:
    message = rich_paged_screen("t", LIST_SCREEN, pagination(0, 9), VIEW, ANYONE)

    assert rows_of(message)[-2] == ["1/3", "➡️"]


def test_last_page_has_no_forward_arrow() -> None:
    message = rich_paged_screen("t", LIST_SCREEN, pagination(2, 9), VIEW, ANYONE)

    assert rows_of(message)[-2] == ["⬅️", "3/3"]


def test_middle_page_has_both_arrows() -> None:
    message = rich_paged_screen("t", LIST_SCREEN, pagination(1, 9), VIEW, ANYONE)

    assert rows_of(message) == [
        ["item3"],
        ["item4"],
        ["item5"],
        ["⬅️", "2/3", "➡️"],
        ["Назад"],
    ]


def test_items_are_laid_out_in_a_grid() -> None:
    screen: ListScreen[str, ProbeView] = ListScreen(
        item=LIST_SCREEN.item,
        footer=Screen(buttons=[button("Назад")]),
        row_width=2,
    )

    message = rich_paged_screen("t", screen, pagination(0, 3), VIEW, ANYONE)

    assert rows_of(message) == [["item0", "item1"], ["item2"], ["Назад"]]


@pytest.mark.parametrize("row_width", [0, MAX_BUTTONS_PER_ROW + 1])
def test_list_row_width_outside_the_api_limit_is_rejected(row_width: int) -> None:
    with pytest.raises(RowWidthError):
        ListScreen(
            item=LIST_SCREEN.item,
            footer=Screen(buttons=[button("Назад")]),
            row_width=row_width,
        )


def test_footer_respects_permissions() -> None:
    message = rich_paged_screen("t", LIST_SCREEN, pagination(0, 1), VIEW, ANYONE)

    assert rows_of(message) == [["item0"], ["Назад"]]


def test_empty_page_still_shows_the_footer() -> None:
    message = rich_paged_screen("t", LIST_SCREEN, pagination(0, 0), VIEW, MANAGER)

    assert rows_of(message) == [["Добавить"], ["Назад"]]
