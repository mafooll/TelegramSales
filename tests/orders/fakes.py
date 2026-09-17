from collections.abc import Mapping, Sequence
from datetime import date, datetime
from types import TracebackType
from typing import Self, override
from uuid import uuid4

from telegramsales.modules.catalog.contracts import (
    ICatalogOffers,
    MediaLayout,
    OfferKey,
    ProductId,
    ProductOffer,
    VariantId,
)
from telegramsales.modules.customers.contracts import (
    ContactsSnapshot,
    CustomerCard,
    CustomerId,
    ICustomerDirectory,
)
from telegramsales.modules.orders.application.ports import (
    ICartQueries,
    ICartRepository,
    IOrderRepository,
    ISelectionRepository,
)
from telegramsales.modules.orders.application.queries import CartRow
from telegramsales.modules.orders.contracts import (
    CartItemId,
    OrderId,
    SelectionId,
)
from telegramsales.modules.orders.domain.entities import (
    CartItem,
    Order,
    Selection,
)
from telegramsales.modules.orders.domain.values import ProductRef
from telegramsales.shared.application.clock import IClock
from telegramsales.shared.application.events import IEventPublisher
from telegramsales.shared.domain.event import DomainEvent, IEventSource
from telegramsales.shared.domain.money import Currency, Money


class FakeCartRepository(ICartRepository):
    def __init__(self, *items: CartItem) -> None:
        self.items: dict[CartItemId, CartItem] = {item.id: item for item in items}
        self._next: int = max((item.id for item in items), default=0) + 1

    @override
    async def next_id(self) -> CartItemId:
        issued = CartItemId(self._next)
        self._next += 1
        return issued

    @override
    async def get(self, item_id: CartItemId) -> CartItem | None:
        return self.items.get(item_id)

    @override
    async def find(
        self,
        customer_id: CustomerId,
        reference: ProductRef,
    ) -> CartItem | None:
        return next(
            (
                item
                for item in self.items.values()
                if item.customer_id == customer_id and item.reference == reference
            ),
            None,
        )

    @override
    async def items_of(self, customer_id: CustomerId) -> list[CartItem]:
        return [
            item for item in self.items.values() if item.customer_id == customer_id
        ]

    @override
    async def add(self, item: CartItem) -> None:
        self.items[item.id] = item

    @override
    async def save(self, item: CartItem) -> None:
        self.items[item.id] = item

    @override
    async def delete(self, item: CartItem) -> None:
        self.items.pop(item.id, None)

    @override
    async def clear(self, customer_id: CustomerId) -> None:
        for item in list(self.items.values()):
            if item.customer_id == customer_id:
                del self.items[item.id]


class FakeSelectionRepository(ISelectionRepository):
    def __init__(self, *selections: Selection) -> None:
        self.selections: dict[SelectionId, Selection] = {
            selection.id: selection for selection in selections
        }

    @override
    async def next_id(self) -> SelectionId:
        return SelectionId(uuid4())

    @override
    async def get(self, selection_id: SelectionId) -> Selection | None:
        return self.selections.get(selection_id)

    @override
    async def add(self, selection: Selection) -> None:
        self.selections[selection.id] = selection


class FakeOrderRepository(IOrderRepository):
    def __init__(self, *orders: Order) -> None:
        self.orders: dict[OrderId, Order] = {order.id: order for order in orders}

    @override
    async def next_id(self) -> OrderId:
        return OrderId(uuid4())

    @override
    async def next_sequence(self, day: date) -> int:
        taken = [
            order.number.sequence
            for order in self.orders.values()
            if order.number.day == day
        ]
        return max(taken, default=0) + 1

    @override
    async def get(self, order_id: OrderId) -> Order | None:
        return self.orders.get(order_id)

    @override
    async def add(self, order: Order) -> None:
        self.orders[order.id] = order

    @override
    async def save(self, order: Order) -> None:
        self.orders[order.id] = order


