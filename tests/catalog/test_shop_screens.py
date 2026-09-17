from aiogram.types import (
    InputRichBlockButtons,
    InputRichBlockCollage,
    InputRichBlockFooter,
    InputRichBlockParagraph,
    InputRichBlockPhoto,
    InputRichBlockSlideshow,
    InputRichMessage,
    RichTextCode,
)

from telegramsales.modules.catalog.application.queries import (
    ShopCatalogView,
    ShopCategoryView,
    ShopProductEntryView,
    ShopProductView,
    ShopVariantView,
)
from telegramsales.modules.catalog.contracts import VariantId
from telegramsales.modules.catalog.domain.enums import MediaLayout
from telegramsales.modules.catalog.presentation.bot.shop_callbacks import (
    ShopAction,
    ShopCallback,
)
from telegramsales.modules.catalog.presentation.bot.shop_screens import (
    CATALOG,
    CATALOGS,
    CATEGORY,
    PRODUCT_CARD,
    PRODUCT_LIST,
    VARIANT_PICKER,
)
from telegramsales.modules.catalog.presentation.bot.views import (
    CountedView,
    ShopCatalogPageView,
    ShopProductsView,
    ShopVariantPickView,
)
from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.pagination import Page
from telegramsales.shared.infrastructure.i18n.fluent import FluentTranslations
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.money import STRIKE
from telegramsales.shared.presentation.bot.pagination import Pagination
from telegramsales.shared.presentation.bot.rich import rich_paged_screen, rich_screen
from telegramsales.shared.settings import LOCALES_PATH
from tests.catalog.factories import CLOTHES, COAT, COATS, OUTERWEAR, SIZE_M, usd

DEFAULT_LOCALE = "ru"
PAGE_SIZE = 8
SIZE_L = VariantId(501)

TRANSLATE = FluentTranslations(LOCALES_PATH, DEFAULT_LOCALE)(DEFAULT_LOCALE)
CUSTOMER = RenderContext(
    actor=Actor(id=7, permissions=frozenset()), translate=TRANSLATE
)


def catalog_view() -> ShopCatalogView:
    return ShopCatalogView(id=CLOTHES, title="Одежда")


def category_view(
    *,
    children: int = 0,
    products: int = 0,
    parent_id: int | None = None,
    parent_title: str | None = None,
) -> ShopCategoryView:
    return ShopCategoryView(
        id=OUTERWEAR,
        catalog_id=CLOTHES,
        parent_id=None if parent_id is None else COATS,
        title="Верхняя одежда",
        catalog_title="Одежда",
        parent_title=parent_title,
        child_count=children,
        product_count=products,
    )


def entry_view(
    *,
    in_stock: bool = True,
    thumbnail: str | None = "photo-1",
) -> ShopProductEntryView:
    return ShopProductEntryView(
        id=COAT,
        title="Пальто оверсайз",
        price=usd("12900"),
        is_in_stock=in_stock,
        thumbnail=thumbnail,
    )


def product_view(  # noqa: PLR0913
    *,
    old_price: str | None = None,
    brand: str | None = None,
    in_stock: bool = True,
    photos: tuple[str, ...] = (),
    video_id: str | None = None,
    layout: MediaLayout = MediaLayout.COLLAGE,
    variants: tuple[ShopVariantView, ...] = (),
) -> ShopProductView:
    return ShopProductView(
        id=COAT,
        catalog_id=CLOTHES,
        category_id=OUTERWEAR,
        article="000042",
        title="Пальто оверсайз",
        description="Тёплое пальто из шерсти.",
        price=usd("12900"),
        old_price=None if old_price is None else usd(old_price),
        brand_title=brand,
        variant_label="Размер" if variants else None,
        is_in_stock=in_stock,
        photo_ids=photos,
        video_id=video_id,
        media_layout=layout,
        variants=variants,
    )


def paged[ItemType](items: list[ItemType]) -> Pagination[ItemType]:
    return Pagination(
        page=Page(items=items, number=0, size=PAGE_SIZE, total=len(items)),
        callback=lambda value: ShopCallback(action=ShopAction.CATALOGS, page=value),
    )


