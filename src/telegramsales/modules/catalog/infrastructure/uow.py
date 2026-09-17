from telegramsales.modules.catalog.application.ports import (
    IBrandRepository,
    ICatalogRepository,
    ICategoryRepository,
    IProductMediaRepository,
    IProductRepository,
    IProductVariantRepository,
)
from telegramsales.modules.catalog.infrastructure.repositories import (
    BrandRepository,
    CatalogRepository,
    CategoryRepository,
    ProductMediaRepository,
    ProductRepository,
    ProductVariantRepository,
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

    @property
    def products(self) -> IProductRepository:
        return ProductRepository(self.session)

    @property
    def variants(self) -> IProductVariantRepository:
        return ProductVariantRepository(self.session)

    @property
    def media(self) -> IProductMediaRepository:
        return ProductMediaRepository(self.session)
