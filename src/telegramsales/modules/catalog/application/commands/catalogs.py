from dataclasses import dataclass

from telegramsales.modules.catalog.application.access import ensure_can_manage
from telegramsales.modules.catalog.application.exceptions import (
    CatalogNotFoundError,
    DuplicateTitleError,
)
from telegramsales.modules.catalog.application.ports import ICatalogUnitOfWork
from telegramsales.modules.catalog.contracts import CatalogId
from telegramsales.modules.catalog.domain.entities import Catalog
from telegramsales.modules.catalog.domain.services import ensure_catalog_is_empty
from telegramsales.modules.catalog.domain.values import Title
from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.clock import IClock


@dataclass(frozen=True, slots=True)
class CreateCatalog:
    title: Title


@dataclass(frozen=True, slots=True)
class RenameCatalog:
    catalog_id: CatalogId
    title: Title


@dataclass(frozen=True, slots=True)
class ChangeCatalogVisibility:
    catalog_id: CatalogId
    is_visible: bool


@dataclass(frozen=True, slots=True)
class DeleteCatalog:
    catalog_id: CatalogId


class CreateCatalogHandler:
    def __init__(self, uow: ICatalogUnitOfWork, clock: IClock) -> None:
        self._uow: ICatalogUnitOfWork = uow
        self._clock: IClock = clock

    async def handle(self, command: CreateCatalog, actor: Actor) -> CatalogId:
        ensure_can_manage(actor)

        async with self._uow as uow:
            if await uow.catalogs.exists_with_title(command.title):
                raise DuplicateTitleError(title=command.title.value)

            catalog = Catalog.create(
                catalog_id=await uow.catalogs.next_id(),
                title=command.title,
                now=self._clock.now(),
            )
            await uow.catalogs.add(catalog)

        return catalog.id


class RenameCatalogHandler:
    def __init__(self, uow: ICatalogUnitOfWork) -> None:
        self._uow: ICatalogUnitOfWork = uow

    async def handle(self, command: RenameCatalog, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            if not (catalog := await uow.catalogs.get(command.catalog_id)):
                raise CatalogNotFoundError(catalog_id=command.catalog_id)

            taken = await uow.catalogs.exists_with_title(
                command.title,
                excluding=catalog.id,
            )
            if taken:
                raise DuplicateTitleError(title=command.title.value)

            catalog.rename(command.title)
            await uow.catalogs.save(catalog)


class ChangeCatalogVisibilityHandler:
    def __init__(self, uow: ICatalogUnitOfWork) -> None:
        self._uow: ICatalogUnitOfWork = uow

    async def handle(self, command: ChangeCatalogVisibility, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            if not (catalog := await uow.catalogs.get(command.catalog_id)):
                raise CatalogNotFoundError(catalog_id=command.catalog_id)

            if command.is_visible:
                catalog.restore()
            else:
                catalog.archive()
            await uow.catalogs.save(catalog)


class DeleteCatalogHandler:
    def __init__(self, uow: ICatalogUnitOfWork) -> None:
        self._uow: ICatalogUnitOfWork = uow

    async def handle(self, command: DeleteCatalog, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            if not (catalog := await uow.catalogs.get(command.catalog_id)):
                raise CatalogNotFoundError(catalog_id=command.catalog_id)

            ensure_catalog_is_empty(
                catalog.id,
                await uow.categories.count_in_catalog(catalog.id),
                await uow.products.count_uncategorized(catalog.id),
            )

            await uow.catalogs.delete(catalog)
