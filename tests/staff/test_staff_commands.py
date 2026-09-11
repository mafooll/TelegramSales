import pytest

from telegramsales.modules.staff.application.commands.staff_members import (
    ChangeStaffRole,
    ChangeStaffRoleHandler,
    GrantStaffAccess,
    GrantStaffAccessHandler,
    RevokeStaffAccess,
    RevokeStaffAccessHandler,
)
from telegramsales.modules.staff.application.exceptions import (
    StaffMemberNotFoundError,
)
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.domain.events import (
    StaffAccessGranted,
    StaffAccessRevoked,
    StaffMemberCreated,
    StaffRoleChanged,
)
from telegramsales.modules.staff.domain.exceptions import (
    AccessAlreadyGrantedError,
    LastOwnerRevokedError,
)
from telegramsales.modules.staff.domain.permissions import StaffPermission
from telegramsales.shared.application.access import PermissionDeniedError
from tests.staff.factories import MEMBER, NOW, OTHER, OWNER, make_member
from tests.staff.fakes import (
    FakeEventPublisher,
    FakeStaffUnitOfWork,
    FixedClock,
    actor_with,
)


def grant_handler(
    uow: FakeStaffUnitOfWork,
) -> tuple[
    GrantStaffAccessHandler,
    FakeEventPublisher,
]:
    events = FakeEventPublisher()
    return GrantStaffAccessHandler(uow, events, FixedClock(NOW)), events


async def test_unknown_member_is_created() -> None:
    uow = FakeStaffUnitOfWork()
    handler, events = grant_handler(uow)

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
    handler, events = grant_handler(uow)

    await handler.handle(
        GrantStaffAccess(staff_id=MEMBER, role=StaffRole.OWNER),
        actor_with(StaffPermission.MANAGE_STAFF),
    )

    assert revoked.is_active
    assert revoked.role is StaffRole.OWNER
    assert isinstance(events.published[0], StaffAccessGranted)


async def test_granting_to_an_active_member_is_rejected() -> None:
    uow = FakeStaffUnitOfWork(make_member(StaffRole.MANAGER))
    handler, events = grant_handler(uow)

    with pytest.raises(AccessAlreadyGrantedError):
        await handler.handle(
            GrantStaffAccess(staff_id=MEMBER, role=StaffRole.OWNER),
            actor_with(StaffPermission.MANAGE_STAFF),
        )

    assert uow.rolled_back
    assert events.published == []


async def test_actor_without_permission_is_rejected() -> None:
    uow = FakeStaffUnitOfWork()
    handler, _ = grant_handler(uow)

    with pytest.raises(PermissionDeniedError):
        await handler.handle(
            GrantStaffAccess(staff_id=MEMBER, role=StaffRole.MANAGER),
            actor_with(),
        )


async def test_permission_is_checked_before_granting() -> None:
    uow = FakeStaffUnitOfWork()
    handler, _ = grant_handler(uow)

    with pytest.raises(PermissionDeniedError):
        await handler.handle(
            GrantStaffAccess(staff_id=MEMBER, role=StaffRole.MANAGER),
            actor_with(),
        )

    assert uow.repository.calls == []


ALLOWED = actor_with(StaffPermission.MANAGE_STAFF, actor_id=OWNER)


def role_handler(
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
    handler, events = role_handler(uow)

    await handler.handle(
        ChangeStaffRole(staff_id=MEMBER, new_role=StaffRole.OWNER), ALLOWED
    )

    assert member.role is StaffRole.OWNER
    assert isinstance(events.published[0], StaffRoleChanged)


async def test_unknown_member_is_rejected_on_changing_a_role() -> None:
    uow = FakeStaffUnitOfWork()
    handler, events = role_handler(uow)

    with pytest.raises(StaffMemberNotFoundError):
        await handler.handle(
            ChangeStaffRole(staff_id=MEMBER, new_role=StaffRole.OWNER), ALLOWED
        )

    assert events.published == []


async def test_demoting_the_last_owner_is_rejected() -> None:
    owner = make_member(StaffRole.OWNER, staff_id=OWNER)
    uow = FakeStaffUnitOfWork(owner)
    handler, events = role_handler(uow)

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
    handler, _ = role_handler(uow)

    await handler.handle(
        ChangeStaffRole(staff_id=OWNER, new_role=StaffRole.MANAGER), ALLOWED
    )

    assert owner.role is StaffRole.MANAGER


async def test_promotion_does_not_count_owners() -> None:
    uow = FakeStaffUnitOfWork(make_member(StaffRole.MANAGER))
    handler, _ = role_handler(uow)

    await handler.handle(
        ChangeStaffRole(staff_id=MEMBER, new_role=StaffRole.OWNER), ALLOWED
    )

    assert "count_active_by_role" not in uow.repository.calls


async def test_permission_is_checked_before_changing_a_role() -> None:
    uow = FakeStaffUnitOfWork(make_member(StaffRole.MANAGER))
    handler, _ = role_handler(uow)

    with pytest.raises(PermissionDeniedError):
        await handler.handle(
            ChangeStaffRole(staff_id=MEMBER, new_role=StaffRole.OWNER), actor_with()
        )

    assert uow.repository.calls == []


def revoke_handler(
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
    handler, events = revoke_handler(uow)

    await handler.handle(RevokeStaffAccess(staff_id=MEMBER), ALLOWED)

    assert member.is_active is False
    assert isinstance(events.published[0], StaffAccessRevoked)


async def test_revoking_the_last_owner_is_rejected() -> None:
    owner = make_member(StaffRole.OWNER, staff_id=OWNER)
    uow = FakeStaffUnitOfWork(owner)
    handler, events = revoke_handler(uow)

    with pytest.raises(LastOwnerRevokedError):
        await handler.handle(RevokeStaffAccess(staff_id=OWNER), ALLOWED)

    assert owner.is_active
    assert uow.rolled_back
    assert events.published == []


async def test_revoking_an_owner_is_allowed_while_another_remains() -> None:
    owner = make_member(StaffRole.OWNER, staff_id=OWNER)
    uow = FakeStaffUnitOfWork(owner, make_member(StaffRole.OWNER, staff_id=OTHER))
    handler, _ = revoke_handler(uow)

    await handler.handle(RevokeStaffAccess(staff_id=OWNER), ALLOWED)

    assert owner.is_active is False


async def test_unknown_member_is_rejected_on_revoking() -> None:
    uow = FakeStaffUnitOfWork()
    handler, _ = revoke_handler(uow)

    with pytest.raises(StaffMemberNotFoundError):
        await handler.handle(RevokeStaffAccess(staff_id=MEMBER), ALLOWED)


async def test_permission_is_checked_before_revoking() -> None:
    uow = FakeStaffUnitOfWork(make_member(StaffRole.MANAGER))
    handler, _ = revoke_handler(uow)

    with pytest.raises(PermissionDeniedError):
        await handler.handle(RevokeStaffAccess(staff_id=MEMBER), actor_with())

    assert uow.repository.calls == []
