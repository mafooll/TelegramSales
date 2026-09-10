import pytest

from telegramsales.shared.application.pagination import Page


def page(number: int, total: int, size: int = 3) -> Page[int]:
    return Page(items=[], number=number, size=size, total=total)


@pytest.mark.parametrize(
    ("total", "size", "expected"),
    [(0, 3, 1), (1, 3, 1), (3, 3, 1), (4, 3, 2), (9, 3, 3), (10, 3, 4)],
)
def test_total_pages_is_rounded_up(total: int, size: int, expected: int) -> None:
    assert page(0, total, size).total_pages == expected


def test_an_empty_result_is_still_one_page() -> None:
    assert page(0, 0).is_single


def test_a_page_is_single_when_everything_fits() -> None:
    assert page(0, 3).is_single


def test_a_page_is_not_single_when_it_overflows() -> None:
    assert not page(0, 4).is_single


def test_the_first_page_has_nothing_before_it() -> None:
    assert not page(0, 9).has_previous


def test_a_later_page_has_something_before_it() -> None:
    assert page(1, 9).has_previous


def test_the_last_page_has_nothing_after_it() -> None:
    assert not page(2, 9).has_next


def test_an_earlier_page_has_something_after_it() -> None:
    assert page(1, 9).has_next


def test_a_page_beyond_the_last_one_has_nothing_after_it() -> None:
    assert not page(7, 9).has_next


@pytest.mark.parametrize(("number", "expected"), [(0, 0), (1, 3), (4, 12)])
def test_offset_skips_the_preceding_pages(number: int, expected: int) -> None:
    assert page(number, 99).offset == expected
