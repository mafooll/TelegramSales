from typing import override

from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.entities import StaffMember
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.infrastructure.models import StaffMemberORM
from telegramsales.shared.infrastructure.database.mapper import IEntityMapper


class StaffMemberMapper(IEntityMapper[StaffMember, StaffMemberORM]):
    @staticmethod
    @override
    def to_entity(model: StaffMemberORM) -> StaffMember:
        return StaffMember(
            id=StaffId(model.id),
            role=StaffRole(model.role),
            is_active=model.is_active,
            created_at=model.created_at,
        )

    @staticmethod
    @override
    def to_model(entity: StaffMember) -> StaffMemberORM:
        return StaffMemberORM(
            id=entity.id,
            role=entity.role.value,
            is_active=entity.is_active,
            created_at=entity.created_at,
        )
