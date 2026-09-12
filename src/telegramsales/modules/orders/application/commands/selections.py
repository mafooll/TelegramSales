from dataclasses import dataclass

from telegramsales.modules.catalog.contracts import ICatalogOffers, OfferKey
from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.application.exceptions import (
    SelectionNotFoundError,
)
from telegramsales.modules.orders.application.ports import IOrdersUnitOfWork
from telegramsales.modules.orders.contracts import SelectionId
from telegramsales.modules.orders.domain.entities import (
    CartItem,
    Selection,
    SelectionLine,
)
from telegramsales.modules.orders.domain.services import (
    capped_quantity,
    ensure_cart_is_not_empty,
)
from telegramsales.shared.application.clock import IClock


@dataclass(frozen=True, slots=True)
class ShareCart:
    customer_id: CustomerId


@dataclass(frozen=True, slots=True)
class AdoptSelection:
    customer_id: CustomerId
    selection_id: SelectionId


@dataclass(frozen=True, slots=True)
class Adoption:
    added: int
    skipped: int


class ShareCartHandler:
    def __init__(
        self,
        uow: IOrdersUnitOfWork,
        offers: ICatalogOffers,
        clock: IClock,
    ) -> None:
        self._uow: IOrdersUnitOfWork = uow
        self._offers: ICatalogOffers = offers
        self._clock: IClock = clock

    async def handle(self, command: ShareCart) -> SelectionId:
        async with self._uow as uow:
            items = await uow.carts.items_of(command.customer_id)
            ensure_cart_is_not_empty(len(items))

            keys: list[OfferKey] = [
                (item.reference.product_id, item.reference.variant_id)
                for item in items
            ]
            offers = await self._offers.offers(keys)

            lines: list[SelectionLine] = []
            for item in items:
                offer = offers.get(
                    (item.reference.product_id, item.reference.variant_id)
                )
                if offer is None:
                    continue
                lines.append(
                    SelectionLine(
                        reference=item.reference,
                        title=offer.title,
                        variant_title=offer.variant_title,
                        quantity=item.quantity,
                    )
                )

            ensure_cart_is_not_empty(len(lines))
            selection = Selection.create(
                selection_id=await uow.selections.next_id(),
                author_id=command.customer_id,
                lines=tuple(lines),
                now=self._clock.now(),
            )
            await uow.selections.add(selection)

        return selection.id


class AdoptSelectionHandler:
    def __init__(
        self,
        uow: IOrdersUnitOfWork,
        offers: ICatalogOffers,
        clock: IClock,
    ) -> None:
        self._uow: IOrdersUnitOfWork = uow
        self._offers: ICatalogOffers = offers
        self._clock: IClock = clock

    async def handle(self, command: AdoptSelection) -> Adoption:
        async with self._uow as uow:
            selection = await uow.selections.get(command.selection_id)
            if selection is None:
                raise SelectionNotFoundError(selection_id=command.selection_id)

            keys: list[OfferKey] = [
                (line.reference.product_id, line.reference.variant_id)
                for line in selection.lines
            ]
            offers = await self._offers.offers(keys)

            added = 0
            for line in selection.lines:
                offer = offers.get(
                    (line.reference.product_id, line.reference.variant_id)
                )
                if offer is None or not offer.is_available:
                    continue

                item = await uow.carts.find(command.customer_id, line.reference)
                if item is None:
                    await uow.carts.add(
                        CartItem.create(
                            item_id=await uow.carts.next_id(),
                            customer_id=command.customer_id,
                            reference=line.reference,
                            quantity=line.quantity,
                            now=self._clock.now(),
                        )
                    )
                else:
                    item.set_quantity(capped_quantity(item.quantity, line.quantity))
                    await uow.carts.save(item)
                added += 1

        return Adoption(added=added, skipped=len(selection.lines) - added)
