from dataclasses import dataclass

from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
    MediaId,
    ProductId,
    VariantId,
)
from telegramsales.modules.catalog.domain.enums import MediaKind, MediaLayout
from telegramsales.shared.domain.money import Money


@dataclass(frozen=True, slots=True)
class CatalogView:
    id: CatalogId
    title: str
    is_active: bool
    category_count: int


@dataclass(frozen=True, slots=True)
class CategoryView:
    id: CategoryId
    catalog_id: CatalogId
    parent_id: CategoryId | None
    title: str
    is_active: bool
    child_count: int


@dataclass(frozen=True, slots=True)
class BrandView:
    id: BrandId
    title: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class ProductView:
    id: ProductId
    catalog_id: CatalogId
    category_id: CategoryId
    article: str
    title: str
    description: str
    price: Money
    old_price: Money | None
    brand_title: str | None
    variant_label: str | None
    is_published: bool
    is_visible: bool
    is_in_stock: bool
    photo_count: int
    video_count: int
    variant_count: int
    photo_ids: tuple[str, ...]
    video_id: str | None
    media_layout: MediaLayout


@dataclass(frozen=True, slots=True)
class ProductEntryView:
    id: ProductId
    title: str
    price: Money
    is_published: bool
    is_visible: bool
    is_in_stock: bool


@dataclass(frozen=True, slots=True)
class VariantView:
    id: VariantId
    title: str
    price: Money
    is_available: bool


@dataclass(frozen=True, slots=True)
class MediaView:
    id: MediaId
    kind: MediaKind
    file_id: str


@dataclass(frozen=True, slots=True)
class ShopCatalogView:
    id: CatalogId
    title: str


@dataclass(frozen=True, slots=True)
class ShopCategoryView:
    id: CategoryId
    catalog_id: CatalogId
    parent_id: CategoryId | None
    title: str
    catalog_title: str
    parent_title: str | None
    child_count: int
    product_count: int


@dataclass(frozen=True, slots=True)
class ShopVariantView:
    id: VariantId
    title: str
    price: Money


@dataclass(frozen=True, slots=True)
class ShopProductEntryView:
    id: ProductId
    title: str
    price: Money
    is_in_stock: bool
    thumbnail: str | None


@dataclass(frozen=True, slots=True)
class ShopProductView:
    id: ProductId
    catalog_id: CatalogId
    category_id: CategoryId
    article: str
    title: str
    description: str
    price: Money
    old_price: Money | None
    brand_title: str | None
    variant_label: str | None
    is_in_stock: bool
    photo_ids: tuple[str, ...]
    video_id: str | None
    media_layout: MediaLayout
    variants: tuple[ShopVariantView, ...]
