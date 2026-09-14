from enum import StrEnum

from aiogram.types import (
    InputRichBlockButtons,
    InputRichBlockParagraph,
    InputRichMessage,
)

from telegramsales.modules.catalog.application.queries import (
    BrandView,
    CatalogView,
    CategoryView,
)
from telegramsales.modules.catalog.domain.permissions import CatalogPermission
from telegramsales.modules.catalog.presentation.bot import texts as catalog_texts
from telegramsales.modules.catalog.presentation.bot.callbacks import (
    CatalogAction,
    CatalogCallback,
)
from telegramsales.modules.catalog.presentation.bot.screens import (
    BRAND_CARD,
    BRAND_LIST,
    CATALOG_CARD,
    CATALOG_LIST,
    CATEGORY_CARD,
    HUB,
    PROMPT,
)
from telegramsales.modules.catalog.presentation.bot.views import (
    CountedView,
    PromptView,
)
from telegramsales.shared.application.pagination import Page
from telegramsales.shared.infrastructure.i18n.fluent import FluentTranslations
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.pagination import Pagination
from telegramsales.shared.presentation.bot.rich import rich_paged_screen, rich_screen
from telegramsales.shared.settings import LOCALES_PATH
from tests.catalog.factories import ACME, CLOTHES, COATS, OUTERWEAR
from tests.catalog.fakes import actor_with

DEFAULT_LOCALE = "ru"
PAGE_SIZE = 8

TRANSLATE = FluentTranslations(LOCALES_PATH, DEFAULT_LOCALE)(DEFAULT_LOCALE)


def context_with(*permissions: StrEnum) -> RenderContext:
    return RenderContext(actor=actor_with(*permissions), translate=TRANSLATE)


MANAGER = context_with(CatalogPermission.MANAGE)
OUTSIDER = context_with()


def catalog_view(
    *, is_active: bool = True, categories: int = 0, uncategorized: int = 0
) -> CatalogView:
    return CatalogView(
        id=CLOTHES,
        title="Одежда",
        is_active=is_active,
        category_count=categories,
        uncategorized_product_count=uncategorized,
    )


def category_view(
    *,
    parent_id: int | None = None,
    is_active: bool = True,
    children: int = 0,
) -> CategoryView:
    return CategoryView(
        id=OUTERWEAR if parent_id is None else COATS,
        catalog_id=CLOTHES,
        parent_id=parent_id,  # pyright: ignore[reportArgumentType]
        title="Верхняя одежда",
        is_active=is_active,
        child_count=children,
    )


def brand_view(*, is_active: bool = True) -> BrandView:
    return BrandView(id=ACME, title="Acme", is_active=is_active)


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


def prompt_view(message_key: str) -> PromptView:
    return PromptView(
        message_key=message_key,
        back=CatalogCallback(action=CatalogAction.HUB),
    )


def empty_pagination[ItemType]() -> Pagination[ItemType]:
    return Pagination(
        page=Page(items=[], number=0, size=PAGE_SIZE, total=0),
        callback=lambda value: CatalogCallback(
            action=CatalogAction.LIST, page=value
        ),
    )


def test_hub_offers_both_sections() -> None:
    assert texts_of(rich_screen(HUB, None, MANAGER)) == [
        "🗂 Каталоги",
        "🏷 Бренды",
        "⬅️ В меню",
    ]


def test_empty_catalog_list_says_so() -> None:
    message = rich_paged_screen(
        CATALOG_LIST, empty_pagination(), CountedView(total=0), MANAGER
    )

    assert paragraphs_of(message) == ["Каталогов пока нет."]


def test_catalog_list_counts_in_plural() -> None:
    message = rich_paged_screen(
        CATALOG_LIST, empty_pagination(), CountedView(total=3), MANAGER
    )

    assert paragraphs_of(message) == ["3 каталога"]


def test_manager_may_create_a_catalog() -> None:
    message = rich_paged_screen(
        CATALOG_LIST, empty_pagination(), CountedView(total=0), MANAGER
    )

    assert texts_of(message) == ["➕ Новый каталог", "⬅️ Назад"]


def test_outsider_sees_no_create_button() -> None:
    message = rich_paged_screen(
        CATALOG_LIST, empty_pagination(), CountedView(total=0), OUTSIDER
    )

    assert texts_of(message) == ["⬅️ Назад"]


def test_empty_catalog_offers_deletion() -> None:
    message = rich_paged_screen(
        CATALOG_CARD, empty_pagination(), catalog_view(), MANAGER
    )

    assert "🗑️ Удалить" in texts_of(message)


def test_catalog_with_categories_hides_deletion() -> None:
    message = rich_paged_screen(
        CATALOG_CARD, empty_pagination(), catalog_view(categories=2), MANAGER
    )

    assert "🗑️ Удалить" not in texts_of(message)


