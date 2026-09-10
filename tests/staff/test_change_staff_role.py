import pytest

from telegramsales.modules.staff.application.commands import (
    ChangeStaffRole,
    ChangeStaffRoleHandler,
)
from telegramsales.modules.staff.application.exceptions import (
    PermissionDeniedError,
    StaffMemberNotFoundError,
)
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.domain.events import StaffRoleChanged
from telegramsales.modules.staff.domain.exceptions import LastOwnerRevokedError
from telegramsales.modules.staff.domain.permissions import StaffPermission
from tests.staff.factories import MEMBER, OTHER, OWNER, make_member
from tests.staff.fakes import FakeEventPublisher, FakeStaffUnitOfWork, actor_with

ALLOWED = actor_with(StaffPermission.MANAGE_STAFF, actor_id=OWNER)


def make_handler(
    uow: FakeStaffUnitOfWork,
) -> tuple[
    ChangeStaffRoleHandler,
    FakeEventPublisher,
]:
    events = FakeEventPublisher()
    return ChangeStaffRoleHandler(uow, events), events


async def test_role_is_changed_and_event_published() -> None:
    member = make_member(StaffRole.MANAGER)
    uow = FakeStaffUnitOfWork(member)
    handler, events = make_handler(uow)

    await handler.handle(
        ChangeStaffRole(staff_id=MEMBER, new_role=StaffRole.OWNER), ALLOWED
    )

    assert member.role is StaffRole.OWNER
    assert isinstance(events.published[0], StaffRoleChanged)


async def test_unknown_member_is_rejected() -> None:
    uow = FakeStaffUnitOfWork()
    handler, events = make_handler(uow)

    with pytest.raises(StaffMemberNotFoundError):
        await handler.handle(
            ChangeStaffRole(staff_id=MEMBER, new_role=StaffRole.OWNER), ALLOWED
        )

    assert events.published == []


async def test_demoting_the_last_owner_is_rejected() -> None:
    owner = make_member(StaffRole.OWNER, staff_id=OWNER)
    uow = FakeStaffUnitOfWork(owner)
    handler, events = make_handler(uow)

    with pytest.raises(LastOwnerRevokedError):
        await handler.handle(
            ChangeStaffRole(staff_id=OWNER, new_role=StaffRole.MANAGER), ALLOWED
        )

    assert owner.role is StaffRole.OWNER
    assert uow.rolled_back
    assert events.published == []


async def test_demoting_an_owner_is_allowed_while_another_remains() -> None:
    owner = make_member(StaffRole.OWNER, staff_id=OWNER)
    second = make_member(StaffRole.OWNER, staff_id=OTHER)
    uow = FakeStaffUnitOfWork(owner, second)
    handler, _ = make_handler(uow)

    await handler.handle(
        ChangeStaffRole(staff_id=OWNER, new_role=StaffRole.MANAGER), ALLOWED
    )

    assert owner.role is StaffRole.MANAGER


async def test_promotion_does_not_count_owners() -> None:
    uow = FakeStaffUnitOfWork(make_member(StaffRole.MANAGER))
    handler, _ = make_handler(uow)

    await handler.handle(
        ChangeStaffRole(staff_id=MEMBER, new_role=StaffRole.OWNER), ALLOWED
    )

    assert "count_active_by_role" not in uow.repository.calls


async def test_permission_is_checked_before_touching_the_repository() -> None:
    uow = FakeStaffUnitOfWork(make_member(StaffRole.MANAGER))
    handler, _ = make_handler(uow)

    with pytest.raises(PermissionDeniedError):
        await handler.handle(
            ChangeStaffRole(staff_id=MEMBER, new_role=StaffRole.OWNER), actor_with()
        )

    assert uow.repository.calls == []
