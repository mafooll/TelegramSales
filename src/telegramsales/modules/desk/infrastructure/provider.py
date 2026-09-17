from typing import final

from dishka import (
    Provider,
    Scope,
    provide,  # pyright: ignore[reportUnknownVariableType]
    provide_all,
)

from telegramsales.modules.desk.application.commands.cards import (
    PublishOrderCardHandler,
    RedrawOrderCardHandler,
)
from telegramsales.modules.desk.application.commands.relay import (
    EditFromCustomerHandler,
    EditFromTopicHandler,
    ReactFromCustomerHandler,
    ReactFromTopicHandler,
    RelayToCustomerHandler,
    RelayToTopicHandler,
)
from telegramsales.modules.desk.application.commands.support import (
    CallForSupportHandler,
)
from telegramsales.modules.desk.application.conversations import Conversations
from telegramsales.modules.desk.application.ports import IDeskUnitOfWork
from telegramsales.modules.desk.application.topics import Topics
from telegramsales.modules.desk.infrastructure.uow import DeskUnitOfWork
from telegramsales.shared.infrastructure.database.manager import DatabaseManager


@final
class DeskProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def unit_of_work(self, manager: DatabaseManager) -> IDeskUnitOfWork:
        return DeskUnitOfWork(manager.session)

    services = provide_all(Topics, Conversations)

    handlers = provide_all(
        PublishOrderCardHandler,
        RedrawOrderCardHandler,
        RelayToTopicHandler,
        RelayToCustomerHandler,
        EditFromCustomerHandler,
        EditFromTopicHandler,
        ReactFromCustomerHandler,
        ReactFromTopicHandler,
        CallForSupportHandler,
    )
