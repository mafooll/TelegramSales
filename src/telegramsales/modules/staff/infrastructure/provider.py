from typing import final

from dishka import (
    Provider,
    Scope,
    provide,  # pyright: ignore[reportUnknownVariableType]
    provide_all,
)
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.staff.application.commands import (
    ChangeStaffRoleHandler,
    GrantStaffAccessHandler,
    RevokeStaffAccessHandler,
)
from telegramsales.modules.staff.application.ports import (
    IStaffQueries,
    IStaffUnitOfWork,
)
from telegramsales.modules.staff.infrastructure.queries import StaffQueries
from telegramsales.modules.staff.infrastructure.uow import StaffUnitOfWork
from telegramsales.shared.infrastructure.database.manager import DatabaseManager


@final
class StaffProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def unit_of_work(self, manager: DatabaseManager) -> IStaffUnitOfWork:
        return StaffUnitOfWork(manager.session)

    @provide
    def queries(self, session: AsyncSession) -> IStaffQueries:
        return StaffQueries(session)

    handlers = provide_all(
        GrantStaffAccessHandler,
        ChangeStaffRoleHandler,
        RevokeStaffAccessHandler,
    )
