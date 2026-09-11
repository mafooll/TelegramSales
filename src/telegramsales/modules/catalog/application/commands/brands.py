from dataclasses import dataclass

from telegramsales.modules.catalog.application.access import ensure_can_manage
from telegramsales.modules.catalog.application.exceptions import (
    BrandNotFoundError,
    DuplicateTitleError,
)
from telegramsales.modules.catalog.application.ports import ICatalogUnitOfWork
from telegramsales.modules.catalog.contracts import BrandId
from telegramsales.modules.catalog.domain.entities import Brand
from telegramsales.modules.catalog.domain.values import Title
from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.clock import IClock


@dataclass(frozen=True, slots=True)
class CreateBrand:
    title: Title


@dataclass(frozen=True, slots=True)
class RenameBrand:
    brand_id: BrandId
    title: Title


@dataclass(frozen=True, slots=True)
class ChangeBrandVisibility:
    brand_id: BrandId
    is_visible: bool


@dataclass(frozen=True, slots=True)
class DeleteBrand:
    brand_id: BrandId


class CreateBrandHandler:
    def __init__(self, uow: ICatalogUnitOfWork, clock: IClock) -> None:
        self._uow: ICatalogUnitOfWork = uow
        self._clock: IClock = clock

    async def handle(self, command: CreateBrand, actor: Actor) -> BrandId:
        ensure_can_manage(actor)

        async with self._uow as uow:
            if await uow.brands.exists_with_title(command.title):
                raise DuplicateTitleError(title=command.title.value)

            brand = Brand.create(
                brand_id=await uow.brands.next_id(),
                title=command.title,
                now=self._clock.now(),
            )
            await uow.brands.add(brand)

        return brand.id


class RenameBrandHandler:
    def __init__(self, uow: ICatalogUnitOfWork) -> None:
        self._uow: ICatalogUnitOfWork = uow

    async def handle(self, command: RenameBrand, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            if not (brand := await uow.brands.get(command.brand_id)):
                raise BrandNotFoundError(brand_id=command.brand_id)

            taken = await uow.brands.exists_with_title(
                command.title,
                excluding=brand.id,
            )
            if taken:
                raise DuplicateTitleError(title=command.title.value)

            brand.rename(command.title)
            await uow.brands.save(brand)


class ChangeBrandVisibilityHandler:
    def __init__(self, uow: ICatalogUnitOfWork) -> None:
        self._uow: ICatalogUnitOfWork = uow

    async def handle(self, command: ChangeBrandVisibility, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            if not (brand := await uow.brands.get(command.brand_id)):
                raise BrandNotFoundError(brand_id=command.brand_id)

            if command.is_visible:
                brand.restore()
            else:
                brand.archive()
            await uow.brands.save(brand)


class DeleteBrandHandler:
    def __init__(self, uow: ICatalogUnitOfWork) -> None:
        self._uow: ICatalogUnitOfWork = uow

    async def handle(self, command: DeleteBrand, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            if not (brand := await uow.brands.get(command.brand_id)):
                raise BrandNotFoundError(brand_id=command.brand_id)

            await uow.brands.delete(brand)
