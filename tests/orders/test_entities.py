from dataclasses import replace

import pytest

from telegramsales.modules.orders.domain.entities import Order, Selection
from telegramsales.modules.orders.domain.enums import OrderStatus
from telegramsales.modules.orders.domain.events import (
    OrderCancelled,
    OrderPlaced,
    OrderStatusChanged,
    OrderTaken,
)
from telegramsales.modules.orders.domain.exceptions import (
    EmptyOrderError,
    EmptySelectionError,
    ForbiddenStatusChangeError,
    MixedCurrencyOrderError,
    OrderAlreadyTakenError,
    OrderIsClosedError,
    QuantityTooLargeError,
)
from telegramsales.modules.orders.domain.services import capped_quantity
from telegramsales.modules.orders.domain.values import (
    MAX_QUANTITY,
    Comment,
    OrderNumber,
    Quantity,
)
from tests.orders.factories import (
    BUYER,
    MANAGER,
    NOW,
    ORDER,
    OTHER_MANAGER,
    SELECTION,
    SIZE_M,
    TODAY,
    make_cart_item,
    make_contacts,
    make_order,
    make_order_line,
    make_selection,
    make_taken_order,
    rub,
    usd,
)


def test_a_cart_item_adds_up_the_same_product() -> None:
    item = make_cart_item(quantity=2)

    item.add_up(Quantity(3))

    assert item.quantity == Quantity(5)


def test_a_cart_item_refuses_to_pass_the_limit() -> None:
    item = make_cart_item(quantity=MAX_QUANTITY)

    with pytest.raises(QuantityTooLargeError):
        item.add_up(Quantity.one())


def test_a_cart_item_keeps_its_variant() -> None:
    item = make_cart_item(variant_id=SIZE_M)

    assert item.reference.variant_id == SIZE_M


def test_capping_stops_at_the_limit() -> None:
    capped = capped_quantity(Quantity(MAX_QUANTITY), Quantity(5))

    assert capped == Quantity(MAX_QUANTITY)


def test_a_line_total_multiplies_the_price() -> None:
    line = make_order_line(price="12900", quantity=3)

    assert line.total == rub("38700")


def test_an_order_sums_up_its_lines() -> None:
    order = make_order(
        lines=(
            make_order_line(price="12900", quantity=2),
            make_order_line("Платье", price="7900"),
        )
    )

    assert order.total == rub("33700")


def test_an_order_without_lines_is_rejected() -> None:
    with pytest.raises(EmptyOrderError):
        Order.place(
            order_id=ORDER,
            number=OrderNumber(day=TODAY, sequence=1),
            customer_id=BUYER,
            contacts=make_contacts(),
            comment=Comment(""),
            lines=(),
            now=NOW,
        )


def test_lines_in_two_currencies_are_rejected() -> None:
    lines = (
        make_order_line(price="12900"),
        replace(make_order_line("Платье"), price=usd("100")),
    )

    with pytest.raises(MixedCurrencyOrderError):
        make_order(lines=lines)


def test_a_placed_order_starts_as_placed() -> None:
    assert make_order().status is OrderStatus.PLACED


def test_a_placed_order_keeps_its_number() -> None:
    order = make_order(sequence=7)

    assert order.number == OrderNumber(day=TODAY, sequence=7)


def test_placing_an_order_registers_an_event() -> None:
    order = make_order()

    events = order.collect_events()

    assert [type(event) for event in events] == [OrderPlaced]


def test_the_placed_event_carries_the_number() -> None:
    order = make_order(sequence=3)
    event = order.collect_events()[0]

    assert isinstance(event, OrderPlaced)
    assert event.number == "2026-09-12-0003"
    assert event.customer_id == BUYER
    assert event.order_id == ORDER


def test_a_customer_can_cancel_a_fresh_order() -> None:
    order = make_order()

    order.cancel_by_customer()

    assert order.status is OrderStatus.CANCELLED


def test_cancelling_registers_both_events() -> None:
    order = make_order()
    _ = order.collect_events()

    order.cancel_by_customer()

    assert [type(event) for event in order.collect_events()] == [
        OrderStatusChanged,
        OrderCancelled,
    ]


def test_a_customer_cancellation_names_no_manager() -> None:
    order = make_order()
    _ = order.collect_events()

    order.cancel_by_customer()
    cancelled = order.collect_events()[1]

    assert isinstance(cancelled, OrderCancelled)
    assert cancelled.manager_id is None


