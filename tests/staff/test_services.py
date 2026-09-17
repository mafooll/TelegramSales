import pytest

from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.modules.staff.domain.exceptions import LastOwnerRevokedError
from telegramsales.modules.staff.domain.services import ensure_owner_remains
from tests.staff.factories import MEMBER, make_member


def test_demoting_the_only_owner_is_rejected() -> None:
    owner = make_member(StaffRole.OWNER)

    with pytest.raises(LastOwnerRevokedError):
        ensure_owner_remains(owner, active_owner_count=1)


def test_demoting_an_owner_is_allowed_while_another_remains() -> None:
    owner = make_member(StaffRole.OWNER)

    ensure_owner_remains(owner, active_owner_count=2)


@pytest.mark.parametrize("active_owner_count", [0, 1, 2])
def test_demoting_a_member_is_always_allowed(active_owner_count: int) -> None:
    member = make_member(StaffRole.MANAGER)

    ensure_owner_remains(member, active_owner_count=active_owner_count)


def test_a_revoked_owner_does_not_block_the_last_one() -> None:
    revoked = make_member(StaffRole.OWNER, is_active=False)

    ensure_owner_remains(revoked, active_owner_count=1)


def test_rejection_carries_the_staff_id() -> None:
    owner = make_member(StaffRole.OWNER)

    with pytest.raises(LastOwnerRevokedError) as exc_info:
        ensure_owner_remains(owner, active_owner_count=1)

    assert exc_info.value.details == {"staff_id": MEMBER}
