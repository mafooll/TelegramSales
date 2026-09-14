from telegramsales.modules.catalog.contracts import CatalogId
from telegramsales.modules.catalog.domain.entities import Brand, Category, Product
from telegramsales.modules.catalog.domain.exceptions import (
    BrandInUseError,
    CatalogHoldsCategoriesError,
    CatalogHoldsProductsError,
    CatalogNotEmptyError,
    CategoryHoldsProductsError,
    CategoryNotEmptyError,
    ForeignCatalogError,
    NestingTooDeepError,
    ProductWithoutPhotoError,
    TooManyPhotosError,
    TooManyVideosError,
    VariantsNotAllowedError,
)

EMPTY = 0
MAX_PHOTOS = 10
MAX_VIDEOS = 1


def ensure_can_hold_children(parent: Category, catalog_id: CatalogId) -> None:
    if parent.catalog_id != catalog_id:
        raise ForeignCatalogError(category_id=parent.id, catalog_id=catalog_id)
    if not parent.is_root:
        raise NestingTooDeepError(category_id=parent.id)


def ensure_catalog_is_empty(catalog_id: CatalogId, category_count: int) -> None:
    if category_count > EMPTY:
        raise CatalogNotEmptyError(
            catalog_id=catalog_id,
            category_count=category_count,
        )


def ensure_catalog_takes_categories(
    catalog_id: CatalogId,
    product_count: int,
) -> None:
    if product_count > EMPTY:
        raise CatalogHoldsProductsError(
            catalog_id=catalog_id,
            product_count=product_count,
        )


def ensure_catalog_takes_products(
    catalog_id: CatalogId,
    category_count: int,
) -> None:
    if category_count > EMPTY:
        raise CatalogHoldsCategoriesError(
            catalog_id=catalog_id,
            category_count=category_count,
        )


def ensure_category_is_empty(
    category: Category,
    child_count: int,
    product_count: int = EMPTY,
) -> None:
    if child_count > EMPTY:
        raise CategoryNotEmptyError(
            category_id=category.id,
            child_count=child_count,
        )
    if product_count > EMPTY:
        raise CategoryHoldsProductsError(
            category_id=category.id,
            product_count=product_count,
        )


def ensure_brand_is_unused(brand: Brand, product_count: int) -> None:
    if product_count > EMPTY:
        raise BrandInUseError(brand_id=brand.id, product_count=product_count)


def ensure_variants_allowed(product: Product) -> None:
    if not product.has_variants:
        raise VariantsNotAllowedError(product_id=product.id)


def ensure_photo_fits(photo_count: int) -> None:
    if photo_count >= MAX_PHOTOS:
        raise TooManyPhotosError(limit=MAX_PHOTOS)


def ensure_video_fits(video_count: int) -> None:
    if video_count >= MAX_VIDEOS:
        raise TooManyVideosError(limit=MAX_VIDEOS)


def ensure_can_be_published(product: Product, photo_count: int) -> None:
    if photo_count == EMPTY:
        raise ProductWithoutPhotoError(product_id=product.id)


def ensure_category_fits(product_category: Category, catalog_id: CatalogId) -> None:
    if product_category.catalog_id != catalog_id:
        raise ForeignCatalogError(
            category_id=product_category.id,
            catalog_id=catalog_id,
        )
