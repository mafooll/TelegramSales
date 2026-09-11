import pytest

from telegramsales.modules.staff.infrastructure.uow import StaffUnitOfWork
from telegramsales.shared.infrastructure.database.uow import (
    SessionFactory,
    UnitOfWorkNotStartedError,
)

pytestmark = pytest.mark.db


async def test_the_repository_is_unavailable_outside_a_transaction(
    session_factory: SessionFactory,
) -> None:
    uow = StaffUnitOfWork(session_factory)

    with pytest.raises(UnitOfWorkNotStartedError):
        _ = uow.staff

    async with uow:
        pass

    with pytest.raises(UnitOfWorkNotStartedError):
        _ = uow.staff
