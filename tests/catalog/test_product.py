import pytest

from telegramsales.modules.catalog.domain.exceptions import (
    DescriptionTooLongError,
    EmptyDescriptionError,
    NonPositivePriceError,
    PriceNotDiscountedError,
)
from telegramsales.modules.catalog.domain.values import (
    ARTICLE_DIGITS,
    MAX_DESCRIPTION_LENGTH,
    Article,
    Description,
    Title,
)
from tests.catalog.factories import NOW, make_product, rub


def test_article_is_padded_to_a_fixed_width() -> None:
    assert Article.of(42).value == "000042"


def test_article_width_matches_the_declared_one() -> None:
    assert len(Article.of(1).value) == ARTICLE_DIGITS


def test_long_numbers_outgrow_the_padding() -> None:
    assert Article.of(1234567).value == "1234567"


def test_description_keeps_its_paragraphs() -> None:
    assert Description("Первая строка.\n\nВторая.").value == (
        "Первая строка.\n\nВторая."
    )


def test_description_is_trimmed_at_the_ends() -> None:
    assert Description("  Тёплое пальто.  ").value == "Тёплое пальто."


@pytest.mark.parametrize("raw", ["", "   ", "\n\n"])
def test_blank_description_is_rejected(raw: str) -> None:
    with pytest.raises(EmptyDescriptionError):
        Description(raw)


def test_description_above_the_limit_is_rejected() -> None:
    with pytest.raises(DescriptionTooLongError):
        Description("я" * (MAX_DESCRIPTION_LENGTH + 1))


def test_new_product_is_not_published() -> None:
    product = make_product()

    assert not product.is_published
    assert product.published_at is None


def test_new_product_is_in_stock_and_visible() -> None:
    product = make_product()

    assert product.is_in_stock
    assert product.is_visible


def test_unpublished_product_is_not_offered() -> None:
    assert not make_product().is_offered


def test_published_product_is_offered() -> None:
    assert make_product(published=True).is_offered


def test_hidden_product_is_not_offered() -> None:
    product = make_product(published=True)
    product.hide()

    assert not product.is_offered


def test_publishing_records_the_moment() -> None:
    product = make_product()
    product.publish(NOW)

    assert product.published_at == NOW


def test_publishing_twice_keeps_the_first_moment() -> None:
    product = make_product(published=True)
    later = NOW.replace(year=NOW.year + 1)
    product.publish(later)

    assert product.published_at == NOW


def test_returning_from_hiding_does_not_republish() -> None:
    product = make_product(published=True)
    product.hide()
    later = NOW.replace(year=NOW.year + 1)
    product.publish(later)

    assert product.published_at == NOW
    assert product.is_visible


def test_running_out_keeps_the_product_offered() -> None:
    product = make_product(published=True)
    product.run_out()

    assert not product.is_in_stock
    assert product.is_offered


def test_restocking_brings_it_back() -> None:
    product = make_product()
    product.run_out()
    product.restock()

    assert product.is_in_stock


def test_product_without_an_old_price_is_not_on_sale() -> None:
    assert not make_product().is_on_sale


def test_old_price_above_the_price_makes_a_sale() -> None:
    product = make_product()
    product.reprice(rub("9900"), rub("12900"))

    assert product.is_on_sale
    assert product.price == rub("9900")


def test_old_price_below_the_price_is_rejected() -> None:
    product = make_product()

    with pytest.raises(PriceNotDiscountedError):
        product.reprice(rub("12900"), rub("9900"))


def test_old_price_equal_to_the_price_is_rejected() -> None:
    product = make_product()

    with pytest.raises(PriceNotDiscountedError):
        product.reprice(rub("9900"), rub("9900"))


def test_a_rejected_price_leaves_the_product_untouched() -> None:
    product = make_product(price="12900")

    with pytest.raises(PriceNotDiscountedError):
        product.reprice(rub("12900"), rub("9900"))

    assert product.price == rub("12900")
    assert product.old_price is None


def test_free_products_are_rejected() -> None:
    with pytest.raises(NonPositivePriceError):
        make_product(price="0")


def test_a_sale_can_be_called_off() -> None:
    product = make_product()
    product.reprice(rub("9900"), rub("12900"))
    product.reprice(rub("12900"))

    assert not product.is_on_sale


def test_product_has_no_variants_by_default() -> None:
    assert not make_product().has_variants


def test_opening_variants_names_the_axis() -> None:
    product = make_product(variant_label="Размер")

    assert product.has_variants
    assert product.variant_label == Title("Размер")


def test_variants_can_be_closed_again() -> None:
    product = make_product(variant_label="Размер")
    product.close_variants()

    assert not product.has_variants
