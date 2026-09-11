from telegramsales.modules.catalog.application.ports import (
    IBrandRepository,
    ICatalogRepository,
    ICategoryRepository,
)
from telegramsales.modules.catalog.infrastructure.repositories import (
    BrandRepository,
    CatalogRepository,
    CategoryRepository,
)
from telegramsales.shared.infrastructure.database.uow import UnitOfWork


class CatalogUnitOfWork(UnitOfWork):
    @property
    def catalogs(self) -> ICatalogRepository:
        return CatalogRepository(self.session)

    @property
    def categories(self) -> ICategoryRepository:
        return CategoryRepository(self.session)

    @property
    def brands(self) -> IBrandRepository:
        return BrandRepository(self.session)
