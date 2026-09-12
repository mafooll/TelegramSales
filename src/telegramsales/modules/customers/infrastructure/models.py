from typing import final

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from telegramsales.modules.customers.domain.values import MAX_DISPLAY_NAME_LENGTH
from telegramsales.shared.domain.contacts import (
    MAX_ADDRESS_LENGTH,
    MAX_NAME_LENGTH,
    MAX_PHONE_DIGITS,
)
from telegramsales.shared.infrastructure.database.base import BaseORM
from telegramsales.shared.infrastructure.database.mixins import WithCreatedAtMixin

PHONE_LENGTH = MAX_PHONE_DIGITS + 1


@final
class CustomerORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
    )
    name: Mapped[str] = mapped_column(String(MAX_DISPLAY_NAME_LENGTH))
    contact_name: Mapped[str | None] = mapped_column(String(MAX_NAME_LENGTH))
    contact_phone: Mapped[str | None] = mapped_column(String(PHONE_LENGTH))
    contact_address: Mapped[str | None] = mapped_column(String(MAX_ADDRESS_LENGTH))
    is_blocked: Mapped[bool] = mapped_column(default=False)
