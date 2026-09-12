from typing import override

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.staff.application.ports import IStaffQueries
from telegramsales.modules.staff.application.queries import StaffMemberView
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.infrastructure.models import StaffMemberORM
from telegramsales.shared.application.pagination import Page


class StaffQueries(IStaffQueries):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    @override
    async def get(self, staff_id: StaffId) -> StaffMemberView | None:
        query = select(
            StaffMemberORM.id,
            StaffMemberORM.role,
            StaffMemberORM.is_active,
            StaffMemberORM.customer_view,
            StaffMemberORM.created_at,
        ).where(StaffMemberORM.id == staff_id)

        if not (row := (await self._session.execute(query)).one_or_none()):
            return None

        return StaffMemberView(
            id=StaffId(row.id),
            role=StaffRole(row.role),
            is_active=row.is_active,
            customer_view=row.customer_view,
            created_at=row.created_at,
        )

    @override
    async def list_page(self, number: int, size: int) -> Page[StaffMemberView]:
        total = (
            await self._session.execute(
                select(func.count()).select_from(StaffMemberORM)
            )
        ).scalar_one()

        query = (
            select(
                StaffMemberORM.id,
                StaffMemberORM.role,
                StaffMemberORM.is_active,
                StaffMemberORM.customer_view,
                StaffMemberORM.created_at,
            )
            .order_by(StaffMemberORM.created_at)
            .limit(size)
            .offset(number * size)
        )
        rows = (await self._session.execute(query)).all()

        return Page(
            items=[
                StaffMemberView(
                    id=StaffId(row.id),
                    role=StaffRole(row.role),
                    is_active=row.is_active,
                    customer_view=row.customer_view,
                    created_at=row.created_at,
                )
                for row in rows
            ],
            number=number,
            size=size,
            total=total,
        )