class FakeOrdersUnitOfWork:
    def __init__(
        self,
        *,
        carts: FakeCartRepository | None = None,
        selections: FakeSelectionRepository | None = None,
        orders: FakeOrderRepository | None = None,
    ) -> None:
        self.cart_repository: FakeCartRepository = carts or FakeCartRepository()
        self.selection_repository: FakeSelectionRepository = (
            selections or FakeSelectionRepository()
        )
        self.order_repository: FakeOrderRepository = orders or FakeOrderRepository()
        self._tracked: list[IEventSource] = []
        self._events: list[DomainEvent] = []
        self.committed: bool = False
        self.rolled_back: bool = False

    @property
    def carts(self) -> ICartRepository:
        return self.cart_repository

    @property
    def selections(self) -> ISelectionRepository:
        return self.selection_repository

    @property
    def orders(self) -> IOrderRepository:
        return self.order_repository

    async def __aenter__(self) -> Self:
        self._tracked = []
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self._events = [
                event
                for entity in self._tracked
                for event in entity.collect_events()
            ]
            self.committed = True
        else:
            self.rolled_back = True

    def track(self, entity: IEventSource) -> None:
        self._tracked.append(entity)

    def collect_events(self) -> list[DomainEvent]:
        events = self._events
        self._events = []
        return events


class FakeCartQueries(ICartQueries):
    def __init__(self, *rows: CartRow) -> None:
        self.rows: list[CartRow] = list(rows)

    @override
    async def rows_of(self, customer_id: CustomerId) -> list[CartRow]:
        return list(self.rows)

    @override
    async def count(self, customer_id: CustomerId) -> int:
        return len(self.rows)


def offer(  # noqa: PLR0913
    product_id: ProductId,
    *,
    variant_id: VariantId | None = None,
    title: str = "Пальто оверсайз",
    price: str = "12900",
    old_price: str | None = None,
    variant_title: str | None = None,
    is_available: bool = True,
    photo_ids: tuple[str, ...] = (),
    media_layout: MediaLayout = MediaLayout.COLLAGE,
) -> ProductOffer:
    return ProductOffer(
        product_id=product_id,
        variant_id=variant_id,
        title=title,
        article="000042",
        variant_title=variant_title,
        price=Money.from_external(price, Currency.USD),
        old_price=(
            None
            if old_price is None
            else Money.from_external(old_price, Currency.USD)
        ),
        is_available=is_available,
        photo_ids=photo_ids,
        media_layout=media_layout,
    )


class FakeCatalogOffers(ICatalogOffers):
    def __init__(self, *offers: ProductOffer) -> None:
        self.catalogue: dict[OfferKey, ProductOffer] = {
            (item.product_id, item.variant_id): item for item in offers
        }

    @override
    async def offer(
        self,
        product_id: ProductId,
        variant_id: VariantId | None,
    ) -> ProductOffer | None:
        return self.catalogue.get((product_id, variant_id))

    @override
    async def offers(
        self,
        keys: Sequence[OfferKey],
    ) -> Mapping[OfferKey, ProductOffer]:
        return {key: self.catalogue[key] for key in keys if key in self.catalogue}


class FakeCustomerDirectory(ICustomerDirectory):
    def __init__(self, *cards: CustomerCard) -> None:
        self.cards: dict[CustomerId, CustomerCard] = {
            card.id: card for card in cards
        }
        self.remembered: list[ContactsSnapshot] = []

    @override
    async def register(self, customer_id: CustomerId, name: str) -> None:
        self.cards[customer_id] = CustomerCard(
            id=customer_id,
            name=name,
            contacts=None,
            is_blocked=False,
        )

    @override
    async def find(self, customer_id: CustomerId) -> CustomerCard | None:
        return self.cards.get(customer_id)

    @override
    async def remember(
        self,
        customer_id: CustomerId,
        contacts: ContactsSnapshot,
    ) -> None:
        self.remembered.append(contacts)
        known = self.cards.get(customer_id)
        self.cards[customer_id] = CustomerCard(
            id=customer_id,
            name=contacts.name,
            contacts=contacts,
            is_blocked=False if known is None else known.is_blocked,
        )


def blocked_card(customer_id: CustomerId) -> CustomerCard:
    return CustomerCard(
        id=customer_id,
        name="Иван Петров",
        contacts=None,
        is_blocked=True,
    )


class FakeEventPublisher(IEventPublisher):
    def __init__(self) -> None:
        self.published: list[DomainEvent] = []

    @override
    async def publish_all(self, events: list[DomainEvent]) -> None:
        self.published.extend(events)


class FixedClock(IClock):
    def __init__(self, moment: datetime) -> None:
        self._moment: datetime = moment

    @override
    def now(self) -> datetime:
        return self._moment
