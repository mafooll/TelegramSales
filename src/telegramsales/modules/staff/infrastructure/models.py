from typing import final

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from telegramsales.modules.staff.domain.enums import StaffRole
from telegramsales.shared.infrastructure.database.base import BaseORM
from telegramsales.shared.infrastructure.database.mixins import WithCreatedAtMixin
from telegramsales.shared.infrastructure.database.types import enum_check

ROLE_LENGTH = 16


@final
class StaffMemberORM(WithCreatedAtMixin, BaseORM):
    __tablename__ = "staff_members"
    __table_args__ = (enum_check("role", StaffRole, name="known_role"),)

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=False,
    )
    role: Mapped[str] = mapped_column(String(ROLE_LENGTH))
    is_active: Mapped[bool] = mapped_column(default=True)
    customer_view: Mapped[bool] = mapped_column(default=False)
