from datetime import UTC, datetime
from typing import override

from telegramsales.shared.application.clock import IClock


class SystemClock(IClock):
    @override
    def now(self) -> datetime:
        return datetime.now(UTC)