def test_visible_catalog_offers_hiding() -> None:
    message = rich_paged_screen(
        CATALOG_CARD, empty_pagination(), catalog_view(), MANAGER
    )

    assert "🚫 Скрыть" in texts_of(message)
    assert "♻️ Вернуть" not in texts_of(message)


def test_hidden_catalog_offers_restoring() -> None:
    message = rich_paged_screen(
        CATALOG_CARD, empty_pagination(), catalog_view(is_active=False), MANAGER
    )

    assert "♻️ Вернуть" in texts_of(message)
    assert "🚫 Скрыть" not in texts_of(message)


def test_catalog_card_counts_categories() -> None:
    message = rich_paged_screen(
        CATALOG_CARD, empty_pagination(), catalog_view(categories=1), MANAGER
    )

    assert paragraphs_of(message) == ["Каталог: Одежда\n1 категория"]


def test_empty_catalog_card_says_there_are_no_categories() -> None:
    message = rich_paged_screen(
        CATALOG_CARD, empty_pagination(), catalog_view(), MANAGER
    )

    assert paragraphs_of(message) == ["Каталог: Одежда\nКатегорий нет"]


def test_catalog_card_offers_a_way_to_uncategorized_products() -> None:
    message = rich_paged_screen(
        CATALOG_CARD, empty_pagination(), catalog_view(), MANAGER
    )

    assert "📦 Без категории" in texts_of(message)


def test_the_uncategorized_products_button_needs_no_permission() -> None:
    message = rich_paged_screen(
        CATALOG_CARD, empty_pagination(), catalog_view(), OUTSIDER
    )

    assert "📦 Без категории" in texts_of(message)


def test_root_category_may_hold_subcategories() -> None:
    message = rich_paged_screen(
        CATEGORY_CARD, empty_pagination(), category_view(), MANAGER
    )

    assert "➕ Новая подкатегория" in texts_of(message)


def test_nested_category_may_not_hold_subcategories() -> None:
    message = rich_paged_screen(
        CATEGORY_CARD,
        empty_pagination(),
        category_view(parent_id=OUTERWEAR),
        MANAGER,
    )

    assert "➕ Новая подкатегория" not in texts_of(message)


def test_category_card_has_exactly_one_way_back() -> None:
    root = rich_paged_screen(
        CATEGORY_CARD, empty_pagination(), category_view(), MANAGER
    )
    nested = rich_paged_screen(
        CATEGORY_CARD,
        empty_pagination(),
        category_view(parent_id=OUTERWEAR),
        MANAGER,
    )

    assert texts_of(root).count("⬅️ Назад") == 1
    assert texts_of(nested).count("⬅️ Назад") == 1


def test_category_with_children_hides_deletion() -> None:
    message = rich_paged_screen(
        CATEGORY_CARD, empty_pagination(), category_view(children=1), MANAGER
    )

    assert "🗑️ Удалить" not in texts_of(message)


def test_brand_card_offers_the_full_set() -> None:
    assert texts_of(rich_screen(BRAND_CARD, brand_view(), MANAGER)) == [
        "✏️ Переименовать",
        "🚫 Скрыть",
        "🗑️ Удалить",
        "⬅️ Назад",
    ]


def test_outsider_only_gets_the_way_back_from_a_brand() -> None:
    assert texts_of(rich_screen(BRAND_CARD, brand_view(), OUTSIDER)) == ["⬅️ Назад"]


def test_brand_card_names_the_brand() -> None:
    assert paragraphs_of(rich_screen(BRAND_CARD, brand_view(), MANAGER)) == [
        "Бренд: Acme"
    ]


def test_brand_list_counts_in_plural() -> None:
    message = rich_paged_screen(
        BRAND_LIST, empty_pagination(), CountedView(total=1), MANAGER
    )

    assert paragraphs_of(message) == ["1 бренд"]


def test_prompt_offers_only_a_way_out() -> None:
    view = prompt_view(catalog_texts.CATALOG_ASK_TITLE)

    assert texts_of(rich_screen(PROMPT, view, MANAGER)) == ["Отмена"]


def test_prompt_shows_the_requested_text() -> None:
    view = prompt_view(catalog_texts.BRAND_ASK_TITLE)

    assert paragraphs_of(rich_screen(PROMPT, view, MANAGER)) == [
        "Пришлите название бренда."
    ]


def test_prompt_needs_no_permission() -> None:
    view = prompt_view(catalog_texts.CATALOG_ASK_TITLE)

    assert texts_of(rich_screen(PROMPT, view, OUTSIDER)) == ["Отмена"]
