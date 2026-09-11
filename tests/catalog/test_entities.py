from telegramsales.modules.catalog.domain.values import Title
from tests.catalog.factories import (
    BEAUTY,
    CLOTHES,
    COATS,
    NOW,
    OUTERWEAR,
    make_brand,
    make_catalog,
    make_category,
)


def test_new_catalog_is_active() -> None:
    assert make_catalog().is_active


def test_new_catalog_remembers_when_it_appeared() -> None:
    assert make_catalog().created_at == NOW


def test_catalog_can_be_renamed() -> None:
    catalog = make_catalog()
    catalog.rename(Title("Женская одежда"))

    assert catalog.title == Title("Женская одежда")


def test_archived_catalog_is_inactive() -> None:
    catalog = make_catalog()
    catalog.archive()

    assert not catalog.is_active


def test_archiving_twice_changes_nothing() -> None:
    catalog = make_catalog()
    catalog.archive()
    catalog.archive()

    assert not catalog.is_active


def test_restored_catalog_is_active_again() -> None:
    catalog = make_catalog()
    catalog.archive()
    catalog.restore()

    assert catalog.is_active


def test_catalogs_with_the_same_id_are_equal() -> None:
    assert make_catalog(title="Одежда") == make_catalog(title="Обувь")


def test_catalogs_with_different_ids_differ() -> None:
    assert make_catalog(CLOTHES) != make_catalog(BEAUTY)


def test_category_without_a_parent_is_root() -> None:
    assert make_category().is_root


def test_category_with_a_parent_is_not_root() -> None:
    nested = make_category(COATS, "Пальто", parent_id=OUTERWEAR)

    assert not nested.is_root


def test_category_belongs_to_its_catalog() -> None:
    assert make_category().catalog_id == CLOTHES


def test_category_can_be_renamed() -> None:
    category = make_category()
    category.rename(Title("Пальто и куртки"))

    assert category.title == Title("Пальто и куртки")


def test_archived_category_is_inactive() -> None:
    category = make_category()
    category.archive()

    assert not category.is_active


def test_restored_category_is_active_again() -> None:
    category = make_category()
    category.archive()
    category.restore()

    assert category.is_active


def test_new_brand_is_active() -> None:
    assert make_brand().is_active


def test_brand_can_be_renamed() -> None:
    brand = make_brand()
    brand.rename(Title("Acme Wear"))

    assert brand.title == Title("Acme Wear")


def test_archived_brand_is_inactive() -> None:
    brand = make_brand()
    brand.archive()

    assert not brand.is_active


def test_a_catalog_and_a_category_with_the_same_number_are_not_equal() -> None:
    assert make_catalog() != make_category()
