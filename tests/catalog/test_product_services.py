import pytest

from telegramsales.modules.catalog.domain.enums import MediaKind
from telegramsales.modules.catalog.domain.exceptions import (
    ForeignCatalogError,
    NonPositivePriceError,
    ProductWithoutPhotoError,
    TooManyPhotosError,
    TooManyVideosError,
    VariantsNotAllowedError,
)
from telegramsales.modules.catalog.domain.services import (
    MAX_PHOTOS,
    MAX_VIDEOS,
    ensure_can_be_published,
    ensure_category_fits,
    ensure_photo_fits,
    ensure_variants_allowed,
    ensure_video_fits,
)
from tests.catalog.factories import (
    BEAUTY,
    CLOTHES,
    make_category,
    make_media,
    make_product,
    make_variant,
    rub,
)


def test_variants_need_an_axis() -> None:
    with pytest.raises(VariantsNotAllowedError):
        ensure_variants_allowed(make_product())


def test_a_product_with_an_axis_accepts_variants() -> None:
    ensure_variants_allowed(make_product(variant_label="Размер"))


def test_photos_fit_up_to_the_limit() -> None:
    ensure_photo_fits(MAX_PHOTOS - 1)


def test_the_photo_above_the_limit_is_rejected() -> None:
    with pytest.raises(TooManyPhotosError):
        ensure_photo_fits(MAX_PHOTOS)


def test_the_second_video_is_rejected() -> None:
    with pytest.raises(TooManyVideosError):
        ensure_video_fits(MAX_VIDEOS)


def test_the_first_video_fits() -> None:
    ensure_video_fits(0)


def test_a_product_without_photos_cannot_be_published() -> None:
    with pytest.raises(ProductWithoutPhotoError):
        ensure_can_be_published(make_product(), 0)


def test_a_single_photo_is_enough_to_publish() -> None:
    ensure_can_be_published(make_product(), 1)


def test_category_of_the_same_catalog_fits() -> None:
    ensure_category_fits(make_category(), CLOTHES)


def test_category_of_another_catalog_is_rejected() -> None:
    with pytest.raises(ForeignCatalogError):
        ensure_category_fits(make_category(), BEAUTY)


def test_variant_falls_back_to_the_product_price() -> None:
    product = make_product(price="12900", variant_label="Размер")

    assert make_variant().price_within(product) == rub("12900")


def test_variant_price_wins_when_set() -> None:
    product = make_product(price="12900", variant_label="Размер")
    variant = make_variant(price_override="14900")

    assert variant.price_within(product) == rub("14900")


def test_a_free_variant_price_is_rejected() -> None:
    variant = make_variant()

    with pytest.raises(NonPositivePriceError):
        variant.reprice(rub("0"))


def test_a_variant_price_can_be_dropped() -> None:
    variant = make_variant(price_override="14900")
    variant.reprice(None)

    assert variant.price_override is None


def test_new_variant_is_available() -> None:
    assert make_variant().is_available


def test_a_variant_can_run_out_alone() -> None:
    variant = make_variant()
    variant.run_out()

    assert not variant.is_available


def test_photo_knows_it_is_a_photo() -> None:
    assert make_media().is_photo


def test_video_is_not_a_photo() -> None:
    assert not make_media(kind=MediaKind.VIDEO).is_photo


def test_media_belongs_to_its_product() -> None:
    assert make_media().product_id == make_product().id
