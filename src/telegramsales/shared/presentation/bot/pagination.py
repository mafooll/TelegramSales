from collections.abc import Callable
from dataclasses import dataclass

from aiogram.filters.callback_data import CallbackData

from telegramsales.shared.application.pagination import Page

type PageCallback = Callable[[int], CallbackData]


@dataclass(frozen=True, slots=True)
class Pagination[ItemType]:
    page: Page[ItemType]
    callback: PageCallback
