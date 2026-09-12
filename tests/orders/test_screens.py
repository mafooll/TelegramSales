from aiogram.types import (
    InputRichBlockButtons,
    InputRichBlockParagraph,
    InputRichMessage,
)

from telegramsales.modules.orders.application.queries import (
    CartLineView,
    CartView,
    OrderEntryView,
    OrderLineView,
    OrderView,
    SelectionLineView,
    SelectionView,
)
from telegramsales.modules.orders.domain.enums import OrderStatus
from telegramsales.modules.orders.domain.values import MAX_QUANTITY
from telegramsales.modules.orders.presentation.bot.callbacks import (
    CartAction,
    CartCallback,
    OrderAction,
    OrderCallback,
)
from telegramsales.modules.orders.presentation.bot.screens import (
    CART,
    CART_LINE,
    CHECKOUT_CONFIRM,
    ORDER_CARD,
    ORDER_LIST,
    PLACED,
    SELECTION,
)
from telegramsales.modules.orders.presentation.bot.views import (
    CheckoutView,
    OrderListView,
    PlacedView,
)
from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.pagination import Page
from telegramsales.shared.infrastructure.i18n.fluent import FluentTranslations
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.pagination import Pagination
from telegramsales.shared.presentation.bot.rich import rich_paged_screen, rich_screen
from telegramsales.shared.settings import LOCALES_PATH
from tests.orders.factories import (
    BUYER,
    CART_ITEM,
    NOW,
    ORDER,
    SELECTION as SELECTION_ID,
    rub,
)

DEFAULT_LOCALE = "ru"
PAGE_SIZE = 8

