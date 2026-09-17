"""add staff members table

Revision ID: 6f2a91c7d4e0
Revises:
Create Date: 2026-09-11 01:55:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "6f2a91c7d4e0"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "staff_members",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('owner', 'manager')",
            name=op.f("ck_staff_members_known_role"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_staff_members")),
    )


def downgrade() -> None:
    op.drop_table("staff_members")
