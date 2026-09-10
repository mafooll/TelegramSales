from dataclasses import dataclass

from telegramsales.modules.staff.application.exceptions import (
    PermissionDeniedError,
    StaffMemberNotFoundError,
)
from telegramsales.modules.staff.application.ports import IStaffUnitOfWork
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.domain.permissions import StaffPermission
from telegramsales.modules.staff.domain.services import ensure_owner_remains
from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.events import IEventPublisher


@dataclass(frozen=True, slots=True)
class ChangeStaffRole:
    staff_id: StaffId
    new_role: StaffRole


class ChangeStaffRoleHandler:
    def __init__(self, uow: IStaffUnitOfWork, events: IEventPublisher) -> None:
        self._uow: IStaffUnitOfWork = uow
        self._events: IEventPublisher = events

    async def handle(self, command: ChangeStaffRole, actor: Actor) -> None:
        if not actor.can(StaffPermission.MANAGE_STAFF):
            raise PermissionDeniedError(
                actor_id=actor.id,
                permission=StaffPermission.MANAGE_STAFF,
            )

        async with self._uow as uow:
            if not (member := await uow.staff.get(command.staff_id)):
                raise StaffMemberNotFoundError(staff_id=command.staff_id)

            if command.new_role is not StaffRole.OWNER:
                owners = await uow.staff.count_active_by_role(StaffRole.OWNER)
                ensure_owner_remains(member, owners)

            member.change_role(command.new_role, changed_by=StaffId(actor.id))
            uow.track(member)
            await uow.staff.save(member)

        await self._events.publish_all(self._uow.collect_events())
