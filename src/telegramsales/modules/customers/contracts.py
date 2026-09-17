from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import NewType

CustomerId = NewType("CustomerId", int)


@dataclass(frozen=True, slots=True)
class ContactsSnapshot:
    name: str
    phone: str
    address: str


@dataclass(frozen=True, slots=True)
class CustomerCard:
    id: CustomerId
    name: str
    contacts: ContactsSnapshot | None
    is_blocked: bool


class ICustomerDirectory(ABC):
    @abstractmethod
    async def register(self, customer_id: CustomerId, name: str) -> None: ...

    @abstractmethod
    async def find(self, customer_id: CustomerId) -> CustomerCard | None: ...

    @abstractmethod
    async def remember(
        self,
        customer_id: CustomerId,
        contacts: ContactsSnapshot,
    ) -> None: ...