def test_a_taken_order_cannot_be_cancelled_by_the_customer() -> None:
    order = make_order()
    order.status = OrderStatus.IN_WORK

    with pytest.raises(OrderAlreadyTakenError):
        order.cancel_by_customer()


def test_an_order_cannot_be_cancelled_twice() -> None:
    order = make_order()
    order.cancel_by_customer()

    with pytest.raises(OrderAlreadyTakenError):
        order.cancel_by_customer()


def test_taking_an_order_moves_it_into_work() -> None:
    order = make_order()

    order.take_in_work(MANAGER)

    assert order.status is OrderStatus.IN_WORK
    assert order.manager_id == MANAGER


def test_taking_an_order_registers_both_events() -> None:
    order = make_order()
    _ = order.collect_events()

    order.take_in_work(MANAGER)

    assert [type(event) for event in order.collect_events()] == [
        OrderStatusChanged,
        OrderTaken,
    ]


def test_another_manager_takes_over_without_moving_the_status() -> None:
    order = make_taken_order(OrderStatus.PAID)

    order.take_in_work(OTHER_MANAGER)

    assert order.manager_id == OTHER_MANAGER
    assert order.status is OrderStatus.PAID
    assert [type(event) for event in order.collect_events()] == [OrderTaken]


def test_a_closed_order_cannot_be_taken() -> None:
    order = make_taken_order(OrderStatus.DONE)

    with pytest.raises(OrderIsClosedError):
        order.take_in_work(MANAGER)


@pytest.mark.parametrize(
    ("status", "requested"),
    [
        (OrderStatus.IN_WORK, OrderStatus.PAID),
        (OrderStatus.IN_WORK, OrderStatus.SHIPPED),
        (OrderStatus.IN_WORK, OrderStatus.DONE),
        (OrderStatus.PAID, OrderStatus.SHIPPED),
        (OrderStatus.PAID, OrderStatus.DONE),
        (OrderStatus.SHIPPED, OrderStatus.DONE),
    ],
)
def test_a_manager_moves_the_order_forward(
    status: OrderStatus,
    requested: OrderStatus,
) -> None:
    order = make_taken_order(status)

    order.change_status(requested)

    assert order.status is requested


@pytest.mark.parametrize(
    ("status", "requested"),
    [
        (OrderStatus.PLACED, OrderStatus.PAID),
        (OrderStatus.IN_WORK, OrderStatus.IN_WORK),
        (OrderStatus.SHIPPED, OrderStatus.PAID),
        (OrderStatus.DONE, OrderStatus.SHIPPED),
        (OrderStatus.CANCELLED, OrderStatus.IN_WORK),
        (OrderStatus.IN_WORK, OrderStatus.CANCELLED),
    ],
)
def test_the_order_refuses_a_backward_step(
    status: OrderStatus,
    requested: OrderStatus,
) -> None:
    order = make_taken_order(status)

    with pytest.raises(ForbiddenStatusChangeError):
        order.change_status(requested)


def test_a_status_change_carries_both_ends() -> None:
    order = make_taken_order()

    order.change_status(OrderStatus.PAID)
    event = order.collect_events()[0]

    assert isinstance(event, OrderStatusChanged)
    assert event.previous is OrderStatus.IN_WORK
    assert event.status is OrderStatus.PAID


def test_a_manager_cancels_an_order_already_in_work() -> None:
    order = make_taken_order()

    order.cancel_by_manager(MANAGER)
    cancelled = order.collect_events()[1]

    assert order.status is OrderStatus.CANCELLED
    assert isinstance(cancelled, OrderCancelled)
    assert cancelled.manager_id == MANAGER


def test_a_closed_order_cannot_be_cancelled_by_the_manager() -> None:
    order = make_taken_order(OrderStatus.DONE)

    with pytest.raises(OrderIsClosedError):
        order.cancel_by_manager(MANAGER)


def test_a_selection_without_lines_is_rejected() -> None:
    with pytest.raises(EmptySelectionError):
        Selection.create(
            selection_id=SELECTION,
            author_id=BUYER,
            lines=(),
            now=NOW,
        )


def test_a_selection_keeps_its_author() -> None:
    assert make_selection().author_id == BUYER
