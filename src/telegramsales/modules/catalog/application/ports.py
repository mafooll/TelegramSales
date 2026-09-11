from abc import ABC, abstractmethod
from types import TracebackType
from typing import Protocol, Self

from telegramsales.modules.catalog.application.queries import (
    BrandView,
    CatalogView,
    CategoryView,
    MediaView,
    ProductEntryView,
    ProductView,
    ShopCatalogView,
    ShopCategoryView,
    ShopProductEntryView,
    ShopProductView,
    VariantView,
)
from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
    MediaId,
    ProductId,
    VariantId,
)
from telegramsales.modules.catalog.domain.entities import (
    Brand,
    Catalog,
    Category,
    Product,
    ProductMedia,
    ProductVariant,
)
from telegramsales.modules.catalog.domain.enums import MediaKind
from telegramsales.modules.catalog.domain.values import Article, Title
from telegramsales.shared.application.pagination import Page
from telegramsales.shared.domain.event import DomainEvent, IEventSource


class ICatalogRepository(ABC):
    @abstractmethod
    async def next_id(self) -> CatalogId: ...

    @abstractmethod
    async def get(self, catalog_id: CatalogId) -> Catalog | None: ...

    @abstractmethod
    async def add(self, catalog: Catalog) -> None: ...

    @abstractmethod
    async def save(self, catalog: Catalog) -> None: ...

    @abstractmethod
    async def delete(self, catalog: Catalog) -> None: ...

    @abstractmethod
    async def exists_with_title(
        self,
        title: Title,
        *,
        excluding: CatalogId | None = None,
    ) -> bool: ...


class ICategoryRepository(ABC):
    @abstractmethod
    async def next_id(self) -> CategoryId: ...

    @abstractmethod
    async def get(self, category_id: CategoryId) -> Category | None: ...

    @abstractmethod
    async def add(self, category: Category) -> None: ...

    @abstractmethod
    async def save(self, category: Category) -> None: ...

    @abstractmethod
    async def delete(self, category: Category) -> None: ...

    @abstractmethod
    async def count_in_catalog(self, catalog_id: CatalogId) -> int: ...

    @abstractmethod
    async def count_children(self, category_id: CategoryId) -> int: ...

    @abstractmethod
    async def exists_with_title(
        self,
        title: Title,
        *,
        catalog_id: CatalogId,
        parent_id: CategoryId | None,
        excluding: CategoryId | None = None,
    ) -> bool: ...


class IBrandRepository(ABC):
    @abstractmethod
    async def next_id(self) -> BrandId: ...

    @abstractmethod
    async def get(self, brand_id: BrandId) -> Brand | None: ...

    @abstractmethod
    async def add(self, brand: Brand) -> None: ...

    @abstractmethod
    async def save(self, brand: Brand) -> None: ...

    @abstractmethod
    async def delete(self, brand: Brand) -> None: ...

    @abstractmethod
    async def exists_with_title(
        self,
        title: Title,
        *,
        excluding: BrandId | None = None,
    ) -> bool: ...


class IProductRepository(ABC):
    @abstractmethod
    async def next_id(self) -> ProductId: ...

    @abstractmethod
    async def next_article(self) -> Article: ...

    @abstractmethod
    async def get(self, product_id: ProductId) -> Product | None: ...

    @abstractmethod
    async def add(self, product: Product) -> None: ...

    @abstractmethod
    async def save(self, product: Product) -> None: ...

    @abstractmethod
    async def delete(self, product: Product) -> None: ...

    @abstractmethod
    async def count_in_category(self, category_id: CategoryId) -> int: ...

    @abstractmethod
    async def count_of_brand(self, brand_id: BrandId) -> int: ...


