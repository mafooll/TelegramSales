import pytest

from telegramsales.modules.orders.application.commands.cart import (
    AddToCart,
    AddToCartHandler,
    ClearCart,
    ClearCartHandler,
    DecreaseCartItem,
    DecreaseCartItemHandler,
    IncreaseCartItem,
    IncreaseCartItemHandler,
    RemoveCartItem,
    RemoveCartItemHandler,
)
from telegramsales.modules.orders.application.exceptions import (
    ProductNotOfferedError,
)
from telegramsales.modules.orders.domain.exceptions import (
    ItemNotInCartError,
    QuantityTooLargeError,
)
from telegramsales.modules.orders.domain.values import MAX_QUANTITY, Quantity
from tests.orders.factories import (
    BUYER,
    CART_ITEM,
    COAT,
    DRESS,
    NOW,
    SIZE_M,
    STRANGER,
    make_cart_item,
)
from tests.orders.fakes import (
    FakeCartRepository,
    FakeCatalogOffers,
    FakeOrdersUnitOfWork,
    FixedClock,
    offer,
)

CLOCK = FixedClock(NOW)


def adding(
    *,
    carts: FakeCartRepository | None = None,
    offers: FakeCatalogOffers | None = None,
) -> tuple[AddToCartHandler, FakeOrdersUnitOfWork]:
    uow = FakeOrdersUnitOfWork(carts=carts)
    catalogue = offers or FakeCatalogOffers(offer(COAT))
    return AddToCartHandler(uow, catalogue, CLOCK), uow


async def test_adding_a_product_fills_the_cart() -> None:
    handler, uow = adding()

    await handler.handle(AddToCart(customer_id=BUYER, product_id=COAT))

    stored = uow.cart_repository.items.values()
    assert [item.reference.product_id for item in stored] == [COAT]


async def test_a_new_line_starts_with_one_item() -> None:
    handler, uow = adding()

    await handler.handle(AddToCart(customer_id=BUYER, product_id=COAT))
    stored = next(iter(uow.cart_repository.items.values()))

    assert stored.quantity == Quantity.one()


async def test_adding_the_same_product_adds_it_up() -> None:
    handler, uow = adding(carts=FakeCartRepository(make_cart_item(quantity=2)))

    await handler.handle(AddToCart(customer_id=BUYER, product_id=COAT))

    assert uow.cart_repository.items[CART_ITEM].quantity == Quantity(3)


async def test_a_variant_is_a_line_of_its_own() -> None:
    carts = FakeCartRepository(make_cart_item())
    handler, uow = adding(
        carts=carts,
        offers=FakeCatalogOffers(offer(COAT), offer(COAT, variant_id=SIZE_M)),
    )

    await handler.handle(
        AddToCart(customer_id=BUYER, product_id=COAT, variant_id=SIZE_M)
    )

    assert len(uow.cart_repository.items) == 2


async def test_a_full_line_refuses_more() -> None:
    handler, _ = adding(
        carts=FakeCartRepository(make_cart_item(quantity=MAX_QUANTITY))
    )

    with pytest.raises(QuantityTooLargeError):
        await handler.handle(AddToCart(customer_id=BUYER, product_id=COAT))


async def test_a_sold_out_product_is_not_added() -> None:
    handler, _ = adding(offers=FakeCatalogOffers(offer(COAT, is_available=False)))

    with pytest.raises(ProductNotOfferedError):
        await handler.handle(AddToCart(customer_id=BUYER, product_id=COAT))


async def test_an_unknown_product_is_not_added() -> None:
    handler, _ = adding()

    with pytest.raises(ProductNotOfferedError):
        await handler.handle(AddToCart(customer_id=BUYER, product_id=DRESS))


async def test_a_line_can_take_one_more() -> None:
    uow = FakeOrdersUnitOfWork(carts=FakeCartRepository(make_cart_item()))

    await IncreaseCartItemHandler(uow).handle(
        IncreaseCartItem(customer_id=BUYER, item_id=CART_ITEM)
    )

    assert uow.cart_repository.items[CART_ITEM].quantity == Quantity(2)


async def test_a_line_can_give_one_back() -> None:
    uow = FakeOrdersUnitOfWork(carts=FakeCartRepository(make_cart_item(quantity=3)))

    await DecreaseCartItemHandler(uow).handle(
        DecreaseCartItem(customer_id=BUYER, item_id=CART_ITEM)
    )

    assert uow.cart_repository.items[CART_ITEM].quantity == Quantity(2)


async def test_the_last_item_leaves_with_the_line() -> None:
    uow = FakeOrdersUnitOfWork(carts=FakeCartRepository(make_cart_item()))

    await DecreaseCartItemHandler(uow).handle(
        DecreaseCartItem(customer_id=BUYER, item_id=CART_ITEM)
    )

    assert uow.cart_repository.items == {}


async def test_a_line_can_be_removed() -> None:
    uow = FakeOrdersUnitOfWork(carts=FakeCartRepository(make_cart_item(quantity=5)))

    await RemoveCartItemHandler(uow).handle(
        RemoveCartItem(customer_id=BUYER, item_id=CART_ITEM)
    )

    assert uow.cart_repository.items == {}


async def test_a_stranger_cannot_touch_another_cart() -> None:
    uow = FakeOrdersUnitOfWork(carts=FakeCartRepository(make_cart_item()))

    with pytest.raises(ItemNotInCartError):
        await RemoveCartItemHandler(uow).handle(
            RemoveCartItem(customer_id=STRANGER, item_id=CART_ITEM)
        )


async def test_an_unknown_line_cannot_be_changed() -> None:
    uow = FakeOrdersUnitOfWork()

    with pytest.raises(ItemNotInCartError):
        await IncreaseCartItemHandler(uow).handle(
            IncreaseCartItem(customer_id=BUYER, item_id=CART_ITEM)
        )


async def test_clearing_takes_only_your_own_lines() -> None:
    mine = make_cart_item()
    theirs = make_cart_item(
        item_id=type(mine.id)(99), customer_id=STRANGER, product_id=DRESS
    )
    uow = FakeOrdersUnitOfWork(carts=FakeCartRepository(mine, theirs))

    await ClearCartHandler(uow).handle(ClearCart(customer_id=BUYER))

    assert list(uow.cart_repository.items) == [theirs.id]
