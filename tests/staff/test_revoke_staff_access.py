import pytest

from telegramsales.modules.staff.application.commands import (
    RevokeStaffAccess,
    RevokeStaffAccessHandler,
)
from telegramsales.modules.staff.application.exceptions import (
    PermissionDeniedError,
    StaffMemberNotFoundError,
)
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.domain.events import StaffAccessRevoked
from telegramsales.modules.staff.domain.exceptions import LastOwnerRevokedError
from telegramsales.modules.staff.domain.permissions import StaffPermission
from tests.staff.factories import MEMBER, OTHER, OWNER, make_member
from tests.staff.fakes import FakeEventPublisher, FakeStaffUnitOfWork, actor_with

ALLOWED = actor_with(StaffPermission.MANAGE_STAFF, actor_id=OWNER)


def make_handler(
    uow: FakeStaffUnitOfWork,
) -> tuple[
    RevokeStaffAccessHandler,
    FakeEventPublisher,
]:
    events = FakeEventPublisher()
    return RevokeStaffAccessHandler(uow, events), events


async def test_access_is_revoked_and_event_published() -> None:
    member = make_member(StaffRole.MANAGER)
    uow = FakeStaffUnitOfWork(member, make_member(StaffRole.OWNER, staff_id=OWNER))
    handler, events = make_handler(uow)

    await handler.handle(RevokeStaffAccess(staff_id=MEMBER), ALLOWED)

    assert member.is_active is False
    assert isinstance(events.published[0], StaffAccessRevoked)


async def test_revoking_the_last_owner_is_rejected() -> None:
    owner = make_member(StaffRole.OWNER, staff_id=OWNER)
    uow = FakeStaffUnitOfWork(owner)
    handler, events = make_handler(uow)

    with pytest.raises(LastOwnerRevokedError):
        await handler.handle(RevokeStaffAccess(staff_id=OWNER), ALLOWED)

    assert owner.is_active
    assert uow.rolled_back
    assert events.published == []


async def test_revoking_an_owner_is_allowed_while_another_remains() -> None:
    owner = make_member(StaffRole.OWNER, staff_id=OWNER)
    uow = FakeStaffUnitOfWork(owner, make_member(StaffRole.OWNER, staff_id=OTHER))
    handler, _ = make_handler(uow)

    await handler.handle(RevokeStaffAccess(staff_id=OWNER), ALLOWED)

    assert owner.is_active is False


async def test_unknown_member_is_rejected() -> None:
    uow = FakeStaffUnitOfWork()
    handler, _ = make_handler(uow)

    with pytest.raises(StaffMemberNotFoundError):
        await handler.handle(RevokeStaffAccess(staff_id=MEMBER), ALLOWED)


async def test_permission_is_checked_before_touching_the_repository() -> None:
    uow = FakeStaffUnitOfWork(make_member(StaffRole.MANAGER))
    handler, _ = make_handler(uow)

    with pytest.raises(PermissionDeniedError):
        await handler.handle(RevokeStaffAccess(staff_id=MEMBER), actor_with())

    assert uow.repository.calls == []
