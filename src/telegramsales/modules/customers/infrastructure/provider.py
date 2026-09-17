from typing import final

from dishka import (
    Provider,
    Scope,
    provide,  # pyright: ignore[reportUnknownVariableType]
    provide_all,
)

from telegramsales.modules.customers.application.commands.customers import (
    RegisterCustomerHandler,
)
from telegramsales.modules.customers.application.directory import CustomerDirectory
from telegramsales.modules.customers.application.ports import ICustomerUnitOfWork
from telegramsales.modules.customers.contracts import ICustomerDirectory
from telegramsales.modules.customers.infrastructure.uow import CustomerUnitOfWork
from telegramsales.shared.application.clock import IClock
from telegramsales.shared.infrastructure.database.manager import DatabaseManager


@final
class CustomerProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def unit_of_work(self, manager: DatabaseManager) -> ICustomerUnitOfWork:
        return CustomerUnitOfWork(manager.session)

    @provide
    def directory(
        self,
        uow: ICustomerUnitOfWork,
        clock: IClock,
        register: RegisterCustomerHandler,
    ) -> ICustomerDirectory:
        return CustomerDirectory(uow, clock, register)

    handlers = provide_all(RegisterCustomerHandler)