TRANSLATE = FluentTranslations(LOCALES_PATH, DEFAULT_LOCALE)(DEFAULT_LOCALE)
CUSTOMER = RenderContext(
    actor=Actor(id=7, permissions=frozenset()), translate=TRANSLATE
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


def cart_line(
    *,
    quantity: int = 1,
    is_available: bool = True,
    variant_title: str | None = None,
) -> CartLineView:
    return CartLineView(
        item_id=CART_ITEM,
        title="Пальто оверсайз",
        variant_title=variant_title,
        price=rub("12900"),
        quantity=quantity,
        total=rub("12900") * quantity,
        is_available=is_available,
    )


def cart_view(*lines: CartLineView) -> CartView:
    total = rub("0")
    for line in lines:
        if line.is_available:
            total = total + line.total
    return CartView(lines=lines, total=total)


def paged[ItemType](items: list[ItemType]) -> Pagination[ItemType]:
    return Pagination(
        page=Page(items=items, number=0, size=PAGE_SIZE, total=len(items)),
        callback=lambda value: CartCallback(action=CartAction.OPEN, page=value),
    )


def order_view(
    *,
    status: OrderStatus = OrderStatus.PLACED,
    comment: str = "",
) -> OrderView:
    return OrderView(
        id=ORDER,
        number="2026-09-12-0001",
        status=status,
        created_at=NOW,
        name="Иван Петров",
        phone="+79991234567",
        address="Москва, Тверская 1",
        comment=comment,
        lines=(
            OrderLineView(
                title="Пальто оверсайз",
                article="000042",
                variant_title="M",
                price=rub("12900"),
                old_price=None,
                quantity=2,
                total=rub("25800"),
            ),
        ),
        total=rub("25800"),
    )


def selection_view(*lines: SelectionLineView) -> SelectionView:
    return SelectionView(
        id=SELECTION_ID,
        author_id=BUYER,
        lines=lines,
    )


def selection_line(
    *,
    is_available: bool = True,
    title: str = "Пальто оверсайз",
) -> SelectionLineView:
    return SelectionLineView(
        title=title,
        variant_title=None,
        price=rub("12900") if is_available else None,
        quantity=1,
        is_available=is_available,
    )


def test_an_empty_cart_says_so() -> None:
    message = rich_paged_screen(CART, paged([]), cart_view(), CUSTOMER)

    assert paragraphs_of(message) == [
        "Корзина пуста. Загляните в магазин и выберите что-нибудь."
    ]


def test_an_empty_cart_offers_no_checkout() -> None:
    message = rich_paged_screen(CART, paged([]), cart_view(), CUSTOMER)

    assert texts_of(message) == ["⬅️ В меню"]


def test_a_cart_line_shows_quantity_and_sum() -> None:
    line = cart_line(quantity=2)

    message = rich_paged_screen(CART, paged([line]), cart_view(line), CUSTOMER)

    assert "Пальто оверсайз · 2 шт · 25 800 ₽" in texts_of(message)


def test_a_variant_is_named_in_the_line() -> None:
    line = cart_line(variant_title="M")

    message = rich_paged_screen(CART, paged([line]), cart_view(line), CUSTOMER)

    assert "Пальто оверсайз · M · 1 шт · 12 900 ₽" in texts_of(message)


def test_a_filled_cart_offers_checkout_and_sharing() -> None:
    line = cart_line()

    message = rich_paged_screen(CART, paged([line]), cart_view(line), CUSTOMER)
    labels = texts_of(message)

    assert "🧾 Оформить заказ" in labels
    assert "🔗 Поделиться" in labels
    assert "🗑️ Очистить" in labels


def test_a_cart_with_a_gone_line_cannot_be_ordered() -> None:
    line = cart_line(is_available=False)

    message = rich_paged_screen(CART, paged([line]), cart_view(line), CUSTOMER)

    assert "🧾 Оформить заказ" not in texts_of(message)


def test_a_gone_line_is_marked() -> None:
    line = cart_line(is_available=False)

    message = rich_paged_screen(CART, paged([line]), cart_view(line), CUSTOMER)

    assert "⚠️ Пальто оверсайз · нет в наличии" in texts_of(message)


def test_the_cart_total_counts_only_what_is_on_offer() -> None:
    view = cart_view(cart_line(), cart_line(is_available=False))

    message = rich_paged_screen(CART, paged(list(view.lines)), view, CUSTOMER)

    assert "Итого 12 900 ₽" in paragraphs_of(message)[0]


def test_a_single_line_cannot_give_one_back() -> None:
    message = rich_screen(CART_LINE, cart_line(), CUSTOMER)

    assert "➖" not in texts_of(message)


def test_a_doubled_line_can_give_one_back() -> None:
    message = rich_screen(CART_LINE, cart_line(quantity=2), CUSTOMER)

    assert "➖" in texts_of(message)


def test_a_full_line_cannot_take_one_more() -> None:
    message = rich_screen(CART_LINE, cart_line(quantity=MAX_QUANTITY), CUSTOMER)

    assert "➕" not in texts_of(message)


def test_a_line_can_always_be_dropped() -> None:
    message = rich_screen(CART_LINE, cart_line(), CUSTOMER)

    assert "🗑️ Убрать" in texts_of(message)


def checkout_view(comment: str = "") -> CheckoutView:
    return CheckoutView(
        name="Иван Петров",
        phone="+79991234567",
        address="Москва, Тверская 1",
        comment=comment,
        lines=2,
        total="25 800 ₽",
    )


def test_the_confirmation_lists_the_contacts() -> None:
    message = rich_screen(CHECKOUT_CONFIRM, checkout_view(), CUSTOMER)
    text = paragraphs_of(message)[0]

    assert "Иван Петров" in text
    assert "+79991234567" in text
    assert "Москва, Тверская 1" in text
    assert "25 800 ₽" in text


def test_the_confirmation_shows_a_comment_when_there_is_one() -> None:
    message = rich_screen(
        CHECKOUT_CONFIRM, checkout_view("позвоните заранее"), CUSTOMER
    )

    assert "Комментарий: позвоните заранее" in paragraphs_of(message)[0]


def test_the_confirmation_stays_silent_without_a_comment() -> None:
    message = rich_screen(CHECKOUT_CONFIRM, checkout_view(), CUSTOMER)

    assert "Комментарий" not in paragraphs_of(message)[0]


def test_the_confirmation_can_be_placed_or_edited() -> None:
    message = rich_screen(CHECKOUT_CONFIRM, checkout_view(), CUSTOMER)
    labels = texts_of(message)

    assert "✅ Оформить" in labels
    assert "✏️ Изменить данные" in labels
    assert "💬 Комментарий" in labels


def test_a_placed_order_names_its_number() -> None:
    message = rich_screen(
        PLACED, PlacedView(number="2026-09-12-0001"), CUSTOMER
    )

    assert "2026-09-12-0001" in paragraphs_of(message)[0]


def test_an_empty_order_list_says_so() -> None:
    message = rich_paged_screen(
        ORDER_LIST, paged([]), OrderListView(total=0), CUSTOMER
    )

    assert paragraphs_of(message) == ["Заказов пока нет."]


def test_an_order_entry_shows_number_status_and_sum() -> None:
    entry = OrderEntryView(
        id=ORDER,
        number="2026-09-12-0001",
        status=OrderStatus.PLACED,
        total=rub("25800"),
        created_at=NOW,
        line_count=1,
    )

    message = rich_paged_screen(
        ORDER_LIST, paged([entry]), OrderListView(total=1), CUSTOMER
    )

    assert "2026-09-12-0001 · оформлен · 25 800 ₽" in texts_of(message)


def test_an_order_card_lists_its_lines() -> None:
    message = rich_screen(ORDER_CARD, order_view(), CUSTOMER)
    text = paragraphs_of(message)[0]

    assert "• Пальто оверсайз · M · 2 шт · 25 800 ₽" in text
    assert "Итого: 25 800 ₽" in text


def test_a_fresh_order_can_be_cancelled() -> None:
    message = rich_screen(ORDER_CARD, order_view(), CUSTOMER)

    assert "✖️ Отменить заказ" in texts_of(message)


def test_an_order_in_work_cannot_be_cancelled_by_the_customer() -> None:
    message = rich_screen(
        ORDER_CARD, order_view(status=OrderStatus.IN_WORK), CUSTOMER
    )

    assert "✖️ Отменить заказ" not in texts_of(message)


def test_the_cancel_button_carries_the_order() -> None:
    message = rich_screen(ORDER_CARD, order_view(), CUSTOMER)
    blocks = message.blocks or []
    callbacks = [
        OrderCallback.unpack(button.callback_data)
        for block in blocks
        if isinstance(block, InputRichBlockButtons)
        for button in block.buttons
        if button.callback_data is not None
    ]
    asked = next(
        entry for entry in callbacks if entry.action is OrderAction.ASK_CANCEL
    )

    assert asked.order_id == ORDER


def test_a_shared_cart_lists_its_lines() -> None:
    message = rich_screen(
        SELECTION, selection_view(selection_line()), CUSTOMER
    )

    assert "• Пальто оверсайз · 1 шт · 12 900 ₽" in paragraphs_of(message)[0]


def test_a_shared_cart_can_be_adopted() -> None:
    message = rich_screen(
        SELECTION, selection_view(selection_line()), CUSTOMER
    )

    assert "📥 Перенести себе" in texts_of(message)


def test_a_gone_line_of_a_shared_cart_is_marked() -> None:
    message = rich_screen(
        SELECTION,
        selection_view(selection_line(is_available=False, title="Платье")),
        CUSTOMER,
    )

    assert "• ⚠️ Платье · больше не продаётся" in paragraphs_of(message)[0]


def test_nothing_to_adopt_hides_the_button() -> None:
    message = rich_screen(
        SELECTION,
        selection_view(selection_line(is_available=False)),
        CUSTOMER,
    )

    assert "📥 Перенести себе" not in texts_of(message)
