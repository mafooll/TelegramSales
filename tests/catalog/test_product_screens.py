from aiogram.types import InputRichBlockButtons, InputRichMessage

from telegramsales.modules.catalog.application.queries import ProductEntryView
from telegramsales.modules.catalog.presentation.bot.callbacks import (
    CatalogAction,
    CatalogCallback,
    CatalogTarget,
)
from telegramsales.modules.catalog.presentation.bot.product_callbacks import (
    ProductAction,
    ProductCallback,
)
from telegramsales.modules.catalog.presentation.bot.product_screens import (
    PRODUCT_LIST,
)
from telegramsales.modules.catalog.presentation.bot.views import ProductListView
from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.pagination import Page
from telegramsales.shared.infrastructure.i18n.fluent import FluentTranslations
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.pagination import Pagination
from telegramsales.shared.presentation.bot.rich import rich_paged_screen
from telegramsales.shared.settings import LOCALES_PATH
from tests.catalog.factories import CLOTHES, OUTERWEAR

DEFAULT_LOCALE = "ru"
PAGE_SIZE = 8

TRANSLATE = FluentTranslations(LOCALES_PATH, DEFAULT_LOCALE)(DEFAULT_LOCALE)
CONTEXT = RenderContext(
    actor=Actor(id=1, permissions=frozenset()), translate=TRANSLATE
)


def paged(view: ProductListView) -> Pagination[ProductEntryView]:
    return Pagination(
        page=Page(items=[], number=0, size=PAGE_SIZE, total=0),
        callback=lambda value: ProductCallback(
            action=ProductAction.LIST,
            catalog_id=view.catalog_id,
            category_id=view.category_id,
            page=value,
        ),
    )


def callbacks_of(message: InputRichMessage) -> list[CatalogCallback]:
    blocks = message.blocks or []
    return [
        CatalogCallback.unpack(button.callback_data)
        for block in blocks
        if isinstance(block, InputRichBlockButtons)
        for button in block.buttons
        if button.callback_data is not None
        and button.callback_data.startswith("cat:")
    ]


def test_a_categorized_list_goes_back_to_its_category() -> None:
    view = ProductListView(catalog_id=CLOTHES, category_id=OUTERWEAR, total=0)

    message = rich_paged_screen(PRODUCT_LIST, paged(view), view, CONTEXT)
    back = callbacks_of(message)

    assert [entry.target for entry in back] == [CatalogTarget.CATEGORY]
    assert [entry.category_id for entry in back] == [OUTERWEAR]


def test_an_uncategorized_list_goes_back_to_its_catalog() -> None:
    view = ProductListView(catalog_id=CLOTHES, category_id=None, total=0)

    message = rich_paged_screen(PRODUCT_LIST, paged(view), view, CONTEXT)
    back = callbacks_of(message)

    assert [entry.target for entry in back] == [CatalogTarget.CATALOG]
    assert [entry.catalog_id for entry in back] == [CLOTHES]
    assert [entry.action for entry in back] == [CatalogAction.CARD]
