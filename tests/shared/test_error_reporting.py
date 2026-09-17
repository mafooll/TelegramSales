from telegramsales.modules.catalog.domain.exceptions import (
    CategoryHoldsProductsError,
    ProductWithoutBrandError,
    ProductWithoutPhotoError,
)
from telegramsales.modules.catalog.presentation.bot.errors import CATALOG_ERRORS
from telegramsales.shared.domain.exceptions import DomainError
from telegramsales.shared.infrastructure.i18n.fluent import FluentTranslations
from telegramsales.shared.presentation.bot.errors import error_text
from telegramsales.shared.settings import LOCALES_PATH
from tests.catalog.factories import COAT, OUTERWEAR

DEFAULT_LOCALE = "ru"
TRANSLATE = FluentTranslations(LOCALES_PATH, DEFAULT_LOCALE)(DEFAULT_LOCALE)
UNKNOWN = "что-то своё"


def told(error: Exception) -> str:
    return error_text(error, CATALOG_ERRORS, TRANSLATE)


def test_a_known_error_speaks_russian() -> None:
    said = told(ProductWithoutPhotoError(product_id=COAT))

    assert said == "Нельзя опубликовать без фотографии. Добавьте хотя бы одну."


def test_the_message_carries_no_identifiers() -> None:
    said = told(ProductWithoutPhotoError(product_id=COAT))

    assert str(COAT) not in said


def test_every_known_error_has_its_own_words() -> None:
    photo = told(ProductWithoutPhotoError(product_id=COAT))
    brand = told(ProductWithoutBrandError(product_id=COAT))

    assert photo != brand


def test_a_category_refusal_tells_what_to_do() -> None:
    said = told(
        CategoryHoldsProductsError(category_id=OUTERWEAR, product_count=3)
    )

    assert "товары" in said


def test_an_unknown_error_falls_back_to_a_neutral_line() -> None:
    said = told(DomainError(UNKNOWN))

    assert said == "Так нельзя. Проверьте условия и попробуйте ещё раз."
    assert UNKNOWN not in said


def test_every_mapped_key_is_translated() -> None:
    for key in CATALOG_ERRORS.values():
        assert TRANSLATE(key) != key
