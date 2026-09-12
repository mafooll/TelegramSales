from collections.abc import Mapping

from telegramsales.modules.desk.presentation.bot import texts
from telegramsales.modules.orders.contracts import OrderCardView, OrderStatus
from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.i18n import ITranslator

STATUS_KEYS: Mapping[OrderStatus, str] = {
    OrderStatus.PLACED: texts.STATUS_PLACED,
    OrderStatus.IN_WORK: texts.STATUS_IN_WORK,
    OrderStatus.PAID: texts.STATUS_PAID,
    OrderStatus.SHIPPED: texts.STATUS_SHIPPED,
    OrderStatus.DONE: texts.STATUS_DONE,
    OrderStatus.CANCELLED: texts.STATUS_CANCELLED,
}

WORK_CHAT_VIEWER = Actor(id=0, permissions=frozenset(), is_shopping=False)


def status_key(status: OrderStatus) -> str:
    return STATUS_KEYS[status]


def variant_suffix(variant_title: str | None, translate: ITranslator) -> str:
    if variant_title is None:
        return ""
    return translate(texts.VARIANT_SUFFIX, variant=variant_title)


def can_take(card: OrderCardView) -> bool:
    return not card.is_closed


def can_cancel(card: OrderCardView) -> bool:
    return not card.is_closed


def can_pay(card: OrderCardView) -> bool:
    return card.can_become(OrderStatus.PAID)


def can_ship(card: OrderCardView) -> bool:
    return card.can_become(OrderStatus.SHIPPED)


def can_finish(card: OrderCardView) -> bool:
    return card.can_become(OrderStatus.DONE)
