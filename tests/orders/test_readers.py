from typing import override

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.application.ports import ISelectionQueries
from telegramsales.modules.orders.application.queries import CartRow, SelectionRow
from telegramsales.modules.orders.application.readers import (
    CartReader,
    SelectionReader,
)
from telegramsales.modules.orders.contracts import CartItemId, SelectionId
from tests.orders.factories import BUYER, COAT, DRESS, SELECTION, SIZE_M, rub
from tests.orders.fakes import FakeCartQueries, FakeCatalogOffers, offer


def row(
    item_id: int = 1,
    *,
    product_id: object = COAT,
    variant_id: object = None,
    quantity: int = 1,
) -> CartRow:
    return CartRow(
        item_id=CartItemId(item_id),
        product_id=product_id,  # pyright: ignore[reportArgumentType]
        variant_id=variant_id,  # pyright: ignore[reportArgumentType]
        quantity=quantity,
    )


class FakeSelectionQueries(ISelectionQueries):
    def __init__(
        self,
        *rows: SelectionRow,
        author: CustomerId | None = BUYER,
    ) -> None:
        self.rows: list[SelectionRow] = list(rows)
        self.author: CustomerId | None = author

    @override
    async def author_of(self, selection_id: SelectionId) -> CustomerId | None:
        return self.author

    @override
    async def rows_of(self, selection_id: SelectionId) -> list[SelectionRow]:
        return list(self.rows)


def selection_row(
    title: str = "Пальто оверсайз",
    *,
    product_id: object = COAT,
    variant_title: str | None = None,
    quantity: int = 1,
) -> SelectionRow:
    return SelectionRow(
        product_id=product_id,  # pyright: ignore[reportArgumentType]
        variant_id=None,
        title=title,
        variant_title=variant_title,
        quantity=quantity,
    )


async def test_a_cart_line_carries_the_current_price() -> None:
    reader = CartReader(
        FakeCartQueries(row(quantity=2)),
        FakeCatalogOffers(offer(COAT, price="10000")),
    )

    view = await reader.read(BUYER)

    assert view.lines[0].price == rub("10000")
    assert view.lines[0].total == rub("20000")


async def test_a_cart_total_adds_the_lines_up() -> None:
    reader = CartReader(
        FakeCartQueries(row(), row(2, product_id=DRESS)),
        FakeCatalogOffers(
            offer(COAT, price="10000"),
            offer(DRESS, title="Платье", price="7000"),
        ),
    )

    view = await reader.read(BUYER)

    assert view.total == rub("17000")


async def test_a_sold_out_line_is_marked_and_left_out_of_the_total() -> None:
    reader = CartReader(
        FakeCartQueries(row(), row(2, product_id=DRESS)),
        FakeCatalogOffers(
            offer(COAT, price="10000"),
            offer(DRESS, title="Платье", price="7000", is_available=False),
        ),
    )

    view = await reader.read(BUYER)

    assert view.has_unavailable
    assert view.total == rub("10000")


async def test_a_vanished_product_drops_out_of_the_cart() -> None:
    reader = CartReader(
        FakeCartQueries(row(product_id=DRESS)),
        FakeCatalogOffers(offer(COAT)),
    )

    view = await reader.read(BUYER)

    assert view.is_empty


async def test_an_empty_cart_totals_nothing() -> None:
    reader = CartReader(FakeCartQueries(), FakeCatalogOffers())

    view = await reader.read(BUYER)

    assert view.total == rub("0")


async def test_a_variant_line_shows_its_title() -> None:
    reader = CartReader(
        FakeCartQueries(row(variant_id=SIZE_M)),
        FakeCatalogOffers(offer(COAT, variant_id=SIZE_M, variant_title="M")),
    )

    view = await reader.read(BUYER)

    assert view.lines[0].variant_title == "M"


async def test_an_unknown_selection_reads_as_nothing() -> None:
    reader = SelectionReader(
        FakeSelectionQueries(author=None), FakeCatalogOffers()
    )

    assert await reader.read(SELECTION) is None


async def test_a_selection_line_shows_the_current_price() -> None:
    reader = SelectionReader(
        FakeSelectionQueries(selection_row()),
        FakeCatalogOffers(offer(COAT, price="11000")),
    )

    view = await reader.read(SELECTION)

    assert view is not None
    assert view.lines[0].price == rub("11000")
    assert view.available_count == 1


async def test_a_gone_line_keeps_the_snapshot_title() -> None:
    reader = SelectionReader(
        FakeSelectionQueries(selection_row("Платье", product_id=DRESS)),
        FakeCatalogOffers(),
    )

    view = await reader.read(SELECTION)

    assert view is not None
    assert view.lines[0].title == "Платье"
    assert view.lines[0].price is None
    assert view.has_unavailable


async def test_a_sold_out_line_is_not_adoptable() -> None:
    reader = SelectionReader(
        FakeSelectionQueries(selection_row()),
        FakeCatalogOffers(offer(COAT, is_available=False)),
    )

    view = await reader.read(SELECTION)

    assert view is not None
    assert view.available_count == 0
