from dataclasses import dataclass

from telegramsales.modules.catalog.application.access import ensure_can_manage
from telegramsales.modules.catalog.application.exceptions import (
    DuplicateTitleError,
    ProductNotFoundError,
    VariantNotFoundError,
)
from telegramsales.modules.catalog.application.ports import ICatalogUnitOfWork
from telegramsales.modules.catalog.contracts import ProductId, VariantId
from telegramsales.modules.catalog.domain.entities import Product, ProductVariant
from telegramsales.modules.catalog.domain.services import ensure_variants_allowed
from telegramsales.modules.catalog.domain.values import Title
from telegramsales.shared.application.access import Actor
from telegramsales.shared.domain.money import Money


@dataclass(frozen=True, slots=True)
class ChangeVariantAxis:
    product_id: ProductId
    label: Title | None


@dataclass(frozen=True, slots=True)
class AddVariant:
    product_id: ProductId
    title: Title
    price_override: Money | None = None


@dataclass(frozen=True, slots=True)
class RenameVariant:
    variant_id: VariantId
    title: Title


@dataclass(frozen=True, slots=True)
class RepriceVariant:
    variant_id: VariantId
    price_override: Money | None


@dataclass(frozen=True, slots=True)
class ChangeVariantAvailability:
    variant_id: VariantId
    is_available: bool


@dataclass(frozen=True, slots=True)
class DeleteVariant:
    variant_id: VariantId


class VariantHandler:
    def __init__(self, uow: ICatalogUnitOfWork) -> None:
        self._uow: ICatalogUnitOfWork = uow

    async def _load_product(
        self,
        uow: ICatalogUnitOfWork,
        product_id: ProductId,
    ) -> Product:
        product = await uow.products.get(product_id)
        if product is None:
            raise ProductNotFoundError(product_id=product_id)
        return product

    async def _load_variant(
        self,
        uow: ICatalogUnitOfWork,
        variant_id: VariantId,
    ) -> ProductVariant:
        variant = await uow.variants.get(variant_id)
        if variant is None:
            raise VariantNotFoundError(variant_id=variant_id)
        return variant


class ChangeVariantAxisHandler(VariantHandler):
    async def handle(self, command: ChangeVariantAxis, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            product = await self._load_product(uow, command.product_id)
            if command.label is None:
                product.close_variants()
            else:
                product.open_variants(command.label)
            await uow.products.save(product)


class AddVariantHandler(VariantHandler):
    async def handle(self, command: AddVariant, actor: Actor) -> VariantId:
        ensure_can_manage(actor)

        async with self._uow as uow:
            product = await self._load_product(uow, command.product_id)
            ensure_variants_allowed(product)

            taken = await uow.variants.exists_with_title(
                command.title,
                product_id=product.id,
            )
            if taken:
                raise DuplicateTitleError(title=command.title.value)

            variant = ProductVariant.create(
                variant_id=await uow.variants.next_id(),
                product_id=product.id,
                title=command.title,
                price_override=command.price_override,
            )
            await uow.variants.add(variant)

        return variant.id


class RenameVariantHandler(VariantHandler):
    async def handle(self, command: RenameVariant, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            variant = await self._load_variant(uow, command.variant_id)

            taken = await uow.variants.exists_with_title(
                command.title,
                product_id=variant.product_id,
                excluding=variant.id,
            )
            if taken:
                raise DuplicateTitleError(title=command.title.value)

            variant.rename(command.title)
            await uow.variants.save(variant)


class RepriceVariantHandler(VariantHandler):
    async def handle(self, command: RepriceVariant, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            variant = await self._load_variant(uow, command.variant_id)
            variant.reprice(command.price_override)
            await uow.variants.save(variant)


class ChangeVariantAvailabilityHandler(VariantHandler):
    async def handle(self, command: ChangeVariantAvailability, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            variant = await self._load_variant(uow, command.variant_id)
            if command.is_available:
                variant.restock()
            else:
                variant.run_out()
            await uow.variants.save(variant)


class DeleteVariantHandler(VariantHandler):
    async def handle(self, command: DeleteVariant, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            variant = await self._load_variant(uow, command.variant_id)
            await uow.variants.delete(variant)
