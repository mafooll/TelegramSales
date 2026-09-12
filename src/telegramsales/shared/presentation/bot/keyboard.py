from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

from aiogram.enums import ButtonStyle
from aiogram.filters.callback_data import CallbackData

from telegramsales.shared.application.i18n import ITranslator, TranslationArgs
from telegramsales.shared.presentation.bot.content import Content
from telegramsales.shared.presentation.bot.context import RenderContext

MAX_BUTTONS_PER_ROW = 8

type TextArgs[ViewType] = Callable[[ViewType], Mapping[str, TranslationArgs]]
type TextRef[ViewType] = Callable[[ViewType, ITranslator], str]
type ContentRef[ViewType] = Callable[[ViewType, ITranslator], Content]


class RowWidthError(ValueError):
    def __init__(self, *, row_width: int) -> None:
        super().__init__(
            f"row width must be between 1 and {MAX_BUTTONS_PER_ROW}, got {row_width}"
        )


def check_row_width(row_width: int) -> None:
    if not 1 <= row_width <= MAX_BUTTONS_PER_ROW:
        raise RowWidthError(row_width=row_width)


def label[ViewType](
    key: str,
    args: TextArgs[ViewType] | None = None,
) -> TextRef[ViewType]:
    def render(view: ViewType, translate: ITranslator) -> str:
        return translate(key) if args is None else translate(key, **args(view))

    return render


@dataclass(frozen=True, slots=True)
class Button[ViewType]:
    text: TextRef[ViewType]
    callback: Callable[[ViewType], CallbackData]
    permission: StrEnum | None = None
    for_customers: bool = False
    for_staff: bool = False
    when: Callable[[ViewType], bool] | None = None
    style: ButtonStyle | None = None

    def is_allowed(self, view: ViewType, context: RenderContext) -> bool:
        if self.permission is not None and not context.actor.can(self.permission):
            return False
        if self.for_customers and not context.actor.is_shopping:
            return False
        if self.for_staff and not context.actor.is_staff:
            return False
        return self.when is None or self.when(view)

    def render(self, view: ViewType, context: RenderContext) -> str:
        return self.text(view, context.translate)


@dataclass(frozen=True, slots=True)
class Screen[ViewType]:
    content: ContentRef[ViewType]
    buttons: Sequence[Button[ViewType]]
    row_width: int = 1
    layout: Sequence[int] = ()

    def __post_init__(self) -> None:
        check_row_width(self.row_width)
        for width in self.layout:
            check_row_width(width)

    def render(self, view: ViewType, context: RenderContext) -> Content:
        return self.content(view, context.translate)


@dataclass(frozen=True, slots=True)
class ListScreen[ItemType, ViewType]:
    content: ContentRef[ViewType]
    item: Button[ItemType]
    footer: Sequence[Button[ViewType]]
    row_width: int = 1
    footer_row_width: int = 1
    footer_layout: Sequence[int] = ()

    def __post_init__(self) -> None:
        check_row_width(self.row_width)
        check_row_width(self.footer_row_width)
        for width in self.footer_layout:
            check_row_width(width)

    def render(self, view: ViewType, context: RenderContext) -> Content:
        return self.content(view, context.translate)
