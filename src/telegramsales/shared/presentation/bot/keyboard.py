from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum

from aiogram.enums import ButtonStyle
from aiogram.filters.callback_data import CallbackData

from telegramsales.shared.application.access import Actor

MAX_BUTTONS_PER_ROW = 8


class RowWidthError(ValueError):
    def __init__(self, *, row_width: int) -> None:
        super().__init__(
            f"row width must be between 1 and {MAX_BUTTONS_PER_ROW}, got {row_width}"
        )


@dataclass(frozen=True, slots=True)
class Button[ViewType]:
    text: str | Callable[[ViewType], str]
    callback: Callable[[ViewType], CallbackData]
    permission: StrEnum | None = None
    when: Callable[[ViewType], bool] | None = None
    style: ButtonStyle | None = None

    def is_allowed(self, view: ViewType, actor: Actor) -> bool:
        if self.permission is not None and not actor.can(self.permission):
            return False
        return self.when is None or self.when(view)

    def render(self, view: ViewType) -> str:
        return self.text(view) if callable(self.text) else self.text


def check_row_width(row_width: int) -> None:
    if not 1 <= row_width <= MAX_BUTTONS_PER_ROW:
        raise RowWidthError(row_width=row_width)


@dataclass(frozen=True, slots=True)
class Screen[ViewType]:
    buttons: Sequence[Button[ViewType]]
    row_width: int = 1

    def __post_init__(self) -> None:
        check_row_width(self.row_width)


@dataclass(frozen=True, slots=True)
class ListScreen[ItemType, ViewType]:
    item: Button[ItemType]
    footer: Screen[ViewType]
    row_width: int = 1

    def __post_init__(self) -> None:
        check_row_width(self.row_width)
