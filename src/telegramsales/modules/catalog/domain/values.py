from dataclasses import dataclass
from typing import Self, override

from telegramsales.modules.catalog.domain.exceptions import (
    DescriptionTooLongError,
    EmptyDescriptionError,
    EmptyTitleError,
    TitleTooLongError,
)
from telegramsales.shared.domain.value_object import DomainValueObject

MAX_TITLE_LENGTH = 48
MAX_DESCRIPTION_LENGTH = 1024
ARTICLE_DIGITS = 6


@dataclass(frozen=True)
class Title(DomainValueObject):
    value: str

    def __post_init__(self) -> None:
        collapsed = " ".join(self.value.split())
        if not collapsed:
            raise EmptyTitleError
        if len(collapsed) > MAX_TITLE_LENGTH:
            raise TitleTooLongError(length=len(collapsed), limit=MAX_TITLE_LENGTH)
        object.__setattr__(self, "value", collapsed)

    @override
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Description(DomainValueObject):
    value: str

    def __post_init__(self) -> None:
        trimmed = self.value.strip()
        if not trimmed:
            raise EmptyDescriptionError
        if len(trimmed) > MAX_DESCRIPTION_LENGTH:
            raise DescriptionTooLongError(
                length=len(trimmed),
                limit=MAX_DESCRIPTION_LENGTH,
            )
        object.__setattr__(self, "value", trimmed)

    @override
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Article(DomainValueObject):
    value: str

    @classmethod
    def of(cls, number: int) -> Self:
        return cls(f"{number:0{ARTICLE_DIGITS}d}")

    @override
    def __str__(self) -> str:
        return self.value