def texts_of(message: InputRichMessage) -> list[str]:
    blocks = message.blocks or []
    return [
        str(button.text)
        for block in blocks
        if isinstance(block, InputRichBlockButtons)
        for button in block.buttons
    ]


def captions_of(message: InputRichMessage) -> list[str]:
    blocks = message.blocks or []
    return [
        str(block.caption.text)
        for block in blocks
        if isinstance(block, InputRichBlockPhoto) and block.caption is not None
    ]


def photo_ids_of(message: InputRichMessage) -> list[str]:
    blocks = message.blocks or []
    return [
        str(block.photo.media)
        for block in blocks
        if isinstance(block, InputRichBlockPhoto)
    ]


def paragraphs_of(message: InputRichMessage) -> list[str]:
    blocks = message.blocks or []
    return [
        str(block.text)
        for block in blocks
        if isinstance(block, InputRichBlockParagraph)
    ]


def callbacks_of(message: InputRichMessage) -> list[ShopCallback]:
    blocks = message.blocks or []
    return [
        ShopCallback.unpack(button.callback_data)
        for block in blocks
        if isinstance(block, InputRichBlockButtons)
        for button in block.buttons
        if button.callback_data is not None
    ]


def test_catalogs_are_listed_by_title() -> None:
    message = rich_paged_screen(
        CATALOGS, paged([catalog_view()]), CountedView(total=1), CUSTOMER
    )

    assert "Одежда" in texts_of(message)


def test_an_empty_shop_says_so() -> None:
    message = rich_paged_screen(CATALOGS, paged([]), CountedView(total=0), CUSTOMER)

    assert paragraphs_of(message) == ["Магазин пока пуст, загляните позже."]


def test_a_catalog_lists_its_categories() -> None:
    view = ShopCatalogPageView(catalog=catalog_view(), total=1)

    message = rich_paged_screen(
        CATALOG, paged([category_view(products=2)]), view, CUSTOMER
    )

    assert "Верхняя одежда" in texts_of(message)


def test_a_category_offers_its_own_products() -> None:
    category = category_view(children=2, products=3)

    message = rich_paged_screen(CATEGORY, paged([]), category, CUSTOMER)

    assert "🛍 Товары (3)" in texts_of(message)


def test_a_category_without_own_products_offers_no_such_button() -> None:
    category = category_view(children=2)

    message = rich_paged_screen(CATEGORY, paged([]), category, CUSTOMER)

    assert "🛍 Товары (0)" not in texts_of(message)


def test_a_top_level_category_goes_back_to_its_catalog() -> None:
    category = category_view(children=1)

    message = rich_paged_screen(CATEGORY, paged([]), category, CUSTOMER)

    assert ShopAction.CATALOG in [entry.action for entry in callbacks_of(message)]


def test_a_subcategory_goes_back_to_its_parent() -> None:
    category = category_view(children=1, parent_id=1)

    message = rich_paged_screen(CATEGORY, paged([]), category, CUSTOMER)
    back = next(
        entry
        for entry in callbacks_of(message)
        if entry.action is ShopAction.CATEGORY
    )

    assert back.category_id == COATS


def product_list_of(*entries: ShopProductEntryView) -> InputRichMessage:
    view = ShopProductsView(
        catalog=catalog_view(),
        category=category_view(products=len(entries)),
        total=len(entries),
    )
    return rich_paged_screen(PRODUCT_LIST, paged(list(entries)), view, CUSTOMER)


def test_a_product_entry_carries_its_price() -> None:
    message = product_list_of(entry_view())

    assert captions_of(message) == ["Пальто оверсайз · 12 900 $"]


def test_an_out_of_stock_entry_replaces_the_price() -> None:
    message = product_list_of(entry_view(in_stock=False))

    assert captions_of(message) == ["Пальто оверсайз · нет в наличии"]


def test_a_product_entry_shows_its_thumbnail() -> None:
    message = product_list_of(entry_view())

    assert photo_ids_of(message) == ["photo-1"]


def test_an_entry_without_a_photo_falls_back_to_text() -> None:
    message = product_list_of(entry_view(thumbnail=None))

    assert photo_ids_of(message) == []
    assert "Пальто оверсайз · 12 900 $" in paragraphs_of(message)


