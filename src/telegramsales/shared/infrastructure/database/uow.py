from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.shared.domain.event import DomainEvent, IEventSource
from telegramsales.shared.domain.exceptions import InfrastructureError

type SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]
type SessionContext = AbstractAsyncContextManager[AsyncSession]


class UnitOfWorkNotStartedError(InfrastructureError):
    def __init__(self) -> None:
        super().__init__("unit of work is not started, use 'async with uow'")


class UnitOfWork:
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory: SessionFactory = session_factory
        self._session: AsyncSession | None = None
        self._session_context: SessionContext | None = None
        self._tracked: list[IEventSource] = []
        self._collected_events: list[DomainEvent] = []

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise UnitOfWorkNotStartedError
        return self._session

    async def __aenter__(self) -> Self:
        self._session_context = self._session_factory()
        self._session = await self._session_context.__aenter__()
        self._tracked = []
        self._collected_events = []
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is None:
                await self.commit()
            else:
                await self.rollback()
        finally:
            if self._session_context is not None:
                await self._session_context.__aexit__(exc_type, exc_val, exc_tb)
            self._session = None
            self._session_context = None
            self._tracked = []

    def track(self, entity: IEventSource) -> None:
        self._tracked.append(entity)

    def collect_events(self) -> list[DomainEvent]:
        events = self._collected_events
        self._collected_events = []
        return events

    async def commit(self) -> None:
        events: list[DomainEvent] = []
        for entity in self._tracked:
            events.extend(entity.collect_events())
        await self.session.commit()
        self._collected_events = events

    async def rollback(self) -> None:
        await self.session.rollback()

    async def flush(self) -> None:
        await self.session.flush()
