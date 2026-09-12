from telegramsales.modules.catalog.contracts import (
    ICatalogOffers,
    OfferKey,
    ProductOffer,
)
from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.application.ports import (
    ICartQueries,
    ISelectionQueries,
)
from telegramsales.modules.orders.application.queries import (
    CartLineView,
    CartView,
    SelectionLineView,
    SelectionRow,
    SelectionView,
)
from telegramsales.modules.orders.contracts import SelectionId
from telegramsales.shared.domain.money import Currency, Money

EMPTY_TOTAL_CURRENCY = Currency.RUB


def _sum_up(lines: tuple[CartLineView, ...]) -> Money:
    offered = [line.total for line in lines if line.is_available]
    if not offered:
        return Money.zero(EMPTY_TOTAL_CURRENCY)
    total, *rest = offered
    for amount in rest:
        total = total + amount
    return total


class CartReader:
    def __init__(self, queries: ICartQueries, offers: ICatalogOffers) -> None:
        self._queries: ICartQueries = queries
        self._offers: ICatalogOffers = offers

    async def read(self, customer_id: CustomerId) -> CartView:
        rows = await self._queries.rows_of(customer_id)
        keys: list[OfferKey] = [
            (row.product_id, row.variant_id) for row in rows
        ]
        offers = await self._offers.offers(keys)

        lines: list[CartLineView] = []
        for row in rows:
            offer = offers.get((row.product_id, row.variant_id))
            if offer is None:
                continue
            lines.append(
                CartLineView(
                    item_id=row.item_id,
                    title=offer.title,
                    variant_title=offer.variant_title,
                    price=offer.price,
                    quantity=row.quantity,
                    total=offer.price * row.quantity,
                    is_available=offer.is_available,
                )
            )

        ordered = tuple(lines)
        return CartView(lines=ordered, total=_sum_up(ordered))


class SelectionReader:
    def __init__(self, queries: ISelectionQueries, offers: ICatalogOffers) -> None:
        self._queries: ISelectionQueries = queries
        self._offers: ICatalogOffers = offers

    async def read(self, selection_id: SelectionId) -> SelectionView | None:
        author_id = await self._queries.author_of(selection_id)
        if author_id is None:
            return None

        rows = await self._queries.rows_of(selection_id)
        keys: list[OfferKey] = [
            (row.product_id, row.variant_id) for row in rows
        ]
        offers = await self._offers.offers(keys)

        return SelectionView(
            id=selection_id,
            author_id=author_id,
            lines=tuple(
                _selection_line(
                    row,
                    offers.get((row.product_id, row.variant_id)),
                )
                for row in rows
            ),
        )


def _selection_line(
    row: SelectionRow,
    offer: ProductOffer | None,
) -> SelectionLineView:
    if offer is None or not offer.is_available:
        return SelectionLineView(
            title=row.title,
            variant_title=row.variant_title,
            price=None,
            quantity=row.quantity,
            is_available=False,
        )
    return SelectionLineView(
        title=offer.title,
        variant_title=offer.variant_title,
        price=offer.price,
        quantity=row.quantity,
        is_available=True,
    )
