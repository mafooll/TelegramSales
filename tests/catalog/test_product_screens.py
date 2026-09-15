from aiogram.types import (
    InputRichBlockButtons,
    InputRichBlockParagraph,
    InputRichMessage,
)

from telegramsales.modules.catalog.application.queries import (
    CatalogView,
    ProductEntryView,
    ProductView,
    VariantView,
)
from telegramsales.modules.catalog.contracts import VariantId
from telegramsales.modules.catalog.domain.enums import MediaLayout
from telegramsales.modules.catalog.domain.permissions import CatalogPermission
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
    MOVE_CATALOG_PICKER,
    MOVE_CATEGORY_PICKER,
    PRODUCT_LIST,
    VARIANT_CARD,
)
from telegramsales.modules.catalog.presentation.bot.views import (
    CatalogPickView,
    CategoryPickView,
    MoveTargetView,
    ProductListView,
    VariantCardView,
)
from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.pagination import Page
from telegramsales.shared.infrastructure.i18n.fluent import FluentTranslations
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.pagination import Pagination
from telegramsales.shared.presentation.bot.rich import rich_paged_screen, rich_screen
from telegramsales.shared.settings import LOCALES_PATH
from tests.catalog.factories import BEAUTY, CLOTHES, COAT, OUTERWEAR, usd

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


MANAGER = RenderContext(
    actor=Actor(
        id=1, permissions=frozenset({CatalogPermission.MANAGE.value})
    ),
    translate=TRANSLATE,
)
OUTSIDER = CONTEXT


def whole[ItemType](items: list[ItemType]) -> Pagination[ItemType]:
    return Pagination(
        page=Page(items=items, number=0, size=PAGE_SIZE, total=len(items)),
        callback=lambda value: ProductCallback(
            action=ProductAction.LIST, page=value
        ),
    )


def product_view() -> ProductView:
    return ProductView(
        id=COAT,
        catalog_id=CLOTHES,
        category_id=OUTERWEAR,
        article="000042",
        title="Пальто оверсайз",
        description="Тёплое пальто.",
        price=usd("12900"),
        old_price=None,
        brand_title="Acme",
        variant_label="Размер",
        is_published=False,
        is_visible=True,
        is_in_stock=True,
        photo_count=1,
        video_count=0,
        variant_count=1,
        photo_ids=(),
        video_id=None,
        media_layout=MediaLayout.COLLAGE,
    )


def catalog_view() -> CatalogView:
    return CatalogView(
        id=CLOTHES,
        title="Одежда",
        is_active=True,
        category_count=0,
        uncategorized_product_count=1,
    )


def variant_card(*, available: bool = True) -> VariantCardView:
    return VariantCardView(
        product=product_view(),
        variant=VariantView(
            id=VariantId(5),
            title="M",
            price=usd("12900"),
            is_available=available,
        ),
    )


def buttons_of(message: InputRichMessage) -> list[str]:
    return [
        str(button.text)
        for block in message.blocks or []
        if isinstance(block, InputRichBlockButtons)
        for button in block.buttons
    ]


def test_a_variant_card_offers_every_edit() -> None:
    message = rich_screen(VARIANT_CARD, variant_card(), MANAGER)

    assert buttons_of(message) == [
        "✏️ Название",
        "💲 Цена",
        "🚫 Нет в наличии",
        "🗑️ Удалить",
        "⬅️ К вариантам",
    ]


def test_a_sold_out_variant_offers_to_sell_again() -> None:
    message = rich_screen(VARIANT_CARD, variant_card(available=False), MANAGER)

    assert "✅ В наличии" in buttons_of(message)
    assert "🚫 Нет в наличии" not in buttons_of(message)


def test_a_variant_card_names_the_product_and_the_axis() -> None:
    message = rich_screen(VARIANT_CARD, variant_card(), MANAGER)
    paragraphs = [
        str(block.text)
        for block in message.blocks or []
        if isinstance(block, InputRichBlockParagraph)
    ]

    assert "Пальто оверсайз" in paragraphs[0]
    assert "Размер: M" in paragraphs[0]


def test_a_customer_sees_no_variant_buttons() -> None:
    message = rich_screen(VARIANT_CARD, variant_card(), OUTSIDER)

    assert buttons_of(message) == ["⬅️ К вариантам"]


def test_the_catalog_picker_lists_every_catalog() -> None:
    picks = [
        CatalogPickView(product_id=COAT, catalog_id=CLOTHES, title="Одежда"),
        CatalogPickView(product_id=COAT, catalog_id=BEAUTY, title="Бьюти"),
    ]
    message = rich_paged_screen(
        MOVE_CATALOG_PICKER, whole(picks), product_view(), MANAGER
    )

    assert buttons_of(message) == ["Одежда", "Бьюти", "⬅️ Назад"]


def test_a_catalog_with_categories_takes_no_bare_product() -> None:
    picks = [
        CategoryPickView(
            product_id=COAT,
            catalog_id=CLOTHES,
            category_id=OUTERWEAR,
            title="Верхняя одежда",
        )
    ]
    view = MoveTargetView(
        product=product_view(), catalog=catalog_view(), takes_products=False
    )

    message = rich_paged_screen(MOVE_CATEGORY_PICKER, whole(picks), view, MANAGER)

    assert buttons_of(message) == ["Верхняя одежда", "⬅️ Назад"]


def test_an_empty_catalog_takes_the_product_directly() -> None:
    view = MoveTargetView(
        product=product_view(), catalog=catalog_view(), takes_products=True
    )

    message = rich_paged_screen(MOVE_CATEGORY_PICKER, whole([]), view, MANAGER)

    assert buttons_of(message) == ["📦 Прямо в каталог", "⬅️ Назад"]
