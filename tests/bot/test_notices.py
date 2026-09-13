import pytest

from telegramsales.apps.bot.notifications import (
    cancellation_notice,
    new_product_announcement,
    status_notice,
)
from telegramsales.modules.catalog.domain.events import ProductPublished
from telegramsales.modules.catalog.presentation.bot import shop_texts
from telegramsales.modules.catalog.presentation.bot.shop_callbacks import (
    ShopAction,
    ShopCallback,
)
from telegramsales.modules.orders.domain.enums import OrderStatus
from telegramsales.modules.orders.domain.events import (
    OrderCancelled,
    OrderStatusChanged,
)
from telegramsales.modules.orders.presentation.bot import texts
from telegramsales.modules.orders.presentation.bot.callbacks import (
    OrderAction,
    OrderCallback,
)
from tests.catalog.factories import CLOTHES, COAT
from tests.orders.factories import BUYER, MANAGER, ORDER

NUMBER = "2026-09-12-0001"
MAX_CALLBACK_BYTES = 64


def status_changed(
    status: OrderStatus,
    previous: OrderStatus = OrderStatus.PLACED,
) -> OrderStatusChanged:
    return OrderStatusChanged(
        order_id=ORDER,
        number=NUMBER,
        customer_id=BUYER,
        previous=previous,
        status=status,
    )


def cancelled(*, by_manager: bool) -> OrderCancelled:
    return OrderCancelled(
        order_id=ORDER,
        number=NUMBER,
        customer_id=BUYER,
        manager_id=MANAGER if by_manager else None,
    )


@pytest.mark.parametrize(
    ("status", "key"),
    [
        (OrderStatus.IN_WORK, texts.NOTICE_IN_WORK),
        (OrderStatus.PAID, texts.NOTICE_PAID),
        (OrderStatus.SHIPPED, texts.NOTICE_SHIPPED),
        (OrderStatus.DONE, texts.NOTICE_DONE),
    ],
)
def test_every_managed_status_reaches_the_customer(
    status: OrderStatus,
    key: str,
) -> None:
    notice = status_notice(status_changed(status))

    assert notice is not None
    assert notice.recipient_id == BUYER
    assert notice.key == key
    assert notice.args == {"number": NUMBER}


def test_the_notice_is_deduplicated_by_order_and_status() -> None:
    notice = status_notice(status_changed(OrderStatus.PAID))

    assert notice is not None
    assert notice.dedup_key == f"order-status:{ORDER}:paid"


def test_a_cancellation_is_not_announced_twice() -> None:
    assert status_notice(status_changed(OrderStatus.CANCELLED)) is None


def test_a_managers_cancellation_reaches_the_customer() -> None:
    notice = cancellation_notice(cancelled(by_manager=True))

    assert notice is not None
    assert notice.key == texts.NOTICE_CANCELLED
    assert notice.dedup_key == f"order-cancelled:{ORDER}"


def test_the_customer_is_not_told_about_their_own_cancellation() -> None:
    assert cancellation_notice(cancelled(by_manager=False)) is None


def published() -> ProductPublished:
    return ProductPublished(
        product_id=COAT,
        catalog_id=CLOTHES,
        title="Пальто оверсайз",
        article="000042",
    )


def test_a_published_product_is_announced_once_per_product() -> None:
    announcement = new_product_announcement(published())

    assert announcement.key == shop_texts.NEW_PRODUCT
    assert announcement.args == {
        "title": "Пальто оверсайз",
        "article": "000042",
    }
    assert announcement.topic == f"new-product:{COAT}"


def test_a_status_notice_leads_to_the_order_list() -> None:
    notice = status_notice(status_changed(OrderStatus.PAID))

    assert notice is not None
    assert notice.action.key == texts.OPEN_ORDERS_BUTTON
    assert notice.action.data == OrderCallback(action=OrderAction.LIST).pack()


def test_a_cancellation_notice_leads_to_the_order_list() -> None:
    notice = cancellation_notice(cancelled(by_manager=True))

    assert notice is not None
    assert notice.action.key == texts.OPEN_ORDERS_BUTTON


def test_an_announcement_leads_to_the_product_card() -> None:
    announcement = new_product_announcement(published())

    assert announcement.action is not None
    assert announcement.action.key == shop_texts.OPEN_PRODUCT_BUTTON
    assert announcement.action.data == ShopCallback(
        action=ShopAction.PRODUCT,
        product_id=COAT,
    ).pack()


def test_every_action_fits_the_callback_limit() -> None:
    notice = status_notice(status_changed(OrderStatus.PAID))
    announcement = new_product_announcement(published())

    assert notice is not None
    assert announcement.action is not None
    assert len(notice.action.data.encode()) <= MAX_CALLBACK_BYTES
    assert len(announcement.action.data.encode()) <= MAX_CALLBACK_BYTES
