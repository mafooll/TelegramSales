from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from aiogram.enums import ButtonStyle
from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InputRichBlockButtons,
    InputRichBlockDivider,
    InputRichBlockFooter,
    InputRichBlockParagraph,
    InputRichBlockPhoto,
    InputRichMessage,
    RichMessageButton,
)
import pytest

from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.i18n import TranslationArgs
from telegramsales.shared.application.pagination import Page
from telegramsales.shared.presentation.bot import texts
from telegramsales.shared.presentation.bot.content import gallery, paragraph
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.keyboard import (
    MAX_BUTTONS_PER_ROW,
    Button,
    ContentRef,
    ListScreen,
    RowWidthError,
    Screen,
    label,
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

SHARED_LABELS = {
    texts.PREVIOUS: "⬅️",
    texts.NEXT: "➡️",
    texts.PAGE_POSITION: "{current}/{total}",
}


def translate(key: str, /, **args: TranslationArgs) -> str:
    template = SHARED_LABELS.get(key, key)
    return template.format(**args) if args else template


def context_with(
    *permissions: StrEnum,
    is_shopping: bool = True,
) -> RenderContext:
    return RenderContext(
        actor=Actor(
            id=1,
            permissions=frozenset(p.value for p in permissions),
            is_shopping=is_shopping,
        ),
        translate=translate,
    )


ANYONE = context_with()
MANAGER = context_with(ProbePermission.MANAGE, is_shopping=False)
SHOPPING_MANAGER = context_with(ProbePermission.MANAGE)

TITLE: ContentRef[ProbeView] = label("Заголовок")


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


def button(  # noqa: PLR0913
    text: str,
    permission: StrEnum | None = None,
    when: Callable[[ProbeView], bool] | None = None,
    style: ButtonStyle | None = None,
    *,
    for_customers: bool = False,
    for_staff: bool = False,
) -> Button[ProbeView]:
    return Button(
        text=label(text),
        callback=lambda _: ProbeCallback(value=text),
        permission=permission,
        for_customers=for_customers,
        for_staff=for_staff,
        when=when,
        style=style,
    )


def screen_of(*buttons: Button[ProbeView], row_width: int = 1) -> Screen[ProbeView]:
    return Screen(content=TITLE, buttons=list(buttons), row_width=row_width)


def test_message_starts_with_the_screen_content() -> None:
    message = rich_screen(screen_of(button("Назад")), VIEW, ANYONE)

    assert paragraphs_of(message) == ["Заголовок"]


def test_content_may_be_computed_from_the_view() -> None:
    screen: Screen[ProbeView] = Screen(
        content=label("Карточка {label}", lambda view: {"label": view.label}),
        buttons=[],
    )

    assert paragraphs_of(rich_screen(screen, VIEW, ANYONE)) == ["Карточка Товар"]


def test_content_may_be_prepared_blocks() -> None:
    screen: Screen[ProbeView] = Screen(
        content=lambda view, _: [
            paragraph(view.label),
            *gallery(["photo-one", "photo-two"]),
        ],
        buttons=[],
    )

    message = rich_screen(screen, VIEW, ANYONE)
    blocks = message.blocks or []

    assert paragraphs_of(message) == ["Товар"]
    assert len(blocks) == 2


def test_button_without_permission_is_visible_to_anyone() -> None:
    assert texts_of(rich_screen(screen_of(button("Назад")), VIEW, ANYONE)) == [
        "Назад"
    ]


def test_button_with_permission_is_hidden_without_it() -> None:
    screen = screen_of(button("Удалить", ProbePermission.MANAGE))

    assert texts_of(rich_screen(screen, VIEW, ANYONE)) == []


def test_button_with_permission_is_shown_with_it() -> None:
    screen = screen_of(button("Удалить", ProbePermission.MANAGE))

    assert texts_of(rich_screen(screen, VIEW, MANAGER)) == ["Удалить"]


def test_customer_button_is_shown_without_permissions() -> None:
    screen = screen_of(button("Корзина", for_customers=True))

    assert texts_of(rich_screen(screen, VIEW, ANYONE)) == ["Корзина"]


def test_customer_button_is_hidden_from_staff() -> None:
    screen = screen_of(button("Корзина", for_customers=True))

    assert texts_of(rich_screen(screen, VIEW, MANAGER)) == []


def test_customer_button_returns_in_the_customer_view() -> None:
    screen = screen_of(button("Корзина", for_customers=True))

    assert texts_of(rich_screen(screen, VIEW, SHOPPING_MANAGER)) == ["Корзина"]


def test_staff_button_is_hidden_from_customers() -> None:
    screen = screen_of(button("Режим", for_staff=True))

    assert texts_of(rich_screen(screen, VIEW, ANYONE)) == []


def test_staff_button_stays_in_the_customer_view() -> None:
    screen = screen_of(button("Режим", for_staff=True))

    assert texts_of(rich_screen(screen, VIEW, SHOPPING_MANAGER)) == ["Режим"]


def test_when_hides_the_button_even_with_permission() -> None:
    screen = screen_of(
        button("Изменить", ProbePermission.MANAGE, lambda view: not view.editable)
    )

    assert texts_of(rich_screen(screen, VIEW, MANAGER)) == []


def test_declaration_order_is_preserved() -> None:
    screen = screen_of(button("Раз"), button("Два"), button("Три"))

    assert texts_of(rich_screen(screen, VIEW, ANYONE)) == ["Раз", "Два", "Три"]


def test_row_width_groups_buttons_into_blocks() -> None:
    screen = screen_of(button("Раз"), button("Два"), button("Три"), row_width=2)

    assert rows_of(rich_screen(screen, VIEW, ANYONE)) == [["Раз", "Два"], ["Три"]]


def test_row_width_at_the_api_limit_is_accepted() -> None:
    screen = screen_of(button("Раз"), row_width=MAX_BUTTONS_PER_ROW)

    assert screen.row_width == MAX_BUTTONS_PER_ROW


@pytest.mark.parametrize("row_width", [0, -1, MAX_BUTTONS_PER_ROW + 1])
def test_row_width_outside_the_api_limit_is_rejected(row_width: int) -> None:
    with pytest.raises(RowWidthError):
        screen_of(button("Раз"), row_width=row_width)


def test_style_reaches_the_button() -> None:
    screen = screen_of(button("Отозвать", style=ButtonStyle.DANGER))

    message = rich_screen(screen, VIEW, ANYONE)
    blocks = message.blocks or []
    block = next(b for b in blocks if isinstance(b, InputRichBlockButtons))

    assert block.buttons[0].style == ButtonStyle.DANGER


def test_callback_data_is_packed() -> None:
    message = rich_screen(screen_of(button("Назад")), VIEW, ANYONE)
    blocks = message.blocks or []
    block = next(b for b in blocks if isinstance(b, InputRichBlockButtons))

    assert block.buttons[0].callback_data == "probe:Назад"


def test_button_text_may_be_computed_from_the_view() -> None:
    screen: Screen[ProbeView] = Screen(
        content=TITLE,
        buttons=[
            Button(
                text=label("Открыть {label}", lambda view: {"label": view.label}),
                callback=lambda _: ProbeCallback(value="open"),
            )
        ],
    )

    assert texts_of(rich_screen(screen, VIEW, ANYONE)) == ["Открыть Товар"]


LIST_SCREEN: ListScreen[str, ProbeView] = ListScreen(
    content=TITLE,
    item=Button(
        text=lambda item, _: item,
        callback=lambda item: ProbeCallback(value=item),
    ),
    footer=[button("Добавить", ProbePermission.MANAGE), button("Назад")],
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


def navigation_buttons(message: InputRichMessage) -> list[RichMessageButton]:
    for block in message.blocks or []:
        if not isinstance(block, InputRichBlockButtons):
            continue
        if any("/" in str(button.text) for button in block.buttons):
            return list(block.buttons)
    return []


CARD_LIST: ListScreen[str, ProbeView] = ListScreen(
    content=TITLE,
    item=Button(
        text=label("Открыть"),
        callback=lambda item: ProbeCallback(value=item),
    ),
    item_photo=lambda item: None if item.endswith("2") else f"photo-{item}",
    item_caption=lambda item, _: f"подпись {item}",
    footnote=lambda view, _: f"Витрина · {view.label}",
    footer=[button("Назад")],
)


def photos_of(message: InputRichMessage) -> list[tuple[str, str | None]]:
    return [
        (
            str(block.photo.media),
            None if block.caption is None else str(block.caption.text),
        )
        for block in (message.blocks or [])
        if isinstance(block, InputRichBlockPhoto)
    ]


def dividers_in(message: InputRichMessage) -> list[int]:
    return [
        position
        for position, block in enumerate(message.blocks or [])
        if isinstance(block, InputRichBlockDivider)
    ]


def first_photo_at(message: InputRichMessage) -> int:
    return next(
        position
        for position, block in enumerate(message.blocks or [])
        if isinstance(block, InputRichBlockPhoto)
    )


def test_a_card_item_shows_its_photo_with_the_caption() -> None:
    message = rich_paged_screen(CARD_LIST, pagination(0, 2), VIEW, ANYONE)

    assert photos_of(message) == [
        ("photo-item0", "подпись item0"),
        ("photo-item1", "подпись item1"),
    ]


def test_a_card_item_keeps_its_own_button() -> None:
    message = rich_paged_screen(CARD_LIST, pagination(0, 2), VIEW, ANYONE)

    assert rows_of(message) == [["Открыть"], ["Открыть"], ["Назад"]]


def test_cards_are_separated_by_dividers_between_them() -> None:
    message = rich_paged_screen(CARD_LIST, pagination(0, 2), VIEW, ANYONE)

    assert dividers_in(message) == [3]
    assert dividers_in(message)[0] > first_photo_at(message)


def test_a_single_card_has_no_divider() -> None:
    message = rich_paged_screen(CARD_LIST, pagination(0, 1), VIEW, ANYONE)

    assert dividers_in(message) == []


def test_an_item_without_a_photo_keeps_the_caption_as_text() -> None:
    message = rich_paged_screen(CARD_LIST, pagination(0, 3), VIEW, ANYONE)

    assert photos_of(message) == [
        ("photo-item0", "подпись item0"),
        ("photo-item1", "подпись item1"),
    ]
    assert "подпись item2" in paragraphs_of(message)


def test_the_footnote_closes_the_message() -> None:
    message = rich_paged_screen(CARD_LIST, pagination(0, 2), VIEW, ANYONE)
    footer = (message.blocks or [])[-1]

    assert isinstance(footer, InputRichBlockFooter)
    assert str(footer.text) == "Витрина · Товар"


def test_list_content_comes_from_the_screen() -> None:
    message = rich_paged_screen(LIST_SCREEN, pagination(0, 2), VIEW, MANAGER)

    assert paragraphs_of(message) == ["Заголовок"]


def test_single_page_has_no_navigation() -> None:
    message = rich_paged_screen(LIST_SCREEN, pagination(0, 2), VIEW, MANAGER)

    assert rows_of(message) == [["item0"], ["item1"], ["Добавить"], ["Назад"]]


def test_navigation_always_keeps_three_buttons() -> None:
    for number in (0, 1, 2):
        message = rich_paged_screen(LIST_SCREEN, pagination(number, 9), VIEW, ANYONE)

        assert rows_of(message)[-2] == ["⬅️", f"{number + 1}/3", "➡️"]


def test_the_first_page_disables_the_back_arrow() -> None:
    message = rich_paged_screen(LIST_SCREEN, pagination(0, 9), VIEW, ANYONE)
    back, _, forward = navigation_buttons(message)

    assert back.disabled is not None
    assert back.callback_data is None
    assert forward.disabled is None


def test_the_last_page_disables_the_forward_arrow() -> None:
    message = rich_paged_screen(LIST_SCREEN, pagination(2, 9), VIEW, ANYONE)
    back, _, forward = navigation_buttons(message)

    assert forward.disabled is not None
    assert forward.callback_data is None
    assert back.disabled is None


def test_middle_page_has_both_arrows() -> None:
    message = rich_paged_screen(LIST_SCREEN, pagination(1, 9), VIEW, ANYONE)

    assert rows_of(message) == [
        ["item3"],
        ["item4"],
        ["item5"],
        ["⬅️", "2/3", "➡️"],
        ["Назад"],
    ]


def test_items_are_laid_out_in_a_grid() -> None:
    screen: ListScreen[str, ProbeView] = ListScreen(
        content=TITLE,
        item=LIST_SCREEN.item,
        footer=[button("Назад")],
        row_width=2,
    )

    message = rich_paged_screen(screen, pagination(0, 3), VIEW, ANYONE)

    assert rows_of(message) == [["item0", "item1"], ["item2"], ["Назад"]]


def test_footer_has_its_own_row_width() -> None:
    screen: ListScreen[str, ProbeView] = ListScreen(
        content=TITLE,
        item=LIST_SCREEN.item,
        footer=[button("Раз"), button("Два")],
        footer_row_width=2,
    )

    message = rich_paged_screen(screen, pagination(0, 1), VIEW, ANYONE)

    assert rows_of(message)[-1] == ["Раз", "Два"]


@pytest.mark.parametrize("row_width", [0, MAX_BUTTONS_PER_ROW + 1])
def test_list_row_width_outside_the_api_limit_is_rejected(row_width: int) -> None:
    with pytest.raises(RowWidthError):
        ListScreen(
            content=TITLE,
            item=LIST_SCREEN.item,
            footer=[button("Назад")],
            row_width=row_width,
        )


@pytest.mark.parametrize("footer_row_width", [0, MAX_BUTTONS_PER_ROW + 1])
def test_footer_row_width_outside_the_api_limit_is_rejected(
    footer_row_width: int,
) -> None:
    with pytest.raises(RowWidthError):
        ListScreen(
            content=TITLE,
            item=LIST_SCREEN.item,
            footer=[button("Назад")],
            footer_row_width=footer_row_width,
        )


def test_footer_respects_permissions() -> None:
    message = rich_paged_screen(LIST_SCREEN, pagination(0, 1), VIEW, ANYONE)

    assert rows_of(message) == [["item0"], ["Назад"]]


def test_empty_page_still_shows_the_footer() -> None:
    message = rich_paged_screen(LIST_SCREEN, pagination(0, 0), VIEW, MANAGER)

    assert rows_of(message) == [["Добавить"], ["Назад"]]
