from telegramsales.modules.desk.application.ports import (
    ICardRegistry,
    IRelayRegistry,
    ITopicRegistry,
)
from telegramsales.modules.desk.infrastructure.repositories import (
    CardRegistry,
    RelayRegistry,
    TopicRegistry,
)
from telegramsales.shared.infrastructure.database.uow import UnitOfWork


class DeskUnitOfWork(UnitOfWork):
    @property
    def topics(self) -> ITopicRegistry:
        return TopicRegistry(self.session)

    @property
    def cards(self) -> ICardRegistry:
        return CardRegistry(self.session)

    @property
    def relays(self) -> IRelayRegistry:
        return RelayRegistry(self.session)
