import pytest

from telegramsales.modules.catalog.domain.exceptions import (
    EmptyTitleError,
    TitleTooLongError,
)
from telegramsales.modules.catalog.domain.values import MAX_TITLE_LENGTH, Title


def test_title_keeps_its_text() -> None:
    assert Title("Верхняя одежда").value == "Верхняя одежда"


def test_title_renders_as_its_text() -> None:
    assert str(Title("Пуховики")) == "Пуховики"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Пуховики  ", "Пуховики"),
        ("Верхняя   одежда", "Верхняя одежда"),
        ("Уход\nза кожей", "Уход за кожей"),
        ("\tПлатья\t", "Платья"),
    ],
)
def test_surrounding_and_repeated_spaces_collapse(raw: str, expected: str) -> None:
    assert Title(raw).value == expected


@pytest.mark.parametrize("raw", ["", "   ", "\n", "\t\t"])
def test_blank_title_is_rejected(raw: str) -> None:
    with pytest.raises(EmptyTitleError):
        Title(raw)


def test_title_at_the_limit_is_accepted() -> None:
    assert len(Title("я" * MAX_TITLE_LENGTH).value) == MAX_TITLE_LENGTH


def test_title_above_the_limit_is_rejected() -> None:
    with pytest.raises(TitleTooLongError):
        Title("я" * (MAX_TITLE_LENGTH + 1))


def test_length_is_measured_after_collapsing() -> None:
    padded = "  " + "я" * MAX_TITLE_LENGTH + "  "

    assert len(Title(padded).value) == MAX_TITLE_LENGTH


def test_too_long_error_carries_both_numbers() -> None:
    with pytest.raises(TitleTooLongError) as exc_info:
        Title("я" * (MAX_TITLE_LENGTH + 5))

    assert exc_info.value.details == {
        "length": MAX_TITLE_LENGTH + 5,
        "limit": MAX_TITLE_LENGTH,
    }


def test_equal_titles_are_equal() -> None:
    assert Title("Платья") == Title("  Платья  ")
