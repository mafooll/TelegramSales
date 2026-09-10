from collections.abc import Sequence
from dataclasses import dataclass
from math import ceil

DEFAULT_PAGE_SIZE = 8


@dataclass(frozen=True, slots=True)
class Page[ItemType]:
    items: Sequence[ItemType]
    number: int
    size: int
    total: int

    @property
    def total_pages(self) -> int:
        return max(1, ceil(self.total / self.size))

    @property
    def has_previous(self) -> bool:
        return self.number > 0

    @property
    def has_next(self) -> bool:
        return self.number + 1 < self.total_pages

    @property
    def is_single(self) -> bool:
        return self.total_pages == 1

    @property
    def offset(self) -> int:
        return self.number * self.size
