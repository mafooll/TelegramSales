from datetime import UTC, datetime
from enum import StrEnum

from aiogram.types import (
    InputRichBlockButtons,
    InputRichBlockParagraph,
    InputRichMessage,
)

from telegramsales.modules.staff.application.queries import StaffMemberView
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.domain.permissions import StaffPermission
from telegramsales.modules.staff.presentation.bot.callbacks import (
    StaffAction,
    StaffCallback,
)
from telegramsales.modules.staff.presentation.bot.screens import (
    MEMBER_CARD,
    STAFF_LIST,
)
from telegramsales.modules.staff.presentation.bot.views import StaffListView
from telegramsales.shared.application.pagination import Page
from telegramsales.shared.infrastructure.i18n.fluent import FluentTranslations
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.pagination import Pagination
from telegramsales.shared.presentation.bot.rich import rich_paged_screen, rich_screen
from telegramsales.shared.settings import LOCALES_PATH
from tests.staff.fakes import actor_with

NOW = datetime(2026, 9, 5, 12, 0, tzinfo=UTC)
MEMBER = StaffId(200)
DEFAULT_LOCALE = "ru"

TRANSLATE = FluentTranslations(LOCALES_PATH, DEFAULT_LOCALE)(DEFAULT_LOCALE)


def context_with(*permissions: StrEnum) -> RenderContext:
    return RenderContext(actor=actor_with(*permissions), translate=TRANSLATE)


MANAGER = context_with(StaffPermission.MANAGE_STAFF, StaffPermission.VIEW_STAFF)
VIEWER = context_with(StaffPermission.VIEW_STAFF)


def view(
    role: StaffRole = StaffRole.MANAGER,
    *,
    is_active: bool = True,
) -> StaffMemberView:
    return StaffMemberView(
        id=MEMBER,
        role=role,
        is_active=is_active,
        customer_view=False,
        created_at=NOW,
    )


def texts_of(message: InputRichMessage) -> list[str]:
    blocks = message.blocks or []
    return [
        str(button.text)
        for block in blocks
        if isinstance(block, InputRichBlockButtons)
        for button in block.buttons
    ]


def paragraphs_of(message: InputRichMessage) -> list[str]:
    blocks = message.blocks or []
    return [
        str(block.text)
        for block in blocks
        if isinstance(block, InputRichBlockParagraph)
    ]


def page_of(total: int) -> Pagination[StaffMemberView]:
    items = [view()] if total else []
    return Pagination(
        page=Page(items=items, number=0, size=8, total=total),
        callback=lambda number: StaffCallback(action=StaffAction.LIST, page=number),
    )


def test_manager_sees_the_add_button_in_the_list() -> None:
    message = rich_paged_screen(
        STAFF_LIST, page_of(1), StaffListView(total=1), MANAGER
    )

    assert texts_of(message) == ["200 · менеджер", "➕ Добавить", "⬅️ В меню"]


def test_viewer_sees_colleagues_but_cannot_add() -> None:
    message = rich_paged_screen(
        STAFF_LIST, page_of(1), StaffListView(total=1), VIEWER
    )

    assert texts_of(message) == ["200 · менеджер", "⬅️ В меню"]


def test_the_way_back_to_the_menu_needs_no_permission() -> None:
    message = rich_paged_screen(
        STAFF_LIST, page_of(1), StaffListView(total=1), context_with()
    )

    assert texts_of(message)[-1] == "⬅️ В меню"


def test_empty_list_says_so_instead_of_counting() -> None:
    message = rich_paged_screen(
        STAFF_LIST, page_of(0), StaffListView(total=0), MANAGER
    )

    assert paragraphs_of(message) == ["В команде пока никого нет."]


def test_list_header_counts_the_team() -> None:
    message = rich_paged_screen(
        STAFF_LIST, page_of(1), StaffListView(total=1), MANAGER
    )

    assert paragraphs_of(message) == ["В команде 1 человек"]


def test_member_card_offers_promotion_only() -> None:
    message = rich_screen(MEMBER_CARD, view(StaffRole.MANAGER), MANAGER)

    assert texts_of(message) == [
        "⬆️ Сделать владельцем",
        "🚫 Отозвать доступ",
        "⬅️ К списку",
    ]


def test_owner_card_offers_demotion_only() -> None:
    message = rich_screen(MEMBER_CARD, view(StaffRole.OWNER), MANAGER)

    assert texts_of(message) == [
        "⬇️ Сделать менеджером",
        "🚫 Отозвать доступ",
        "⬅️ К списку",
    ]


def test_revoked_card_offers_restore_only() -> None:
    message = rich_screen(MEMBER_CARD, view(is_active=False), MANAGER)

    assert texts_of(message) == ["♻️ Вернуть доступ", "⬅️ К списку"]


def test_viewer_sees_no_actions_on_a_card() -> None:
    message = rich_screen(MEMBER_CARD, view(), VIEWER)

    assert texts_of(message) == ["⬅️ К списку"]


def test_revoked_member_is_marked_in_the_list() -> None:
    revoked = Pagination(
        page=Page(items=[view(is_active=False)], number=0, size=8, total=1),
        callback=lambda number: StaffCallback(action=StaffAction.LIST, page=number),
    )
    message = rich_paged_screen(STAFF_LIST, revoked, StaffListView(total=1), VIEWER)

    assert texts_of(message)[0] == "🚫 200 · менеджер"


def test_card_shows_the_role_in_words() -> None:
    message = rich_screen(MEMBER_CARD, view(StaffRole.OWNER), VIEWER)

    assert paragraphs_of(message) == ["Участник 200\nРоль: владелец"]
