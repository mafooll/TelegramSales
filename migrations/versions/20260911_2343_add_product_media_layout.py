"""add product media layout

Revision ID: 5fe356cda1ae
Revises: 23b6d70c6b0d
Create Date: 2026-09-11 23:43:26.573805

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = '5fe356cda1ae'
down_revision: str | Sequence[str] | None = '23b6d70c6b0d'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


LAYOUTS = "media_layout IN ('collage', 'slideshow')"


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "media_layout",
            sa.String(length=10),
            server_default="collage",
            nullable=False,
        ),
    )
    op.create_check_constraint("known_layout", "products", LAYOUTS)


def downgrade() -> None:
    op.drop_constraint(op.f("ck_products_known_layout"), "products", type_="check")
    op.drop_column("products", "media_layout")
