from enum import StrEnum

from aiogram.types import InputRichBlockButtons, InputRichMessage
import pytest

from telegramsales.apps.bot.access import ROLE_PERMISSIONS, StaticPermissionResolver
from telegramsales.apps.bot.menu import MAIN_MENU
from telegramsales.modules.catalog.domain.permissions import CatalogPermission
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.domain.permissions import StaffPermission
from telegramsales.shared.application.access import Actor, PermissionCode
from telegramsales.shared.infrastructure.i18n.fluent import FluentTranslations
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.rich import rich_screen
from telegramsales.shared.settings import LOCALES_PATH

DEFAULT_LOCALE = "ru"
TRANSLATE = FluentTranslations(LOCALES_PATH, DEFAULT_LOCALE)(DEFAULT_LOCALE)
RESOLVER = StaticPermissionResolver()

MODULE_PERMISSIONS: tuple[StrEnum, ...] = (*StaffPermission, *CatalogPermission)
NOTHING: frozenset[PermissionCode] = frozenset()


def button_texts(message: InputRichMessage) -> list[str]:
    return [
        str(button.text)
        for block in (message.blocks or [])
        if isinstance(block, InputRichBlockButtons)
        for button in block.buttons
    ]


def menu_of(role: StaffRole | None) -> list[str]:
    permissions = NOTHING if role is None else RESOLVER.permissions_of(role)
    context = RenderContext(
        actor=Actor(id=1, permissions=permissions),
        translate=TRANSLATE,
    )
    return button_texts(rich_screen(MAIN_MENU, None, context))


def test_every_role_is_declared() -> None:
    assert set(ROLE_PERMISSIONS) == set(StaffRole)


def test_owner_holds_every_declared_permission() -> None:
    granted = RESOLVER.permissions_of(StaffRole.OWNER)

    assert granted == frozenset(
        permission.value for permission in MODULE_PERMISSIONS
    )


@pytest.mark.parametrize("permission", MODULE_PERMISSIONS)
def test_no_permission_is_left_unassigned(permission: StrEnum) -> None:
    assigned = NOTHING.union(*ROLE_PERMISSIONS.values())

    assert permission.value in assigned


def test_manager_runs_the_catalog() -> None:
    granted = RESOLVER.permissions_of(StaffRole.MANAGER)

    assert CatalogPermission.MANAGE.value in granted


def test_manager_does_not_manage_staff() -> None:
    granted = RESOLVER.permissions_of(StaffRole.MANAGER)

    assert StaffPermission.MANAGE_STAFF.value not in granted


def test_unknown_role_grants_nothing() -> None:
    assert RESOLVER.permissions_of("courier") == NOTHING


def test_owner_sees_both_sections() -> None:
    assert menu_of(StaffRole.OWNER) == ["🗂 Управление каталогом", "👥 Персонал"]


def test_manager_sees_both_sections() -> None:
    assert menu_of(StaffRole.MANAGER) == ["🗂 Управление каталогом", "👥 Персонал"]


def test_customer_sees_no_admin_buttons() -> None:
    assert menu_of(None) == []
