from collections.abc import Hashable

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.shared.infrastructure.database.base import BaseORM


class Repository[ModelType: BaseORM, IdType: Hashable]:
    def __init__(self, session: AsyncSession, model_type: type[ModelType]) -> None:
        self._session: AsyncSession = session
        self._model_type: type[ModelType] = model_type

    async def get(self, model_id: IdType) -> ModelType | None:
        return await self._session.get(self._model_type, model_id)

    async def add(self, model: ModelType, *, flush: bool = True) -> ModelType:
        self._session.add(model)
        if flush:
            await self._session.flush()
        return model

    async def merge(self, model: ModelType, *, flush: bool = True) -> ModelType:
        merged = await self._session.merge(model)
        if flush:
            await self._session.flush()
        return merged

    async def delete(self, model: ModelType, *, flush: bool = True) -> None:
        await self._session.delete(model)
        if flush:
            await self._session.flush()

    async def paginate(
        self,
        query: Select[tuple[ModelType]],
        limit: int,
        offset: int,
    ) -> tuple[list[ModelType], int]:
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self._session.execute(count_query)).scalar_one()
        rows = await self._session.execute(query.limit(limit).offset(offset))
        return list(rows.scalars().all()), total
