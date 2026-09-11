from telegramsales.modules.catalog.contracts import (
    BrandId,
    CatalogId,
    CategoryId,
    ProductId,
)
from telegramsales.shared.domain.exceptions import DomainError
from telegramsales.shared.domain.money import Money


class EmptyTitleError(DomainError):
    def __init__(self) -> None:
        super().__init__("title must not be empty")


class TitleTooLongError(DomainError):
    def __init__(self, *, length: int, limit: int) -> None:
        super().__init__(
            f"title must be at most {limit} characters, got {length}",
            details={"length": length, "limit": limit},
        )


class NestingTooDeepError(DomainError):
    def __init__(self, *, category_id: CategoryId) -> None:
        super().__init__(
            f"category {category_id} is already nested and cannot hold children",
            details={"category_id": category_id},
        )


class ForeignCatalogError(DomainError):
    def __init__(self, *, category_id: CategoryId, catalog_id: CatalogId) -> None:
        super().__init__(
            f"category {category_id} does not belong to catalog {catalog_id}",
            details={"category_id": category_id, "catalog_id": catalog_id},
        )


class CatalogNotEmptyError(DomainError):
    def __init__(self, *, catalog_id: CatalogId, category_count: int) -> None:
        super().__init__(
            f"catalog {catalog_id} still holds {category_count} categories",
            details={"catalog_id": catalog_id, "category_count": category_count},
        )


class CategoryNotEmptyError(DomainError):
    def __init__(self, *, category_id: CategoryId, child_count: int) -> None:
        super().__init__(
            f"category {category_id} still holds {child_count} subcategories",
            details={"category_id": category_id, "child_count": child_count},
        )


class EmptyDescriptionError(DomainError):
    def __init__(self) -> None:
        super().__init__("description must not be empty")


class DescriptionTooLongError(DomainError):
    def __init__(self, *, length: int, limit: int) -> None:
        super().__init__(
            f"description must be at most {limit} characters, got {length}",
            details={"length": length, "limit": limit},
        )


class NonPositivePriceError(DomainError):
    def __init__(self) -> None:
        super().__init__("price must be greater than zero")


class PriceNotDiscountedError(DomainError):
    def __init__(self, *, price: Money, old_price: Money) -> None:
        super().__init__(
            f"old price {old_price} must be greater than price {price}",
            details={"price": str(price), "old_price": str(old_price)},
        )


class TooManyPhotosError(DomainError):
    def __init__(self, *, limit: int) -> None:
        super().__init__(
            f"a product holds at most {limit} photos",
            details={"limit": limit},
        )


class TooManyVideosError(DomainError):
    def __init__(self, *, limit: int) -> None:
        super().__init__(
            f"a product holds at most {limit} videos",
            details={"limit": limit},
        )


class VariantsNotAllowedError(DomainError):
    def __init__(self, *, product_id: ProductId) -> None:
        super().__init__(
            f"product {product_id} has no variant axis",
            details={"product_id": str(product_id)},
        )


class ProductWithoutPhotoError(DomainError):
    def __init__(self, *, product_id: ProductId) -> None:
        super().__init__(
            f"product {product_id} needs at least one photo to be published",
            details={"product_id": str(product_id)},
        )


class CategoryHoldsProductsError(DomainError):
    def __init__(self, *, category_id: CategoryId, product_count: int) -> None:
        super().__init__(
            f"category {category_id} still holds {product_count} products",
            details={"category_id": category_id, "product_count": product_count},
        )


class BrandInUseError(DomainError):
    def __init__(self, *, brand_id: BrandId, product_count: int) -> None:
        super().__init__(
            f"brand {brand_id} is used by {product_count} products",
            details={"brand_id": brand_id, "product_count": product_count},
        )
