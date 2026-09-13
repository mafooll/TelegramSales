from dataclasses import dataclass

from aiogram.filters.callback_data import CallbackData

from telegramsales.modules.orders.application.queries import (
    CartLineView,
    SelectionLineView,
)
from telegramsales.modules.orders.domain.enums import OrderStatus
from telegramsales.modules.orders.domain.values import MAX_QUANTITY, MIN_QUANTITY
from telegramsales.modules.orders.presentation.bot import texts
from telegramsales.shared.application.i18n import ITranslator

NOTICE_KEYS = {
    OrderStatus.IN_WORK: texts.NOTICE_IN_WORK,
    OrderStatus.PAID: texts.NOTICE_PAID,
    OrderStatus.SHIPPED: texts.NOTICE_SHIPPED,
    OrderStatus.DONE: texts.NOTICE_DONE,
    OrderStatus.CANCELLED: texts.NOTICE_CANCELLED,
}

STATUS_KEYS = {
    OrderStatus.PLACED: texts.STATUS_PLACED,
    OrderStatus.IN_WORK: texts.STATUS_IN_WORK,
    OrderStatus.PAID: texts.STATUS_PAID,
    OrderStatus.SHIPPED: texts.STATUS_SHIPPED,
    OrderStatus.DONE: texts.STATUS_DONE,
    OrderStatus.CANCELLED: texts.STATUS_CANCELLED,
}


@dataclass(frozen=True, slots=True)
class PromptView:
    message_key: str
    back: CallbackData


@dataclass(frozen=True, slots=True)
class CheckoutView:
    name: str
    phone: str
    address: str
    comment: str
    lines: int
    total: str


@dataclass(frozen=True, slots=True)
class PlacedView:
    number: str


@dataclass(frozen=True, slots=True)
class OrderListView:
    total: int


def cart_line_key(line: CartLineView) -> str:
    return texts.CART_LINE if line.is_available else texts.CART_LINE_GONE


def cart_line_card_key(line: CartLineView) -> str:
    return texts.CART_LINE_CARD if line.is_available else texts.CART_LINE_CARD_GONE


def selection_line_key(line: SelectionLineView) -> str:
    return texts.SELECTION_LINE if line.is_available else texts.SELECTION_LINE_GONE


def status_key(status: OrderStatus) -> str:
    return STATUS_KEYS[status]


def notice_key(status: OrderStatus) -> str | None:
    return NOTICE_KEYS.get(status)


def can_add_more(line: CartLineView) -> bool:
    return line.quantity < MAX_QUANTITY


def can_take_away(line: CartLineView) -> bool:
    return line.quantity > MIN_QUANTITY


def variant_suffix(variant_title: str | None, translate: ITranslator) -> str:
    if variant_title is None:
        return ""
    return translate(texts.VARIANT_SUFFIX, variant=variant_title)
