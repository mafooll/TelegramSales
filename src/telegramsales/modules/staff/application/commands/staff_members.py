from dataclasses import dataclass

from telegramsales.modules.staff.application.access import ensure_can_manage
from telegramsales.modules.staff.application.exceptions import (
    StaffMemberNotFoundError,
)
from telegramsales.modules.staff.application.ports import IStaffUnitOfWork
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.modules.staff.domain.entities import StaffMember
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.domain.services import ensure_owner_remains
from telegramsales.shared.application.access import Actor
from telegramsales.shared.application.clock import IClock
from telegramsales.shared.application.events import IEventPublisher


@dataclass(frozen=True, slots=True)
class GrantStaffAccess:
    staff_id: StaffId
    role: StaffRole


@dataclass(frozen=True, slots=True)
class ChangeStaffRole:
    staff_id: StaffId
    new_role: StaffRole


@dataclass(frozen=True, slots=True)
class RevokeStaffAccess:
    staff_id: StaffId


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
        ensure_can_manage(actor)

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


class ChangeStaffRoleHandler:
    def __init__(self, uow: IStaffUnitOfWork, events: IEventPublisher) -> None:
        self._uow: IStaffUnitOfWork = uow
        self._events: IEventPublisher = events

    async def handle(self, command: ChangeStaffRole, actor: Actor) -> None:
        ensure_can_manage(actor)

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


class RevokeStaffAccessHandler:
    def __init__(self, uow: IStaffUnitOfWork, events: IEventPublisher) -> None:
        self._uow: IStaffUnitOfWork = uow
        self._events: IEventPublisher = events

    async def handle(self, command: RevokeStaffAccess, actor: Actor) -> None:
        ensure_can_manage(actor)

        async with self._uow as uow:
            if not (member := await uow.staff.get(command.staff_id)):
                raise StaffMemberNotFoundError(staff_id=command.staff_id)

            owners = await uow.staff.count_active_by_role(StaffRole.OWNER)
            ensure_owner_remains(member, owners)

            member.revoke_access(revoked_by=StaffId(actor.id))
            uow.track(member)
            await uow.staff.save(member)

        await self._events.publish_all(self._uow.collect_events())
