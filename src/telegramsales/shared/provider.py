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
from telegramsales.shared.application.i18n import ITranslatorFactory
from telegramsales.shared.infrastructure.clock import SystemClock
from telegramsales.shared.infrastructure.database.manager import DatabaseManager
from telegramsales.shared.infrastructure.events.bus import InProcessEventBus
from telegramsales.shared.infrastructure.i18n.fluent import FluentTranslations
from telegramsales.shared.settings import (
    LOCALES_PATH,
    AppSettings,
    PostgresSettings,
)


@final
class SharedProvider(Provider):
    scope = Scope.APP

    @provide
    def app_settings(self) -> AppSettings:
        return AppSettings()

    @provide
    def postgres_settings(self) -> PostgresSettings:
        return PostgresSettings()

    @provide
    def translations(self, settings: AppSettings) -> ITranslatorFactory:
        return FluentTranslations(LOCALES_PATH, settings.default_locale)

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
    def event_bus(self) -> InProcessEventBus:
        return InProcessEventBus()

    @provide
    def event_publisher(self, bus: InProcessEventBus) -> IEventPublisher:
        return bus

    @provide(scope=Scope.REQUEST)
    async def session(self, manager: DatabaseManager) -> AsyncIterator[AsyncSession]:
        async with manager.session() as opened:
            yield opened
