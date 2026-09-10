from collections.abc import AsyncIterator
from typing import final

from dishka import (
    Provider,
    Scope,
    provide,  # pyright: ignore[reportUnknownVariableType]
)
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.shared.application.clock import IClock
from telegramsales.shared.application.events import IEventPublisher
from telegramsales.shared.infrastructure.clock import SystemClock
from telegramsales.shared.infrastructure.database.manager import DatabaseManager
from telegramsales.shared.infrastructure.events.bus import EventBus
from telegramsales.shared.settings import PostgresSettings


@final
class SharedProvider(Provider):
    scope = Scope.APP

    @provide
    def postgres_settings(self) -> PostgresSettings:
        return PostgresSettings()

    @provide
    async def database_manager(
        self,
        settings: PostgresSettings,
    ) -> AsyncIterator[DatabaseManager]:
        manager = DatabaseManager(
            db_url=settings.url,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
        )
        yield manager
        await manager.dispose()

    @provide
    def clock(self) -> IClock:
        return SystemClock()

    @provide
    def event_bus(self) -> EventBus:
        return EventBus()

    @provide
    def event_publisher(self, bus: EventBus) -> IEventPublisher:
        return bus

    @provide(scope=Scope.REQUEST)
    async def session(self, manager: DatabaseManager) -> AsyncIterator[AsyncSession]:
        async with manager.session() as opened:
            yield opened