def test_the_list_ends_with_the_breadcrumbs() -> None:
    message = product_list_of(entry_view())

    assert breadcrumbs_of(message) == "Витрина · Одежда · Верхняя одежда"


def breadcrumbs_of(message: InputRichMessage) -> str:
    footer = (message.blocks or [])[-1]
    assert isinstance(footer, InputRichBlockFooter)
    return str(footer.text)


def test_the_breadcrumbs_name_the_parent_category() -> None:
    view = ShopProductsView(
        catalog=catalog_view(),
        category=category_view(products=1, parent_id=1, parent_title="Пальто"),
        total=1,
    )
    message = rich_paged_screen(PRODUCT_LIST, paged([entry_view()]), view, CUSTOMER)

    assert breadcrumbs_of(message) == "Витрина · Одежда · Пальто · Верхняя одежда"


def bare_catalog_list(*entries: ShopProductEntryView) -> InputRichMessage:
    view = ShopProductsView(
        catalog=catalog_view(), category=None, total=len(entries)
    )
    return rich_paged_screen(PRODUCT_LIST, paged(list(entries)), view, CUSTOMER)


def test_a_catalog_without_categories_titles_the_list_with_itself() -> None:
    message = bare_catalog_list(entry_view())

    assert "Одежда" in paragraphs_of(message)[0]
    assert "Без категории" not in paragraphs_of(message)[0]


def test_a_bare_catalog_list_stops_the_breadcrumbs_at_the_catalog() -> None:
    message = bare_catalog_list(entry_view())

    assert breadcrumbs_of(message) == "Витрина · Одежда"


def test_a_bare_catalog_list_goes_back_to_the_catalogs() -> None:
    message = bare_catalog_list()

    assert [entry.action for entry in callbacks_of(message)] == [
        ShopAction.CATALOGS
    ]


def test_a_leaf_category_sends_the_list_back_to_the_catalog() -> None:
    view = ShopProductsView(
        catalog=catalog_view(), category=category_view(products=1), total=1
    )

    message = rich_paged_screen(PRODUCT_LIST, paged([]), view, CUSTOMER)

    assert [entry.action for entry in callbacks_of(message)] == [ShopAction.CATALOG]


def test_a_branching_category_sends_the_list_back_to_itself() -> None:
    view = ShopProductsView(
        catalog=catalog_view(),
        category=category_view(children=2, products=1),
        total=1,
    )

    message = rich_paged_screen(PRODUCT_LIST, paged([]), view, CUSTOMER)

    assert [entry.action for entry in callbacks_of(message)] == [ShopAction.CATEGORY]


def test_a_leaf_subcategory_sends_the_list_back_to_its_parent() -> None:
    view = ShopProductsView(
        catalog=catalog_view(),
        category=category_view(products=1, parent_id=1),
        total=1,
    )

    message = rich_paged_screen(PRODUCT_LIST, paged([]), view, CUSTOMER)
    back = callbacks_of(message)

    assert [entry.category_id for entry in back] == [COATS]


def test_the_card_shows_the_description() -> None:
    message = rich_screen(PRODUCT_CARD, product_view(), CUSTOMER)

    assert "Тёплое пальто из шерсти." in paragraphs_of(message)


def test_the_card_shows_the_price() -> None:
    message = rich_screen(PRODUCT_CARD, product_view(), CUSTOMER)

    assert paragraphs_of(message)[0] == "Пальто оверсайз\n12 900 $"


def test_the_article_is_a_copyable_block() -> None:
    message = rich_screen(PRODUCT_CARD, product_view(), CUSTOMER)
    article = (message.blocks or [])[1]

    assert isinstance(article, InputRichBlockParagraph)
    assert article.text == ["Артикул:", " ", RichTextCode(text="000042")]


def test_an_old_price_is_struck_through() -> None:
    message = rich_screen(PRODUCT_CARD, product_view(old_price="15900"), CUSTOMER)

    assert f"1{STRIKE}5{STRIKE}" in paragraphs_of(message)[0]


