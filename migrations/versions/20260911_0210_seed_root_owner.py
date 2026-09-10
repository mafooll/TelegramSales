"""seed root owner

Revision ID: b3c8d5e91af2
Revises: 6f2a91c7d4e0
Create Date: 2026-09-11 02:10:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from telegramsales.shared.settings import AppSettings

revision: str = "b3c8d5e91af2"
down_revision: str | Sequence[str] | None = "6f2a91c7d4e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ROOT_ROLE = "owner"


def upgrade() -> None:
    op.execute(
        sa.text(
            "insert into staff_members (id, role, is_active) "
            "values (:root_id, :role, true) "
            "on conflict (id) do nothing"
        ).bindparams(root_id=AppSettings().root_id, role=ROOT_ROLE)
    )


def downgrade() -> None:
    op.execute(
        sa.text("delete from staff_members where id = :root_id").bindparams(
            root_id=AppSettings().root_id
        )
    )
