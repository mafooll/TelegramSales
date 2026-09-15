from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from telegramsales.shared.infrastructure.database.telemetry import (
    log_queries as log_engine_queries,
)


class DatabaseManager:
    def __init__(
        self,
        db_url: str,
        *,
        echo: bool = False,
        log_queries: bool = False,
        **engine_kwargs: Any,
    ) -> None:
        self._engine: AsyncEngine = create_async_engine(
            db_url,
            echo=echo,
            pool_pre_ping=True,
            **engine_kwargs,
        )
        if log_queries:
            log_engine_queries(self._engine)

        self._session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        session = self._session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def dispose(self) -> None:
        await self._engine.dispose()