def test_a_card_without_a_sale_shows_one_price() -> None:
    message = rich_screen(PRODUCT_CARD, product_view(), CUSTOMER)

    assert STRIKE not in paragraphs_of(message)[0]


def test_a_brand_is_named_when_the_product_has_one() -> None:
    message = rich_screen(PRODUCT_CARD, product_view(brand="Acme"), CUSTOMER)

    assert "Бренд: Acme" in paragraphs_of(message)


def test_a_product_without_a_brand_says_nothing_about_brands() -> None:
    message = rich_screen(PRODUCT_CARD, product_view(), CUSTOMER)

    assert not any(text.startswith("Бренд") for text in paragraphs_of(message))


def test_variants_are_listed_with_their_prices() -> None:
    variants = (
        ShopVariantView(id=SIZE_M, title="M", price=usd("12900")),
        ShopVariantView(id=SIZE_L, title="L", price=usd("13900")),
    )

    message = rich_screen(PRODUCT_CARD, product_view(variants=variants), CUSTOMER)

    assert "Размер:\n• M — 12 900 $\n• L — 13 900 $" in paragraphs_of(message)


def test_an_out_of_stock_card_says_so() -> None:
    message = rich_screen(PRODUCT_CARD, product_view(in_stock=False), CUSTOMER)

    assert "Нет в наличии" in paragraphs_of(message)


def test_a_card_in_stock_stays_silent_about_stock() -> None:
    message = rich_screen(PRODUCT_CARD, product_view(), CUSTOMER)

    assert "Нет в наличии" not in paragraphs_of(message)


def test_photos_follow_the_chosen_layout() -> None:
    product = product_view(photos=("one", "two"), layout=MediaLayout.SLIDESHOW)

    message = rich_screen(PRODUCT_CARD, product, CUSTOMER)

    assert any(
        isinstance(block, InputRichBlockSlideshow) for block in message.blocks or []
    )


def test_a_collage_is_the_other_layout() -> None:
    product = product_view(photos=("one", "two"))

    message = rich_screen(PRODUCT_CARD, product, CUSTOMER)

    assert any(
        isinstance(block, InputRichBlockCollage) for block in message.blocks or []
    )


def test_the_card_goes_back_to_its_category() -> None:
    message = rich_screen(PRODUCT_CARD, product_view(), CUSTOMER)
    back = next(
        entry
        for entry in callbacks_of(message)
        if entry.action is ShopAction.PRODUCTS
    )

    assert back.category_id == OUTERWEAR


def test_the_customer_sees_no_admin_buttons() -> None:
    message = rich_screen(PRODUCT_CARD, product_view(), CUSTOMER)

    assert texts_of(message) == ["🧺 В корзину", "🧺 Корзина", "⬅️ Назад"]


def test_a_product_in_stock_can_go_to_the_cart() -> None:
    message = rich_screen(PRODUCT_CARD, product_view(), CUSTOMER)
    actions = [entry.action for entry in callbacks_of(message)]

    assert ShopAction.ADD in actions


def test_an_out_of_stock_product_cannot_go_to_the_cart() -> None:
    message = rich_screen(PRODUCT_CARD, product_view(in_stock=False), CUSTOMER)
    actions = [entry.action for entry in callbacks_of(message)]

    assert ShopAction.ADD not in actions


def test_a_product_with_variants_asks_to_pick_one_first() -> None:
    variants = (ShopVariantView(id=SIZE_M, title="M", price=usd("12900")),)

    message = rich_screen(PRODUCT_CARD, product_view(variants=variants), CUSTOMER)
    actions = [entry.action for entry in callbacks_of(message)]

    assert ShopAction.VARIANTS in actions
    assert ShopAction.ADD not in actions


def test_a_picked_variant_carries_both_identifiers() -> None:
    pick = ShopVariantPickView(
        product_id=COAT,
        variant_id=SIZE_M,
        title="M",
        price=usd("12900"),
    )

    message = rich_paged_screen(
        VARIANT_PICKER, paged([pick]), product_view(), CUSTOMER
    )
    added = next(
        entry for entry in callbacks_of(message) if entry.action is ShopAction.ADD
    )

    assert added.product_id == COAT
    assert added.variant_id == SIZE_M
