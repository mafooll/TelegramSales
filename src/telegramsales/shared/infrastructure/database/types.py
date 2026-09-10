from enum import StrEnum

from sqlalchemy import CheckConstraint


def enum_check(
    column: str, enum_type: type[StrEnum], *, name: str
) -> CheckConstraint:
    allowed = ", ".join(f"'{member.value}'" for member in enum_type)
    return CheckConstraint(f"{column} IN ({allowed})", name=name)
