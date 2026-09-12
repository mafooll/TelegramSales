from dataclasses import dataclass

from telegramsales.modules.catalog.contracts import ICatalogOffers, OfferKey
from telegramsales.modules.customers.contracts import (
    ContactsSnapshot,
    CustomerId,
    ICustomerDirectory,
)
from telegramsales.modules.orders.application.exceptions import (
    CartHasUnavailableLinesError,
    CustomerCannotOrderError,
    OrderNotFoundError,
)
from telegramsales.modules.orders.application.ports import IOrdersUnitOfWork
from telegramsales.modules.orders.contracts import OrderId
from telegramsales.modules.orders.domain.entities import Order, OrderLine
from telegramsales.modules.orders.domain.services import ensure_cart_is_not_empty
from telegramsales.modules.orders.domain.values import Comment, OrderNumber
from telegramsales.shared.application.clock import IClock
from telegramsales.shared.application.events import IEventPublisher
from telegramsales.shared.domain.contacts import Contacts


@dataclass(frozen=True, slots=True)
class PlaceOrder:
    customer_id: CustomerId
    contacts: Contacts
    comment: Comment


@dataclass(frozen=True, slots=True)
class CancelOrder:
    customer_id: CustomerId
    order_id: OrderId


class PlaceOrderHandler:
    def __init__(
        self,
        uow: IOrdersUnitOfWork,
        offers: ICatalogOffers,
        directory: ICustomerDirectory,
        events: IEventPublisher,
        clock: IClock,
    ) -> None:
        self._uow: IOrdersUnitOfWork = uow
        self._offers: ICatalogOffers = offers
        self._directory: ICustomerDirectory = directory
        self._events: IEventPublisher = events
        self._clock: IClock = clock

    async def handle(self, command: PlaceOrder) -> str:
        await self._ensure_can_order(command.customer_id)
        await self._directory.remember(
            command.customer_id,
            ContactsSnapshot(
                name=command.contacts.name.value,
                phone=command.contacts.phone.value,
                address=command.contacts.address.value,
            ),
        )

        async with self._uow as uow:
            items = await uow.carts.items_of(command.customer_id)
            ensure_cart_is_not_empty(len(items))

            keys: list[OfferKey] = [
                (item.reference.product_id, item.reference.variant_id)
                for item in items
            ]
            offers = await self._offers.offers(keys)

            lines: list[OrderLine] = []
            missing = 0
            for item in items:
                offer = offers.get(
                    (item.reference.product_id, item.reference.variant_id)
                )
                if offer is None or not offer.is_available:
                    missing += 1
                    continue
                lines.append(
                    OrderLine(
                        reference=item.reference,
                        title=offer.title,
                        article=offer.article,
                        variant_title=offer.variant_title,
                        price=offer.price,
                        old_price=offer.old_price,
                        quantity=item.quantity,
                    )
                )

            if missing:
                raise CartHasUnavailableLinesError(lines=missing)

            now = self._clock.now()
            order = Order.place(
                order_id=await uow.orders.next_id(),
                number=OrderNumber(
                    day=now.date(),
                    sequence=await uow.orders.next_sequence(now.date()),
                ),
                customer_id=command.customer_id,
                contacts=command.contacts,
                comment=command.comment,
                lines=tuple(lines),
                now=now,
            )
            await uow.orders.add(order)
            await uow.carts.clear(command.customer_id)
            uow.track(order)

        await self._events.publish_all(self._uow.collect_events())
        return order.number.value

    async def _ensure_can_order(self, customer_id: CustomerId) -> None:
        card = await self._directory.find(customer_id)
        if card is not None and card.is_blocked:
            raise CustomerCannotOrderError(customer_id=customer_id)


class CancelOrderHandler:
    def __init__(self, uow: IOrdersUnitOfWork, events: IEventPublisher) -> None:
        self._uow: IOrdersUnitOfWork = uow
        self._events: IEventPublisher = events

    async def handle(self, command: CancelOrder) -> None:
        async with self._uow as uow:
            order = await uow.orders.get(command.order_id)
            if order is None or order.customer_id != command.customer_id:
                raise OrderNotFoundError(order_id=command.order_id)

            order.cancel_by_customer()
            uow.track(order)
            await uow.orders.save(order)

        await self._events.publish_all(self._uow.collect_events())
