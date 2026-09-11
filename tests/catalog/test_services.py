import pytest

from telegramsales.modules.catalog.domain.exceptions import (
    CatalogNotEmptyError,
    CategoryNotEmptyError,
    ForeignCatalogError,
    NestingTooDeepError,
)
from telegramsales.modules.catalog.domain.services import (
    ensure_can_hold_children,
    ensure_catalog_is_empty,
    ensure_category_is_empty,
)
from tests.catalog.factories import (
    BEAUTY,
    CLOTHES,
    COATS,
    OUTERWEAR,
    make_category,
)


def test_root_category_may_hold_children() -> None:
    ensure_can_hold_children(make_category(), CLOTHES)


def test_nested_category_may_not_hold_children() -> None:
    nested = make_category(COATS, "Пальто", parent_id=OUTERWEAR)

    with pytest.raises(NestingTooDeepError):
        ensure_can_hold_children(nested, CLOTHES)


def test_nesting_error_names_the_offending_category() -> None:
    nested = make_category(COATS, "Пальто", parent_id=OUTERWEAR)

    with pytest.raises(NestingTooDeepError) as exc_info:
        ensure_can_hold_children(nested, CLOTHES)

    assert exc_info.value.details == {"category_id": COATS}


def test_parent_from_another_catalog_is_rejected() -> None:
    with pytest.raises(ForeignCatalogError):
        ensure_can_hold_children(make_category(), BEAUTY)


def test_foreign_catalog_is_checked_before_nesting() -> None:
    nested = make_category(COATS, "Пальто", parent_id=OUTERWEAR)

    with pytest.raises(ForeignCatalogError):
        ensure_can_hold_children(nested, BEAUTY)


def test_empty_catalog_may_be_deleted() -> None:
    ensure_catalog_is_empty(CLOTHES, 0)


def test_catalog_with_categories_may_not_be_deleted() -> None:
    with pytest.raises(CatalogNotEmptyError):
        ensure_catalog_is_empty(CLOTHES, 3)


def test_catalog_error_reports_what_is_left() -> None:
    with pytest.raises(CatalogNotEmptyError) as exc_info:
        ensure_catalog_is_empty(CLOTHES, 3)

    assert exc_info.value.details == {"catalog_id": CLOTHES, "category_count": 3}


def test_empty_category_may_be_deleted() -> None:
    ensure_category_is_empty(make_category(), 0)


def test_category_with_children_may_not_be_deleted() -> None:
    with pytest.raises(CategoryNotEmptyError):
        ensure_category_is_empty(make_category(), 2)
