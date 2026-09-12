import pytest

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.application.commands.orders import (
    CancelOrder,
    CancelOrderHandler,
    PlaceOrder,
    PlaceOrderHandler,
)
from telegramsales.modules.orders.application.exceptions import (
    CartHasUnavailableLinesError,
    CustomerCannotOrderError,
    OrderNotFoundError,
)
from telegramsales.modules.orders.domain.enums import OrderStatus
from telegramsales.modules.orders.domain.events import (
    OrderCancelled,
    OrderPlaced,
)
from telegramsales.modules.orders.domain.exceptions import EmptyCartError
from telegramsales.modules.orders.domain.values import Comment
from tests.orders.factories import (
    BUYER,
    COAT,
    DRESS,
    NOW,
    ORDER,
    SIZE_M,
    STRANGER,
    make_cart_item,
    make_contacts,
    make_order,
    rub,
)
from tests.orders.fakes import (
    FakeCartRepository,
    FakeCatalogOffers,
    FakeCustomerDirectory,
    FakeEventPublisher,
    FakeOrderRepository,
    FakeOrdersUnitOfWork,
    FixedClock,
    blocked_card,
    offer,
)

CLOCK = FixedClock(NOW)


def placing(
    *,
    carts: FakeCartRepository | None = None,
    offers: FakeCatalogOffers | None = None,
    orders: FakeOrderRepository | None = None,
    directory: FakeCustomerDirectory | None = None,
) -> tuple[PlaceOrderHandler, FakeOrdersUnitOfWork, FakeEventPublisher]:
    uow = FakeOrdersUnitOfWork(carts=carts, orders=orders)
    events = FakeEventPublisher()
    handler = PlaceOrderHandler(
        uow,
        offers or FakeCatalogOffers(offer(COAT)),
        directory or FakeCustomerDirectory(),
        events,
        CLOCK,
    )
    return handler, uow, events


def order_for(customer_id: CustomerId = BUYER) -> PlaceOrder:
    return PlaceOrder(
        customer_id=customer_id,
        contacts=make_contacts(),
        comment=Comment(""),
    )


async def test_an_order_takes_its_lines_from_the_cart() -> None:
    handler, uow, _ = placing(carts=FakeCartRepository(make_cart_item(quantity=2)))

    await handler.handle(order_for())
    placed = next(iter(uow.order_repository.orders.values()))

    assert [line.title for line in placed.lines] == ["Пальто оверсайз"]
    assert placed.total == rub("25800")


async def test_an_order_snapshots_the_current_price() -> None:
    handler, uow, _ = placing(
        carts=FakeCartRepository(make_cart_item()),
        offers=FakeCatalogOffers(offer(COAT, price="9900", old_price="12900")),
    )

    await handler.handle(order_for())
    placed = next(iter(uow.order_repository.orders.values()))

    assert placed.lines[0].price == rub("9900")
    assert placed.lines[0].old_price == rub("12900")


async def test_a_variant_title_reaches_the_order() -> None:
    handler, uow, _ = placing(
        carts=FakeCartRepository(make_cart_item(variant_id=SIZE_M)),
        offers=FakeCatalogOffers(offer(COAT, variant_id=SIZE_M, variant_title="M")),
    )

    await handler.handle(order_for())
    placed = next(iter(uow.order_repository.orders.values()))

    assert placed.lines[0].variant_title == "M"


async def test_the_first_order_of_the_day_is_the_first_number() -> None:
    handler, uow, _ = placing(carts=FakeCartRepository(make_cart_item()))

    await handler.handle(order_for())
    placed = next(iter(uow.order_repository.orders.values()))

    assert placed.number.value == "2026-09-12-0001"


async def test_the_next_order_of_the_day_counts_on() -> None:
    handler, _, _ = placing(
        carts=FakeCartRepository(make_cart_item()),
        orders=FakeOrderRepository(make_order(sequence=4)),
    )

    number = await handler.handle(order_for())

    assert number == "2026-09-12-0005"


async def test_placing_empties_the_cart() -> None:
    handler, uow, _ = placing(carts=FakeCartRepository(make_cart_item()))

    await handler.handle(order_for())

    assert uow.cart_repository.items == {}


async def test_an_empty_cart_cannot_be_ordered() -> None:
    handler, _, _ = placing()

    with pytest.raises(EmptyCartError):
        await handler.handle(order_for())


async def test_a_sold_out_line_blocks_the_order() -> None:
    handler, _, _ = placing(
        carts=FakeCartRepository(make_cart_item()),
        offers=FakeCatalogOffers(offer(COAT, is_available=False)),
    )

    with pytest.raises(CartHasUnavailableLinesError):
        await handler.handle(order_for())


async def test_a_vanished_product_blocks_the_order() -> None:
    handler, _, _ = placing(
        carts=FakeCartRepository(make_cart_item(product_id=DRESS))
    )

    with pytest.raises(CartHasUnavailableLinesError):
        await handler.handle(order_for())


async def test_a_blocked_customer_cannot_order() -> None:
    handler, _, _ = placing(
        carts=FakeCartRepository(make_cart_item()),
        directory=FakeCustomerDirectory(blocked_card(BUYER)),
    )

    with pytest.raises(CustomerCannotOrderError):
        await handler.handle(order_for())


async def test_contacts_are_remembered_for_the_next_time() -> None:
    directory = FakeCustomerDirectory()
    handler, _, _ = placing(
        carts=FakeCartRepository(make_cart_item()),
        directory=directory,
    )

    await handler.handle(order_for())

    assert [snapshot.phone for snapshot in directory.remembered] == ["+79991234567"]


async def test_placing_publishes_the_event() -> None:
    handler, _, events = placing(carts=FakeCartRepository(make_cart_item()))

    await handler.handle(order_for())

    assert [type(event) for event in events.published] == [OrderPlaced]


async def test_a_customer_cancels_an_open_order() -> None:
    uow = FakeOrdersUnitOfWork(orders=FakeOrderRepository(make_order()))
    events = FakeEventPublisher()

    await CancelOrderHandler(uow, events).handle(
        CancelOrder(customer_id=BUYER, order_id=ORDER)
    )

    assert uow.order_repository.orders[ORDER].status is OrderStatus.CANCELLED


async def test_cancelling_publishes_the_event() -> None:
    placed = make_order()
    _ = placed.collect_events()
    uow = FakeOrdersUnitOfWork(orders=FakeOrderRepository(placed))
    events = FakeEventPublisher()

    await CancelOrderHandler(uow, events).handle(
        CancelOrder(customer_id=BUYER, order_id=ORDER)
    )

    assert [type(event) for event in events.published] == [OrderCancelled]


async def test_a_stranger_cannot_cancel_an_order() -> None:
    uow = FakeOrdersUnitOfWork(orders=FakeOrderRepository(make_order()))

    with pytest.raises(OrderNotFoundError):
        await CancelOrderHandler(uow, FakeEventPublisher()).handle(
            CancelOrder(customer_id=STRANGER, order_id=ORDER)
        )


async def test_an_unknown_order_cannot_be_cancelled() -> None:
    uow = FakeOrdersUnitOfWork()

    with pytest.raises(OrderNotFoundError):
        await CancelOrderHandler(uow, FakeEventPublisher()).handle(
            CancelOrder(customer_id=BUYER, order_id=ORDER)
        )
