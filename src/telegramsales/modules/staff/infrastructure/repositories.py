from typing import override

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from telegramsales.modules.staff.application.ports import IStaffRepository
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.entities import StaffMember
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.infrastructure.mappers import StaffMemberMapper
from telegramsales.modules.staff.infrastructure.models import StaffMemberORM
from telegramsales.shared.infrastructure.database.repository import Repository


class StaffRepository(IStaffRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session
        self._models: Repository[StaffMemberORM, int] = Repository(
            session,
            StaffMemberORM,
        )

    @override
    async def get(self, staff_id: StaffId) -> StaffMember | None:
        model = await self._models.get(staff_id)
        return StaffMemberMapper.to_entity(model) if model is not None else None

    @override
    async def add(self, member: StaffMember) -> None:
        await self._models.add(StaffMemberMapper.to_model(member))

    @override
    async def save(self, member: StaffMember) -> None:
        await self._models.merge(StaffMemberMapper.to_model(member))

    @override
    async def count_active_by_role(self, role: StaffRole) -> int:
        query = (
            select(func.count())
            .select_from(StaffMemberORM)
            .where(
                StaffMemberORM.role == role.value,
                StaffMemberORM.is_active.is_(True),
            )
        )
        return (await self._session.execute(query)).scalar_one()
