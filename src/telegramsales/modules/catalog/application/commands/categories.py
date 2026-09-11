from dataclasses import dataclass

from telegramsales.modules.catalog.application.access import ensure_can_manage
from telegramsales.modules.catalog.application.exceptions import (
    CatalogNotFoundError,
    CategoryNotFoundError,
    DuplicateTitleError,
)
from telegramsales.modules.catalog.application.ports import ICatalogUnitOfWork
from telegramsales.modules.catalog.contracts import CatalogId, CategoryId
from telegramsales.modules.catalog.domain.entities import Category
from telegramsales.modules.catalog.domain.services import (
    ensure_can_hold_children,
    ensure_category_is_empty,
)
from telegramsales.modules.catalog.domain.values import Title
from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.clock import IClock


@dataclass(frozen=True, slots=True)
class CreateCategory:
    catalog_id: CatalogId
    title: Title
    parent_id: CategoryId | None = None


@dataclass(frozen=True, slots=True)
class RenameCategory:
    category_id: CategoryId
    title: Title


@dataclass(frozen=True, slots=True)
class ChangeCategoryVisibility:
    category_id: CategoryId
    is_visible: bool


@dataclass(frozen=True, slots=True)
class DeleteCategory:
    category_id: CategoryId


class CreateCategoryHandler:
    def __init__(self, uow: ICatalogUnitOfWork, clock: IClock) -> None:
        self._uow: ICatalogUnitOfWork = uow
        self._clock: IClock = clock

    async def handle(self, command: CreateCategory, actor: Actor) -> CategoryId:
        ensure_can_manage(actor)

        async with self._uow as uow:
            if not await uow.catalogs.get(command.catalog_id):
                raise CatalogNotFoundError(catalog_id=command.catalog_id)

            if command.parent_id is not None:
                parent = await uow.categories.get(command.parent_id)
                if parent is None:
                    raise CategoryNotFoundError(category_id=command.parent_id)
                ensure_can_hold_children(parent, command.catalog_id)

            taken = await uow.categories.exists_with_title(
                command.title,
                catalog_id=command.catalog_id,
                parent_id=command.parent_id,
            )
            if taken:
                raise DuplicateTitleError(title=command.title.value)

            category = Category.create(
                category_id=await uow.categories.next_id(),
                catalog_id=command.catalog_id,
                title=command.title,
                now=self._clock.now(),
                parent_id=command.parent_id,
            )
            await uow.categories.add(category)

        return category.id


class RenameCategoryHandler:
    def __init__(self, uow: ICatalogUnitOfWork) -> None:
        self._uow: ICatalogUnitOfWork = uow

    async def handle(self, command: RenameCategory, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            if not (category := await uow.categories.get(command.category_id)):
                raise CategoryNotFoundError(category_id=command.category_id)

            taken = await uow.categories.exists_with_title(
                command.title,
                catalog_id=category.catalog_id,
                parent_id=category.parent_id,
                excluding=category.id,
            )
            if taken:
                raise DuplicateTitleError(title=command.title.value)

            category.rename(command.title)
            await uow.categories.save(category)


class ChangeCategoryVisibilityHandler:
    def __init__(self, uow: ICatalogUnitOfWork) -> None:
        self._uow: ICatalogUnitOfWork = uow

    async def handle(self, command: ChangeCategoryVisibility, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            if not (category := await uow.categories.get(command.category_id)):
                raise CategoryNotFoundError(category_id=command.category_id)

            if command.is_visible:
                category.restore()
            else:
                category.archive()
            await uow.categories.save(category)


class DeleteCategoryHandler:
    def __init__(self, uow: ICatalogUnitOfWork) -> None:
        self._uow: ICatalogUnitOfWork = uow

    async def handle(self, command: DeleteCategory, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            if not (category := await uow.categories.get(command.category_id)):
                raise CategoryNotFoundError(category_id=command.category_id)

            children = await uow.categories.count_children(category.id)
            products = await uow.products.count_in_category(category.id)
            ensure_category_is_empty(category, children, products)

            await uow.categories.delete(category)
