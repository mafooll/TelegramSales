from typing import final

from dishka import (
    Provider,
    Scope,
    provide,  # pyright: ignore[reportUnknownVariableType]
)
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.catalog.application.ports import (
    ICatalogQueries,
    ICatalogUnitOfWork,
)
from telegramsales.modules.catalog.infrastructure.queries import CatalogQueries
from telegramsales.modules.catalog.infrastructure.uow import CatalogUnitOfWork
from telegramsales.shared.infrastructure.database.manager import DatabaseManager


@final
class CatalogProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def unit_of_work(self, manager: DatabaseManager) -> ICatalogUnitOfWork:
        return CatalogUnitOfWork(manager.session)

    @provide
    def queries(self, session: AsyncSession) -> ICatalogQueries:
        return CatalogQueries(session)
