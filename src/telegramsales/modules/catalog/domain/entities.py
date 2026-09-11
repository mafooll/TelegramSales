from dataclasses import dataclass
from datetime import datetime
from typing import Self

from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
    MediaId,
    ProductId,
    VariantId,
)
from telegramsales.modules.catalog.domain.enums import MediaKind, MediaLayout
from telegramsales.modules.catalog.domain.pricing import (
    ensure_positive_price,
    ensure_sellable_price,
)
from telegramsales.modules.catalog.domain.values import Article, Description, Title
from telegramsales.shared.domain.entity import DomainEntity
from telegramsales.shared.domain.money import Money

DEFAULT_SORT_ORDER = 0


@dataclass(eq=False, kw_only=True)
class Catalog(DomainEntity[CatalogId]):
    title: Title
    created_at: datetime
    sort_order: int = DEFAULT_SORT_ORDER
    is_active: bool = True

    @classmethod
    def create(
        cls,
        *,
        catalog_id: CatalogId,
        title: Title,
        now: datetime,
    ) -> Self:
        return cls(id=catalog_id, title=title, created_at=now)

    def rename(self, title: Title) -> None:
        self.title = title

    def archive(self) -> None:
        self.is_active = False

    def restore(self) -> None:
        self.is_active = True


@dataclass(eq=False, kw_only=True)
class Category(DomainEntity[CategoryId]):
    catalog_id: CatalogId
    title: Title
    created_at: datetime
    parent_id: CategoryId | None = None
    sort_order: int = DEFAULT_SORT_ORDER
    is_active: bool = True

    @classmethod
    def create(
        cls,
        *,
        category_id: CategoryId,
        catalog_id: CatalogId,
        title: Title,
        now: datetime,
        parent_id: CategoryId | None = None,
    ) -> Self:
        return cls(
            id=category_id,
            catalog_id=catalog_id,
            title=title,
            created_at=now,
            parent_id=parent_id,
        )

    @property
    def is_root(self) -> bool:
        return self.parent_id is None

    def rename(self, title: Title) -> None:
        self.title = title

    def archive(self) -> None:
        self.is_active = False

    def restore(self) -> None:
        self.is_active = True


@dataclass(eq=False, kw_only=True)
class Brand(DomainEntity[BrandId]):
    title: Title
    created_at: datetime
    sort_order: int = DEFAULT_SORT_ORDER
    is_active: bool = True

    @classmethod
    def create(cls, *, brand_id: BrandId, title: Title, now: datetime) -> Self:
        return cls(id=brand_id, title=title, created_at=now)

    def rename(self, title: Title) -> None:
        self.title = title

    def archive(self) -> None:
        self.is_active = False

    def restore(self) -> None:
        self.is_active = True


@dataclass(eq=False, kw_only=True)
class Product(DomainEntity[ProductId]):
    catalog_id: CatalogId
    category_id: CategoryId
    title: Title
    description: Description
    article: Article
    price: Money
    created_at: datetime
    brand_id: BrandId | None = None
    old_price: Money | None = None
    variant_label: Title | None = None
    media_layout: MediaLayout = MediaLayout.COLLAGE
    published_at: datetime | None = None
    is_visible: bool = True
    is_in_stock: bool = True

    def __post_init__(self) -> None:
        ensure_sellable_price(self.price, self.old_price)

    @classmethod
    def create(  # noqa: PLR0913
        cls,
        *,
        product_id: ProductId,
        catalog_id: CatalogId,
        category_id: CategoryId,
        title: Title,
        description: Description,
        article: Article,
        price: Money,
        now: datetime,
        brand_id: BrandId | None = None,
    ) -> Self:
        return cls(
            id=product_id,
            catalog_id=catalog_id,
            category_id=category_id,
            title=title,
            description=description,
            article=article,
            price=price,
            created_at=now,
            brand_id=brand_id,
        )

    @property
    def is_published(self) -> bool:
        return self.published_at is not None

    @property
    def is_on_sale(self) -> bool:
        return self.old_price is not None

    @property
    def is_offered(self) -> bool:
        return self.is_published and self.is_visible

    @property
    def has_variants(self) -> bool:
        return self.variant_label is not None

    def rename(self, title: Title) -> None:
        self.title = title

    def describe(self, description: Description) -> None:
        self.description = description

    def move_to(self, catalog_id: CatalogId, category_id: CategoryId) -> None:
        self.catalog_id = catalog_id
        self.category_id = category_id

    def rebrand(self, brand_id: BrandId | None) -> None:
        self.brand_id = brand_id

    def reprice(self, price: Money, old_price: Money | None = None) -> None:
        ensure_sellable_price(price, old_price)
        self.price = price
        self.old_price = old_price

    def show_media_as(self, layout: MediaLayout) -> None:
        self.media_layout = layout

    def open_variants(self, label: Title) -> None:
        self.variant_label = label

    def close_variants(self) -> None:
        self.variant_label = None

    def publish(self, now: datetime) -> None:
        if self.published_at is None:
            self.published_at = now
        self.is_visible = True

    def hide(self) -> None:
        self.is_visible = False

    def show(self) -> None:
        self.is_visible = True

    def run_out(self) -> None:
        self.is_in_stock = False

    def restock(self) -> None:
        self.is_in_stock = True


@dataclass(eq=False, kw_only=True)
class ProductVariant(DomainEntity[VariantId]):
    product_id: ProductId
    title: Title
    position: int = DEFAULT_SORT_ORDER
    price_override: Money | None = None
    is_available: bool = True

    @classmethod
    def create(
        cls,
        *,
        variant_id: VariantId,
        product_id: ProductId,
        title: Title,
        position: int = DEFAULT_SORT_ORDER,
        price_override: Money | None = None,
    ) -> Self:
        return cls(
            id=variant_id,
            product_id=product_id,
            title=title,
            position=position,
            price_override=price_override,
        )

    def price_within(self, product: Product) -> Money:
        return self.price_override or product.price

    def rename(self, title: Title) -> None:
        self.title = title

    def reprice(self, price_override: Money | None) -> None:
        if price_override is not None:
            ensure_positive_price(price_override)
        self.price_override = price_override

    def run_out(self) -> None:
        self.is_available = False

    def restock(self) -> None:
        self.is_available = True


@dataclass(eq=False, kw_only=True)
class ProductMedia(DomainEntity[MediaId]):
    product_id: ProductId
    kind: MediaKind
    file_id: str
    position: int = DEFAULT_SORT_ORDER

    @classmethod
    def create(
        cls,
        *,
        media_id: MediaId,
        product_id: ProductId,
        kind: MediaKind,
        file_id: str,
        position: int = DEFAULT_SORT_ORDER,
    ) -> Self:
        return cls(
            id=media_id,
            product_id=product_id,
            kind=kind,
            file_id=file_id,
            position=position,
        )

    @property
    def is_photo(self) -> bool:
        return self.kind is MediaKind.PHOTO