class IProductVariantRepository(ABC):
    @abstractmethod
    async def next_id(self) -> VariantId: ...

    @abstractmethod
    async def get(self, variant_id: VariantId) -> ProductVariant | None: ...

    @abstractmethod
    async def add(self, variant: ProductVariant) -> None: ...

    @abstractmethod
    async def save(self, variant: ProductVariant) -> None: ...

    @abstractmethod
    async def delete(self, variant: ProductVariant) -> None: ...

    @abstractmethod
    async def count_for(self, product_id: ProductId) -> int: ...

    @abstractmethod
    async def exists_with_title(
        self,
        title: Title,
        *,
        product_id: ProductId,
        excluding: VariantId | None = None,
    ) -> bool: ...


class IProductMediaRepository(ABC):
    @abstractmethod
    async def next_id(self) -> MediaId: ...

    @abstractmethod
    async def get(self, media_id: MediaId) -> ProductMedia | None: ...

    @abstractmethod
    async def add(self, media: ProductMedia) -> None: ...

    @abstractmethod
    async def delete(self, media: ProductMedia) -> None: ...

    @abstractmethod
    async def count_of_kind(self, product_id: ProductId, kind: MediaKind) -> int: ...


class ICatalogUnitOfWork(Protocol):
    @property
    def catalogs(self) -> ICatalogRepository: ...

    @property
    def categories(self) -> ICategoryRepository: ...

    @property
    def brands(self) -> IBrandRepository: ...

    @property
    def products(self) -> IProductRepository: ...

    @property
    def variants(self) -> IProductVariantRepository: ...

    @property
    def media(self) -> IProductMediaRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None: ...

    def track(self, entity: IEventSource) -> None: ...

    def collect_events(self) -> list[DomainEvent]: ...


class ICatalogQueries(ABC):
    @abstractmethod
    async def get_catalog(self, catalog_id: CatalogId) -> CatalogView | None: ...

    @abstractmethod
    async def list_catalogs(self, number: int, size: int) -> Page[CatalogView]: ...

    @abstractmethod
    async def get_category(self, category_id: CategoryId) -> CategoryView | None: ...

    @abstractmethod
    async def list_categories(
        self,
        catalog_id: CatalogId,
        parent_id: CategoryId | None,
        number: int,
        size: int,
    ) -> Page[CategoryView]: ...

    @abstractmethod
    async def get_brand(self, brand_id: BrandId) -> BrandView | None: ...

    @abstractmethod
    async def list_brands(self, number: int, size: int) -> Page[BrandView]: ...


class IProductQueries(ABC):
    @abstractmethod
    async def get_product(self, product_id: ProductId) -> ProductView | None: ...

    @abstractmethod
    async def list_products(
        self,
        category_id: CategoryId,
        number: int,
        size: int,
    ) -> Page[ProductEntryView]: ...

    @abstractmethod
    async def list_variants(self, product_id: ProductId) -> list[VariantView]: ...

    @abstractmethod
    async def list_media(self, product_id: ProductId) -> list[MediaView]: ...

    @abstractmethod
    async def product_of_media(self, media_id: MediaId) -> ProductId | None: ...

    @abstractmethod
    async def product_of_variant(
        self,
        variant_id: VariantId,
    ) -> ProductId | None: ...


class IShopQueries(ABC):
    @abstractmethod
    async def list_catalogs(
        self,
        number: int,
        size: int,
    ) -> Page[ShopCatalogView]: ...

    @abstractmethod
    async def get_catalog(self, catalog_id: CatalogId) -> ShopCatalogView | None: ...

    @abstractmethod
    async def get_category(
        self,
        category_id: CategoryId,
    ) -> ShopCategoryView | None: ...

    @abstractmethod
    async def list_categories(
        self,
        catalog_id: CatalogId,
        parent_id: CategoryId | None,
        number: int,
        size: int,
    ) -> Page[ShopCategoryView]: ...

    @abstractmethod
    async def list_products(
        self,
        category_id: CategoryId,
        number: int,
        size: int,
    ) -> Page[ShopProductEntryView]: ...

    @abstractmethod
    async def get_product(self, product_id: ProductId) -> ShopProductView | None: ...
