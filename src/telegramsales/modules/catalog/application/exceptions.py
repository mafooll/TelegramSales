from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
    MediaId,
    ProductId,
    VariantId,
)
from telegramsales.shared.domain.exceptions import ApplicationError


class CatalogNotFoundError(ApplicationError):
    def __init__(self, *, catalog_id: CatalogId) -> None:
        super().__init__(
            f"catalog {catalog_id} is not found",
            details={"catalog_id": catalog_id},
        )


class CategoryNotFoundError(ApplicationError):
    def __init__(self, *, category_id: CategoryId) -> None:
        super().__init__(
            f"category {category_id} is not found",
            details={"category_id": category_id},
        )


class BrandNotFoundError(ApplicationError):
    def __init__(self, *, brand_id: BrandId) -> None:
        super().__init__(
            f"brand {brand_id} is not found",
            details={"brand_id": brand_id},
        )


class DuplicateTitleError(ApplicationError):
    def __init__(self, *, title: str) -> None:
        super().__init__(
            f"title {title} is already taken",
            details={"title": title},
        )


class ProductNotFoundError(ApplicationError):
    def __init__(self, *, product_id: ProductId) -> None:
        super().__init__(
            f"product {product_id} is not found",
            details={"product_id": str(product_id)},
        )


class VariantNotFoundError(ApplicationError):
    def __init__(self, *, variant_id: VariantId) -> None:
        super().__init__(
            f"variant {variant_id} is not found",
            details={"variant_id": variant_id},
        )


class MediaNotFoundError(ApplicationError):
    def __init__(self, *, media_id: MediaId) -> None:
        super().__init__(
            f"media {media_id} is not found",
            details={"media_id": media_id},
        )
