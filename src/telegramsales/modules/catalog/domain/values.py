from dataclasses import dataclass
from typing import override

from telegramsales.modules.catalog.domain.exceptions import (
    EmptyTitleError,
    TitleTooLongError,
)
from telegramsales.shared.domain.value_object import DomainValueObject

MAX_TITLE_LENGTH = 48


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
