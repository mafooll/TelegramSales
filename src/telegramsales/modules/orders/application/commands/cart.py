from dataclasses import dataclass

from telegramsales.modules.catalog.contracts import (
    ICatalogOffers,
    ProductId,
    VariantId,
)
from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.orders.application.exceptions import (
    ProductNotOfferedError,
)
from telegramsales.modules.orders.application.ports import IOrdersUnitOfWork
from telegramsales.modules.orders.contracts import CartItemId
from telegramsales.modules.orders.domain.entities import CartItem
from telegramsales.modules.orders.domain.exceptions import ItemNotInCartError
from telegramsales.modules.orders.domain.values import ProductRef, Quantity
from telegramsales.shared.application.clock import IClock


@dataclass(frozen=True, slots=True)
class AddToCart:
    customer_id: CustomerId
    product_id: ProductId
    variant_id: VariantId | None = None


@dataclass(frozen=True, slots=True)
class IncreaseCartItem:
    customer_id: CustomerId
    item_id: CartItemId


@dataclass(frozen=True, slots=True)
class DecreaseCartItem:
    customer_id: CustomerId
    item_id: CartItemId


@dataclass(frozen=True, slots=True)
class RemoveCartItem:
    customer_id: CustomerId
    item_id: CartItemId


@dataclass(frozen=True, slots=True)
class ClearCart:
    customer_id: CustomerId


async def _owned(
    uow: IOrdersUnitOfWork,
    item_id: CartItemId,
    customer_id: CustomerId,
) -> CartItem:
    item = await uow.carts.get(item_id)
    if item is None or item.customer_id != customer_id:
        raise ItemNotInCartError(item_id=item_id)
    return item


class AddToCartHandler:
    def __init__(
        self,
        uow: IOrdersUnitOfWork,
        offers: ICatalogOffers,
        clock: IClock,
    ) -> None:
        self._uow: IOrdersUnitOfWork = uow
        self._offers: ICatalogOffers = offers
        self._clock: IClock = clock

    async def handle(self, command: AddToCart) -> None:
        offer = await self._offers.offer(command.product_id, command.variant_id)
        if offer is None or not offer.is_available:
            raise ProductNotOfferedError(product_id=command.product_id)

        reference = ProductRef(
            product_id=command.product_id,
            variant_id=command.variant_id,
        )
        async with self._uow as uow:
            item = await uow.carts.find(command.customer_id, reference)
            if item is None:
                await uow.carts.add(
                    CartItem.create(
                        item_id=await uow.carts.next_id(),
                        customer_id=command.customer_id,
                        reference=reference,
                        quantity=Quantity.one(),
                        now=self._clock.now(),
                    )
                )
                return

            item.add_up(Quantity.one())
            await uow.carts.save(item)


class IncreaseCartItemHandler:
    def __init__(self, uow: IOrdersUnitOfWork) -> None:
        self._uow: IOrdersUnitOfWork = uow

    async def handle(self, command: IncreaseCartItem) -> None:
        async with self._uow as uow:
            item = await _owned(uow, command.item_id, command.customer_id)
            item.set_quantity(item.quantity.increased())
            await uow.carts.save(item)


class DecreaseCartItemHandler:
    def __init__(self, uow: IOrdersUnitOfWork) -> None:
        self._uow: IOrdersUnitOfWork = uow

    async def handle(self, command: DecreaseCartItem) -> None:
        async with self._uow as uow:
            item = await _owned(uow, command.item_id, command.customer_id)
            if item.quantity.is_lowest:
                await uow.carts.delete(item)
                return

            item.set_quantity(item.quantity.decreased())
            await uow.carts.save(item)


class RemoveCartItemHandler:
    def __init__(self, uow: IOrdersUnitOfWork) -> None:
        self._uow: IOrdersUnitOfWork = uow

    async def handle(self, command: RemoveCartItem) -> None:
        async with self._uow as uow:
            item = await _owned(uow, command.item_id, command.customer_id)
            await uow.carts.delete(item)


class ClearCartHandler:
    def __init__(self, uow: IOrdersUnitOfWork) -> None:
        self._uow: IOrdersUnitOfWork = uow

    async def handle(self, command: ClearCart) -> None:
        async with self._uow as uow:
            await uow.carts.clear(command.customer_id)
