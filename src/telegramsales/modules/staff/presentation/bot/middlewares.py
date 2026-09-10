from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, override

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from dishka.integrations.aiogram import CONTAINER_NAME

from telegramsales.modules.staff.application.ports import IStaffQueries
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.shared.application.access import (
    Actor,
    IPermissionResolver,
    PermissionCode,
)

if TYPE_CHECKING:
    from dishka import AsyncContainer

NO_PERMISSIONS: frozenset[PermissionCode] = frozenset()


class ActorMiddleware(BaseMiddleware):
    @override
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        container: AsyncContainer = data[CONTAINER_NAME]
        queries = await container.get(IStaffQueries)
        member = await queries.get(StaffId(user.id))

        permissions = NO_PERMISSIONS
        if member is not None and member.is_active:
            resolver = await container.get(IPermissionResolver)
            permissions = resolver.permissions_of(member.role)

        data["actor"] = Actor(id=user.id, permissions=permissions)
        return await handler(event, data)
