import asyncio
from collections.abc import AsyncGenerator, Iterator
from contextlib import asynccontextmanager

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from telegramsales.shared.infrastructure.database.base import BaseORM
from telegramsales.shared.infrastructure.database.uow import SessionFactory
from telegramsales.shared.settings import PostgresSettings

TEST_DATABASE_SUFFIX = "_test"


def _url_for(settings: PostgresSettings, database: str) -> str:
    return settings.sqlalchemy_url.set(database=database).render_as_string(
        hide_password=False
    )


async def _recreate_database(maintenance_url: str, name: str) -> None:
    engine = create_async_engine(maintenance_url, isolation_level="AUTOCOMMIT")
    try:
        async with engine.connect() as connection:
            await connection.execute(text(f'drop database if exists "{name}"'))
            await connection.execute(text(f'create database "{name}"'))
    finally:
        await engine.dispose()


async def _create_schema(url: str) -> None:
    engine = create_async_engine(url)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(BaseORM.metadata.create_all)
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def database_url() -> Iterator[str]:
    settings = PostgresSettings()
    name = f"{settings.db}{TEST_DATABASE_SUFFIX}"
    url = _url_for(settings, name)

    try:
        asyncio.run(_recreate_database(_url_for(settings, "postgres"), name))
        asyncio.run(_create_schema(url))
    except OSError as exc:
        pytest.skip(f"postgres is not reachable: {exc}", allow_module_level=True)

    yield url

    asyncio.run(_recreate_database(_url_for(settings, "postgres"), name))


@pytest.fixture
async def connection(database_url: str) -> AsyncGenerator[AsyncConnection]:
    engine = create_async_engine(database_url)
    async with engine.connect() as opened:
        transaction = await opened.begin()
        yield opened
        await transaction.rollback()
    await engine.dispose()


@pytest.fixture
async def session(connection: AsyncConnection) -> AsyncGenerator[AsyncSession]:
    maker = async_sessionmaker(bind=connection, expire_on_commit=False)
    async with maker() as opened:
        yield opened


@pytest.fixture
def session_factory(connection: AsyncConnection) -> SessionFactory:
    maker = async_sessionmaker(bind=connection, expire_on_commit=False)

    @asynccontextmanager
    async def factory() -> AsyncGenerator[AsyncSession]:
        async with maker() as opened:
            yield opened

    return factory
