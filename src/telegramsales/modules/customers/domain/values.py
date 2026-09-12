from dataclasses import dataclass
from typing import override

from telegramsales.shared.domain.value_object import DomainValueObject

MAX_DISPLAY_NAME_LENGTH = 128
UNKNOWN_NAME = "без имени"


@dataclass(frozen=True)
class DisplayName(DomainValueObject):
    value: str

    def __post_init__(self) -> None:
        collapsed = " ".join(self.value.split()) or UNKNOWN_NAME
        object.__setattr__(self, "value", collapsed[:MAX_DISPLAY_NAME_LENGTH])

    @override
    def __str__(self) -> str:
        return self.value
