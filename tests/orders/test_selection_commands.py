import pytest

from telegramsales.modules.orders.application.commands.selections import (
    AdoptSelection,
    AdoptSelectionHandler,
    ShareCart,
    ShareCartHandler,
)
from telegramsales.modules.orders.application.exceptions import (
    SelectionNotFoundError,
)
from telegramsales.modules.orders.domain.exceptions import EmptyCartError
from telegramsales.modules.orders.domain.values import MAX_QUANTITY, Quantity
from tests.orders.factories import (
    BUYER,
    CART_ITEM,
    COAT,
    DRESS,
    NOW,
    SELECTION,
    SIZE_M,
    STRANGER,
    make_cart_item,
    make_selection,
    make_selection_line,
)
from tests.orders.fakes import (
    FakeCartRepository,
    FakeCatalogOffers,
    FakeOrdersUnitOfWork,
    FakeSelectionRepository,
    FixedClock,
    offer,
)

CLOCK = FixedClock(NOW)


def sharing(
    carts: FakeCartRepository,
    offers: FakeCatalogOffers | None = None,
) -> tuple[ShareCartHandler, FakeOrdersUnitOfWork]:
    uow = FakeOrdersUnitOfWork(carts=carts)
    catalogue = offers or FakeCatalogOffers(offer(COAT))
    return ShareCartHandler(uow, catalogue, CLOCK), uow


def adopting(
    *,
    carts: FakeCartRepository | None = None,
    selections: FakeSelectionRepository | None = None,
    offers: FakeCatalogOffers | None = None,
) -> tuple[AdoptSelectionHandler, FakeOrdersUnitOfWork]:
    uow = FakeOrdersUnitOfWork(carts=carts, selections=selections)
    catalogue = offers or FakeCatalogOffers(offer(COAT))
    return AdoptSelectionHandler(uow, catalogue, CLOCK), uow


async def test_sharing_snapshots_the_cart() -> None:
    handler, uow = sharing(FakeCartRepository(make_cart_item(quantity=3)))

    selection_id = await handler.handle(ShareCart(customer_id=BUYER))
    stored = uow.selection_repository.selections[selection_id]

    assert [line.title for line in stored.lines] == ["Пальто оверсайз"]
    assert stored.lines[0].quantity == Quantity(3)


async def test_a_shared_line_keeps_the_variant_title() -> None:
    handler, uow = sharing(
        FakeCartRepository(make_cart_item(variant_id=SIZE_M)),
        FakeCatalogOffers(offer(COAT, variant_id=SIZE_M, variant_title="M")),
    )

    selection_id = await handler.handle(ShareCart(customer_id=BUYER))
    stored = uow.selection_repository.selections[selection_id]

    assert stored.lines[0].variant_title == "M"


async def test_the_author_is_written_down() -> None:
    handler, uow = sharing(FakeCartRepository(make_cart_item()))

    selection_id = await handler.handle(ShareCart(customer_id=BUYER))

    assert uow.selection_repository.selections[selection_id].author_id == BUYER


async def test_an_empty_cart_cannot_be_shared() -> None:
    handler, _ = sharing(FakeCartRepository())

    with pytest.raises(EmptyCartError):
        await handler.handle(ShareCart(customer_id=BUYER))


async def test_a_cart_of_vanished_products_cannot_be_shared() -> None:
    handler, _ = sharing(FakeCartRepository(make_cart_item(product_id=DRESS)))

    with pytest.raises(EmptyCartError):
        await handler.handle(ShareCart(customer_id=BUYER))


async def test_adopting_fills_the_reader_cart() -> None:
    handler, uow = adopting(selections=FakeSelectionRepository(make_selection()))

    adoption = await handler.handle(
        AdoptSelection(customer_id=STRANGER, selection_id=SELECTION)
    )

    assert adoption.added == 1
    assert [item.customer_id for item in uow.cart_repository.items.values()] == [
        STRANGER
    ]


async def test_adopting_keeps_the_quantity() -> None:
    selection = make_selection(lines=(make_selection_line(quantity=4),))
    handler, uow = adopting(selections=FakeSelectionRepository(selection))

    await handler.handle(
        AdoptSelection(customer_id=STRANGER, selection_id=SELECTION)
    )
    stored = next(iter(uow.cart_repository.items.values()))

    assert stored.quantity == Quantity(4)


async def test_a_sold_out_line_is_skipped() -> None:
    handler, uow = adopting(
        selections=FakeSelectionRepository(make_selection()),
        offers=FakeCatalogOffers(offer(COAT, is_available=False)),
    )

    adoption = await handler.handle(
        AdoptSelection(customer_id=STRANGER, selection_id=SELECTION)
    )

    assert adoption == type(adoption)(added=0, skipped=1)
    assert uow.cart_repository.items == {}


async def test_a_vanished_line_is_skipped() -> None:
    selection = make_selection(
        lines=(make_selection_line(product_id=DRESS, title="Платье"),)
    )
    handler, _ = adopting(selections=FakeSelectionRepository(selection))

    adoption = await handler.handle(
        AdoptSelection(customer_id=STRANGER, selection_id=SELECTION)
    )

    assert adoption.skipped == 1


async def test_adopting_adds_up_with_what_is_already_there() -> None:
    handler, uow = adopting(
        carts=FakeCartRepository(make_cart_item(quantity=2)),
        selections=FakeSelectionRepository(
            make_selection(lines=(make_selection_line(quantity=3),))
        ),
    )

    await handler.handle(AdoptSelection(customer_id=BUYER, selection_id=SELECTION))

    assert uow.cart_repository.items[CART_ITEM].quantity == Quantity(5)


async def test_adopting_never_passes_the_limit() -> None:
    handler, uow = adopting(
        carts=FakeCartRepository(make_cart_item(quantity=MAX_QUANTITY)),
        selections=FakeSelectionRepository(
            make_selection(lines=(make_selection_line(quantity=5),))
        ),
    )

    await handler.handle(AdoptSelection(customer_id=BUYER, selection_id=SELECTION))

    assert uow.cart_repository.items[CART_ITEM].quantity == Quantity(MAX_QUANTITY)


async def test_an_unknown_selection_cannot_be_adopted() -> None:
    handler, _ = adopting()

    with pytest.raises(SelectionNotFoundError):
        await handler.handle(
            AdoptSelection(customer_id=BUYER, selection_id=SELECTION)
        )
