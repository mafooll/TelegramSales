from dataclasses import dataclass
from typing import override

from telegramsales.shared.domain.exceptions import DomainError
from telegramsales.shared.domain.value_object import DomainValueObject

MAX_NAME_LENGTH = 64
MAX_ADDRESS_LENGTH = 256
MIN_PHONE_DIGITS = 5
MAX_PHONE_DIGITS = 15
PHONE_PREFIX = "+"


class EmptyNameError(DomainError):
    def __init__(self) -> None:
        super().__init__("contact name must not be empty")


class NameTooLongError(DomainError):
    def __init__(self, *, length: int, limit: int) -> None:
        super().__init__(
            f"contact name is {length} characters long, limit is {limit}",
            details={"length": length, "limit": limit},
        )


class MalformedPhoneError(DomainError):
    def __init__(self, *, value: str) -> None:
        super().__init__(
            f"{value} does not look like a phone number",
            details={"value": value},
        )


class EmptyAddressError(DomainError):
    def __init__(self) -> None:
        super().__init__("address must not be empty")


class AddressTooLongError(DomainError):
    def __init__(self, *, length: int, limit: int) -> None:
        super().__init__(
            f"address is {length} characters long, limit is {limit}",
            details={"length": length, "limit": limit},
        )


@dataclass(frozen=True)
class PersonName(DomainValueObject):
    value: str

    def __post_init__(self) -> None:
        collapsed = " ".join(self.value.split())
        if not collapsed:
            raise EmptyNameError
        if len(collapsed) > MAX_NAME_LENGTH:
            raise NameTooLongError(length=len(collapsed), limit=MAX_NAME_LENGTH)
        object.__setattr__(self, "value", collapsed)

    @override
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Phone(DomainValueObject):
    value: str

    def __post_init__(self) -> None:
        digits = "".join(
            character for character in self.value if character.isdigit()
        )
        if not MIN_PHONE_DIGITS <= len(digits) <= MAX_PHONE_DIGITS:
            raise MalformedPhoneError(value=self.value)
        object.__setattr__(self, "value", PHONE_PREFIX + digits)

    @override
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Address(DomainValueObject):
    value: str

    def __post_init__(self) -> None:
        trimmed = " ".join(self.value.split())
        if not trimmed:
            raise EmptyAddressError
        if len(trimmed) > MAX_ADDRESS_LENGTH:
            raise AddressTooLongError(
                length=len(trimmed),
                limit=MAX_ADDRESS_LENGTH,
            )
        object.__setattr__(self, "value", trimmed)

    @override
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Contacts(DomainValueObject):
    name: PersonName
    phone: Phone
    address: Address
