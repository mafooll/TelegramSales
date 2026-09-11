from typing import final

from dishka import (
    Provider,
    Scope,
    provide,  # pyright: ignore[reportUnknownVariableType]
    provide_all,
)
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.catalog.application.commands.brands import (
    ChangeBrandVisibilityHandler,
    CreateBrandHandler,
    DeleteBrandHandler,
    RenameBrandHandler,
)
from telegramsales.modules.catalog.application.commands.catalogs import (
    ChangeCatalogVisibilityHandler,
    CreateCatalogHandler,
    DeleteCatalogHandler,
    RenameCatalogHandler,
)
from telegramsales.modules.catalog.application.commands.categories import (
    ChangeCategoryVisibilityHandler,
    CreateCategoryHandler,
    DeleteCategoryHandler,
    RenameCategoryHandler,
)
from telegramsales.modules.catalog.application.ports import (
    ICatalogQueries,
    ICatalogUnitOfWork,
    IProductQueries,
)
from telegramsales.modules.catalog.infrastructure.queries import (
    CatalogQueries,
    ProductQueries,
)
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

    @provide
    def product_queries(self, session: AsyncSession) -> IProductQueries:
        return ProductQueries(session)

    handlers = provide_all(
        CreateCatalogHandler,
        RenameCatalogHandler,
        ChangeCatalogVisibilityHandler,
        DeleteCatalogHandler,
        CreateCategoryHandler,
        RenameCategoryHandler,
        ChangeCategoryVisibilityHandler,
        DeleteCategoryHandler,
        CreateBrandHandler,
        RenameBrandHandler,
        ChangeBrandVisibilityHandler,
        DeleteBrandHandler,
    )
