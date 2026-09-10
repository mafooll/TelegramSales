from dataclasses import dataclass

from telegramsales.modules.staff.application.exceptions import PermissionDeniedError
from telegramsales.modules.staff.application.ports import IStaffUnitOfWork
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.entities import StaffMember
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.domain.permissions import StaffPermission
from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.clock import IClock
from telegramsales.shared.application.events import IEventPublisher


@dataclass(frozen=True, slots=True)
class GrantStaffAccess:
    staff_id: StaffId
    role: StaffRole


class GrantStaffAccessHandler:
    def __init__(
        self,
        uow: IStaffUnitOfWork,
        events: IEventPublisher,
        clock: IClock,
    ) -> None:
        self._uow: IStaffUnitOfWork = uow
        self._events: IEventPublisher = events
        self._clock: IClock = clock

    async def handle(self, command: GrantStaffAccess, actor: Actor) -> None:
        if not actor.can(StaffPermission.MANAGE_STAFF):
            raise PermissionDeniedError(
                actor_id=actor.id,
                permission=StaffPermission.MANAGE_STAFF,
            )

        async with self._uow as uow:
            if not (member := await uow.staff.get(command.staff_id)):
                member = StaffMember.create(
                    staff_id=command.staff_id,
                    role=command.role,
                    created_by=StaffId(actor.id),
                    now=self._clock.now(),
                )
                await uow.staff.add(member)
            else:
                member.grant_access(command.role, granted_by=StaffId(actor.id))
                await uow.staff.save(member)

            uow.track(member)

        await self._events.publish_all(self._uow.collect_events())
