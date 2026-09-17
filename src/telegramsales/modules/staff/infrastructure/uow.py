from telegramsales.modules.staff.application.ports import IStaffRepository
from telegramsales.modules.staff.infrastructure.repositories import StaffRepository
from telegramsales.shared.infrastructure.database.uow import UnitOfWork


class StaffUnitOfWork(UnitOfWork):
    @property
    def staff(self) -> IStaffRepository:
        return StaffRepository(self.session)
