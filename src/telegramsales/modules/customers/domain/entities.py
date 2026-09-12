from dataclasses import dataclass
from datetime import datetime
from typing import Self

from telegramsales.modules.customers.contracts import CustomerId
from telegramsales.modules.customers.domain.exceptions import CustomerBlockedError
from telegramsales.modules.customers.domain.values import DisplayName
from telegramsales.shared.domain.contacts import Contacts
from telegramsales.shared.domain.entity import DomainEntity


@dataclass(eq=False, kw_only=True)
class Customer(DomainEntity[CustomerId]):
    name: DisplayName
    created_at: datetime
    contacts: Contacts | None = None
    is_blocked: bool = False

    @classmethod
    def create(
        cls,
        *,
        customer_id: CustomerId,
        name: DisplayName,
        now: datetime,
    ) -> Self:
        return cls(id=customer_id, name=name, created_at=now)

    def rename(self, name: DisplayName) -> None:
        self.name = name

    def remember(self, contacts: Contacts) -> None:
        self.contacts = contacts

    def block(self) -> None:
        self.is_blocked = True

    def unblock(self) -> None:
        self.is_blocked = False

    def ensure_can_order(self) -> None:
        if self.is_blocked:
            raise CustomerBlockedError(customer_id=self.id)
