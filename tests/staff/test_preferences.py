import pytest

from telegramsales.modules.staff.application.commands.preferences import (
    SwitchCustomerView,
    SwitchCustomerViewHandler,
)
from telegramsales.modules.staff.application.exceptions import (
    StaffMemberNotFoundError,
)
from telegramsales.modules.staff.domain.exceptions import (
    InactiveStaffMemberError,
)
from tests.staff.factories import MEMBER, make_member
from tests.staff.fakes import FakeStaffUnitOfWork, actor_with


def handler_for(uow: FakeStaffUnitOfWork) -> SwitchCustomerViewHandler:
    return SwitchCustomerViewHandler(uow)


async def test_a_member_turns_the_customer_view_on() -> None:
    uow = FakeStaffUnitOfWork(make_member())

    enabled = await handler_for(uow).handle(
        SwitchCustomerView(enabled=True),
        actor_with(actor_id=MEMBER),
    )

    assert enabled
    assert uow.repository.members[MEMBER].customer_view


async def test_a_member_turns_the_customer_view_off() -> None:
    member = make_member()
    member.switch_customer_view(enabled=True)
    uow = FakeStaffUnitOfWork(member)

    enabled = await handler_for(uow).handle(
        SwitchCustomerView(enabled=False),
        actor_with(actor_id=MEMBER),
    )

    assert not enabled
    assert not uow.repository.members[MEMBER].customer_view


async def test_the_change_is_saved() -> None:
    uow = FakeStaffUnitOfWork(make_member())

    await handler_for(uow).handle(
        SwitchCustomerView(enabled=True),
        actor_with(actor_id=MEMBER),
    )

    assert "save" in uow.repository.calls
    assert uow.committed


async def test_an_unknown_member_cannot_switch() -> None:
    uow = FakeStaffUnitOfWork()

    with pytest.raises(StaffMemberNotFoundError):
        await handler_for(uow).handle(
            SwitchCustomerView(enabled=True),
            actor_with(actor_id=MEMBER),
        )


async def test_a_revoked_member_cannot_switch() -> None:
    uow = FakeStaffUnitOfWork(make_member(is_active=False))

    with pytest.raises(InactiveStaffMemberError):
        await handler_for(uow).handle(
            SwitchCustomerView(enabled=True),
            actor_with(actor_id=MEMBER),
        )
