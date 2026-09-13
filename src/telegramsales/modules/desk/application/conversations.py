from telegramsales.modules.customers.contracts import CustomerId, ICustomerDirectory
from telegramsales.modules.desk.application.ports import IDeskUnitOfWork
from telegramsales.modules.orders.contracts import IOrderPresence


class Conversations:
    def __init__(
        self,
        uow: IDeskUnitOfWork,
        presence: IOrderPresence,
        directory: ICustomerDirectory,
    ) -> None:
        self._uow: IDeskUnitOfWork = uow
        self._presence: IOrderPresence = presence
        self._directory: ICustomerDirectory = directory

    async def is_blocked(self, customer_id: CustomerId) -> bool:
        card = await self._directory.find(customer_id)
        return card is not None and card.is_blocked

    async def is_open(self, customer_id: CustomerId) -> bool:
        if await self.is_blocked(customer_id):
            return False

        async with self._uow as uow:
            topic = await uow.topics.of_customer(customer_id)
        if topic is not None:
            return True
        return await self._presence.has_orders(customer_id)
