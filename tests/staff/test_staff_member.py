import pytest

from telegramsales.modules.staff.domain.entities import StaffMember
from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.domain.events import (
    StaffAccessGranted,
    StaffAccessRevoked,
    StaffMemberCreated,
    StaffRoleChanged,
)
from telegramsales.modules.staff.domain.exceptions import (
    AccessAlreadyGrantedError,
    AccessAlreadyRevokedError,
    InactiveStaffMemberError,
    RoleAlreadyAssignedError,
)
from tests.staff.factories import MEMBER, NOW, OWNER, make_member


def test_create_sets_identity_role_and_timestamp() -> None:
    member = StaffMember.create(
        staff_id=MEMBER,
        role=StaffRole.MANAGER,
        created_by=OWNER,
        now=NOW,
    )

    assert member.id == MEMBER
    assert member.role is StaffRole.MANAGER
    assert member.created_at == NOW
    assert member.is_active


def test_create_registers_staff_member_created() -> None:
    member = StaffMember.create(
        staff_id=MEMBER,
        role=StaffRole.MANAGER,
        created_by=OWNER,
        now=NOW,
    )

    events = member.collect_events()

    assert len(events) == 1
    event = events[0]
    assert isinstance(event, StaffMemberCreated)
    assert event.staff_id == MEMBER
    assert event.role is StaffRole.MANAGER
    assert event.created_by == OWNER


@pytest.mark.parametrize(
    ("role", "expected"),
    [(StaffRole.OWNER, True), (StaffRole.MANAGER, False)],
)
def test_is_owner_follows_the_role(role: StaffRole, *, expected: bool) -> None:
    assert make_member(role).is_owner is expected


def test_revoked_owner_is_not_an_owner() -> None:
    member = make_member(StaffRole.OWNER, is_active=False)

    assert member.is_owner is False


def test_change_role_replaces_the_role() -> None:
    member = make_member(StaffRole.MANAGER)

    member.change_role(StaffRole.OWNER, changed_by=OWNER)

    assert member.role is StaffRole.OWNER


def test_change_role_registers_staff_role_changed() -> None:
    member = make_member(StaffRole.MANAGER)

    member.change_role(StaffRole.OWNER, changed_by=OWNER)

    events = member.collect_events()
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, StaffRoleChanged)
    assert event.staff_id == MEMBER
    assert event.old_role is StaffRole.MANAGER
    assert event.new_role is StaffRole.OWNER
    assert event.changed_by == OWNER


def test_change_role_to_the_same_role_is_rejected() -> None:
    member = make_member(StaffRole.MANAGER)

    with pytest.raises(RoleAlreadyAssignedError):
        member.change_role(StaffRole.MANAGER, changed_by=OWNER)


def test_rejected_change_leaves_no_trace() -> None:
    member = make_member(StaffRole.MANAGER)

    with pytest.raises(RoleAlreadyAssignedError):
        member.change_role(StaffRole.MANAGER, changed_by=OWNER)

    assert member.role is StaffRole.MANAGER
    assert member.collect_events() == []


def test_revoked_member_cannot_change_role() -> None:
    member = make_member(StaffRole.MANAGER, is_active=False)

    with pytest.raises(InactiveStaffMemberError):
        member.change_role(StaffRole.OWNER, changed_by=OWNER)


def test_revoke_access_deactivates_and_registers_event() -> None:
    member = make_member(StaffRole.MANAGER)

    member.revoke_access(revoked_by=OWNER)

    assert member.is_active is False
    events = member.collect_events()
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, StaffAccessRevoked)
    assert event.staff_id == MEMBER
    assert event.revoked_by == OWNER


def test_revoking_twice_is_rejected() -> None:
    member = make_member(StaffRole.MANAGER, is_active=False)

    with pytest.raises(AccessAlreadyRevokedError):
        member.revoke_access(revoked_by=OWNER)


def test_grant_access_restores_with_the_given_role() -> None:
    member = make_member(StaffRole.MANAGER, is_active=False)

    member.grant_access(StaffRole.OWNER, granted_by=OWNER)

    assert member.is_active is True
    assert member.role is StaffRole.OWNER
    events = member.collect_events()
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, StaffAccessGranted)
    assert event.role is StaffRole.OWNER
    assert event.granted_by == OWNER


def test_granting_to_an_active_member_is_rejected() -> None:
    member = make_member(StaffRole.MANAGER)

    with pytest.raises(AccessAlreadyGrantedError):
        member.grant_access(StaffRole.OWNER, granted_by=OWNER)


def test_members_are_equal_by_identity_only() -> None:
    one = make_member(StaffRole.MANAGER)
    another = make_member(StaffRole.OWNER)

    assert one == another
    assert len({one, another}) == 1
