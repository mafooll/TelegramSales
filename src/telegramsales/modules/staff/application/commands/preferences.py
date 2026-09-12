from dataclasses import dataclass

from telegramsales.modules.staff.application.exceptions import (
    StaffMemberNotFoundError,
)
from telegramsales.modules.staff.application.ports import IStaffUnitOfWork
from telegramsales.modules.staff.contracts import StaffId
from telegramsales.shared.application.access import Actor


@dataclass(frozen=True, slots=True)
class SwitchCustomerView:
    enabled: bool


class SwitchCustomerViewHandler:
    def __init__(self, uow: IStaffUnitOfWork) -> None:
        self._uow: IStaffUnitOfWork = uow

    async def handle(self, command: SwitchCustomerView, actor: Actor) -> bool:
        staff_id = StaffId(actor.id)

        async with self._uow as uow:
            if not (member := await uow.staff.get(staff_id)):
                raise StaffMemberNotFoundError(staff_id=staff_id)

            member.switch_customer_view(enabled=command.enabled)
            await uow.staff.save(member)

            return member.customer_view
