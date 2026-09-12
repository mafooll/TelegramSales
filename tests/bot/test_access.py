from enum import StrEnum

from aiogram.types import InputRichBlockButtons, InputRichMessage
import pytest

from telegramsales.apps.bot.access import ROLE_PERMISSIONS, StaticPermissionResolver
from telegramsales.apps.bot.menu import MAIN_MENU, MenuView
from telegramsales.modules.catalog.domain.permissions import CatalogPermission
from telegramsales.modules.orders.domain.permissions import OrdersPermission
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

MODULE_PERMISSIONS: tuple[StrEnum, ...] = (
    *StaffPermission,
    *CatalogPermission,
    *OrdersPermission,
)
NOTHING: frozenset[PermissionCode] = frozenset()


def button_texts(message: InputRichMessage) -> list[str]:
    return [
        str(button.text)
        for block in (message.blocks or [])
        if isinstance(block, InputRichBlockButtons)
        for button in block.buttons
    ]


def menu_of(role: StaffRole | None, *, is_shopping: bool = False) -> list[str]:
    permissions = NOTHING if role is None else RESOLVER.permissions_of(role)
    actor = Actor(
        id=1,
        permissions=permissions,
        is_shopping=role is None or is_shopping,
    )
    context = RenderContext(actor=actor, translate=TRANSLATE)
    view = MenuView(is_shopping=actor.is_shopping)
    return button_texts(rich_screen(MAIN_MENU, view, context))


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


def test_manager_runs_the_orders() -> None:
    granted = RESOLVER.permissions_of(StaffRole.MANAGER)

    assert OrdersPermission.VIEW_ORDERS.value in granted
    assert OrdersPermission.MANAGE_ORDERS.value in granted


def test_manager_does_not_manage_staff() -> None:
    granted = RESOLVER.permissions_of(StaffRole.MANAGER)

    assert StaffPermission.MANAGE_STAFF.value not in granted


def test_unknown_role_grants_nothing() -> None:
    assert RESOLVER.permissions_of("courier") == NOTHING


SHOP = "🛍 Магазин"
CART = "🧺 Корзина"
ORDERS = "🧾 Мои заказы"
CATALOG = "🗂 Управление каталогом"
STAFF = "👥 Персонал"
SHOP_MODE_ON = "🛍 Режим покупателя"
SHOP_MODE_OFF = "🙈 Выйти из режима покупателя"
CUSTOMER_MENU = [SHOP, CART, ORDERS]
STAFF_MENU = [CATALOG, STAFF]


def test_owner_sees_only_the_staff_side() -> None:
    assert menu_of(StaffRole.OWNER) == [*STAFF_MENU, SHOP_MODE_ON]


def test_manager_sees_only_the_staff_side() -> None:
    assert menu_of(StaffRole.MANAGER) == [*STAFF_MENU, SHOP_MODE_ON]


def test_staff_in_the_customer_view_sees_the_shop_and_the_way_back() -> None:
    assert menu_of(StaffRole.MANAGER, is_shopping=True) == [
        *CUSTOMER_MENU,
        SHOP_MODE_OFF,
    ]


def test_staff_in_the_customer_view_keeps_no_admin_buttons() -> None:
    shown = menu_of(StaffRole.OWNER, is_shopping=True)

    assert CATALOG not in shown
    assert STAFF not in shown


def test_customer_sees_only_the_shop_side() -> None:
    assert menu_of(None) == CUSTOMER_MENU
