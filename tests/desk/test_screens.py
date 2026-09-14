from aiogram.types import (
    InputRichBlockButtons,
    InputRichBlockParagraph,
    InputRichMessage,
)

from telegramsales.modules.desk.presentation.bot.screens import ORDER_CARD
from telegramsales.modules.desk.presentation.bot.views import WORK_CHAT_VIEWER
from telegramsales.modules.orders.contracts import OrderCardView, OrderStatus
from telegramsales.shared.infrastructure.i18n.fluent import FluentTranslations
from telegramsales.shared.presentation.bot.context import RenderContext
from telegramsales.shared.presentation.bot.rich import rich_screen
from telegramsales.shared.settings import LOCALES_PATH
from tests.desk.factories import MANAGER, make_card

DEFAULT_LOCALE = "ru"
TRANSLATE = FluentTranslations(LOCALES_PATH, DEFAULT_LOCALE)(DEFAULT_LOCALE)
WORK_CHAT = RenderContext(actor=WORK_CHAT_VIEWER, translate=TRANSLATE)

TAKE = "🙋 Взять в работу"
REASSIGN = "🔄 Перевести на себя"
PAID = "💰 Оплачен"
SHIPPED = "📦 Отправлен"
DONE = "✅ Выполнен"
CANCEL = "✖️ Отменить"


def card_of(card: OrderCardView) -> InputRichMessage:
    return rich_screen(ORDER_CARD, card, WORK_CHAT)


def buttons_of(message: InputRichMessage) -> list[str]:
    return [
        str(button.text)
        for block in (message.blocks or [])
        if isinstance(block, InputRichBlockButtons)
        for button in block.buttons
    ]


def text_of(message: InputRichMessage) -> str:
    return "\n".join(
        str(block.text)
        for block in (message.blocks or [])
        if isinstance(block, InputRichBlockParagraph)
    )


def test_a_fresh_order_can_only_be_taken_or_cancelled() -> None:
    assert buttons_of(card_of(make_card())) == [TAKE, CANCEL]


def test_an_order_in_work_moves_along_the_funnel() -> None:
    card = make_card(status=OrderStatus.IN_WORK, manager_id=MANAGER)

    assert buttons_of(card_of(card)) == [REASSIGN, PAID, SHIPPED, DONE, CANCEL]


def test_a_shipped_order_can_only_be_finished() -> None:
    card = make_card(status=OrderStatus.SHIPPED, manager_id=MANAGER)

    assert buttons_of(card_of(card)) == [REASSIGN, DONE, CANCEL]


def test_a_closed_order_keeps_no_buttons() -> None:
    card = make_card(status=OrderStatus.DONE, manager_id=MANAGER)

    assert buttons_of(card_of(card)) == []


def test_the_card_carries_the_contacts_and_the_lines() -> None:
    text = text_of(card_of(make_card(comment="позвоните заранее")))

    assert "2026-09-12-0001" in text
    assert "Пальто оверсайз" in text
    assert "000042" in text
    assert "+79991234567" in text
    assert "позвоните заранее" in text
    assert "25 800 $" in text


def test_an_untaken_order_says_so() -> None:
    assert "никто не взял" in text_of(card_of(make_card()))


def test_an_untaken_order_offers_to_take_it() -> None:
    assert TAKE in buttons_of(card_of(make_card()))


def test_a_taken_order_names_the_manager() -> None:
    card = make_card(status=OrderStatus.IN_WORK, manager_id=MANAGER)

    assert str(MANAGER) in text_of(card_of(card))
