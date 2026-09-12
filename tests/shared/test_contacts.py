import pytest

from telegramsales.shared.domain.contacts import (
    MAX_ADDRESS_LENGTH,
    MAX_NAME_LENGTH,
    Address,
    AddressTooLongError,
    EmptyAddressError,
    EmptyNameError,
    MalformedPhoneError,
    NameTooLongError,
    PersonName,
    Phone,
)


def test_a_name_keeps_its_text() -> None:
    assert PersonName("Иван Петров").value == "Иван Петров"


def test_spaces_in_a_name_are_collapsed() -> None:
    assert PersonName("  Иван   Петров ").value == "Иван Петров"


def test_an_empty_name_is_rejected() -> None:
    with pytest.raises(EmptyNameError):
        PersonName("   ")


def test_a_long_name_is_rejected() -> None:
    with pytest.raises(NameTooLongError):
        PersonName("я" * (MAX_NAME_LENGTH + 1))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("+7 999 123-45-67", "+79991234567"),
        ("89991234567", "+89991234567"),
        ("(999) 123 45 67", "+9991234567"),
    ],
)
def test_a_phone_keeps_only_digits(raw: str, expected: str) -> None:
    assert Phone(raw).value == expected


@pytest.mark.parametrize("raw", ["", "123", "телефон", "+" + "9" * 16])
def test_a_malformed_phone_is_rejected(raw: str) -> None:
    with pytest.raises(MalformedPhoneError):
        Phone(raw)


def test_an_address_is_trimmed() -> None:
    assert Address(" Москва,  Тверская 1 ").value == "Москва, Тверская 1"


def test_an_empty_address_is_rejected() -> None:
    with pytest.raises(EmptyAddressError):
        Address(" ")


def test_a_long_address_is_rejected() -> None:
    with pytest.raises(AddressTooLongError):
        Address("я" * (MAX_ADDRESS_LENGTH + 1))


def test_equal_phones_are_one_value() -> None:
    assert Phone("+7 999 111 22 33") == Phone("79991112233")
