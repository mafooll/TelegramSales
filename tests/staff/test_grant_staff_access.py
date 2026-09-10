import pytest

from telegramsales.modules.staff.application.commands import (
    GrantStaffAccess,
    GrantStaffAccessHandler,
)
from telegramsales.modules.staff.application.exceptions import PermissionDeniedError
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.domain.events import (
    StaffAccessGranted,
    StaffMemberCreated,
)
from telegramsales.modules.staff.domain.exceptions import AccessAlreadyGrantedError
from telegramsales.modules.staff.domain.permissions import StaffPermission
from tests.staff.factories import MEMBER, NOW, make_member
from tests.staff.fakes import (
    FakeEventPublisher,
    FakeStaffUnitOfWork,
    FixedClock,
    actor_with,
)


def make_handler(
    uow: FakeStaffUnitOfWork,
) -> tuple[
    GrantStaffAccessHandler,
    FakeEventPublisher,
]:
    events = FakeEventPublisher()
    return GrantStaffAccessHandler(uow, events, FixedClock(NOW)), events


async def test_unknown_member_is_created() -> None:
    uow = FakeStaffUnitOfWork()
    handler, events = make_handler(uow)

    await handler.handle(
        GrantStaffAccess(staff_id=MEMBER, role=StaffRole.MANAGER),
        actor_with(StaffPermission.MANAGE_STAFF),
    )

    created = uow.repository.members[MEMBER]
    assert created.role is StaffRole.MANAGER
    assert created.is_active
    assert created.created_at == NOW
    assert isinstance(events.published[0], StaffMemberCreated)


async def test_revoked_member_is_restored_with_the_given_role() -> None:
    revoked = make_member(StaffRole.MANAGER, is_active=False)
    uow = FakeStaffUnitOfWork(revoked)
    handler, events = make_handler(uow)

    await handler.handle(
        GrantStaffAccess(staff_id=MEMBER, role=StaffRole.OWNER),
        actor_with(StaffPermission.MANAGE_STAFF),
    )

    assert revoked.is_active
    assert revoked.role is StaffRole.OWNER
    assert isinstance(events.published[0], StaffAccessGranted)


async def test_granting_to_an_active_member_is_rejected() -> None:
    uow = FakeStaffUnitOfWork(make_member(StaffRole.MANAGER))
    handler, events = make_handler(uow)

    with pytest.raises(AccessAlreadyGrantedError):
        await handler.handle(
            GrantStaffAccess(staff_id=MEMBER, role=StaffRole.OWNER),
            actor_with(StaffPermission.MANAGE_STAFF),
        )

    assert uow.rolled_back
    assert events.published == []


async def test_actor_without_permission_is_rejected() -> None:
    uow = FakeStaffUnitOfWork()
    handler, _ = make_handler(uow)

    with pytest.raises(PermissionDeniedError):
        await handler.handle(
            GrantStaffAccess(staff_id=MEMBER, role=StaffRole.MANAGER),
            actor_with(),
        )


async def test_permission_is_checked_before_touching_the_repository() -> None:
    uow = FakeStaffUnitOfWork()
    handler, _ = make_handler(uow)

    with pytest.raises(PermissionDeniedError):
        await handler.handle(
            GrantStaffAccess(staff_id=MEMBER, role=StaffRole.MANAGER),
            actor_with(),
        )

    assert uow.repository.calls == []
