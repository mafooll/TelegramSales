from telegramsales.modules.catalog.contracts import (
    CatalogId,
    CategoryId,
)
from telegramsales.shared.domain.exceptions import DomainError


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
